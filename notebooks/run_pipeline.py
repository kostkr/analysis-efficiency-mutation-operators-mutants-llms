from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

import demo_generate_classic as classic
import demo_generate_llm as llm
import demo_pipeline as collect
from bug_id_lists import BUG_IDS_BY_PROJECT
from defect4j.generators import PITConfig, LLMConfig

WORKSPACE = Path(__file__).parent / "demo_collection_workspace"
CONTAINER_NAME = "defects4j-container"
CONTAINER_WORKSPACE = "/workspace"

BATCH_SIZE = 10


def _flatten_bug_refs(bug_ids_by_project: dict[str, list[int]]) -> list[tuple[str, int]]:
    refs: list[tuple[str, int]] = []
    for project, bug_ids in bug_ids_by_project.items():
        refs.extend((project, bug_id) for bug_id in bug_ids)
    return refs


def _build_bug_id_batches(
    bug_ids_by_project: dict[str, list[int]],
) -> list[dict[str, list[int]]]:
    refs = _flatten_bug_refs(bug_ids_by_project)
    batches: list[dict[str, list[int]]] = []
    for offset in range(0, len(refs), BATCH_SIZE):
        chunk = refs[offset:offset + BATCH_SIZE]
        batch: dict[str, list[int]] = {}
        for project, bug_id in chunk:
            batch.setdefault(project, []).append(bug_id)
        batches.append(batch)
    return batches

BUG_ID_BATCHES = _build_bug_id_batches(BUG_IDS_BY_PROJECT)

RUN_CLASSIC_GENERATION = True
RUN_LLM_QWEN3_6_Q6 = True
RUN_LLM_GEMMA4_26B_Q6 = True
RUN_COLLECTION = True


# ── Classic generation ────────────────────────────────────────────
PIT_BUG_WORKERS = 10
PIT_CLASS_WORKERS = 1
PIT_CONFIG = PITConfig(
    timeout_s=600,
    mutators="ALL",
)


# ── LLM generation ────────────────────────────────────────────
LLM_MODEL_PRESETS = {
    "qwen3.6_35b_q6": {
        "model": "batiai/qwen3.6-35b:q6",
        "output_name": "qwen3.6_35b-q6",
    },
    "gemma4_26b_q6": {
        "model": "batiai/gemma4-26b:q6",
        "output_name": "gemma4_26b-q6",
    },
}

LLM_TIMEOUT_S = 1800
LLM_KEEP_ALIVE = "1m"

def _enabled_llm_configs() -> list[LLMConfig]:
    enabled: list[LLMConfig] = []
    llm_run_flags = [
        (RUN_LLM_QWEN3_6_Q6, "qwen3.6_35b_q6"),
        (RUN_LLM_GEMMA4_26B_Q6, "gemma4_26b_q6"),
    ]
    for is_enabled, preset_key in llm_run_flags:
        if not is_enabled:
            continue
        preset = LLM_MODEL_PRESETS[preset_key]
        enabled.append(LLMConfig(
            model=str(preset["model"]),
            output_name=str(preset["output_name"]),
            endpoint="http://127.0.0.1:11434/api/generate",
            timeout_s=LLM_TIMEOUT_S,
            keep_alive=LLM_KEEP_ALIVE,
        ))
    return enabled


# ── Mutant execution pipeline ──────────────────────────────────────────────
COLLECT_TEST_TIMEOUT_S = 2700
COLLECT_MAX_WORKERS = 14


def main() -> int:
    total_batches = len(BUG_ID_BATCHES)
    for batch_number, bug_ids_by_project in enumerate(BUG_ID_BATCHES, start=1):
        print(
            f"\n=== Running batch {batch_number}/{total_batches}: {bug_ids_by_project} ===",
            flush=True,
        )

        if RUN_CLASSIC_GENERATION:
            rc = classic.main(classic.ClassicGenerationConfig(
                container_name=CONTAINER_NAME,
                container_workspace=CONTAINER_WORKSPACE,
                workspace=WORKSPACE,
                bug_workers=PIT_BUG_WORKERS,
                class_workers=PIT_CLASS_WORKERS,
                bug_ids_by_project=bug_ids_by_project,
                pit_config=PIT_CONFIG,
            ))
            if rc != 0:
                return int(rc)

        for llm_config in _enabled_llm_configs():
            rc = llm.main(llm.LLMGenerationConfig(
                container_name=CONTAINER_NAME,
                container_workspace=CONTAINER_WORKSPACE,
                workspace=WORKSPACE,
                bug_ids_by_project=bug_ids_by_project,
                llm_config=llm_config,
            ))
            if rc != 0:
                return int(rc)

        if RUN_COLLECTION:
            rc = collect.main(collect.CollectionConfig(
                bug_ids_by_project=bug_ids_by_project,
                test_timeout_s=COLLECT_TEST_TIMEOUT_S,
                collect_max_workers=COLLECT_MAX_WORKERS,
                container_name=CONTAINER_NAME,
                container_workspace=CONTAINER_WORKSPACE,
                local_workspace=WORKSPACE,
            ))
            if rc != 0:
                return int(rc)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
