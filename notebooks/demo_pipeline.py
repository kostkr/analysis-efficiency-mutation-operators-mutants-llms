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

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from defect4j import Defects4J, MutantBank, Storage, DataCollector

SEP = "━" * 64
LOCAL_WORKSPACE = Path(__file__).parent / "demo_collection_workspace"
LOCAL_RESULTS_ROOT = LOCAL_WORKSPACE   # bug dirs live directly under demo_collection_workspace/

# ── Edit only this block ─────────────────────────────────────────────────────

BUGS: list[tuple[str, int]] = [
    ("Lang", 1),
    ("Lang", 3),
]

TEST_TIMEOUT_S = 600
COLLECT_MAX_WORKERS = 12

# ── Runtime defaults (normally no need to change) ────────────────────────────

CONTAINER_NAME = os.environ.get("D4J_CONTAINER", "defects4j-container")
CONTAINER_WORKSPACE = os.environ.get("D4J_CONTAINER_WORKSPACE", "/workspace")


def validate_config() -> list[tuple[str, int]]:
    plan: list[tuple[str, int]] = []
    for raw_project, raw_bug_id in BUGS:
        project = str(raw_project).strip()
        if not project:
            raise ValueError("Each BUGS entry must have a non-empty project name.")

        try:
            bug_id = int(raw_bug_id)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid bug id for project {project!r}: {raw_bug_id!r}") from exc

        if bug_id < 1:
            raise ValueError(f"Bug id must be >= 1 for project {project!r}, got {bug_id}.")

        plan.append((project, bug_id))

    if not plan:
        raise ValueError("BUGS must contain at least one (project, bug_id) entry.")

    if int(TEST_TIMEOUT_S) < 1:
        raise ValueError("TEST_TIMEOUT_S must be >= 1.")

    if int(COLLECT_MAX_WORKERS) < 1:
        raise ValueError("COLLECT_MAX_WORKERS must be >= 1.")

    return plan


def discover_runtime_workspace(container_name: str, container_workspace: str) -> Path:
    """Find the host path mounted into the container at /workspace."""
    cmd = [
        "podman", "inspect", container_name,
        "--format", "{{json .Mounts}}",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    mounts = json.loads(r.stdout.strip())
    for m in mounts:
        if m.get("Destination") == container_workspace:
            return Path(m["Source"])
    raise RuntimeError(
        f"Could not find a bind mount for {container_workspace!r} in container {container_name!r}."
    )


def sync_bug_inputs(local_storage: Storage, runtime_storage: Storage, project: str, bug_id: int) -> None:
    """Copy local mutants/*.json into the real runtime workspace for one bug."""
    src = local_storage.mutants_dir(project, bug_id)
    dst = runtime_storage.mutants_dir(project, bug_id)

    if not src.exists():
        return

    # Exact sync for input json files of this selected bug
    for old in dst.glob("*.json"):
        old.unlink()
    for path in sorted(src.glob("*.json")):
        shutil.copy2(path, dst / path.name)


def sync_bug_outputs_back(local_storage: Storage, runtime_storage: Storage, project: str, bug_id: int) -> None:
    """Copy updated meta.json and results/ back to the local workspace view."""
    local_storage.bug_dir(project, bug_id)
    runtime_storage.bug_dir(project, bug_id)

    src_meta = runtime_storage.meta_path(project, bug_id)
    if src_meta.exists():
        shutil.copy2(src_meta, local_storage.meta_path(project, bug_id))

    src_results = runtime_storage.results_dir(project, bug_id)
    dst_results = local_storage.results_dir(project, bug_id)
    if dst_results.exists():
        shutil.rmtree(dst_results)
    if src_results.exists():
        shutil.copytree(src_results, dst_results)
    else:
        dst_results.mkdir(parents=True, exist_ok=True)


def normalize_local_mutant_file(mutant_file: Path) -> tuple[int, int]:
    """Ensure the local mutant JSON contains up-to-date duplicate markers."""
    bank = MutantBank(mutant_file).load()
    duplicate_count = bank.duplicate_count()
    bank.save()
    return len(bank), duplicate_count


def print_intro(plan: list[tuple[str, int]]) -> None:
    print(SEP)
    print("REAL DEFECTS4J COLLECTION PIPELINE")
    print(SEP)
    print(f"Container    : {CONTAINER_NAME}")
    print(f"Workspace    : {LOCAL_WORKSPACE}")
    print(f"Workers      : {int(COLLECT_MAX_WORKERS)}")
    print(f"Timeout      : {int(TEST_TIMEOUT_S)}s")
    print(f"Bug plan     : {plan}")


def print_bug_summary(local_storage: Storage, project: str, bug_id: int) -> None:
    bug_key = f"{project.upper()}_{bug_id}"
    print(f"\n{SEP}\nRESULT SUMMARY FOR {bug_key}\n{SEP}")

    meta = local_storage.read_meta(project, bug_id)
    totals = meta.get("totals", {}) if isinstance(meta, dict) else {}
    if totals:
        print(
            "meta totals:"
            f" input={int(totals.get('input_mutants', 0) or 0)}"
            f" unique={int(totals.get('unique_mutants', 0) or 0)}"
            f" duplicates={int(totals.get('duplicate_mutants', 0) or 0)}"
            f" executed={int(totals.get('mutants', 0) or 0)}"
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
        print(f"  {path.relative_to(LOCAL_WORKSPACE)}  ({count} records)")
    print(f"Total records written: {total_records}")


def main() -> int:
    plan = validate_config()

    d4j = Defects4J(
        container=CONTAINER_NAME,
        workspace=CONTAINER_WORKSPACE,
        timeout_default=300,
    )
    d4j.assert_running()

    runtime_workspace = discover_runtime_workspace(CONTAINER_NAME, CONTAINER_WORKSPACE)
    local_storage = Storage(LOCAL_RESULTS_ROOT)
    runtime_storage = Storage(runtime_workspace)
    collector = DataCollector(d4j, runtime_storage, host_ws=runtime_workspace, verbose=True)

    print_intro(plan)

    for project, bug_id in plan:
        bug_key = f"{project.upper()}_{bug_id}"
        local_mutant_files = local_storage.mutant_files(project, bug_id)

        print(f"\n{SEP}\nPREPARING {bug_key}\n{SEP}")
        if not local_mutant_files:
            print(f"No mutant files found in {local_storage.mutants_dir(project, bug_id)}")
            continue

        print("Local mutant files:")
        for path in local_mutant_files:
            total_mutants, duplicate_mutants = normalize_local_mutant_file(path)
            print(
                f"  {path.relative_to(LOCAL_WORKSPACE)}"
                f"  (mutants={total_mutants}, duplicates={duplicate_mutants})"
            )

        sync_bug_inputs(local_storage, runtime_storage, project, bug_id)
        runtime_storage.clear_results(project, bug_id)

        total_records = 0
        for mutant_file in runtime_storage.mutant_files(project, bug_id):
            bank = MutantBank(mutant_file).load()
            total_records += collector.collect_bug(
                project,
                bug_id,
                bank,
                test_timeout=TEST_TIMEOUT_S,
                max_workers=COLLECT_MAX_WORKERS,
            )

        sync_bug_outputs_back(local_storage, runtime_storage, project, bug_id)

        print(f"Total result records written for {bug_key}: {total_records}")
        print_bug_summary(local_storage, project, bug_id)

    print(f"\n{SEP}\nLOCAL SUMMARY\n{SEP}")
    print(local_storage.summary())
    print(f"\nLocal workspace updated at: {LOCAL_WORKSPACE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
