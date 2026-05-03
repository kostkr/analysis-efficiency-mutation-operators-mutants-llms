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
  4. Run PIT CLI once per class against the Defects4J classpath
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
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from defect4j import Defects4J
from defect4j.generators import PITPipeline, PITConfig

# ── Settings you can change ──────────────────────────────────────────────────

CONTAINER_NAME      = "defects4j-container"
CONTAINER_WORKSPACE = "/workspace"

WORKSPACE = Path(__file__).parent / "demo_collection_workspace"

# Fixed worker layout for a 14-core machine.
#
# Why this is locked:
# - Lang bugs usually mutate one modified class, so class-level parallelism adds
#   little while increasing contention.
# - The main speedup comes from running many independent bug jobs at once.
# - 12 bug workers keeps the 14-core container busy while leaving headroom for
#   the OS, Python coordination, and PIT/JVM overhead.
BUG_WORKERS = 6
CLASS_WORKERS = 1

# Bugs to generate mutants for.
# Keys must be valid Defects4J project identifiers.
BUG_IDS_BY_PROJECT: dict[str, list[int]] = {
    "Lang": [
        1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
    ],
}

PIT_CONFIG = PITConfig(
    timeout_s    = 600,          # seconds per PIT run (per mutated class)
    mutators     = "ALL",
    target_tests = "",          # empty → use defects4j export -p tests.relevant
    pit_version  = "1.17.0",
)

SEP = "━" * 64
_PRINT_LOCK = threading.Lock()


def _log(msg: str) -> None:
    with _PRINT_LOCK:
        print(msg, flush=True)


def _validate_workers() -> None:
    if int(BUG_WORKERS) < 1:
        raise ValueError("BUG_WORKERS must be >= 1")
    if int(CLASS_WORKERS) < 1:
        raise ValueError("CLASS_WORKERS must be >= 1")


def main() -> int:
    _validate_workers()
    d4j = Defects4J(container=CONTAINER_NAME, workspace=CONTAINER_WORKSPACE)

    if not d4j.is_running():
        _log(f"ERROR: Container '{CONTAINER_NAME}' is not running.")
        _log(f"  Start it with:  podman start -ai {CONTAINER_NAME}")
        _log(f"  Or build+start: cd defect4j && docker-compose up -d")
        return 1

    plan: list[tuple[str, int]] = [
        (project, bug_id)
        for project, ids in BUG_IDS_BY_PROJECT.items()
        for bug_id in ids
    ]
    bug_workers = min(int(BUG_WORKERS), len(plan) or 1)
    class_workers = int(CLASS_WORKERS)

    _log(SEP)
    _log("CLASSIC MUTANT GENERATOR  (PIT)")
    _log(SEP)
    _log(f"  Container : {CONTAINER_NAME}")
    _log(f"  Workspace : {WORKSPACE}")
    _log(f"  Mutators  : {PIT_CONFIG.mutators}")
    _log(f"  Timeout   : {PIT_CONFIG.timeout_s}s per class")
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
        worker_d4j = Defects4J(container=CONTAINER_NAME, workspace=CONTAINER_WORKSPACE)
        pipeline = PITPipeline(
            d4j=worker_d4j,
            workspace=WORKSPACE,
            config=PIT_CONFIG,
            verbose=False,
            max_workers=class_workers,
        )
        bank = pipeline.run(project, bug_id)
        out_path = WORKSPACE / f"{project.upper()}_{bug_id}" / "mutants" / "classic.json"
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
        rel    = path.relative_to(WORKSPACE.parent)
        _log(f"  {status}  {key:12s}  {count:4d} mutants  →  {rel}")
        total += count
    _log("")
    _log(f"  Total mutants generated: {total}")
    _log(f"  Workspace: {WORKSPACE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
