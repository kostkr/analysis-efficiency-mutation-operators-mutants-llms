"""
demo_generate_llm.py
====================
Generate LLM mutants for a list of Defects4J bugs and save them to the demo
workspace as ``{model}.json``.

This module is intentionally used as a lower-level runner by ``run_pipeline.py``
so the top-level pipeline file can stay focused on configuration only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
import sys

sys.path.insert(0, str(Path(__file__).parent))

from defect4j import Defects4J
from defect4j.generators import LLMConfig, LLMPipeline
from defect4j.generators.llm.generator import model_stem

SEP = "━" * 64


@dataclass
class LLMGenerationConfig:
    container_name: str
    container_workspace: str
    workspace: Path
    bug_ids_by_project: dict[str, list[int]]
    llm_config: LLMConfig


def _log(msg: str) -> None:
    print(msg, flush=True)


def validate_config(config: LLMGenerationConfig) -> list[tuple[str, int]]:
    if int(config.llm_config.timeout_s) < 1:
        raise ValueError("config.llm_config.timeout_s must be >= 1")

    plan: list[tuple[str, int]] = []
    for raw_project, raw_bug_ids in config.bug_ids_by_project.items():
        project = str(raw_project).strip()
        if not project:
            raise ValueError("Each bug_ids_by_project key must be a non-empty project name")
        for raw_bug_id in raw_bug_ids:
            bug_id = int(raw_bug_id)
            if bug_id < 1:
                raise ValueError(f"Bug id must be >= 1 for project {project!r}, got {bug_id}")
            plan.append((project, bug_id))

    if not plan:
        raise ValueError("config.bug_ids_by_project must contain at least one bug")
    return plan


def main(config: LLMGenerationConfig) -> int:
    plan = validate_config(config)
    d4j = Defects4J(container=config.container_name, workspace=config.container_workspace)
    if not d4j.is_running():
        _log(f"ERROR: Container '{config.container_name}' is not running.")
        _log(f"  Start it with:  podman start -ai {config.container_name}")
        return 1

    _log(SEP)
    _log("LLM MUTANT GENERATOR")
    _log(SEP)
    _log(f"  Container     : {config.container_name}")
    _log(f"  Workspace     : {config.workspace}")
    _log(f"  Model         : {config.llm_config.model}")
    _log(f"  Output name   : {model_stem(config.llm_config.output_name or config.llm_config.model)}")
    _log(f"  Endpoint      : {config.llm_config.endpoint}")
    _log(f"  Timeout       : {config.llm_config.timeout_s}s per method")
    _log("  Mutants/method: selective prompt-guided generation")
    _log("  Scope         : only fixed-version methods overlapping buggy diff")
    _log("  Ollama load   : sequential single request")
    _log("  Thinking      : disabled (think=false)")
    _log("  Response mode : stream=true")
    _log("  Passes/method : exactly one")
    _log("  Bug order     : sequential")
    _log("  Save mode     : streaming (mutants persisted immediately)")
    _log(f"  Bugs          : {plan}")
    _log("")

    results: list[tuple[str, int, int, Path]] = []
    for project, bug_id in plan:
        bug_key = f"{project.upper()}_{bug_id}"
        t0 = time.perf_counter()
        _log(f"→ START {bug_key}")
        worker_d4j = Defects4J(container=config.container_name, workspace=config.container_workspace)
        pipeline = LLMPipeline(
            d4j=worker_d4j,
            workspace=config.workspace,
            config=config.llm_config,
            verbose=True,
        )
        try:
            bank = pipeline.run(project, bug_id)
        except Exception as exc:
            elapsed = round(time.perf_counter() - t0, 1)
            _log(f"✗ ERROR {bug_key}  {type(exc).__name__}: {exc}  time={elapsed}s")
            out_path = config.workspace / f"{project.upper()}_{bug_id}" / "mutants" / (
                model_stem(config.llm_config.output_name or config.llm_config.model) + ".json"
            )
            results.append((project, bug_id, 0, out_path))
            continue
        out_path = config.workspace / f"{project.upper()}_{bug_id}" / "mutants" / (
            model_stem(config.llm_config.output_name or config.llm_config.model) + ".json"
        )
        elapsed = round(time.perf_counter() - t0, 1)
        _log(f"✓ DONE  {bug_key}  mutants={len(bank)}  time={elapsed}s")
        results.append((project, bug_id, len(bank), out_path))

    results.sort(key=lambda item: (item[0], item[1]))
    _log(SEP)
    _log("SUMMARY")
    _log(SEP)
    total = 0
    for project, bug_id, count, path in results:
        key = f"{project.upper()}_{bug_id}"
        status = "✓" if count > 0 else "✗ (0 mutants)"
        rel = path.relative_to(config.workspace.parent)
        _log(f"  {status}  {key:12s}  {count:4d} mutants  →  {rel}")
        total += count
    _log("")
    _log(f"  Total mutants generated: {total}")
    _log(f"  Workspace: {config.workspace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(
        "demo_generate_llm.py no longer contains embedded runtime settings. "
        "Import it from Python and pass LLMGenerationConfig, or use run_pipeline.py."
    )









