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
- mutants marked with `dublicate=true` are skipped during execution
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING

from .container import ParallelCheckoutPool

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

    def collect_bug(
        self,
        project: str,
        bug_id: int,
        bank: "MutantBank",
        test_timeout: int = 600,
        max_workers: int = 1,
    ) -> int:
        """
        Process one mutant bank for one bug.

        Mutants marked with ``dublicate=true`` are ignored and only counted in
        bug-level metadata.
        """
        mutant_set = bank.path.stem
        mutant_file = bank.path.name
        c_path = self._ensure_checkout(project, bug_id)
        bank.mark_duplicates()
        runnable_mutants = bank.non_duplicates()
        duplicate_count = len(bank) - len(runnable_mutants)

        self._log(
            f"\n{'=' * 64}\n"
            f"  {project}-{bug_id}  |  set={mutant_set}  |  mutants={len(bank)}  |  run={len(runnable_mutants)}  |  duplicates={duplicate_count}  |  workers={max(1, min(int(max_workers), len(runnable_mutants) or 1))}\n"
            f"{'=' * 64}"
        )

        workers = max(1, min(int(max_workers), len(runnable_mutants) or 1))
        if not runnable_mutants:
            records: list[dict] = []
            total_tests = 0
            all_tests: list[str] = []
        elif workers == 1:
            records, total_tests, all_tests = self._collect_sequential(
                mutants=runnable_mutants,
                bug_id=bug_id,
                container_path=c_path,
                mutant_set=mutant_set,
                test_timeout=test_timeout,
            )
        else:
            records, total_tests, all_tests = self._collect_parallel(
                project=project,
                bug_id=bug_id,
                mutants=runnable_mutants,
                mutant_set=mutant_set,
                test_timeout=test_timeout,
                workers=workers,
                base_container_path=c_path,
            )

        self.storage.write_result_set(project, bug_id, mutant_set, records)
        self.storage.update_meta(project, bug_id, total_tests=total_tests, all_tests=all_tests)
        self._log(f"  written  : {len(records)} result records → {mutant_file}  (duplicates skipped={duplicate_count})")
        return len(records)

    def _collect_sequential(
        self,
        mutants: list["Mutant"],
        bug_id: int,
        container_path: str,
        mutant_set: str,
        test_timeout: int,
    ) -> tuple[list[dict], int, list[str]]:
        records: list[dict] = []
        total_tests = 0
        all_tests: set[str] = set()
        for mutant in mutants:
            record, mutant_total_tests, mutant_all_tests = self._run_one(
                mutant=mutant,
                bug_id=bug_id,
                container_path=container_path,
                mutant_set=mutant_set,
                test_timeout=test_timeout,
            )
            records.append(record)
            total_tests = max(total_tests, mutant_total_tests)
            all_tests.update(mutant_all_tests)
        return records, total_tests, sorted(all_tests)

    def _collect_parallel(
        self,
        project: str,
        bug_id: int,
        mutants: list["Mutant"],
        mutant_set: str,
        test_timeout: int,
        workers: int,
        base_container_path: str,
    ) -> tuple[list[dict], int, list[str]]:
        records: list[dict | None] = [None] * len(mutants)
        total_tests = 0
        all_tests: set[str] = set()
        pool = self.d4j.parallel_checkouts(
            project=project,
            bug_id=bug_id,
            host_workspace=self.host_ws,
            max_workers=workers,
            version="f",
            base_container_path=base_container_path,
        )
        pool.prepare()

        try:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(
                        self._run_one_in_parallel_checkout,
                        pool,
                        mutant,
                        bug_id,
                        mutant_set,
                        test_timeout,
                    ): index
                    for index, mutant in enumerate(mutants)
                }

                for future in as_completed(futures):
                    index = futures[future]
                    record, mutant_total_tests, mutant_all_tests = future.result()
                    records[index] = record
                    total_tests = max(total_tests, mutant_total_tests)
                    all_tests.update(mutant_all_tests)
        finally:
            pool.cleanup()

        return [r for r in records if r is not None], total_tests, sorted(all_tests)

    def _ensure_checkout(self, project: str, bug_id: int) -> str:
        c_path = f"/tmp/defect4j-base/{project}_{bug_id}_f"
        out, _, rc = self.d4j.exec(
            f"test -d {c_path} && find {c_path} -mindepth 1 -maxdepth 1 | head -1"
        )
        if rc == 0 and out.strip():
            return c_path
        self._log("  checkout : running defects4j checkout…")
        self.d4j.checkout(project, bug_id, "f", dest=c_path, timeout=180)
        return c_path


    def _run_one_in_parallel_checkout(
        self,
        pool: ParallelCheckoutPool,
        mutant: "Mutant",
        bug_id: int,
        mutant_set: str,
        test_timeout: int,
    ) -> tuple[dict, int, list[str]]:
        checkout = pool.acquire()
        try:
            return self._run_one(
                mutant=mutant,
                bug_id=bug_id,
                container_path=checkout.container_path,
                mutant_set=mutant_set,
                test_timeout=test_timeout,
                worker_id=checkout.worker_id,
            )
        finally:
            pool.release(checkout)


    def _run_one(
        self,
        mutant: "Mutant",
        bug_id: int,
        container_path: str,
        mutant_set: str,
        test_timeout: int,
        worker_id: int | None = None,
    ) -> tuple[dict, int, list[str]]:
        status = [f"[{mutant.id}]", mutant_set]
        if worker_id is not None:
            status.append(f"worker={worker_id}")
        if mutant.rule:
            status.append(f'"{mutant.rule}"')

        record: dict = {
            "mutant_id":      mutant.id,
            "filepath":       mutant.filepath,
            "compiled":       None,
            "compile_error":  "",
            "run_time_s":     0,
            "timed_out":      False,
            "test_executed":  False,
            "failing_count":  0,
            "failing_tests":  [],
        }
        total_tests = 0
        all_tests: list[str] = []

        result = self.d4j.run_mutant_relevant(
            container_path=container_path,
            mutant=mutant,
            timeout=test_timeout,
        )
        record.update({k: v for k, v in result.items() if k in record})
        total_tests = int(result.get("total_tests", 0) or 0)
        all_tests = list(result.get("all_tests", []) or [])

        if record["compiled"] is False and str(record["compile_error"]).startswith("apply_failed:"):
            status.append("→ APPLY FAILED")
            self._log("  " + " ".join(status))
            return record, total_tests, all_tests

        if record["compiled"] is False:
            status.append(f"→ COMPILE FAIL ({record['run_time_s']}s)")
            self._log("  " + " ".join(status))
            return record, total_tests, all_tests

        if record["timed_out"]:
            status.append(f"→ TIMEOUT ({test_timeout}s)")
        else:
            killed = bool(record["failing_tests"])
            status.append(
                f"→ {'KILLED' if killed else 'SURVIVED'}"
                f"  failing={record['failing_count']}/{total_tests}"
                f" ({record['run_time_s']}s)"
            )
        self._log("  " + " ".join(status))

        return record, total_tests, all_tests

