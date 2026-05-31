"""
demo_pipeline.py
================
Real collection-only runner for Defects4J.

Edit only the small CONFIG block below:
- which bugs to run
- how many workers to use inside the container
- per-mutant test timeout

The rest of the container/runtime wiring stays fixed and is discovered
automatically.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from defect4j import Defects4J, MutantBank, Storage, DataCollector

SEP = "━" * 64

# ── Edit only this block ─────────────────────────────────────────────────────

@dataclass
class CollectionConfig:
    bug_ids_by_project: dict[str, list[int]]
    test_timeout_s: int
    collect_max_workers: int
    container_name: str
    container_workspace: str
    local_workspace: Path


def validate_config(config: CollectionConfig) -> list[tuple[str, int]]:
    plan: list[tuple[str, int]] = []
    for raw_project, raw_bug_ids in dict(config.bug_ids_by_project).items():
        project = str(raw_project).strip()
        if not project:
            raise ValueError("Each bug_ids_by_project entry must have a non-empty project name.")

        for raw_bug_id in raw_bug_ids:
            try:
                bug_id = int(raw_bug_id)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid bug id for project {project!r}: {raw_bug_id!r}") from exc

            if bug_id < 1:
                raise ValueError(f"Bug id must be >= 1 for project {project!r}, got {bug_id}.")

            plan.append((project, bug_id))

    if not plan:
        raise ValueError("config.bug_ids_by_project must contain at least one bug.")

    if int(config.test_timeout_s) < 1:
        raise ValueError("config.test_timeout_s must be >= 1.")

    if int(config.collect_max_workers) < 1:
        raise ValueError("config.collect_max_workers must be >= 1.")

    return plan


def prepare_local_mutant_bank(mutant_file: Path) -> tuple[MutantBank, int, int]:
    """Load one local mutant JSON once and compute duplicate counts in memory."""
    bank = MutantBank(mutant_file).load(quiet=True)
    duplicate_count = bank.duplicate_count()
    return bank, len(bank), duplicate_count


def print_intro(plan: list[tuple[str, int]], config: CollectionConfig) -> None:
    print(SEP)
    print("REAL DEFECTS4J COLLECTION PIPELINE")
    print(SEP)
    print(f"Container    : {config.container_name}")
    print(f"Workspace    : {config.local_workspace}")
    print("Storage mode : direct workspace access (no bind-mount discovery)")
    print(f"Workers      : {int(config.collect_max_workers)}")
    print(f"Timeout      : {int(config.test_timeout_s)}s")
    print("Profiles     : full relevant `defects4j test -r`")
    print("Optimisation : reuse worker build artifacts between successful mutants")
    print(f"Bug plan     : {plan}")


def print_bug_summary(local_storage: Storage, project: str, bug_id: int, local_workspace: Path) -> None:
    bug_key = f"{project.upper()}_{bug_id}"
    print(f"\n{SEP}\nRESULT SUMMARY FOR {bug_key}\n{SEP}")

    meta = local_storage.read_meta(project, bug_id)
    totals = meta.get("totals", {}) if isinstance(meta, dict) else {}
    suite_profile = meta.get("suite_profile", {}) if isinstance(meta, dict) else {}
    bug_profile = meta.get("bug_profile", {}) if isinstance(meta, dict) else {}
    if totals:
        print(
            "meta totals:"
            f" input={int(totals.get('input_mutants', 0) or 0)}"
            f" unique={int(totals.get('unique_mutants', 0) or 0)}"
            f" duplicates={int(totals.get('duplicate_mutants', 0) or 0)}"
            f" executed={int(totals.get('mutants', 0) or 0)}"
        )
    if suite_profile:
        suite_classes = suite_profile.get("relevant_test_classes", []) or []
        suite_tests = suite_profile.get("all_tests", []) or []
        print(
            "suite profile:"
            f" mode={suite_profile.get('mode', 'relevant')}"
            f" classes={int(suite_profile.get('class_count', len(suite_classes)) or 0)}"
            f" tests={int(suite_profile.get('total_tests', len(suite_tests)) or 0)}"
        )
    if bug_profile:
        failing_tests = bug_profile.get("failing_tests", []) or []
        print(
            "bug profile:"
            f" failing_tests={len(failing_tests)}"
        )

    output_files = sorted(local_storage.results_dir(project, bug_id).glob("*.json"))
    if not output_files:
        print("No output files were written.")
        return

    print("results files:")
    total_records = 0
    for path in output_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        count = len(payload) if isinstance(payload, list) else 1
        total_records += count
        print(f"  {path.relative_to(local_workspace)}  ({count} records)")
    print(f"Total records written: {total_records}")


def print_run_summary(local_storage: Storage, plan: list[tuple[str, int]]) -> None:
    print(f"\n{SEP}\nRUN SUMMARY\n{SEP}")
    print(f"Storage @ {local_storage.workspace.resolve()}")
    total_records = 0
    for project, bug_id in plan:
        result_files = sorted(local_storage.results_dir(project, bug_id).glob("*.json"))
        by_set: dict[str, int] = {}
        for path in result_files:
            payload = json.loads(path.read_text(encoding="utf-8"))
            count = len(payload) if isinstance(payload, list) else 1
            by_set[path.stem] = count
        total = sum(by_set.values())
        print(
            f"  {project.upper()}_{bug_id}: {len(result_files)} result files, {total} records"
            + (f" ({', '.join(f'{k}={v}' for k, v in sorted(by_set.items()))})" if by_set else "")
        )
        total_records += total
    print(f"  Total records: {total_records}")


def main(config: CollectionConfig) -> int:
    plan = validate_config(config)

    d4j = Defects4J(
        container=config.container_name,
        workspace=config.container_workspace,
        timeout_default=300,
    )
    d4j.assert_running()

    storage = Storage(config.local_workspace)
    collector = DataCollector(
        d4j,
        storage,
        host_ws=config.local_workspace,
        verbose=True,
    )

    print_intro(plan, config)

    for project, bug_id in plan:
        bug_key = f"{project.upper()}_{bug_id}"
        local_mutant_files = storage.mutant_files(project, bug_id)

        print(f"\n{SEP}\nPREPARING {bug_key}\n{SEP}")
        if not local_mutant_files:
            storage.begin_run(project, bug_id)
            storage.update_meta(project, bug_id)
            print(f"No mutant files found in {storage.mutants_dir_path(project, bug_id)}")
            continue

        print("Local mutant files:")
        banks: list[MutantBank] = []
        for path in local_mutant_files:
            bank, total_mutants, duplicate_mutants = prepare_local_mutant_bank(path)
            banks.append(bank)
            print(
                f"  {path.relative_to(config.local_workspace)}"
                f"  (mutants={total_mutants}, duplicates={duplicate_mutants})"
            )

        storage.begin_run(project, bug_id)

        total_records = collector.collect_bug_banks(
            project,
            bug_id,
            banks,
            test_timeout=config.test_timeout_s,
            max_workers=config.collect_max_workers,
        )

        print(f"Total result records written for {bug_key}: {total_records}")
        print_bug_summary(storage, project, bug_id, config.local_workspace)

    print_run_summary(storage, plan)
    print(f"\nLocal workspace updated at: {config.local_workspace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(
        "demo_pipeline.py no longer contains embedded runtime settings. "
        "Import it from Python and pass CollectionConfig, or use run_pipeline.py."
    )
