"""
demo_pipeline.py
================
Real collection-only runner for Defects4J.

How it works
------------
You work with the local folder:
    notebooks/demo_collection_workspace/

The running container is mounted to a different host workspace. This script:
1. reads your local `BUG/mutants/*.json`
2. copies those selected bug inputs into the real mounted workspace
3. runs Defects4J inside the container
4. copies `meta.json` and `results/` back into `notebooks/demo_collection_workspace`

So after running:
- your local `mutans/` stays untouched
- your local `meta.json` is updated
- your local `results/` is rewritten with fresh data

No metrics are computed here.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from defect4j import Defects4J, MutantBank, Storage, DataCollector

SEP = "━" * 64
LOCAL_WORKSPACE = Path(__file__).parent / "demo_collection_workspace"
LOCAL_RESULTS_ROOT = LOCAL_WORKSPACE   # bug dirs live directly under demo_collection_workspace/
CONTAINER_NAME = "defects4j-container"
CONTAINER_WORKSPACE = "/workspace"
TEST_TIMEOUT_S = 600

PROJECT_IDENTIFIERS = [
    "Chart",
    "Cli",
    "Closure",
    "Codec",
    "Collections",
    "Compress",
    "Csv",
    "Gson",
    "JacksonCore",
    "JacksonDatabind",
    "JacksonXml",
    "Jsoup",
    "JxPath",
    "Lang",
    "Math",
    "Mockito",
    "Time",
]

BUG_IDS_BY_PROJECT: dict[str, list[int]] = {
    "Lang": [1, 3],
}


def validate_projects() -> None:
    unknown = [p for p in BUG_IDS_BY_PROJECT if p not in PROJECT_IDENTIFIERS]
    if unknown:
        raise ValueError(
            f"Unknown project identifiers: {unknown}. "
            f"Allowed values: {PROJECT_IDENTIFIERS}"
        )


def iter_bug_plan() -> list[tuple[str, int]]:
    plan: list[tuple[str, int]] = []
    for project in PROJECT_IDENTIFIERS:
        for bug_id in BUG_IDS_BY_PROJECT.get(project, []):
            plan.append((project, int(bug_id)))
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


def print_intro(plan: list[tuple[str, int]]) -> None:
    print(SEP)
    print("REAL DEFECTS4J COLLECTION PIPELINE")
    print(SEP)
    print(f"Container    : {CONTAINER_NAME}")
    print(f"Workspace    : {LOCAL_WORKSPACE}")
    print(f"Bug plan     : {plan}")


def print_bug_summary(local_storage: Storage, project: str, bug_id: int) -> None:
    bug_key = f"{project.upper()}_{bug_id}"
    print(f"\n{SEP}\nRESULT SUMMARY FOR {bug_key}\n{SEP}")

    meta_path = local_storage.meta_path(project, bug_id)
    if meta_path.exists():
        print("meta.json:")
        print(meta_path.read_text(encoding="utf-8"))

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
    validate_projects()
    plan = iter_bug_plan()

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
            print(f"  {path.relative_to(LOCAL_WORKSPACE)}")

        sync_bug_inputs(local_storage, runtime_storage, project, bug_id)
        runtime_storage.clear_results(project, bug_id)

        total_records = 0
        for mutant_file in runtime_storage.mutant_files(project, bug_id):
            bank = MutantBank(mutant_file).load()
            total_records += collector.collect_bug(project, bug_id, bank, test_timeout=TEST_TIMEOUT_S)

        sync_bug_outputs_back(local_storage, runtime_storage, project, bug_id)

        print(f"Total result records written for {bug_key}: {total_records}")
        print_bug_summary(local_storage, project, bug_id)

    print(f"\n{SEP}\nLOCAL SUMMARY\n{SEP}")
    print(local_storage.summary())
    print(f"\nLocal workspace updated at: {LOCAL_WORKSPACE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
