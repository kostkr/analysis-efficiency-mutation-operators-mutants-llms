"""
storage.py — Simple host-side storage for the collection phase.

Layout
------
workspace/
  LANG_1/
    mutants/
      gpt-5-mini.json
      classic.json
    meta.json
    results/
      gpt-5-mini.json
      classic.json

Rules
-----
- `mutants/` contains INPUT files created before the run and is never deleted.
- `results/` contains OUTPUT files and is fully rewritten for each bug run.
- `meta.json` stores bug-level metadata and run statistics.
- Nothing persistent is stored inside the container.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


class Storage:
    """Host-side directory manager for collection-only runs."""

    def __init__(self, workspace: Path | str = Path("workspace")):
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    #  Paths                                                               #
    # ------------------------------------------------------------------ #
    def _bug_dir_path(self, project: str, bug_id: int) -> Path:
        return self.workspace / f"{project.upper()}_{bug_id}"

    def bug_dir(self, project: str, bug_id: int) -> Path:
        d = self._bug_dir_path(project, bug_id)
        d.mkdir(parents=True, exist_ok=True)
        (d / "mutants").mkdir(exist_ok=True)
        (d / "results").mkdir(exist_ok=True)
        self.ensure_meta(project, bug_id)
        return d

    def mutants_dir_path(self, project: str, bug_id: int) -> Path:
        return self._bug_dir_path(project, bug_id) / "mutants"

    def results_dir_path(self, project: str, bug_id: int) -> Path:
        return self._bug_dir_path(project, bug_id) / "results"

    def mutants_dir(self, project: str, bug_id: int) -> Path:
        d = self.bug_dir(project, bug_id) / "mutants"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def results_dir(self, project: str, bug_id: int) -> Path:
        d = self.bug_dir(project, bug_id) / "results"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def meta_path(self, project: str, bug_id: int) -> Path:
        return self.bug_dir(project, bug_id) / "meta.json"

    # ------------------------------------------------------------------ #
    #  Metadata                                                            #
    # ------------------------------------------------------------------ #
    def ensure_meta(self, project: str, bug_id: int) -> None:
        p = self.workspace / f"{project.upper()}_{bug_id}" / "meta.json"
        if p.exists():
            return
        p.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_text(
            p,
            json.dumps(
                {
                    "project": project,
                    "bug_id": int(bug_id),
                    "created_at": _now(),
                },
                indent=2,
                ensure_ascii=False,
            ),
        )

    def read_meta(self, project: str, bug_id: int) -> dict:
        self.ensure_meta(project, bug_id)
        return json.loads(self.meta_path(project, bug_id).read_text(encoding="utf-8"))

    def update_meta(
        self,
        project: str,
        bug_id: int,
        total_tests: int | None = None,
        all_tests: list[str] | None = None,
        suite_profile: dict | None = None,
        bug_profile: dict | None = None,
    ) -> dict:
        """
        Recompute and persist bug-level summary statistics.

        Each result file is read exactly once.
        ``created_at`` is updated on every run (serves as last-updated timestamp).
        When provided, ``suite_profile`` and ``bug_profile`` become the authoritative
        baseline used for later mutant-vs-bug comparisons.

        Legacy ``total_tests`` / ``all_tests`` inputs are accepted for backward
        compatibility, but the persisted metadata keeps suite data only inside
        ``suite_profile`` to avoid duplicated storage.
        """
        meta = self.read_meta(project, bug_id)
        mutant_paths = self.mutant_files(project, bug_id)
        mutant_files = [p.name for p in mutant_paths]

        by_set_inputs: dict[str, list[dict]] = {}
        for path in mutant_paths:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                by_set_inputs[path.stem] = payload

        # ── load every result file exactly once ───────────────────────────
        results_root = self.results_dir(project, bug_id)
        by_set_records: dict[str, list[dict]] = {}
        for path in sorted(results_root.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                by_set_records[path.stem] = payload

        by_set: dict[str, dict] = {}
        for set_name in sorted(set(by_set_inputs) | set(by_set_records)):
            summary = self._summarize_records(by_set_records.get(set_name, []))
            summary.update(self._summarize_mutant_inputs(by_set_inputs.get(set_name, [])))
            by_set[set_name] = summary
        totals = self._merge_set_summaries(by_set.values())

        normalized_suite = self._normalize_suite_profile(
            suite_profile
            or meta.get("suite_profile")
            or self._legacy_suite_profile(total_tests=total_tests, all_tests=all_tests)
        )
        normalized_bug = self._normalize_bug_profile(bug_profile or meta.get("bug_profile"))

        meta = {
            "project": project,
            "bug_id": int(bug_id),
            "created_at": _now(),
            "mutant_files": mutant_files,
            "totals": totals,
            "by_set": by_set,
        }
        if normalized_bug is not None:
            meta["bug_profile"] = normalized_bug
        if normalized_suite is not None:
            meta["suite_profile"] = normalized_suite
        # Remove legacy / removed keys if present in old meta files
        for key in (
            "all_tests",
            "total_tests",
            "trigger_tests",
            "trigger_test_count",
            "last_run_at",
            "result_files",
        ):
            meta.pop(key, None)

        _atomic_write_text(
            self.meta_path(project, bug_id),
            json.dumps(meta, indent=2, ensure_ascii=False),
        )
        return meta

    def _summarize_records(self, records: list[dict]) -> dict:
        """
        Compute bug/set-level counters in a single O(n) pass with O(1) memory.

        killed   = compiled + tests ran + at least one failing test
        survived = compiled + tests ran + no failing tests + not timed out
        (timed-out mutants are counted separately; they are neither killed nor survived)
        """
        total          = 0
        apply_failed   = 0
        compile_failed = 0
        compiled       = 0
        timed_out      = 0
        killed         = 0
        survived       = 0

        for r in records:
            total += 1
            c = r.get("compiled")
            if c is True:
                compiled += 1
                if r.get("timed_out"):
                    timed_out += 1
                elif r.get("failing_tests"):
                    killed += 1
                else:
                    survived += 1
            elif c is False:
                err = str(r.get("compile_error", ""))
                if err.startswith("apply_failed:"):
                    apply_failed += 1
                else:
                    compile_failed += 1

        return {
            "mutants":       total,
            "apply_failed":  apply_failed,
            "compiled":      compiled,
            "compile_failed": compile_failed,
            "timed_out":     timed_out,
            "killed":        killed,
            "survived":      survived,
        }

    def _summarize_mutant_inputs(self, records: list[dict]) -> dict:
        from .mutant import MutantBank

        if not records:
            return {
                "input_mutants": 0,
                "duplicate_mutants": 0,
                "unique_mutants": 0,
            }

        bank = MutantBank.from_dicts(records)
        bank.mark_duplicates()
        duplicate_mutants = bank.duplicate_count()
        input_mutants = len(bank)
        return {
            "input_mutants": input_mutants,
            "duplicate_mutants": duplicate_mutants,
            "unique_mutants": input_mutants - duplicate_mutants,
        }

    def _merge_set_summaries(self, summaries) -> dict:
        totals = {
            "input_mutants": 0,
            "duplicate_mutants": 0,
            "unique_mutants": 0,
            "mutants": 0,
            "apply_failed": 0,
            "compiled": 0,
            "compile_failed": 0,
            "timed_out": 0,
            "killed": 0,
            "survived": 0,
        }
        for summary in summaries:
            for key in totals:
                totals[key] += int(summary.get(key, 0) or 0)
        return totals

    def _legacy_suite_profile(
        self,
        total_tests: int | None,
        all_tests: list[str] | None,
    ) -> dict | None:
        if total_tests is None and not all_tests:
            return None
        normalized_all_tests = sorted(set(all_tests or []))
        relevant_test_classes: list[str] = []
        return {
            "mode": "relevant",
            "relevant_test_classes": relevant_test_classes,
            "class_count": len(relevant_test_classes),
            "all_tests": normalized_all_tests,
            "total_tests": max(int(total_tests or 0), len(normalized_all_tests)),
        }

    def _normalize_suite_profile(self, profile: dict | None) -> dict | None:
        if not isinstance(profile, dict) or not profile:
            return None
        all_tests = sorted(set(profile.get("all_tests", [])))
        relevant_classes = sorted(set(profile.get("relevant_test_classes", [])))
        return {
            "mode": str(profile.get("mode", "relevant") or "relevant"),
            "relevant_test_classes": relevant_classes,
            "class_count": max(int(profile.get("class_count", 0) or 0), len(relevant_classes)),
            "all_tests": all_tests,
            "total_tests": max(int(profile.get("total_tests", 0) or 0), len(all_tests)),
        }

    def _normalize_bug_profile(self, profile: dict | None) -> dict | None:
        if not isinstance(profile, dict) or not profile:
            return None
        failing_tests = sorted(set(profile.get("failing_tests", [])))
        return {"failing_tests": failing_tests}

    # ------------------------------------------------------------------ #
    #  Inputs                                                              #
    # ------------------------------------------------------------------ #
    def mutant_files(self, project: str, bug_id: int) -> list[Path]:
        """Return all mutant JSON files from `mutants/`, sorted by name."""
        root = self.mutants_dir_path(project, bug_id)
        if not root.exists():
            return []
        return sorted(p for p in root.glob("*.json") if p.is_file())

    # ------------------------------------------------------------------ #
    #  Outputs                                                             #
    # ------------------------------------------------------------------ #
    def clear_results(self, project: str, bug_id: int) -> None:
        """Delete only the bug output folder and recreate it. Inputs stay untouched."""
        d = self.bug_dir(project, bug_id) / "results"
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    def results_file_path(self, project: str, bug_id: int, mutant_set: str) -> Path:
        return self.results_dir(project, bug_id) / f"{mutant_set}.json"

    def write_result_set(self, project: str, bug_id: int, mutant_set: str, records: list[dict]) -> None:
        """Write one output JSON file for one mutant-set file."""
        p = self.results_file_path(project, bug_id, mutant_set)
        _atomic_write_text(p, json.dumps(records, indent=2, ensure_ascii=False))

    def load_results(self, project: str, bug_id: int, mutant_set: str | None = None) -> list[dict]:
        """Load all raw result records for one bug."""
        root = self.results_dir(project, bug_id)
        if not root.exists():
            return []
        records: list[dict] = []
        if mutant_set is None:
            files = sorted(root.glob("*.json"))
        else:
            files = [root / f"{mutant_set}.json"] if (root / f"{mutant_set}.json").exists() else []
        for path in files:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                records.extend(payload)
        return records

    def list_bugs(self) -> list[tuple[str, int]]:
        """Return all bug folders under result/."""
        bugs: list[tuple[str, int]] = []
        root = self.workspace
        if not root.exists():
            return bugs
        for d in sorted(root.iterdir()):
            if not d.is_dir():
                continue
            meta_path = d / "meta.json"
            if not meta_path.exists():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            bugs.append((meta["project"], int(meta["bug_id"])))
        return bugs

    def summary(self) -> str:
        lines = [f"Storage @ {self.workspace.resolve()}"]
        total_records = 0
        for project, bug_id in self.list_bugs():
            result_files = sorted(self.results_dir(project, bug_id).glob("*.json"))
            by_set: dict[str, int] = {}
            for path in result_files:
                payload = json.loads(path.read_text(encoding="utf-8"))
                count = len(payload) if isinstance(payload, list) else 1
                by_set[path.stem] = count
            total = sum(by_set.values())
            lines.append(
                f"  {project.upper()}_{bug_id}: {len(result_files)} result files, {total} records"
                + (f" ({', '.join(f'{k}={v}' for k, v in sorted(by_set.items()))})" if by_set else "")
            )
            total_records += total
        lines.append(f"  Total records: {total_records}")
        return "\n".join(lines)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")


def _atomic_write_text(path: Path, payload: str) -> None:
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(path)

