"""llm/pipeline.py — end-to-end LLM mutant generation pipeline."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

from ..base import LLMConfig, GeneratorJob
from ..source_finder import SourceFinder
from ...mutant import mark_duplicate_mutants
from .generator import LLMGenerator

if TYPE_CHECKING:
    from ...container import Defects4J
    from ...mutant import Mutant, MutantBank

class LLMPipeline:
    """Generate LLM mutants for bug-diff methods and save them to workspace."""

    CHECKOUT_ROOT = "/tmp/defect4j-generate"

    def __init__(
        self,
        d4j: "Defects4J",
        workspace: Path | str,
        config: LLMConfig | None = None,
        verbose: bool = True,
    ) -> None:
        self.d4j = d4j
        self.workspace = Path(workspace)
        self.config = config or LLMConfig()
        self.verbose = verbose
        self._finder = SourceFinder(d4j)
        self._generator = LLMGenerator(self.config, logger=self._log)

    def run(self, project: str, bug_id: int) -> "MutantBank":
        t0 = time.perf_counter()
        self._log(f"\n{'=' * 60}")
        self._log(f"  LLMPipeline  {project}-{bug_id}  model={self.config.model}")
        self._log(f"{'=' * 60}")

        self._log("  checkout      : preparing fixed checkout")
        fixed_path = self._ensure_checkout(project, bug_id, "f")
        self._log("  checkout      : preparing buggy checkout")
        buggy_path = self._ensure_checkout(project, bug_id, "b")
        self._log("  source scan   : finding diff-overlapping methods")
        jobs = self._finder.find_jobs(project, bug_id, fixed_path, container_path_buggy=buggy_path)
        self._log(f"  methods found : {len(jobs)}")
        out_path = self._out_path(project, bug_id)
        if not jobs:
            self._log("  No bug-diff methods — saving empty mutant file.")
            return self._empty_bank(project, bug_id, out_path)

        for job in jobs:
            self._log(
                f"    • {job.method_name}  lines {job.method_start}-{job.method_end}"
                f"  bug_lines={job.changed_lines}"
            )

        bank = self._save([], out_path)
        self._log(f"  output file   : initialized {out_path}")
        self._log(f"  streaming     : method-complete saves → {out_path}")
        self._log("  request mode  : exactly one LLM call per method")
        mutants = self._run_jobs(jobs, bank)
        marked = mark_duplicate_mutants(bank.mutants)
        duplicate_count = sum(1 for mutant in marked if mutant.dublicate)
        for index, mutant in enumerate(marked, start=1):
            mutant.id = index
        bank = self._save(marked, out_path)
        elapsed = round(time.perf_counter() - t0, 1)
        self._log(f"  mutants raw   : {len(mutants)}")
        self._log(f"  duplicates    : {duplicate_count}")
        self._log(f"  mutants saved : {len(marked)}")
        self._log(f"  saved         : {len(marked)} mutants → {out_path}  ({elapsed}s)")
        return bank

    def _run_jobs(self, jobs: list[GeneratorJob], bank: "MutantBank") -> list["Mutant"]:
        jobs = list(jobs)
        if not jobs:
            return []
        seen_unique_signatures: set[tuple[str, int, str]] = set()
        flattened: list["Mutant"] = []
        total_jobs = len(jobs)
        for index, job in enumerate(jobs, start=1):
            self._log(
                f"  method start  : {index}/{total_jobs}  {job.method_name}  lines {job.method_start}-{job.method_end}  bug_lines={job.changed_lines}"
            )
            chunk = self._generate_job_once(job, bank, seen_unique_signatures)
            if chunk:
                flattened.extend(chunk)
        return flattened

    def _generate_job_once(
        self,
        job: GeneratorJob,
        bank: "MutantBank",
        seen_unique_signatures: set[tuple[str, int, str]],
    ) -> list["Mutant"]:
        method_lines = sum(1 for line in job.method_source.splitlines() if line.strip())
        if method_lines <= 0:
            self._log(f"  {job.method_name}: skipped=no non-empty source lines")
            return []
        self._log(
            f"  method plan   : {job.method_name}  source_lines={method_lines}  file={job.filepath}"
        )

        self._log(f"  method call   : {job.method_name}  prompt_mode=selective")
        t0 = time.perf_counter()
        collected = self._generator.generate_batch(job)
        elapsed = round(time.perf_counter() - t0, 1)
        if collected:
            saved_total, duplicate_count = self._persist_chunk(bank, collected, seen_unique_signatures)
            preview = "; ".join(
                f"line {mutant.line}: rule={mutant.rule} gen_time_s={mutant.gen_time_s} dublicate={str(mutant.dublicate).lower()} after={mutant.aftercode[:60]}"
                for mutant in collected[:3]
            )
            self._log(
                f"  method preview: {job.method_name}  {preview}"
            )
        else:
            saved_total = len(bank.mutants)
            duplicate_count = 0
        self._log(
            f"  method saved  : {job.method_name}  returned={len(collected)} saved_total={saved_total} chunk_duplicates={duplicate_count} runtime={elapsed}s"
        )
        return collected

    def _ensure_checkout(self, project: str, bug_id: int, version: str) -> str:
        c_path = f"{self.CHECKOUT_ROOT}/{project}_{bug_id}_{version}"
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
        stem = self._generator.model_stem()
        d = self.workspace / f"{project.upper()}_{bug_id}" / "mutants"
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{stem}.json"

    def _save(self, mutants: list["Mutant"], path: Path) -> "MutantBank":
        from ...mutant import MutantBank
        bank = MutantBank(path)
        bank.mutants = list(mutants)
        bank.save(quiet=True)
        return bank

    def _empty_bank(self, project: str, bug_id: int, out_path: Path | None = None) -> "MutantBank":
        from ...mutant import MutantBank
        path = out_path or self._out_path(project, bug_id)
        bank = MutantBank(path)
        bank.save(quiet=True)
        return bank

    def _persist_chunk(
        self,
        bank: "MutantBank",
        mutants: list["Mutant"],
        seen_unique_signatures: set[tuple[str, int, str]],
    ) -> tuple[int, int]:
        duplicate_count = 0
        for mutant in mutants:
            mutant_signature = mutant.signature()
            mutant.dublicate = (
                mutant_signature == mutant.original_signature()
                or mutant_signature in seen_unique_signatures
            )
            if mutant.dublicate:
                duplicate_count += 1
            if not mutant.dublicate:
                seen_unique_signatures.add(mutant_signature)
            mutant.id = len(bank.mutants) + 1
            bank.mutants.append(mutant)
        bank.save(quiet=True)
        self._log(
            f"  file update   : wrote {len(mutants)} mutant(s) to {bank.path.name}  total_now={len(bank.mutants)}"
        )
        return len(bank.mutants), duplicate_count

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg, flush=True)
