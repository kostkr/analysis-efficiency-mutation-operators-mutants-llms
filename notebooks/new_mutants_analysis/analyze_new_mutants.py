#!/usr/bin/env python3
"""
Collect and classify LLM mutants that are "new" relative to classic PIT mutants.

A mutant is NEW (per thesis definition 5.3.1) when BOTH conditions hold:
  1. No same-line classic mutant shares the same syntactic signature
     (filepath, line, normalised precode, normalised aftercode).
  2. No classic mutant (on ANY line) shares the same set of failing tests.

Each new mutant is then classified into one of five categories derived directly
from the four PIT operator families described in Chapter 3 of the thesis:

  design      — Mutanty projektowe (Conditionals Boundary, Math, Negate Conditionals,
                Increments, Invert Negatives, Inline Constant, Remove Increments)
  integration — Mutanty integracyjne (Void Method Call, Non Void Method Calls,
                Argument Propagation)
  object      — Mutanty obiektowe (Constructor Calls, Big Integer, Big Decimal,
                Member Variable, Naked Receiver)
  grammar     — Mutanty na gramatyce (Empty/False/True/Null/Primitive Returns,
                Remove Conditional, Switch, Remove Switch)
  beyond_classic — the change does NOT fit any of the four PIT families; this
                   indicates a genuinely new operator introduced by the LLM.

This taxonomy is academically grounded: every category corresponds to an
explicit section of Chapter 3, so the distribution can be reported in the
thesis conclusion to argue whether LLMs mainly recombine known patterns or
produce mutations beyond the classical PIT repertoire.

Usage
-----
    python notebooks/new_mutants_analysis/analyze_new_mutants.py [--workspace PATH]

Output
------
  new_mutants.json  — full record list (saved beside the workspace directory)
  new_mutants.csv   — flat table for spreadsheet analysis

Fields per record
-----------------
  bug_key       : e.g. "CHART_1"
  project       : e.g. "CHART"
  model         : "gemma4" | "qwen3.6"
  mutant_id     : int
  filepath      : source file path
  line          : int
  precode       : original source line
  aftercode     : mutated source line
  failing_tests : list[str]  (empty → mutant survived)
  killed        : bool
  pit_family    : one of the five categories above
  pit_signals   : list of PIT operator names that triggered the classification
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Resolve path to calculate_metrics.py (one level up from this file)
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from calculate_metrics import (  # noqa: E402
    CLASSIC_TYPE,
    DEFAULT_WORKSPACE,
    Observation,
    is_final_metric_mutant,
    load_bugs,
    llm_nmr_syntactic_signature,
    llm_nmr_test_signature,
    mutation_compare_key,
    mutation_location,
    failing_tests,
)


# ---------------------------------------------------------------------------
# PIT family labels (Chapter 3 of the thesis)
# ---------------------------------------------------------------------------
FAMILY_DESIGN      = "design"        # Mutanty projektowe
FAMILY_INTEGRATION = "integration"   # Mutanty integracyjne
FAMILY_OBJECT      = "object"        # Mutanty obiektowe
FAMILY_GRAMMAR     = "grammar"       # Mutanty na gramatyce
FAMILY_BEYOND      = "beyond_classic"  # Truly new — outside the PIT repertoire

ALL_FAMILIES = [FAMILY_DESIGN, FAMILY_INTEGRATION, FAMILY_OBJECT,
                FAMILY_GRAMMAR, FAMILY_BEYOND]


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def _norm(text: str) -> str:
    """Normalise a code fragment for heuristic comparison."""
    return mutation_compare_key(text)


def _tokens(text: str) -> list[str]:
    """Tokenise normalised code into identifiers and punctuation."""
    return re.findall(r'[A-Za-z_][A-Za-z0-9_.]*|[^\s]', _norm(text))


# ---------------------------------------------------------------------------
# PIT-family heuristics
# ---------------------------------------------------------------------------
# Each checker returns a (matched: bool, signals: list[str]) pair.
# `signals` names the specific PIT operators that matched.

# Relational operators, split by mutation type
_COND_BOUNDARY_PAIRS = {("<", "<="), ("<=", "<"), (">", ">="), (">=", ">")}
_NEGATE_COND_PAIRS   = {("==", "!="), ("!=", "=="),
                         ("<",  ">="), (">=",  "<"),
                         ("<=",  ">"), (">",  "<=")}
_REL_OPS_RE = re.compile(r'(<=|>=|!=|==|<(?![<=])|>(?![>=]))')

# Arithmetic/bitwise/shift operators used by the Math mutator
_MATH_OPS_RE = re.compile(r'(\+\+|--|<<|>>|>>>|[+\-*/%&|^])')

# Default Java values produced by Non Void Method Calls / grammar mutators
_JAVA_DEFAULTS = {"0", "0.0", "0.0f", "0.0d", "0l", "false", "null",
                  "\"\"", "optional.empty()"}

# Increment tokens
_INC_RE = re.compile(r'\+\+|--')


def _check_design(pre: str, post: str) -> tuple[bool, list[str]]:
    """
    Mutanty projektowe (Chapter 3.2.1):
      Conditionals Boundary, Increments, Invert Negatives, Math,
      Negate Conditionals, Inline Constant, Remove Increments.
    """
    signals: list[str] = []

    # --- Conditionals Boundary / Negate Conditionals / ROR ---
    # ROR (Relational Operator Replacement, PIT ALL group) covers ALL relational op
    # substitutions — not just the specific pairs implemented in the experiment.
    pre_rel  = _REL_OPS_RE.findall(pre)
    post_rel = _REL_OPS_RE.findall(post)
    if pre_rel != post_rel:
        pairs = set(zip(pre_rel, post_rel))
        if pairs & _COND_BOUNDARY_PAIRS:
            signals.append("Conditionals Boundary")
        if pairs & _NEGATE_COND_PAIRS:
            signals.append("Negate Conditionals")
        # Any other relational op substitution (same count) → ROR
        if not (pairs & (_COND_BOUNDARY_PAIRS | _NEGATE_COND_PAIRS)) and \
                len(pre_rel) == len(post_rel) > 0:
            signals.append("ROR")

    # --- Math: arithmetic / bitwise / shift operator change ---
    pre_math  = [op for op in _MATH_OPS_RE.findall(pre)  if op not in ("++", "--")]
    post_math = [op for op in _MATH_OPS_RE.findall(post) if op not in ("++", "--")]
    if pre_math != post_math:
        signals.append("Math")

    # --- Increments: ++ swapped with --, or vice-versa ---
    pre_inc  = _INC_RE.findall(pre)
    post_inc = _INC_RE.findall(post)
    if set(pre_inc) != set(post_inc) and (pre_inc or post_inc):
        signals.append("Increments")

    # --- Remove Increments: ++ or -- removed entirely ---
    if pre_inc and not post_inc:
        signals.append("Remove Increments")

    # --- Invert Negatives: unary minus added / removed before an identifier ---
    # e.g. "return x" → "return -x"  or  "return -size" → "return size"
    unary_re = re.compile(r'(?<![+\-*/%<>=!&|^,(])\s*-\s*(?=[a-zA-Z_(])')
    pre_unary  = len(unary_re.findall(pre))
    post_unary = len(unary_re.findall(post))
    if pre_unary != post_unary:
        signals.append("Invert Negatives")

    # --- Inline Constant: a numeric or character literal changed ---
    num_re = re.compile(r'\b\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?[LlFfDd]?\b')
    char_re = re.compile(r"'.'")
    pre_nums  = num_re.findall(pre) + char_re.findall(pre)
    post_nums = num_re.findall(post) + char_re.findall(post)
    if pre_nums != post_nums and (pre_nums or post_nums):
        # Avoid double-counting pure boolean changes (those go to grammar)
        if not ({"true", "false"} >= {*pre_nums, *post_nums}):
            signals.append("Inline Constant")

    return bool(signals), list(dict.fromkeys(signals))  # preserve order, deduplicate


def _check_integration(pre: str, post: str) -> tuple[bool, list[str]]:
    """
    Mutanty integracyjne (Chapter 3.2.2):
      Void Method Call, Non Void Method Calls, Argument Propagation.
    """
    signals: list[str] = []
    pre_stripped  = pre.strip()
    post_stripped = post.strip()

    method_call_re = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
    pre_calls  = method_call_re.findall(pre)
    post_calls = method_call_re.findall(post)

    # --- Void Method Call: a method-call statement completely removed ---
    # Heuristic: pre has a method call, post is empty or just ";"
    if pre_calls and (not post_stripped or post_stripped == ";"):
        signals.append("Void Method Call")
        return True, signals

    # --- Non Void Method Calls: method call replaced by a Java default value ---
    if pre_calls and not post_calls:
        post_val = post_stripped.rstrip(";").strip().lower()
        if post_val in _JAVA_DEFAULTS:
            signals.append("Non Void Method Calls")
            return True, signals

    # Also handle assignment form: "x = someMethod()" → "x = 0"
    assign_re = re.compile(r'=\s*([^=].*?)(?:;|$)')
    pre_rhs  = assign_re.search(pre)
    post_rhs = assign_re.search(post)
    if pre_rhs and post_rhs:
        pre_rhs_str  = pre_rhs.group(1).strip().rstrip(";").lower()
        post_rhs_str = post_rhs.group(1).strip().rstrip(";").lower()
        if method_call_re.search(pre_rhs_str) and post_rhs_str in _JAVA_DEFAULTS:
            signals.append("Non Void Method Calls")
            return True, signals

    # --- Argument Propagation: method call replaced by one of its arguments ---
    # Heuristic: pre has exactly one method call, post is a simple identifier
    # or primitive that appeared as an argument in pre.
    if len(pre_calls) == 1 and len(post_calls) == 0:
        args_re = re.compile(r'\(([^()]*)\)')
        args_match = args_re.search(pre)
        if args_match:
            args = [a.strip() for a in args_match.group(1).split(",") if a.strip()]
            post_val = post_stripped.rstrip(";").strip()
            if any(a == post_val for a in args):
                signals.append("Argument Propagation")
                return True, signals

    return bool(signals), signals


def _check_object(pre: str, post: str) -> tuple[bool, list[str]]:
    """
    Mutanty obiektowe (Chapter 3.2.3):
      Constructor Calls, Big Integer, Big Decimal, Member Variable, Naked Receiver.
    """
    signals: list[str] = []

    # --- Constructor Calls: new X(...) → null ---
    new_re = re.compile(r'\bnew\s+[A-Z][A-Za-z0-9_]*\s*\(')
    if new_re.search(pre) and "null" in post.split():
        signals.append("Constructor Calls")
        return True, signals

    # --- Big Integer / Big Decimal: method on BigInteger/BigDecimal swapped ---
    big_re = re.compile(r'\b(BigInteger|BigDecimal)\b')
    if big_re.search(pre) or big_re.search(post):
        method_re = re.compile(r'\.(add|subtract|multiply|divide|remainder|negate|abs'
                                r'|pow|mod|gcd|max|min|compareTo|equals|valueOf'
                                r'|intValue|longValue|doubleValue|floatValue)\s*\(')
        pre_methods  = method_re.findall(pre)
        post_methods = method_re.findall(post)
        if pre_methods != post_methods:
            if big_re.search(pre) and "BigInteger" in pre:
                signals.append("Big Integer")
            else:
                signals.append("Big Decimal")
            return True, signals

    # --- Member Variable: field assignment removed, field keeps Java default ---
    # Heuristic: "this.field = something" → "this.field = 0/null/false/\"\"" or gone
    field_assign_re = re.compile(r'(?:this\.)?\b\w+\s*=\s*(?!.*=)')
    if field_assign_re.search(pre) and not field_assign_re.search(post):
        signals.append("Member Variable")
        return True, signals
    if field_assign_re.search(pre) and field_assign_re.search(post):
        post_rhs = post.split("=", 1)[-1].strip().rstrip(";").strip().lower()
        if post_rhs in _JAVA_DEFAULTS:
            signals.append("Member Variable")
            return True, signals

    # --- Naked Receiver: obj.method(args) → obj ---
    # Heuristic: pre has "receiver.methodName(..." and post is just the receiver
    naked_re = re.compile(r'(\b\w+(?:\.\w+)*)\s*\.\s*[a-zA-Z_]\w*\s*\(')
    pre_naked = naked_re.findall(pre)
    if pre_naked:
        post_val = post.strip().rstrip(";").strip()
        for receiver in pre_naked:
            if post_val == receiver or post_val.endswith("." + receiver):
                signals.append("Naked Receiver")
                return True, signals

    return bool(signals), signals


def _check_grammar(pre: str, post: str) -> tuple[bool, list[str]]:
    """
    Mutanty na gramatyce (Chapter 3.2.4):
      Empty Returns, False Returns, True Returns, Null Returns, Primitive Returns,
      Remove Conditional, Switch, Remove Switch.
    """
    signals: list[str] = []
    pre_stripped  = pre.strip()
    post_stripped = post.strip()

    # --- Return-based mutators ---
    pre_is_return  = pre_stripped.startswith("return")
    post_is_return = post_stripped.startswith("return")

    if pre_is_return and post_is_return:
        pre_val  = pre_stripped[len("return"):].strip().rstrip(";").strip().lower()
        post_val = post_stripped[len("return"):].strip().rstrip(";").strip().lower()

        if post_val == "false":
            signals.append("False Returns")
        elif post_val == "true":
            signals.append("True Returns")
        elif post_val == "null":
            signals.append("Null Returns")
        elif post_val in {"0", "0l", "0.0", "0.0f", "0.0d"}:
            signals.append("Primitive Returns")
        elif post_val in {'""', "optional.empty()", "collections.emptylist()",
                          "collections.emptyset()", "collections.emptymap()",
                          "optional.empty()"}:
            signals.append("Empty Returns")
        elif post_val != pre_val:
            # Generic return-value change — still grammar family
            signals.append("Primitive Returns / Empty Returns")

        if signals:
            return True, signals

    # --- Remove Conditional: if-condition forced to true/false ---
    # "if (someExpr)" → "if (true)" or "if (false)"
    if_re = re.compile(r'if\s*\((.+?)\)')
    pre_if  = if_re.search(pre_stripped)
    post_if = if_re.search(post_stripped)
    if pre_if and post_if:
        post_cond = post_if.group(1).strip().lower()
        if post_cond in ("true", "false"):
            signals.append("Remove Conditional")
            return True, signals

    # Remove Conditional: entire if-block removed (post is empty / just the body)
    if pre_stripped.startswith("if") and not post_stripped.startswith("if"):
        if not post_stripped or post_stripped.strip("{}").strip() == pre_stripped.split("{", 1)[-1].rstrip("}").strip():
            signals.append("Remove Conditional")
            return True, signals

    # --- Switch / Remove Switch ---
    switch_re = re.compile(r'\bcase\b|\bswitch\b|\bdefault\b')
    pre_has_switch  = bool(switch_re.search(pre))
    post_has_switch = bool(switch_re.search(post))
    if pre_has_switch or post_has_switch:
        if pre_has_switch and not post_has_switch:
            signals.append("Remove Switch")
        else:
            signals.append("Switch")
        return True, signals

    return bool(signals), signals


# ---------------------------------------------------------------------------
# Main classifier
# ---------------------------------------------------------------------------

def classify_pit_family(precode: str, aftercode: str) -> tuple[str, list[str]]:
    """
    Map a new LLM mutant to one of the four PIT operator families, or to
    'beyond_classic' if none of the family heuristics match.

    The order of checks follows the Chapter 3 ordering of families.

    Returns
    -------
    (pit_family, pit_signals)
        pit_family  : one of FAMILY_DESIGN / FAMILY_INTEGRATION / FAMILY_OBJECT
                      / FAMILY_GRAMMAR / FAMILY_BEYOND
        pit_signals : names of the specific PIT operators that triggered the match
    """
    pre  = _norm(precode)
    post = _norm(aftercode)

    # Check grammar first for return statements — they are unambiguous and
    # would otherwise partially match Inline Constant (numeric return values).
    pre_is_return = pre.strip().startswith("return")
    if pre_is_return:
        matched, sigs = _check_grammar(pre, post)
        if matched:
            return FAMILY_GRAMMAR, sigs

    # Check integration next — method removal patterns are distinctive.
    matched, sigs = _check_integration(pre, post)
    if matched:
        return FAMILY_INTEGRATION, sigs

    # Check object — constructor/field/receiver patterns.
    matched, sigs = _check_object(pre, post)
    if matched:
        return FAMILY_OBJECT, sigs

    # Check design — operator / literal / increment changes.
    matched, sigs = _check_design(pre, post)
    if matched:
        return FAMILY_DESIGN, sigs

    # Check grammar for the remaining constructs (conditionals, switch).
    matched, sigs = _check_grammar(pre, post)
    if matched:
        return FAMILY_GRAMMAR, sigs

    # Nothing matched → genuinely new operator not covered by PIT.
    return FAMILY_BEYOND, []


# ---------------------------------------------------------------------------
# Core logic: collect new mutants
# ---------------------------------------------------------------------------

def collect_new_mutants(
    workspace: Path,
    requested_bug_keys: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    """Return a list of dicts, one for each new LLM mutant."""
    bugs = load_bugs(workspace=workspace, requested_bug_keys=requested_bug_keys)
    records: list[dict[str, Any]] = []

    for bug in bugs:
        classic_final = [
            obs for obs in bug.observations
            if obs.mutant_type == CLASSIC_TYPE and is_final_metric_mutant(obs)
        ]
        if not classic_final:
            continue

        classic_by_line: dict[tuple[str, int], list[Observation]] = {}
        for obs in classic_final:
            classic_by_line.setdefault(mutation_location(obs.mutant), []).append(obs)

        all_classic_profiles: set[frozenset[str]] = {
            llm_nmr_test_signature(obs) for obs in classic_final
        }

        llm_types = {
            obs.mutant_type for obs in bug.observations
            if obs.mutant_type != CLASSIC_TYPE
        }

        for model in sorted(llm_types):
            target_final = [
                obs for obs in bug.observations
                if obs.mutant_type == model and is_final_metric_mutant(obs)
            ]
            for obs in target_final:
                candidates = classic_by_line.get(mutation_location(obs.mutant), [])
                target_syntax  = llm_nmr_syntactic_signature(obs.mutant)
                target_profile = llm_nmr_test_signature(obs)

                syntactic_match    = any(
                    llm_nmr_syntactic_signature(c.mutant) == target_syntax
                    for c in candidates
                )
                test_profile_match = target_profile in all_classic_profiles

                if syntactic_match or test_profile_match:
                    continue  # not new

                precode   = str(obs.mutant.get("precode", ""))
                aftercode = str(obs.mutant.get("aftercode", ""))
                family, signals = classify_pit_family(precode, aftercode)
                ft = sorted(failing_tests(obs))

                records.append({
                    "bug_key":       bug.key,
                    "project":       bug.project,
                    "model":         model,
                    "mutant_id":     obs.mutant_id,
                    "filepath":      str(obs.mutant.get("filepath", "")),
                    "line":          obs.mutant.get("line"),
                    "precode":       precode,
                    "aftercode":     aftercode,
                    "failing_tests": ft,
                    "killed":        bool(ft),
                    "pit_family":    family,
                    "pit_signals":   signals,
                })

    return records


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------

def print_summary(records: list[dict[str, Any]]) -> None:
    total = len(records)
    if not total:
        print("No new mutants found.")
        return

    print(f"\nNew LLM mutants total: {total}")

    # -- by model --
    by_model: dict[str, int] = {}
    for r in records:
        by_model[r["model"]] = by_model.get(r["model"], 0) + 1
    print("\nBy model:")
    for model, n in sorted(by_model.items()):
        print(f"  {model:<22} {n:>6}  ({n / total * 100:.1f}%)")

    # -- by PIT family --
    by_family: dict[str, int] = {}
    for r in records:
        by_family[r["pit_family"]] = by_family.get(r["pit_family"], 0) + 1
    print("\nBy PIT family (Chapter 3 taxonomy):")
    family_order = [FAMILY_DESIGN, FAMILY_INTEGRATION, FAMILY_OBJECT,
                    FAMILY_GRAMMAR, FAMILY_BEYOND]
    for fam in family_order:
        n = by_family.get(fam, 0)
        label = {
            FAMILY_DESIGN:      "design      (Mutanty projektowe)",
            FAMILY_INTEGRATION: "integration (Mutanty integracyjne)",
            FAMILY_OBJECT:      "object      (Mutanty obiektowe)",
            FAMILY_GRAMMAR:     "grammar     (Mutanty na gramatyce)",
            FAMILY_BEYOND:      "beyond_classic (poza PIT)",
        }[fam]
        bar = "#" * int(n / total * 40) if total else ""
        print(f"  {label:<44} {n:>5}  ({n / total * 100:.1f}%)  {bar}")

    # -- family × model breakdown --
    models = sorted(by_model)
    col_w  = 12
    header = f"{'PIT family':<20}" + "".join(f"{m:>{col_w}}" for m in models)
    print(f"\nPIT family × model breakdown:")
    print(header)
    print("-" * len(header))
    for fam in family_order:
        row = f"{fam:<20}"
        for m in models:
            n = sum(1 for r in records if r["pit_family"] == fam and r["model"] == m)
            row += f"{n:>{col_w}}"
        print(row)

    # -- kill rate per PIT family --
    print("\nKill rate per PIT family:")
    for fam in family_order:
        fam_recs = [r for r in records if r["pit_family"] == fam]
        if not fam_recs:
            continue
        killed = sum(1 for r in fam_recs if r["killed"])
        print(f"  {fam:<20} {killed:>5}/{len(fam_recs):<5}  ({killed / len(fam_recs) * 100:.1f}%)")

    # -- top signals within beyond_classic --
    beyond = [r for r in records if r["pit_family"] == FAMILY_BEYOND]
    if beyond:
        print(f"\nbeyond_classic: {len(beyond)} mutants (sample precode → aftercode):")
        for r in beyond[:10]:
            pre  = r["precode"].strip()[:60]
            post = r["aftercode"].strip()[:60]
            print(f"  [{r['bug_key']}] {pre!r:62}  →  {post!r}")
        if len(beyond) > 10:
            print(f"  … and {len(beyond) - 10} more")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Collect new LLM mutants (not covered by classic PIT) and classify "
            "them into the four PIT operator families from Chapter 3 of the thesis."
        )
    )
    parser.add_argument(
        "--workspace", type=Path, default=DEFAULT_WORKSPACE,
        help=f"Workspace directory (default: {DEFAULT_WORKSPACE})",
    )
    parser.add_argument(
        "--bugs", nargs="*", default=None,
        help="Optional subset of bug keys to analyse (e.g. LANG_1 MATH_5).",
    )
    parser.add_argument(
        "--output-json", type=Path, default=None,
        help="Path for full JSON output (default: new_mutants.json next to workspace).",
    )
    parser.add_argument(
        "--output-csv", type=Path, default=None,
        help="Path for CSV output (default: new_mutants.csv next to workspace).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    workspace = args.workspace.resolve()
    requested = tuple(args.bugs or ())

    print(f"Workspace : {workspace}")
    print(f"Taxonomy  : 4 PIT families from Chapter 3 + beyond_classic")
    records = collect_new_mutants(workspace=workspace, requested_bug_keys=requested)

    out_dir   = workspace.parent
    json_path = args.output_json or (out_dir / "new_mutants.json")
    csv_path  = args.output_csv  or (out_dir / "new_mutants.csv")

    # JSON
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"JSON saved → {json_path}  ({len(records)} records)")

    # CSV
    csv_fields = [
        "bug_key", "project", "model", "mutant_id",
        "filepath", "line", "pit_family", "pit_signals",
        "killed", "precode", "aftercode", "failing_tests",
    ]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            row = {
                **r,
                "pit_signals":   "; ".join(r["pit_signals"]),
                "failing_tests": "; ".join(r["failing_tests"]),
            }
            writer.writerow(row)
    print(f"CSV saved  → {csv_path}  ({len(records)} records)")

    print_summary(records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
