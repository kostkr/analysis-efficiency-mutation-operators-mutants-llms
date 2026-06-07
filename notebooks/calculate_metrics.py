#!/usr/bin/env python3
"""
Calculate exactly the chapter 5 metrics for collected Defects4J mutant data.

By default the script scans every bug directory in:

    notebooks/demo_collection_workspace/

and reports metrics separately for the three collected mutant types:

    classic
    gemma4
    qwen3.6

The actual file stems are normalized to these labels, for example
``gemma4_26b-a4b-it-q4_K_M.json`` becomes ``gemma4``.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_WORKSPACE = Path(__file__).resolve().parent / "demo_collection_workspace"
CLASSIC_TYPE = "classic"
EXPECTED_TYPES = (CLASSIC_TYPE, "gemma4", "qwen3.6")
CHAPTER_5_METRICS = (
    "Mutants",
    "CMR",
    "DMR",
    "EMR",
    "Mutation Score",
    "LLM-NMR",
    "RBDR",
    "AOR",
    "CR",
    "HAOR",
    "HOMR",
    "AMGT",
    "CPUM",
)


@dataclass(frozen=True)
class Observation:
    bug_key: str
    mutant_type: str
    set_name: str
    mutant_id: int
    mutant: dict[str, Any]
    result: dict[str, Any] | None
    duplicate: bool


@dataclass(frozen=True)
class BugData:
    key: str
    project: str
    bug_id: int
    meta: dict[str, Any]
    observations: tuple[Observation, ...]
    warnings: tuple[str, ...]

    @property
    def bug_profile(self) -> set[str]:
        profile = self.meta.get("bug_profile")
        if not isinstance(profile, dict):
            return set()
        return set(as_list(profile.get("failing_tests")))

    @property
    def suite_test_count(self) -> int:
        profile = self.meta.get("suite_profile")
        if not isinstance(profile, dict):
            return 0
        total = as_int(profile.get("total_tests"))
        if total is not None:
            return total
        return len(as_list(profile.get("all_tests")))

    @property
    def input_mutant_count(self) -> int:
        return len(self.observations)


@dataclass(frozen=True)
class TypeMetrics:
    scope: str
    mutant_type: str
    generated: int
    non_duplicate: int
    result_records: int
    missing_results: int
    duplicates: int
    compiled: int
    compiled_duplicates: int
    compile_failed: int
    timed_out: int
    invalid: int
    killed_useful: int
    survived_useful: int
    useful: int
    profile_ready: int
    generation_time_s: float
    execution_time_s: float
    total_time_s: float
    detected_bugs: int
    high_ochiai_bugs: int
    high_ochiai_mutants: int
    new_mutants: int | None
    cmr: float | None
    dmr: float | None
    emr: float | None
    mutation_score: float | None
    llm_nmr: float | None
    rbdr: float | None
    aor: float | None
    cr: float | None
    high_ochiai_bug_rate: float | None
    high_ochiai_mutant_rate: float | None
    amgt: float | None
    cpum: float | None
    warnings: tuple[str, ...]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    workspace = args.workspace.resolve()
    requested_bug_keys = tuple(args.bugs or ())

    bugs = load_bugs(workspace=workspace, requested_bug_keys=requested_bug_keys)
    if not bugs:
        print(f"No bug data found in {workspace}", file=sys.stderr)
        return 2

    mutant_types = ordered_types(
        {obs.mutant_type for bug in bugs for obs in bug.observations}
    )
    aggregate_metrics = [
        calculate_metrics(scope="ALL_SELECTED", mutant_type=mutant_type, bugs=bugs)
        for mutant_type in mutant_types
    ]
    per_bug_metrics = [
        calculate_metrics(scope=bug.key, mutant_type=mutant_type, bugs=(bug,))
        for bug in bugs
        for mutant_type in mutant_types
        if any(obs.mutant_type == mutant_type for obs in bug.observations)
    ]

    verdict = build_verdict(
        bugs=bugs,
        mutant_types=mutant_types,
        aggregate_metrics=aggregate_metrics,
    )
    payload = {
        "workspace": str(workspace),
        "bugs": [bug.key for bug in bugs],
        "metrics": list(CHAPTER_5_METRICS),
        "data_readiness": data_readiness_payload(bugs, mutant_types),
        "aggregate_metrics": [metrics_to_dict(item) for item in aggregate_metrics],
        "per_bug_metrics": [metrics_to_dict(item) for item in per_bug_metrics],
        "verdict": verdict,
    }

    print_report(
        bugs=bugs,
        mutant_types=mutant_types,
        aggregate_metrics=aggregate_metrics,
        per_bug_metrics=per_bug_metrics,
        verdict=verdict,
    )

    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nJSON report written to {args.output_json}")

    if args.strict and verdict["status"] != "OK":
        return 1
    return 0


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate chapter 5 metrics for all demo_collection_workspace data."
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=DEFAULT_WORKSPACE,
        help=f"Workspace with bug folders (default: {DEFAULT_WORKSPACE})",
    )
    parser.add_argument(
        "--bugs",
        nargs="*",
        default=None,
        help="Optional bug folders to include, for example LANG_1 LANG_3. Omit to include all.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Optional path for a machine-readable report.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 when some applicable chapter 5 metric is not calculable.",
    )
    return parser.parse_args(argv)


def load_bugs(workspace: Path, requested_bug_keys: tuple[str, ...]) -> tuple[BugData, ...]:
    requested = {normalize_bug_key(key) for key in requested_bug_keys}
    bug_dirs = sorted(
        [
        child
        for child in (workspace.iterdir() if workspace.exists() else ())
        if child.is_dir()
        and (child / "meta.json").exists()
        and (not requested or normalize_bug_key(child.name) in requested)
        ],
        key=bug_dir_sort_key,
    )

    bugs: list[BugData] = []
    for bug_dir in bug_dirs:
        warnings: list[str] = []
        meta = read_json_object(bug_dir / "meta.json", warnings)
        project = str(meta.get("project") or bug_dir.name.split("_", 1)[0])
        bug_id = as_int(meta.get("bug_id")) or as_int(bug_dir.name.rsplit("_", 1)[-1]) or 0
        bug_key = f"{project.upper()}_{bug_id}"
        mutants_dir = bug_dir / "mutants"
        results_dir = bug_dir / "results"
        observations: list[Observation] = []

        if not mutants_dir.exists():
            warnings.append(f"{bug_key}: missing mutants directory")
        if not results_dir.exists():
            warnings.append(f"{bug_key}: missing results directory")

        for mutant_path in sorted(mutants_dir.glob("*.json")) if mutants_dir.exists() else ():
            set_name = mutant_path.stem
            mutant_type = canonical_type(set_name)
            mutants = read_json_list(mutant_path, warnings)
            result_path = results_dir / mutant_path.name
            results = read_json_list(result_path, warnings) if result_path.exists() else []
            if not result_path.exists():
                warnings.append(f"{bug_key}/{set_name}: missing result file {result_path.name}")

            duplicate_ids, duplicate_warnings = detect_duplicate_ids(mutants)
            warnings.extend(f"{bug_key}/{set_name}: {item}" for item in duplicate_warnings)
            result_by_id, result_warnings = index_results(results)
            warnings.extend(f"{bug_key}/{set_name}: {item}" for item in result_warnings)

            mutant_ids: set[int] = set()
            for mutant in mutants:
                mutant_id = as_int(mutant.get("id"))
                if mutant_id is None:
                    continue
                mutant_ids.add(mutant_id)
                observations.append(
                    Observation(
                        bug_key=bug_key,
                        mutant_type=mutant_type,
                        set_name=set_name,
                        mutant_id=mutant_id,
                        mutant=mutant,
                        result=result_by_id.get(mutant_id),
                        duplicate=mutant_id in duplicate_ids,
                    )
                )

            extra_results = sorted(set(result_by_id) - mutant_ids)
            if extra_results:
                warnings.append(
                    f"{bug_key}/{set_name}: result records without matching mutants: "
                    f"{extra_results[:10]}{' ...' if len(extra_results) > 10 else ''}"
                )

        marked_observations = mark_duplicates_by_type(observations)
        bugs.append(
            BugData(
                key=bug_key,
                project=project,
                bug_id=bug_id,
                meta=meta,
                observations=marked_observations,
                warnings=tuple(warnings),
            )
        )

    return tuple(bugs)


def bug_dir_sort_key(path: Path) -> tuple[str, int, str]:
    name = path.name.upper().replace("-", "_")
    project, _, suffix = name.rpartition("_")
    try:
        bug_id = int(suffix)
    except ValueError:
        return (name, 0, name)
    return (project, bug_id, name)


def read_json_object(path: Path, warnings: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"{path}: cannot read JSON object: {exc}")
        return {}
    if not isinstance(payload, dict):
        warnings.append(f"{path}: expected JSON object")
        return {}
    return payload


def read_json_list(path: Path, warnings: list[str]) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"{path}: cannot read JSON list: {exc}")
        return []
    if not isinstance(payload, list):
        warnings.append(f"{path}: expected JSON list")
        return []
    records = []
    for index, item in enumerate(payload):
        if isinstance(item, dict):
            records.append(item)
        else:
            warnings.append(f"{path}: item #{index} is not an object")
    return records


def index_results(results: list[dict[str, Any]]) -> tuple[dict[int, dict[str, Any]], list[str]]:
    indexed: dict[int, dict[str, Any]] = {}
    warnings: list[str] = []
    for result in results:
        mutant_id = as_int(result.get("mutant_id"))
        if mutant_id is None:
            warnings.append("result record without integer mutant_id")
            continue
        if mutant_id in indexed:
            warnings.append(f"duplicate result record for mutant_id={mutant_id}")
        indexed[mutant_id] = result
    return indexed, warnings


def detect_duplicate_ids(mutants: list[dict[str, Any]]) -> tuple[set[int], list[str]]:
    seen_signatures: set[tuple[str, int, str]] = set()
    seen_ids: set[int] = set()
    duplicate_ids: set[int] = set()
    warnings: list[str] = []

    for mutant in mutants:
        mutant_id = as_int(mutant.get("id"))
        if mutant_id is None:
            warnings.append("mutant record without integer id")
            continue
        if mutant_id in seen_ids:
            warnings.append(f"duplicate mutant id={mutant_id}")
        seen_ids.add(mutant_id)

        original_signature = (
            str(mutant.get("filepath", "")),
            as_int(mutant.get("line")) or 0,
            normalize_code_fragment(str(mutant.get("precode", ""))),
        )
        signature = mutation_signature(mutant)
        if signature == original_signature or signature in seen_signatures:
            duplicate_ids.add(mutant_id)
            continue
        seen_signatures.add(signature)

    return duplicate_ids, warnings


def mark_duplicates_by_type(observations: list[Observation]) -> tuple[Observation, ...]:
    groups: dict[tuple[str, str], list[Observation]] = {}
    for obs in observations:
        groups.setdefault((obs.bug_key, obs.mutant_type), []).append(obs)

    duplicate_keys: set[tuple[str, str, str, int]] = set()
    for group in groups.values():
        seen_signatures: set[tuple[str, int, str]] = set()
        for obs in sorted(group, key=lambda item: (item.set_name, item.mutant_id)):
            signature = mutation_signature(obs.mutant)
            if obs.duplicate or signature in seen_signatures:
                duplicate_keys.add((obs.bug_key, obs.mutant_type, obs.set_name, obs.mutant_id))
                continue
            seen_signatures.add(signature)

    return tuple(
        Observation(
            bug_key=obs.bug_key,
            mutant_type=obs.mutant_type,
            set_name=obs.set_name,
            mutant_id=obs.mutant_id,
            mutant=obs.mutant,
            result=obs.result,
            duplicate=(obs.bug_key, obs.mutant_type, obs.set_name, obs.mutant_id) in duplicate_keys,
        )
        for obs in observations
    )


def calculate_metrics(
    scope: str,
    mutant_type: str,
    bugs: tuple[BugData, ...],
) -> TypeMetrics:
    observations = [
        obs
        for bug in bugs
        for obs in bug.observations
        if obs.mutant_type == mutant_type
    ]
    with_results = [obs for obs in observations if obs.result is not None]
    non_duplicate = [obs for obs in observations if not obs.duplicate]
    compile_status_by_signature = build_compile_status_by_signature(observations)
    compilable_all = [
        obs
        for obs in observations
        if counts_as_compilable_for_cmr(obs, compile_status_by_signature)
    ]
    useful = [obs for obs in non_duplicate if is_final_metric_mutant(obs)]
    profile_ready = useful
    warnings: list[str] = []
    per_bug_ochiai_values: list[float] = []
    high_ochiai_mutants = 0
    linked = 0
    detected_bugs = 0

    for bug in bugs:
        bug_observations = [obs for obs in bug.observations if obs.mutant_type == mutant_type]
        bug_profile_ready = [obs for obs in bug_observations if is_final_metric_mutant(obs)]
        bug_tests = bug.bug_profile

        if not bug_observations:
            warnings.append(f"{bug.key}/{mutant_type}: missing mutant file")
        if not bug_tests:
            warnings.append(f"{bug.key}: missing bug_profile.failing_tests")
            continue

        bug_detected = False
        bug_ochiai_values: list[float] = []
        for obs in bug_profile_ready:
            failing = failing_tests(obs)
            if ochiai(failing, bug_tests) >= 0.8:
                high_ochiai_mutants += 1
            if failing & bug_tests:
                linked += 1
                bug_detected = True
            bug_ochiai_values.append(ochiai(failing, bug_tests))
        per_bug_ochiai_values.append(statistics.fmean(bug_ochiai_values) if bug_ochiai_values else 0.0)
        if bug_detected:
            detected_bugs += 1

    new_mutants, llm_nmr, novelty_warnings = calculate_llm_nmr(mutant_type, bugs)
    warnings.extend(novelty_warnings)

    generated = len(observations)
    result_records = len(with_results)
    missing_results = sum(1 for obs in non_duplicate if obs.result is None)
    duplicates = sum(1 for obs in observations if obs.duplicate)
    compiled = len(compilable_all)
    compiled_duplicates = sum(
        1
        for obs in observations
        if obs.duplicate and counts_as_compilable_for_cmr(obs, compile_status_by_signature)
    )
    compile_failed = sum(1 for obs in non_duplicate if is_compile_failed(obs))
    timed_out = sum(1 for obs in non_duplicate if is_timed_out(obs))
    invalid = generated - len(useful)
    killed_useful = sum(1 for obs in profile_ready if failing_tests(obs))
    survived_useful = sum(1 for obs in profile_ready if is_survived(obs))
    high_ochiai_bugs = sum(1 for value in per_bug_ochiai_values if value >= 0.8)
    generation_time_s = sum_generation_time(observations, warnings)
    execution_time_s = sum_execution_time(observations, warnings)
    total_time_s = generation_time_s + execution_time_s

    if missing_results:
        warnings.append(f"{scope}/{mutant_type}: {missing_results} non-duplicate mutants have no result")

    return TypeMetrics(
        scope=scope,
        mutant_type=mutant_type,
        generated=generated,
        non_duplicate=len(non_duplicate),
        result_records=result_records,
        missing_results=missing_results,
        duplicates=duplicates,
        compiled=compiled,
        compiled_duplicates=compiled_duplicates,
        compile_failed=compile_failed,
        timed_out=timed_out,
        invalid=invalid,
        killed_useful=killed_useful,
        survived_useful=survived_useful,
        useful=len(useful),
        profile_ready=len(profile_ready),
        generation_time_s=generation_time_s,
        execution_time_s=execution_time_s,
        total_time_s=total_time_s,
        detected_bugs=detected_bugs,
        high_ochiai_bugs=high_ochiai_bugs,
        high_ochiai_mutants=high_ochiai_mutants,
        new_mutants=new_mutants,
        cmr=safe_div(compiled, generated),
        dmr=safe_div(duplicates, compiled),
        emr=safe_div(survived_useful, len(profile_ready)),
        mutation_score=safe_div(killed_useful, len(profile_ready)),
        llm_nmr=llm_nmr,
        rbdr=safe_div(detected_bugs, len(bugs)),
        aor=statistics.fmean(per_bug_ochiai_values) if per_bug_ochiai_values else None,
        cr=safe_div(linked, len(profile_ready)),
        high_ochiai_bug_rate=safe_div(high_ochiai_bugs, len(bugs)),
        high_ochiai_mutant_rate=safe_div(high_ochiai_mutants, len(profile_ready)),
        amgt=safe_div(total_time_s, generated),
        cpum=safe_div(total_time_s, len(useful)),
        warnings=tuple(warnings),
    )


def calculate_llm_nmr(
    mutant_type: str,
    bugs: tuple[BugData, ...],
) -> tuple[int | None, float | None, list[str]]:
    if mutant_type == CLASSIC_TYPE:
        return None, None, []

    warnings: list[str] = []
    new_mutants = 0
    comparable_final_count = 0

    for bug in bugs:
        classic_final = [
            obs
            for obs in bug.observations
            if obs.mutant_type == CLASSIC_TYPE and is_final_metric_mutant(obs)
        ]
        target_final = [
            obs
            for obs in bug.observations
            if obs.mutant_type == mutant_type and is_final_metric_mutant(obs)
        ]

        if not target_final:
            continue
        if not classic_final:
            warnings.append(f"{bug.key}/{mutant_type}: cannot compute LLM-NMR without classic mutants")
            continue

        comparable_final_count += len(target_final)

        classic_by_line: dict[tuple[str, int], list[Observation]] = {}
        for obs in classic_final:
            classic_by_line.setdefault(mutation_location(obs.mutant), []).append(obs)

        for obs in target_final:
            candidates = classic_by_line.get(mutation_location(obs.mutant), [])
            if not candidates:
                new_mutants += 1
                continue

            target_syntax = llm_nmr_syntactic_signature(obs.mutant)
            target_profile = llm_nmr_test_signature(obs)
            syntactic_match = any(
                llm_nmr_syntactic_signature(candidate.mutant) == target_syntax
                for candidate in candidates
            )
            test_profile_match = any(
                llm_nmr_test_signature(candidate) == target_profile
                for candidate in candidates
            )
            if not syntactic_match and not test_profile_match:
                new_mutants += 1

    if new_mutants > comparable_final_count:
        warnings.append(f"{mutant_type}: new mutant count exceeds useful mutant count")
    llm_nmr = safe_div(new_mutants, comparable_final_count) if comparable_final_count else None
    if llm_nmr is not None and not (0.0 <= llm_nmr <= 1.0):
        warnings.append(f"{mutant_type}: LLM-NMR outside [0, 1]")
    return new_mutants, llm_nmr, warnings


def print_report(
    bugs: tuple[BugData, ...],
    mutant_types: tuple[str, ...],
    aggregate_metrics: list[TypeMetrics],
    per_bug_metrics: list[TypeMetrics],
    verdict: dict[str, Any],
) -> None:
    print("Chapter 5 metric readiness")
    print("==========================")
    print(f"Workspace bugs: {', '.join(bug.key for bug in bugs)}")
    print(f"Metrics: {', '.join(CHAPTER_5_METRICS)}")

    print("\nData readiness")
    print_table(
        ["Bug", "Type", "Generated", "Duplicates", "Results", "Missing", "Final", "BugFail", "SuiteTests", "Status"],
        [
            readiness_row(bug, mutant_type)
            for bug in bugs
            for mutant_type in mutant_types
            if any(obs.mutant_type == mutant_type for obs in bug.observations)
        ],
    )

    print("\nAggregate chapter 5 metrics")
    print_table(
        ["Type", "Mutants", "CMR", "DMR", "EMR", "Mut.Score", "LLM-NMR", "RBDR", "AOR", "CR", "HAOR", "HOMR", "AMGT s", "CPUM s"],
        [metrics_row(item) for item in aggregate_metrics],
    )

    print("\nPer-bug chapter 5 metrics")
    print_table(
        ["Bug", "Type", "Mutants", "CMR", "DMR", "EMR", "Mut.Score", "LLM-NMR", "RBDR", "AOR", "CR", "HAOR", "HOMR", "AMGT s", "CPUM s"],
        [metrics_row(item, include_scope=True) for item in per_bug_metrics],
    )

    all_warnings = collect_warnings(bugs, aggregate_metrics)
    print(f"\nVerdict: {verdict['status']} - {verdict['message']}")
    if all_warnings:
        print("\nWhy some metrics may be unsafe")
        for warning in all_warnings:
            print(f"- {warning}")


def readiness_row(bug: BugData, mutant_type: str) -> list[str]:
    observations = [obs for obs in bug.observations if obs.mutant_type == mutant_type]
    non_duplicate = [obs for obs in observations if not obs.duplicate]
    warnings = readiness_warnings(bug, mutant_type, observations)
    return [
        bug.key,
        mutant_type,
        str(len(observations)),
        str(sum(1 for obs in observations if obs.duplicate)),
        str(sum(1 for obs in non_duplicate if obs.result is not None)),
        str(sum(1 for obs in non_duplicate if obs.result is None)),
        str(sum(1 for obs in observations if is_final_metric_mutant(obs))),
        str(len(bug.bug_profile)),
        str(bug.suite_test_count),
        "OK" if not warnings else "WARN",
    ]


def metrics_row(metrics: TypeMetrics, include_scope: bool = False) -> list[str]:
    row = [
        metrics.mutant_type,
        str(metrics.generated),
        format_percent(metrics.cmr),
        format_percent(metrics.dmr),
        format_percent(metrics.emr),
        format_percent(metrics.mutation_score),
        format_percent(metrics.llm_nmr),
        format_percent(metrics.rbdr),
        format_percent(metrics.aor),
        format_percent(metrics.cr),
        format_percent(metrics.high_ochiai_bug_rate),
        format_percent(metrics.high_ochiai_mutant_rate),
        format_seconds(metrics.amgt),
        format_seconds(metrics.cpum),
    ]
    if include_scope:
        return [metrics.scope] + row
    return row


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    if not rows:
        print("(no rows)")
        return
    widths = [
        max(len(str(row[index])) for row in [headers] + rows)
        for index in range(len(headers))
    ]
    print(" | ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(" | ".join(str(value).ljust(widths[index]) for index, value in enumerate(row)))


def readiness_warnings(
    bug: BugData,
    mutant_type: str,
    observations: list[Observation],
) -> list[str]:
    warnings: list[str] = []
    non_duplicate = [obs for obs in observations if not obs.duplicate]
    if not observations:
        warnings.append(f"{bug.key}/{mutant_type}: missing mutant data")
    if not bug.bug_profile:
        warnings.append(f"{bug.key}: missing bug_profile.failing_tests")
    if bug.suite_test_count <= 0:
        warnings.append(f"{bug.key}: missing suite_profile.total_tests/all_tests")
    if any(obs.result is None for obs in non_duplicate):
        warnings.append(f"{bug.key}/{mutant_type}: missing result records")
    if any(is_compiled(obs) and not has_complete_profile(obs) for obs in non_duplicate):
        warnings.append(f"{bug.key}/{mutant_type}: missing failing_tests profile")
    if any(has_complete_profile(obs) and has_explicit_partial_profile_marker(obs) for obs in non_duplicate):
        warnings.append(
            f"{bug.key}/{mutant_type}: result records contain partial test profiles; "
            "rerun collection before treating RBDR/AOR/CR/HAOR as final"
        )
    return warnings


def collect_warnings(
    bugs: tuple[BugData, ...],
    metrics: list[TypeMetrics],
) -> list[str]:
    warnings: list[str] = []
    for bug in bugs:
        warnings.extend(bug.warnings)
        for mutant_type in EXPECTED_TYPES:
            observations = [obs for obs in bug.observations if obs.mutant_type == mutant_type]
            warnings.extend(readiness_warnings(bug, mutant_type, observations))
    for item in metrics:
        warnings.extend(item.warnings)
    return sorted(set(warnings))


def data_readiness_payload(
    bugs: tuple[BugData, ...],
    mutant_types: tuple[str, ...],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bug in bugs:
        for mutant_type in mutant_types:
            observations = [obs for obs in bug.observations if obs.mutant_type == mutant_type]
            if not observations:
                continue
            non_duplicate = [obs for obs in observations if not obs.duplicate]
            rows.append(
                {
                    "bug": bug.key,
                    "type": mutant_type,
                    "generated": len(observations),
                    "duplicates": sum(1 for obs in observations if obs.duplicate),
                    "result_records": sum(1 for obs in non_duplicate if obs.result is not None),
                    "missing_result_records": sum(1 for obs in non_duplicate if obs.result is None),
                    "final_metric_mutants": sum(1 for obs in observations if is_final_metric_mutant(obs)),
                    "bug_failing_tests": len(bug.bug_profile),
                    "suite_tests": bug.suite_test_count,
                    "warnings": readiness_warnings(bug, mutant_type, observations),
                }
            )
    return rows


def build_verdict(
    bugs: tuple[BugData, ...],
    mutant_types: tuple[str, ...],
    aggregate_metrics: list[TypeMetrics],
) -> dict[str, Any]:
    warnings = collect_warnings(bugs, aggregate_metrics)
    missing_types = [mutant_type for mutant_type in EXPECTED_TYPES if mutant_type not in mutant_types]
    unavailable_metrics: list[str] = []

    for item in aggregate_metrics:
        applicable_metrics = {
            "CMR": item.cmr,
            "DMR": item.dmr,
            "EMR": item.emr,
            "Mutation Score": item.mutation_score,
            "RBDR": item.rbdr,
            "AOR": item.aor,
            "CR": item.cr,
            "HAOR": item.high_ochiai_bug_rate,
            "HOMR": item.high_ochiai_mutant_rate,
            "AMGT": item.amgt,
            "CPUM": item.cpum,
        }
        if item.mutant_type != CLASSIC_TYPE:
            applicable_metrics["LLM-NMR"] = item.llm_nmr
        unavailable_metrics.extend(
            f"{item.mutant_type}:{metric}"
            for metric, value in applicable_metrics.items()
            if value is None
        )

    if missing_types or unavailable_metrics or warnings:
        details: list[str] = []
        if missing_types:
            details.append(f"missing types: {', '.join(missing_types)}")
        if unavailable_metrics:
            details.append(f"unavailable metrics: {', '.join(unavailable_metrics)}")
        if warnings:
            details.append(f"warnings: {len(warnings)}")
        return {"status": "WARN", "message": "; ".join(details)}

    return {
        "status": "OK",
        "message": "all applicable chapter 5 metrics are calculable for all workspace data",
    }


def metrics_to_dict(metrics: TypeMetrics) -> dict[str, Any]:
    return {
        "scope": metrics.scope,
        "type": metrics.mutant_type,
        "counts": {
            "generated": metrics.generated,
            "non_duplicate": metrics.non_duplicate,
            "result_records": metrics.result_records,
            "missing_results": metrics.missing_results,
            "duplicates": metrics.duplicates,
            "compiled": metrics.compiled,
            "compiled_duplicates": metrics.compiled_duplicates,
            "compile_failed": metrics.compile_failed,
            "timed_out": metrics.timed_out,
            "invalid": metrics.invalid,
            "killed_useful": metrics.killed_useful,
            "survived_useful": metrics.survived_useful,
            "useful": metrics.useful,
            "profile_ready": metrics.profile_ready,
            "detected_bugs": metrics.detected_bugs,
            "high_ochiai_bugs": metrics.high_ochiai_bugs,
            "high_ochiai_mutants": metrics.high_ochiai_mutants,
            "new_mutants": metrics.new_mutants,
            "generation_time_s": metrics.generation_time_s,
            "execution_time_s": metrics.execution_time_s,
            "total_time_s": metrics.total_time_s,
        },
        "metrics": {
            "Generated (all)": metrics.generated,
            "CMR": metrics.cmr,
            "DMR": metrics.dmr,
            "EMR": metrics.emr,
            "Mutation Score": metrics.mutation_score,
            "LLM-NMR": metrics.llm_nmr,
            "RBDR": metrics.rbdr,
            "AOR": metrics.aor,
            "CR": metrics.cr,
            "HAOR": metrics.high_ochiai_bug_rate,
            "HOMR": metrics.high_ochiai_mutant_rate,
            "AMGT": metrics.amgt,
            "CPUM": metrics.cpum,
        },
        "warnings": list(metrics.warnings),
    }


def canonical_type(set_name: str) -> str:
    lowered = set_name.lower()
    if lowered == CLASSIC_TYPE:
        return CLASSIC_TYPE
    if lowered.startswith("qwen3.6") or lowered.startswith("qwen3_6") or lowered.startswith("qwen"):
        return "qwen3.6"
    if lowered.startswith("gemma4") or lowered.startswith("gemini4"):
        return "gemma4"
    return set_name


def ordered_types(types: set[str]) -> tuple[str, ...]:
    ordered = [item for item in EXPECTED_TYPES if item in types]
    ordered.extend(sorted(types - set(ordered)))
    return tuple(ordered)


def mutation_signature(mutant: dict[str, Any]) -> tuple[str, int, str]:
    return (
        str(mutant.get("filepath", "")),
        as_int(mutant.get("line")) or 0,
        mutation_compare_key(str(mutant.get("aftercode", ""))),
    )


def original_code_signature(mutant: dict[str, Any]) -> tuple[str, int, str]:
    return (
        str(mutant.get("filepath", "")),
        as_int(mutant.get("line")) or 0,
        normalize_code_fragment(str(mutant.get("precode", ""))),
    )


def compile_signature_key(obs: Observation) -> tuple[str, str, tuple[str, int, str]]:
    return (obs.bug_key, obs.mutant_type, mutation_signature(obs.mutant))


def build_compile_status_by_signature(
    observations: list[Observation],
) -> dict[tuple[str, str, tuple[str, int, str]], bool]:
    status_by_signature: dict[tuple[str, str, tuple[str, int, str]], bool] = {}
    for obs in observations:
        if obs.result is None:
            continue
        key = compile_signature_key(obs)
        status_by_signature[key] = status_by_signature.get(key, False) or is_compilable(obs)
    return status_by_signature


def counts_as_compilable_for_cmr(
    obs: Observation,
    status_by_signature: dict[tuple[str, str, tuple[str, int, str]], bool],
) -> bool:
    if is_compilable(obs):
        return True
    if obs.result is not None:
        return False
    if not obs.duplicate:
        return False
    if mutation_signature(obs.mutant) == original_code_signature(obs.mutant):
        return True
    return status_by_signature.get(compile_signature_key(obs), False)


def mutation_location(mutant: dict[str, Any]) -> tuple[str, int]:
    return (
        str(mutant.get("filepath", "")),
        as_int(mutant.get("line")) or 0,
    )


def llm_nmr_syntactic_signature(mutant: dict[str, Any]) -> tuple[str, int, str, str]:
    return (
        str(mutant.get("filepath", "")),
        as_int(mutant.get("line")) or 0,
        normalize_code_fragment(str(mutant.get("precode", ""))),
        normalize_code_fragment(str(mutant.get("aftercode", ""))),
    )


def llm_nmr_test_signature(obs: Observation) -> frozenset[str]:
    return frozenset(failing_tests(obs))


def normalize_code_fragment(text: str) -> str:
    return mutation_compare_key(text)


def mutation_compare_key(text: str) -> str:
    normalized = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    normalized_lines = [strip_trailing_line_comment(line) for line in normalized.split("\n")]
    return re.sub(r"\s+", " ", "\n".join(normalized_lines)).strip()


def same_mutation_code(left: str, right: str) -> bool:
    return mutation_compare_key(left) == mutation_compare_key(right)


def strip_trailing_line_comment(line: str) -> str:
    trimmed = line.rstrip()
    comment_start = trailing_line_comment_start(trimmed)
    return trimmed[:comment_start].rstrip() if comment_start is not None else trimmed


def trailing_line_comment_start(line: str) -> int | None:
    in_string = False
    in_char = False
    escape = False
    for index in range(len(line) - 1):
        char = line[index]
        nxt = line[index + 1]
        if escape:
            escape = False
            continue
        if char == "\\" and (in_string or in_char):
            escape = True
            continue
        if char == '"' and not in_char:
            in_string = not in_string
            continue
        if char == "'" and not in_string:
            in_char = not in_char
            continue
        if not in_string and not in_char and char == "/" and nxt == "/":
            return index
    return None


def strip_java_comments(text: str) -> str:
    result: list[str] = []
    index = 0
    in_string = False
    in_char = False
    in_text_block = False

    while index < len(text):
        char = text[index]

        if in_text_block:
            if text.startswith('"""', index):
                result.append('"""')
                index += 3
                in_text_block = False
            else:
                result.append(char)
                index += 1
            continue

        if in_string:
            result.append(char)
            if char == "\\" and index + 1 < len(text):
                result.append(text[index + 1])
                index += 2
            elif char == '"':
                in_string = False
                index += 1
            else:
                index += 1
            continue

        if in_char:
            result.append(char)
            if char == "\\" and index + 1 < len(text):
                result.append(text[index + 1])
                index += 2
            elif char == "'":
                in_char = False
                index += 1
            else:
                index += 1
            continue

        if text.startswith('"""', index):
            result.append('"""')
            index += 3
            in_text_block = True
        elif char == '"':
            result.append(char)
            index += 1
            in_string = True
        elif char == "'":
            result.append(char)
            index += 1
            in_char = True
        elif text.startswith("//", index):
            newline_index = text.find("\n", index + 2)
            if newline_index == -1:
                break
            result.append("\n")
            index = newline_index + 1
        elif text.startswith("/*", index):
            end_index = text.find("*/", index + 2)
            if end_index == -1:
                break
            result.append(" ")
            index = end_index + 2
        else:
            result.append(char)
            index += 1

    return "".join(result)


def failing_tests(obs: Observation) -> set[str]:
    if obs.result is None:
        return set()
    return set(as_list(obs.result.get("failing_tests")))


def has_complete_profile(obs: Observation) -> bool:
    if obs.result is None:
        return False
    return (
        is_compilable(obs)
        and not is_timed_out(obs)
        and obs.result.get("test_executed") is True
        and isinstance(obs.result.get("failing_tests"), list)
    )


def has_full_relevant_profile_marker(obs: Observation) -> bool:
    if obs.result is None:
        return False
    return (
        obs.result.get("profile_scope") == "relevant_full"
        and obs.result.get("test_command") == "defects4j test -r"
    )


def has_explicit_partial_profile_marker(obs: Observation) -> bool:
    if obs.result is None:
        return False
    scope = obs.result.get("profile_scope")
    if scope is None:
        return False
    return scope != "relevant_full"


def is_final_metric_mutant(obs: Observation) -> bool:
    return not obs.duplicate and has_complete_profile(obs)


def is_emr_eligible(obs: Observation) -> bool:
    return not obs.duplicate and is_compilable(obs) and not is_timed_out(obs)


def is_compilable(obs: Observation) -> bool:
    return (
        obs.result is not None
        and obs.result.get("compiled") is True
        and not has_compile_error(obs)
    )


def is_compiled(obs: Observation) -> bool:
    return is_compilable(obs) and not is_timed_out(obs)


def is_compile_failed(obs: Observation) -> bool:
    return (
        obs.result is not None
        and not is_timed_out(obs)
        and (obs.result.get("compiled") is False or has_compile_error(obs))
    )


def is_timed_out(obs: Observation) -> bool:
    return obs.result is not None and bool(obs.result.get("timed_out"))


def has_compile_error(obs: Observation) -> bool:
    if obs.result is None:
        return False
    return bool(str(obs.result.get("compile_error", "")).strip())


def is_survived(obs: Observation) -> bool:
    return has_complete_profile(obs) and not failing_tests(obs)


def ochiai(mutant_tests: set[str], bug_tests: set[str]) -> float:
    if not mutant_tests or not bug_tests:
        return 0.0
    return len(mutant_tests & bug_tests) / math.sqrt(len(mutant_tests) * len(bug_tests))


def sum_generation_time(observations: list[Observation], warnings: list[str]) -> float:
    total = 0.0
    for obs in observations:
        value = obs.mutant.get("gen_time_s")
        if isinstance(value, int | float):
            total += float(value)
        elif isinstance(value, str):
            try:
                total += float(value)
            except ValueError:
                warnings.append(f"{obs.bug_key}/{obs.set_name}/{obs.mutant_id}: invalid gen_time_s")
        else:
            warnings.append(f"{obs.bug_key}/{obs.set_name}/{obs.mutant_id}: invalid gen_time_s")
    return total


def sum_execution_time(observations: list[Observation], warnings: list[str]) -> float:
    total = 0.0
    for obs in observations:
        if obs.result is None:
            continue
        value = obs.result.get("run_time_s", obs.result.get("wall_time_s", obs.result.get("test_time_s")))
        if isinstance(value, int | float):
            total += float(value)
        elif isinstance(value, str):
            try:
                total += float(value)
            except ValueError:
                warnings.append(f"{obs.bug_key}/{obs.set_name}/{obs.mutant_id}: invalid run_time_s")
    return total


def safe_div(numerator: float | int, denominator: float | int) -> float | None:
    if denominator == 0:
        return None
    return float(numerator) / float(denominator)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def as_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return round(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def normalize_bug_key(value: str) -> str:
    return value.upper().replace("-", "_")


def format_percent(value: float | None) -> str:
    return "NA" if value is None else f"{value * 100:.2f}%"


def format_float(value: float | None) -> str:
    return "NA" if value is None else f"{value:.4f}"


def format_seconds(value: float | None) -> str:
    return "NA" if value is None else f"{value:.4f}"


if __name__ == "__main__":
    raise SystemExit(main())
