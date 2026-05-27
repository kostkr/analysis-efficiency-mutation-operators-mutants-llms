"""pit/pipeline.py — end-to-end PIT mutant generation pipeline.

Scope policy
------------
The diff is used only to find which methods belong to the bug. Once such a
method is selected, **all** PIT mutations reported for that method are written
to ``classic.json``.

Performance notes
-----------------
- The project is compiled once per bug run, never per mutant.
- PIT is run once per class, not once per method and not once per mutant.
- Defects4J exports are cached inside :class:`PITGenerator` per checkout.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from pathlib import Path
from typing import TYPE_CHECKING

from ...mutant import mark_duplicate_mutants
from ..base import PITConfig, GeneratorJob
from ..source_finder import SourceFinder
from .generator import PITGenerator

if TYPE_CHECKING:
    from ...container import Defects4J
    from ...mutant import Mutant, MutantBank


class PITPipeline:
    """End-to-end PIT mutant generation pipeline for one Defects4J bug."""

    OUTPUT_FILE = "classic.json"

    def __init__(
        self,
        d4j: "Defects4J",
        workspace: Path | str,
        config: PITConfig | None = None,
        verbose: bool = True,
        max_workers: int = 1,
    ) -> None:
        self.d4j        = d4j
        self.workspace  = Path(workspace)
        self.config     = config or PITConfig()
        self.verbose    = verbose
        self.max_workers = max(1, int(max_workers))
        self._finder    = SourceFinder(d4j)
        self._generator = PITGenerator(self.config, d4j)

    # ------------------------------------------------------------------ #

    def run(self, project: str, bug_id: int) -> "MutantBank":
        """Run the full pipeline for *project*-*bug_id* and return the saved bank.

        Steps
        -----
        1. Checkout fixed version (skipped if already present in container)
        2. Find GeneratorJobs — one per method that overlaps the bug diff
        3. Compile the checkout once with ``defects4j compile``
        4. Run PIT once per class and keep all mutations PIT reported for each
           bug-related method
        5. Assign sequential IDs
        6. Save → ``workspace/{PROJECT}_{BUG_ID}/mutants/classic.json``
        """
        t_start = time.perf_counter()
        self._log(f"\n{'='*60}")
        self._log(f"  PITPipeline  {project}-{bug_id}")
        self._log(f"{'='*60}")

        c_path = self._ensure_checkout(project, bug_id, "f")
        b_path = self._ensure_checkout(project, bug_id, "b")

        jobs = self._finder.find_jobs(project, bug_id, c_path, container_path_buggy=b_path)
        self._log(f"  methods found : {len(jobs)}")
        for j in jobs:
            self._log(
                f"    • {j.method_name}  lines {j.method_start}-{j.method_end}"
                f"  bug_lines={j.changed_lines}"
            )

        if not jobs:
            self._log("  No bug-diff methods — nothing saved.")
            return self._empty_bank(project, bug_id)

        self._log("  d4j compile   : running defects4j compile…")
        if not self._d4j_compile(c_path):
            self._log("  ✗  defects4j compile failed — aborting.")
            return self._empty_bank(project, bug_id)
        self._log("  d4j compile   : OK")

        all_mutants = self._run_by_class(project, bug_id, c_path, jobs)
        saved_mutants = mark_duplicate_mutants(all_mutants)
        duplicate_count = sum(1 for m in saved_mutants if m.dublicate)

        self._log(f"  mutants raw   : {len(all_mutants)}")
        self._log(f"  duplicates    : {duplicate_count}")
        self._log(f"  mutants saved : {len(saved_mutants)}")

        for i, m in enumerate(saved_mutants, start=1):
            m.id = i

        out_path = self._out_path(project, bug_id)
        bank = self._save(saved_mutants, out_path)

        elapsed = round(time.perf_counter() - t_start, 1)
        self._log(f"  saved         : {len(saved_mutants)} mutants → {out_path}  ({elapsed}s)")
        return bank

    # ------------------------------------------------------------------ #
    #  Internals                                                           #
    # ------------------------------------------------------------------ #

    def _run_by_class(
        self,
        project: str,
        bug_id: int,
        base_container_path: str,
        jobs: list[GeneratorJob],
    ) -> list["Mutant"]:
        """Run PIT once per class, then keep all mutations for each selected method."""
        from itertools import groupby

        keyfn = lambda j: (j.class_fqn, j.container_path)
        class_groups = [
            ((fqn, container_path), list(class_jobs))
            for (fqn, container_path), class_jobs in groupby(sorted(jobs, key=keyfn), key=keyfn)
        ]
        if not class_groups:
            return []

        workers = min(self.max_workers, len(class_groups))
        if workers <= 1:
            all_mutants: list["Mutant"] = []
            for _, class_jobs in class_groups:
                all_mutants.extend(self._generate_for_class_group(class_jobs, base_container_path))
            return all_mutants

        pool = self.d4j.parallel_checkouts(
            project=project,
            bug_id=bug_id,
            host_workspace=self.workspace,
            max_workers=workers,
            version="f",
            base_container_path=base_container_path,
        )
        pool.prepare()

        ordered_results: list[list["Mutant"] | None] = [None] * len(class_groups)
        try:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(self._generate_for_class_group_in_checkout, pool, class_jobs): index
                    for index, (_, class_jobs) in enumerate(class_groups)
                }
                for future in as_completed(futures):
                    ordered_results[futures[future]] = future.result()
        finally:
            pool.cleanup()

        all_mutants: list["Mutant"] = []
        for chunk in ordered_results:
            if chunk:
                all_mutants.extend(chunk)
        return all_mutants

    def _generate_for_class_group_in_checkout(
        self,
        pool,
        class_jobs: list[GeneratorJob],
    ) -> list["Mutant"]:
        checkout = pool.acquire()
        try:
            return self._generate_for_class_group(class_jobs, checkout.container_path)
        finally:
            pool.release(checkout)

    def _generate_for_class_group(
        self,
        class_jobs: list[GeneratorJob],
        container_path: str,
    ) -> list["Mutant"]:
        class_jobs = list(class_jobs)
        first = class_jobs[0]
        fqn = first.class_fqn
        method_names = sorted({job.method_name for job in class_jobs if job.method_name})
        self._log(f"\n  class: {fqn}")

        wide_job = GeneratorJob(
            project=first.project,
            bug_id=first.bug_id,
            container_path=container_path,
            host_path=first.host_path,
            filepath=first.filepath,
            class_fqn=fqn,
            method_name=",".join(method_names),
            method_source="",
            method_start=1,
            method_end=999_999,
        )

        t0 = time.perf_counter()
        try:
            class_selected = self._generator.generate(wide_job)
        except Exception as exc:
            self._log(f"    class_error={type(exc).__name__}: {exc}")
            return []
        elapsed = round(time.perf_counter() - t0, 1)
        self._log(
            f"    methods={len(method_names)}  class_total={len(class_selected)}  runtime={elapsed}s"
        )

        if class_selected:
            per_mutant = round(elapsed / len(class_selected), 2)
            for m in class_selected:
                m.gen_time_s = per_mutant

        return class_selected

    def _d4j_compile(self, container_path: str) -> bool:
        """Compile once with ``defects4j compile`` — no mutant recompilation is done."""
        _, _, rc = self.d4j.exec(
            self._clean_compile_cmd(container_path),
            timeout=180,
        )
        return rc == 0

    def _ensure_checkout(self, project: str, bug_id: int, version: str) -> str:
        c_path = f"/tmp/defect4j-generate/{project}_{bug_id}_{version}"
        out, _, _ = self.d4j.exec(
            f'test -d "{c_path}" && ls -A "{c_path}" | head -1 && echo _EXISTS_'
        )
        if "_EXISTS_" in out:
            self._log(f"  checkout      : already exists ({c_path})")
            return c_path
        self._log("  checkout      : running defects4j checkout…")
        self.d4j.checkout(project, bug_id, version, dest=c_path, timeout=180)
        return c_path

    def _out_path(self, project: str, bug_id: int) -> Path:
        d = self.workspace / f"{project.upper()}_{bug_id}" / "mutants"
        d.mkdir(parents=True, exist_ok=True)
        return d / self.OUTPUT_FILE

    def _save(self, mutants: list["Mutant"], path: Path) -> "MutantBank":
        from ...mutant import MutantBank
        bank = MutantBank(path)
        bank.mutants = list(mutants)
        bank.save()
        return bank

    def _empty_bank(self, project: str, bug_id: int) -> "MutantBank":
        from ...mutant import MutantBank
        return MutantBank(self._out_path(project, bug_id))

    def _clean_compile_cmd(self, container_path: str) -> str:
        return (
            f"cd {container_path} && "
            f"git reset --hard -q >/dev/null 2>&1 || true && "
            f"rm -rf target/pit-reports target/pit-reports-* && "
            f"defects4j compile 2>&1"
        )

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg, flush=True)

