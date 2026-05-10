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
        self._profile_cache: dict[tuple[str, int], dict] = {}

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
        c_path = self._ensure_checkout(project, bug_id, version="f")
        profiles = self._ensure_profiles(project, bug_id, c_path, test_timeout)
        baseline_total_tests = len(profiles["suite_profile"].get("all_tests", []))
        bank.mark_duplicates()
        runnable_mutants = [mutant for mutant in bank if not mutant.dublicate]
        duplicate_count = len(bank) - len(runnable_mutants)

        self._log(
            f"\n{'=' * 64}\n"
            f"  {project}-{bug_id}  |  set={mutant_set}  |  mutants={len(bank)}  |  run={len(runnable_mutants)}  |  duplicates={duplicate_count}  |  workers={max(1, min(int(max_workers), len(runnable_mutants) or 1))}\n"
            f"{'=' * 64}"
        )

        workers = max(1, min(int(max_workers), len(runnable_mutants) or 1))
        if not runnable_mutants:
            records: list[dict] = []
        elif workers == 1:
            self._warm_checkout(c_path, test_timeout)
            records = self._collect_sequential(
                mutants=runnable_mutants,
                bug_id=bug_id,
                container_path=c_path,
                mutant_set=mutant_set,
                test_timeout=test_timeout,
                baseline_total_tests=baseline_total_tests,
            )
        else:
            records = self._collect_parallel(
                project=project,
                bug_id=bug_id,
                mutants=runnable_mutants,
                mutant_set=mutant_set,
                test_timeout=test_timeout,
                workers=workers,
                base_container_path=c_path,
                baseline_total_tests=baseline_total_tests,
            )

        self.storage.write_result_set(project, bug_id, mutant_set, records)
        self.storage.update_meta(
            project,
            bug_id,
            suite_profile=profiles["suite_profile"],
            bug_profile=profiles["bug_profile"],
        )
        self._log(f"  written  : {len(records)} result records → {mutant_file}  (duplicates skipped={duplicate_count})")
        return len(records)

    def _collect_sequential(
        self,
        mutants: list["Mutant"],
        bug_id: int,
        container_path: str,
        mutant_set: str,
        test_timeout: int,
        baseline_total_tests: int,
    ) -> list[dict]:
        records: list[dict] = []
        for mutant in mutants:
            record = self._run_one(
                mutant=mutant,
                bug_id=bug_id,
                container_path=container_path,
                mutant_set=mutant_set,
                test_timeout=test_timeout,
                baseline_total_tests=baseline_total_tests,
            )
            records.append(record)
        return records

    def _collect_parallel(
        self,
        project: str,
        bug_id: int,
        mutants: list["Mutant"],
        mutant_set: str,
        test_timeout: int,
        workers: int,
        base_container_path: str,
        baseline_total_tests: int,
    ) -> list[dict]:
        records: list[dict | None] = [None] * len(mutants)
        pool = self.d4j.parallel_checkouts(
            project=project,
            bug_id=bug_id,
            host_workspace=self.host_ws,
            max_workers=workers,
            version="f",
            base_container_path=base_container_path,
        )
        pool.prepare()
        self._warm_parallel_checkouts(pool, workers=workers, test_timeout=test_timeout)

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
                        baseline_total_tests,
                    ): index
                    for index, mutant in enumerate(mutants)
                }

                for future in as_completed(futures):
                    index = futures[future]
                    record = future.result()
                    records[index] = record
        finally:
            pool.cleanup()

        return [r for r in records if r is not None]

    def _warm_checkout(self, container_path: str, test_timeout: int) -> None:
        warm_time = self.d4j.warm_relevant_suite(container_path, timeout=test_timeout)
        self._log(f"  warmup   : checkout warmed in {warm_time}s")

    def _warm_parallel_checkouts(
        self,
        pool: ParallelCheckoutPool,
        workers: int,
        test_timeout: int,
    ) -> None:
        workspaces = pool.workspaces
        if not workspaces:
            return

        warm_times: list[float | None] = [None] * len(workspaces)
        with ThreadPoolExecutor(max_workers=min(workers, len(workspaces))) as executor:
            futures = {
                executor.submit(
                    self.d4j.warm_relevant_suite,
                    checkout.container_path,
                    test_timeout,
                ): index
                for index, checkout in enumerate(workspaces)
            }
            for future in as_completed(futures):
                warm_times[futures[future]] = future.result()

        completed = [t for t in warm_times if t is not None]
        if completed:
            avg = round(sum(completed) / len(completed), 2)
            self._log(
                f"  warmup   : {len(completed)} parallel checkouts warmed "
                f"(avg {avg}s, max {max(completed):.2f}s)"
            )

    def _ensure_checkout(self, project: str, bug_id: int, version: str = "f") -> str:
        c_path = f"/tmp/defect4j-base/{project}_{bug_id}_{version}"
        out, _, rc = self.d4j.exec(
            f"test -d {c_path} && find {c_path} -mindepth 1 -maxdepth 1 | head -1"
        )
        if rc == 0 and out.strip():
            self.d4j.reset_checkout(c_path)
            return c_path
        self._log("  checkout : running defects4j checkout…")
        self.d4j.checkout(project, bug_id, version, dest=c_path, timeout=180)
        self.d4j.reset_checkout(c_path)
        return c_path


    def _run_one_in_parallel_checkout(
        self,
        pool: ParallelCheckoutPool,
        mutant: "Mutant",
        bug_id: int,
        mutant_set: str,
        test_timeout: int,
        baseline_total_tests: int,
    ) -> dict:
        checkout = pool.acquire()
        try:
            return self._run_one(
                mutant=mutant,
                bug_id=bug_id,
                container_path=checkout.container_path,
                mutant_set=mutant_set,
                test_timeout=test_timeout,
                baseline_total_tests=baseline_total_tests,
                worker_id=checkout.worker_id,
            )
        finally:
            pool.release(checkout)

    def _ensure_profiles(
        self,
        project: str,
        bug_id: int,
        container_path: str,
        test_timeout: int,
    ) -> dict:
        key = (project.upper(), int(bug_id))
        cached = self._profile_cache.get(key)
        if cached is not None:
            return cached

        self._log("  profile  : verifying fixed clean suite and buggy bug profile under `defects4j test -r`…")
        suite_profile = self.d4j.relevant_test_profile(container_path, timeout=test_timeout)
        if suite_profile.get("failing_tests"):
            raise RuntimeError(
                f"Fixed checkout {project}-{bug_id} is not clean under defects4j test -r: "
                f"{suite_profile['failing_tests']}"
            )

        buggy_path = self._ensure_checkout(project, bug_id, version="b")
        buggy_profile = self.d4j.relevant_test_profile(buggy_path, timeout=test_timeout)
        actual_bug_failing = sorted(set(buggy_profile.get("failing_tests", [])))
        if not actual_bug_failing:
            raise RuntimeError(
                f"Buggy checkout {project}-{bug_id} produced no failing tests under defects4j test -r"
            )

        bug_tests = sorted(set(self.d4j.trigger_tests(container_path)))
        suite_tests = set(suite_profile.get("all_tests", []))
        buggy_suite_tests = set(buggy_profile.get("all_tests", []))
        missing_trigger_tests = sorted(set(bug_tests) - buggy_suite_tests)
        if missing_trigger_tests:
            raise RuntimeError(
                f"Trigger tests are missing from buggy `defects4j test -r` for {project}-{bug_id}: "
                f"{missing_trigger_tests}"
            )

        missing_trigger_failures = sorted(set(bug_tests) - set(actual_bug_failing))
        if missing_trigger_failures:
            raise RuntimeError(
                f"Trigger tests did not fail on buggy `defects4j test -r` for {project}-{bug_id}: "
                f"{missing_trigger_failures}"
            )

        failing_outside_suite = sorted(set(actual_bug_failing) - suite_tests)
        if failing_outside_suite:
            raise RuntimeError(
                f"Buggy failing tests are outside fixed-suite all_tests for {project}-{bug_id}: "
                f"{failing_outside_suite}"
            )

        bug_profile = {
            "failing_tests": actual_bug_failing,
        }
        suite_total_tests = len(suite_profile.get("all_tests", []))
        trigger_count = len(bug_tests)
        actual_bug_count = len(actual_bug_failing)
        extras = actual_bug_count - trigger_count
        self._log(
            f"  profile  : clean relevant suite={suite_total_tests} tests in {suite_profile['run_time_s']}s; "
            f"buggy failures={actual_bug_count} tests (trigger export={trigger_count}" 
            f"{', extra_buggy_failures=' + str(extras) if extras > 0 else ''})"
        )
        profiles = {
            "suite_profile": suite_profile,
            "bug_profile": bug_profile,
        }
        self._profile_cache[key] = profiles
        return profiles


    def _run_one(
        self,
        mutant: "Mutant",
        bug_id: int,
        container_path: str,
        mutant_set: str,
        test_timeout: int,
        baseline_total_tests: int,
        worker_id: int | None = None,
    ) -> dict:
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

        result = self.d4j.run_mutant_relevant(
            container_path=container_path,
            mutant=mutant,
            timeout=test_timeout,
        )
        record.update({k: v for k, v in result.items() if k in record})

        if record["compiled"] is False and str(record["compile_error"]).startswith("apply_failed:"):
            status.append("→ APPLY FAILED")
            self._log("  " + " ".join(status))
            return record

        if record["compiled"] is False:
            status.append(f"→ COMPILE FAIL ({record['run_time_s']}s)")
            self._log("  " + " ".join(status))
            return record

        if record["timed_out"]:
            status.append(f"→ TIMEOUT ({test_timeout}s)")
        else:
            killed = bool(record["failing_tests"])
            status.append(
                f"→ {'KILLED' if killed else 'SURVIVED'}"
                f"  failing={record['failing_count']}/{baseline_total_tests}"
                f" ({record['run_time_s']}s)"
            )
        self._log("  " + " ".join(status))

        return record

