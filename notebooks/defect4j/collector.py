"""
collector.py — Simple collection engine.

Purpose
-------
Run compile/test for mutants and save RAW results on the host filesystem.
No metrics are computed here.

Important behavior
------------------
- input mutant files live in `BUG_ID/mutants/` and are never deleted
- output result files live in `BUG_ID/results/` and can be fully rewritten
- the container is used only to execute compile/test commands
- every mutant-set input file produces one JSON output file with a list of records
- ALL mutants are run — deduplication is the responsibility of the mutant generator
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .container import Defects4J
    from .mutant import Mutant, MutantBank
    from .storage import Storage


class DataCollector:
    """Collection-only runner for one shared Defects4J execution environment."""

    def __init__(
        self,
        d4j: "Defects4J",
        storage: "Storage",
        host_ws: Path = Path("workspace"),
        verbose: bool = True,
    ):
        self.d4j = d4j
        self.storage = storage
        self.host_ws = Path(host_ws)
        self._log = print if verbose else lambda *a, **kw: None

    def collect_bug(self, project: str, bug_id: int, bank: "MutantBank", test_timeout: int = 600) -> int:
        """
        Process one mutant bank for one bug.

        Runs ALL mutants from the bank without any deduplication.
        Deduplication is the responsibility of the mutant generator.
        """
        mutant_set = bank.path.stem
        mutant_file = bank.path.name
        c_path = self._ensure_checkout(project, bug_id)
        h_path = self._host_path(project, bug_id)

        self._log(
            f"\n{'=' * 64}\n"
            f"  {project}-{bug_id}  |  set={mutant_set}  |  mutants={len(bank)}\n"
            f"{'=' * 64}"
        )

        records: list[dict] = []
        for mutant in bank:
            record = self._run_one(
                mutant=mutant,
                bug_id=bug_id,
                host_path=h_path,
                container_path=c_path,
                mutant_set=mutant_set,
                test_timeout=test_timeout,
            )
            records.append(record)

        self.storage.write_result_set(project, bug_id, mutant_set, records)
        self.storage.update_meta(project, bug_id)
        self._log(f"  written  : {len(records)} result records → {mutant_file}")
        return len(records)

    def _ensure_checkout(self, project: str, bug_id: int) -> str:
        c_path = f"{self.d4j.workspace}/checkouts/{project}_{bug_id}_f"
        h_path = self._host_path(project, bug_id)
        if h_path.exists() and any(h_path.iterdir()):
            return c_path
        self._log("  checkout : running defects4j checkout…")
        self.d4j.checkout(project, bug_id, "f", dest=c_path, timeout=180)
        return c_path

    def _host_path(self, project: str, bug_id: int) -> Path:
        return self.host_ws / "checkouts" / f"{project}_{bug_id}_f"


    def _run_one(
        self,
        mutant: "Mutant",
        bug_id: int,
        host_path: Path,
        container_path: str,
        mutant_set: str,
        test_timeout: int,
    ) -> dict:
        import time

        status = [f"[{mutant.id}]", mutant_set]
        if mutant.rule:
            status.append(f'"{mutant.rule}"')

        record: dict = {
            "mutant_id":      mutant.id,
            "filepath":       mutant.filepath,
            "compiled":       None,
            "compile_error":  "",
            "compile_time_s": 0,
            "run_time_s":     0,
            "timed_out":      False,
            "test_executed":  False,
            "failing_count":  0,
            "passing_count":  0,
            "failing_tests":  [],
            "passing_tests":  [],
        }

        ok, backup, apply_error = mutant.apply(host_path)
        if not ok:
            record["compiled"] = False
            record["compile_error"] = apply_error
            status.append("→ APPLY FAILED")
            self._log("  " + " ".join(status))
            return record

        try:
            t0 = time.perf_counter()
            compiled, err_msg = self.d4j.compile_result(container_path)
            record["compile_time_s"] = round(time.perf_counter() - t0, 2)
            record["compiled"] = compiled
            record["compile_error"] = err_msg

            if not compiled:
                status.append(f"→ COMPILE FAIL ({record['compile_time_s']}s)")
                self._log("  " + " ".join(status))
                return record

            try:
                t0 = time.perf_counter()
                # Use defects4j's built-in relevant-tests mode (-r):
                # D4J knows which test classes cover the modified source files.
                # This is far faster than the full suite while still exercising
                # the mutated class, and it correctly writes the all_tests file.
                failing, all_tests = self.d4j.test_full(
                    container_path, timeout=test_timeout, relevant=True
                )
                record["run_time_s"]    = round(time.perf_counter() - t0, 2)
                record["test_executed"] = True
                record["failing_count"] = len(failing)
                record["passing_count"] = len(all_tests) - len(failing)
                record["failing_tests"] = sorted(failing)
                record["passing_tests"] = sorted(all_tests - failing)
                killed = bool(failing)
                status.append(
                    f"→ {'KILLED' if killed else 'SURVIVED'}"
                    f"  failing={record['failing_count']}/{record['failing_count'] + record['passing_count']}"
                    f" ({record['compile_time_s']}s + {record['run_time_s']}s)"
                )
            except subprocess.TimeoutExpired:
                record["timed_out"]     = True
                record["run_time_s"]    = test_timeout
                record["test_executed"] = True
                status.append(f"→ TIMEOUT ({test_timeout}s)")

            self._log("  " + " ".join(status))
        finally:
            if backup is not None:
                mutant.restore(host_path, backup)

        return record

