"""
demo_generate_classic.py
========================
Generate classic (PIT) mutants for a list of Defects4J bugs and save them to
the demo workspace as ``classic.json``.

How it works
------------
For each bug in ``BUG_IDS_BY_PROJECT``:

  1. Checkout the fixed version inside the container (skipped if already present)
  2. Diff buggy vs fixed  →  find Java methods that overlap the bug changes
  3. Ensure the checkout is compiled with ``defects4j compile``
     (skipped if ``target/classes`` and ``target/tests`` already exist)
  4. Run the direct custom PIT generator once per class against the Defects4J classpath
  5. Save ALL PIT mutations reported for those matched methods
  6. Divide total PIT runtime equally across produced mutants (``gen_time_s``)
  7. Save:
     ``demo_collection_workspace/{PROJECT}_{ID}/mutants/classic.json``

Performance
-----------
- no per-mutant compilation is performed
- compilation happens at most once per bug checkout
- PIT runs once per class, not once per method and not once per mutant
- Defects4J exports are cached inside the generator

Configuration
-------------
Edit ``BUG_IDS_BY_PROJECT`` and ``PIT_CONFIG`` below before running.

Usage
-----
    python demo_generate_classic.py

Output example
--------------
    demo_collection_workspace/
        LANG_1/mutants/classic.json   ← X PIT mutants for matched bug methods
        LANG_3/mutants/classic.json   ← Y PIT mutants for matched bug methods
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from defect4j import Defects4J
from defect4j.generators import PITPipeline, PITConfig

# ── Settings you can change ──────────────────────────────────────────────────

@dataclass
class ClassicGenerationConfig:
    container_name: str
    container_workspace: str
    workspace: Path
    # Fixed worker layout for a 14-core machine.
    #
    # Why this is locked:
    # - Lang bugs usually mutate one modified class, so class-level parallelism adds
    #   little while increasing contention.
    # - The main speedup comes from running many independent bug jobs at once.
    # - 12 bug workers keeps the 14-core container busy while leaving headroom for
    #   the OS, Python coordination, and PIT/JVM overhead.
    bug_workers: int
    class_workers: int
    bug_ids_by_project: dict[str, list[int]]
    pit_config: PITConfig

SEP = "━" * 64
_PRINT_LOCK = threading.Lock()


def _log(msg: str) -> None:
    with _PRINT_LOCK:
        print(msg, flush=True)


def validate_config(config: ClassicGenerationConfig) -> list[tuple[str, int]]:
    if int(config.bug_workers) < 1:
        raise ValueError("config.bug_workers must be >= 1")
    if int(config.class_workers) < 1:
        raise ValueError("config.class_workers must be >= 1")
    if int(config.pit_config.timeout_s) < 1:
        raise ValueError("config.pit_config.timeout_s must be >= 1")

    plan: list[tuple[str, int]] = []
    for raw_project, raw_bug_ids in config.bug_ids_by_project.items():
        project = str(raw_project).strip()
        if not project:
            raise ValueError("Each bug_ids_by_project key must be a non-empty project name")
        for raw_bug_id in raw_bug_ids:
            try:
                bug_id = int(raw_bug_id)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid bug id for project {project!r}: {raw_bug_id!r}") from exc
            if bug_id < 1:
                raise ValueError(f"Bug id must be >= 1 for project {project!r}, got {bug_id}")
            plan.append((project, bug_id))

    if not plan:
        raise ValueError("config.bug_ids_by_project must contain at least one bug")

    return plan


def main(config: ClassicGenerationConfig) -> int:
    plan = validate_config(config)
    d4j = Defects4J(container=config.container_name, workspace=config.container_workspace)

    if not d4j.is_running():
        _log(f"ERROR: Container '{config.container_name}' is not running.")
        _log(f"  Start it with:  podman start -ai {config.container_name}")
        _log(f"  Or build+start: cd defect4j && docker-compose up -d")
        return 1

    bug_workers = min(int(config.bug_workers), len(plan) or 1)
    class_workers = int(config.class_workers)

    _log(SEP)
    _log("CLASSIC MUTANT GENERATOR  (PIT)")
    _log(SEP)
    _log(f"  Container : {config.container_name}")
    _log(f"  Workspace : {config.workspace}")
    _log(f"  Mutators  : {config.pit_config.mutators}")
    _log(f"  Timeout   : {config.pit_config.timeout_s}s per class")
    _log(f"  Bug jobs  : {bug_workers}")
    _log(f"  Class jobs: {class_workers}")
    _log("  Workers   : locked for 14-core host (bug-heavy parallelism)")
    _log(f"  Bugs      : {plan}")
    _log("")

    results: list[tuple[str, int, int, Path]] = []

    def run_one(project: str, bug_id: int) -> tuple[str, int, int, Path]:
        bug_key = f"{project.upper()}_{bug_id}"
        t0 = __import__("time").perf_counter()
        _log(f"→ START {bug_key}")
        worker_d4j = Defects4J(container=config.container_name, workspace=config.container_workspace)
        pipeline = PITPipeline(
            d4j=worker_d4j,
            workspace=config.workspace,
            config=config.pit_config,
            verbose=False,
            max_workers=class_workers,
        )
        bank = pipeline.run(project, bug_id)
        out_path = config.workspace / f"{project.upper()}_{bug_id}" / "mutants" / "classic.json"
        elapsed = round(__import__("time").perf_counter() - t0, 1)
        _log(f"✓ DONE  {bug_key}  mutants={len(bank)}  time={elapsed}s")
        return project, bug_id, len(bank), out_path

    with ThreadPoolExecutor(max_workers=bug_workers) as executor:
        futures = {
            executor.submit(run_one, project, bug_id): (project, bug_id)
            for project, bug_id in plan
        }
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda item: (item[0], item[1]))

    _log(SEP)
    _log("SUMMARY")
    _log(SEP)
    total = 0
    for project, bug_id, count, path in results:
        key    = f"{project.upper()}_{bug_id}"
        status = "✓" if count > 0 else "✗ (0 mutants)"
        rel    = path.relative_to(config.workspace.parent)
        _log(f"  {status}  {key:12s}  {count:4d} mutants  →  {rel}")
        total += count
    _log("")
    _log(f"  Total mutants generated: {total}")
    _log(f"  Workspace: {config.workspace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(
        "demo_generate_classic.py no longer contains embedded runtime settings. "
        "Import it from Python and pass ClassicGenerationConfig, or use run_pipeline.py."
    )
