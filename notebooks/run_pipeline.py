from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

import demo_generate_classic as classic
import demo_generate_llm as llm
import demo_pipeline as collect
from defect4j.generators import PITConfig, LLMConfig

WORKSPACE = Path(__file__).parent / "demo_collection_workspace"
CONTAINER_NAME = "defects4j-container"
CONTAINER_WORKSPACE = "/workspace"

BUG_IDS_BY_PROJECT = {
    "Lang": [
        1, 3,
        # 4, 5, 6, 7,
        # 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
        # 19, 20, 21, 22, 23, 24,
        # 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
        # 41, 42, 43, 44, 45, 46, 47,
        # 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61,
        62, 63, 64, 65
    ]
}

RUN_CLASSIC_GENERATION = False
RUN_LLM_QWEN3_6_35B_A3B = False
RUN_LLM_GEMMA4_26B_A4B_Q4 = False
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
    "qwen3.6_35b_a3b": {
        "model": "qwen3.6:35b-a3b",
        "output_name": "qwen3.6_35b-a3b",
    },
    "gemma4_26b_a4b_q4": {
        "model": "gemma4:26b-a4b-it-q4_K_M",
        "output_name": "gemma4_26b-a4b-it-q4_K_M",
    },
}

LLM_TIMEOUT_S = 1800
LLM_KEEP_ALIVE = "1m"

def _enabled_llm_configs() -> list[LLMConfig]:
    enabled: list[LLMConfig] = []
    llm_run_flags = [
        (RUN_LLM_QWEN3_6_35B_A3B, "qwen3.6_35b_a3b"),
        (RUN_LLM_GEMMA4_26B_A4B_Q4, "gemma4_26b_a4b_q4"),
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
COLLECT_TEST_TIMEOUT_S = 900
COLLECT_MAX_WORKERS = 13


def main() -> int:
    if RUN_CLASSIC_GENERATION:
        rc = classic.main(classic.ClassicGenerationConfig(
            container_name=CONTAINER_NAME,
            container_workspace=CONTAINER_WORKSPACE,
            workspace=WORKSPACE,
            bug_workers=PIT_BUG_WORKERS,
            class_workers=PIT_CLASS_WORKERS,
            bug_ids_by_project=BUG_IDS_BY_PROJECT,
            pit_config=PIT_CONFIG,
        ))
        if rc != 0:
            return int(rc)

    for llm_config in _enabled_llm_configs():
        rc = llm.main(llm.LLMGenerationConfig(
            container_name=CONTAINER_NAME,
            container_workspace=CONTAINER_WORKSPACE,
            workspace=WORKSPACE,
            bug_ids_by_project=BUG_IDS_BY_PROJECT,
            llm_config=llm_config,
        ))
        if rc != 0:
            return int(rc)

    if RUN_COLLECTION:
        rc = collect.main(collect.CollectionConfig(
            bug_ids_by_project=BUG_IDS_BY_PROJECT,
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
