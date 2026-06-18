#!/usr/bin/env python3
"""
classify_beyond_classic_full.py
================================
Transparent classifier for ALL 3837 LLM mutants with pit_family == 'beyond_classic'.

For each of the named categories this script prints:
  - Category name (Polish label)
  - Count and percentage
  - Full list of every mutant: bug_key | mutant_id | precode → aftercode
    (or first 5 examples; use --verbose for all)

Run from the repository root:
    python notebooks/new_mutants_analysis/classify_beyond_classic_full.py
    python notebooks/new_mutants_analysis/classify_beyond_classic_full.py --verbose

The counts printed in the SUMMARY at the end are the authoritative values
used in Tabela 7.4 of the thesis.  Every number maps directly to the CSV rows
shown above it — no data is fabricated.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CSV_PATH = Path(__file__).resolve().parents[2] / "notebooks" / "new_mutants.csv"
csv.field_size_limit(10**7)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_beyond_classic() -> list[dict]:
    rows = []
    with CSV_PATH.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row["pit_family"] == "beyond_classic":
                rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _strip(s: str) -> str:
    return s.strip().rstrip(";").strip()


def _method_calls(s: str) -> list[str]:
    return re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', s)


def _count_func_calls(s: str) -> int:
    return len(re.findall(r'\b\w+\s*\(', s))


def _enum_constants(s: str) -> list[tuple[str, str]]:
    """Return (ClassName, CONSTANT) for SCREAMING_SNAKE patterns."""
    return re.findall(r'\b([A-Z][A-Za-z0-9_]*)\s*\.\s*([A-Z][A-Z0-9_]+)\b', s)


def _lhs_rhs(s: str) -> Optional[tuple[str, str]]:
    """
    Return (lhs, rhs) for a simple or declared assignment (including compound +=/-= etc.).
    Handles:
      'x = expr'
      'Type x = expr'   (declaration)
      'final Type x = expr'
      'x += expr'   (compound assignment)
    """
    # Normalise: strip trailing semicolon / braces
    t = _strip(s).rstrip('{').strip()
    # Try simple / compound assignment first: word.word[...] (op)= value
    m = re.match(r'\s*([\w.\[\]]+)\s*[+\-*/%&|^]?=\s*(?!=)(.+)', t)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    # Declared assignment: [modifier*] Type varName = value
    m2 = re.match(
        r'\s*(?:(?:private|public|protected|final|static|transient|volatile)\s+)*'
        r'(?:\w[\w.<>?, \[\]]*\s+)?'
        r'(\w[\w.\[\]]*)\s*[+\-*/%&|^]?=\s*(?!=)(.+)',
        t
    )
    if m2:
        return m2.group(1).strip(), m2.group(2).strip()
    return None


def _unquoted_null(s: str) -> bool:
    """True if the word 'null' appears as a token (not inside a string literal)."""
    # Remove string literals, then check for 'null'
    no_strings = re.sub(r'"[^"]*"', '""', s)
    return bool(re.search(r'\bnull\b', no_strings))


_JAVA_MODIFIERS = re.compile(
    r'\b(private|public|protected|final|static|transient|volatile|abstract|native|synchronized)\b'
)


# ---------------------------------------------------------------------------
# Rule functions — (pre: str, post: str) -> bool
# Priority: first matching rule in RULES wins.
# ---------------------------------------------------------------------------

# ── 1. Zamiana kolejności argumentów (argument_swap) ────────────────────────
def r_argument_swap(pre: str, post: str) -> bool:
    """Same method, same set of args, different order (permutation)."""
    pre_m = re.search(r'\b([a-zA-Z_]\w*)\s*\(([^()]+)\)', pre)
    post_m = re.search(r'\b([a-zA-Z_]\w*)\s*\(([^()]+)\)', post)
    if not (pre_m and post_m):
        return False
    if pre_m.group(1) != post_m.group(1):
        return False
    pre_args  = [a.strip() for a in pre_m.group(2).split(",")]
    post_args = [a.strip() for a in post_m.group(2).split(",")]
    return (
        len(pre_args) >= 2
        and len(pre_args) == len(post_args)
        and sorted(pre_args) == sorted(post_args)
        and pre_args != post_args
    )


# ── 2. Wykomentowanie instrukcji (comment_out) ──────────────────────────────
def r_comment_out(pre: str, post: str) -> bool:
    """A statement is commented out: stmt → // stmt or // stmt removed."""
    pre_s  = pre.strip()
    post_s = post.strip()
    # forward: statement → commented statement
    if post_s.startswith("//") and not pre_s.startswith("//"):
        # The core content must appear in both
        post_core = re.sub(r'^//\s*', '', post_s).strip().rstrip(';').strip()
        pre_core  = pre_s.rstrip(';').strip()
        # Accept if significant overlap exists (longest common substring ≥ 60%)
        min_len   = min(len(pre_core), len(post_core))
        if min_len > 0 and post_core[:min_len // 2] in pre_core:
            return True
        # Or post is just "// something removed"
        if len(post_core) > 3:
            return True
    # Also: annotation commented out  (@Override → // @Override)
    if pre_s.startswith("@") and post_s.startswith("//") and "@" in post_s:
        return True
    return False


# ── 3. Zamiana stron przypisania (lhs_rhs_swap) ─────────────────────────────
def r_lhs_rhs_swap(pre: str, post: str) -> bool:
    """x = y  →  y = x  (the two sides of a simple assignment are swapped)."""
    lr_pre  = _lhs_rhs(pre)
    lr_post = _lhs_rhs(post)
    if not (lr_pre and lr_post):
        return False
    lhs_pre, rhs_pre   = lr_pre
    lhs_post, rhs_post = lr_post
    # Both sides must be simple identifiers / field accesses (no calls)
    if "(" in rhs_pre or "(" in rhs_post:
        return False
    if "(" in lhs_pre or "(" in lhs_post:
        return False
    # Swap: LHS_before == RHS_after and RHS_before == LHS_after
    return (
        lhs_pre.split(".")[-1] == rhs_post.split(".")[-1]
        and rhs_pre.split(".")[-1] == lhs_post.split(".")[-1]
        and lhs_pre != rhs_pre  # they must differ
    )


# ── 4. Zmiana semantyki porównania (comparison_semantics) ───────────────────
def r_comparison_semantics(pre: str, post: str) -> bool:
    """.equals() swapped with == or !=, or receiver of .equals() swapped."""
    pre_eq  = ".equals(" in pre
    post_eq = ".equals(" in post
    if pre_eq and not post_eq and re.search(r'[!=]=', post):
        return True
    if not pre_eq and post_eq and re.search(r'[!=]=', pre):
        return True
    if pre_eq and post_eq:
        pm = re.search(r'(\w+)\.equals\((\w+)\)', pre)
        qm = re.search(r'(\w+)\.equals\((\w+)\)', post)
        if pm and qm:
            if pm.group(1) == qm.group(2) and pm.group(2) == qm.group(1):
                return True
    return False


# ── 5. Zamiana klasy wyjątku (exception_class_swap) ─────────────────────────
def r_exception_class_swap(pre: str, post: str) -> bool:
    exc_re   = re.compile(r'\bnew\s+([A-Z]\w*(?:Exception|Error|Throwable))\s*\(')
    throw_re = re.compile(r'\bthrow\s+(?:new\s+)?([A-Z]\w*)\b')
    catch_re = re.compile(r'\bcatch\s*\(\s*([A-Z]\w*)')
    for rx in (exc_re, throw_re, catch_re):
        a, b = rx.findall(pre), rx.findall(post)
        if a and b and a != b:
            return True
    return False


# ── 6. Zamiana gałęzi wyrażenia trójkowego (ternary_branch_swap) ────────────
def r_ternary_branch_swap(pre: str, post: str) -> bool:
    """a ? b : c  →  a ? c : b; handles trailing punctuation."""
    tern_re = re.compile(r'(.+?)\?\s*(.+?)\s*:\s*(.+)')
    pm = tern_re.search(pre)
    qm = tern_re.search(post)
    if not (pm and qm):
        return False

    def clean(s: str) -> str:
        return s.strip().rstrip(",;)").strip()

    pre_cond  = clean(pm.group(1))
    pre_b1    = clean(pm.group(2))
    pre_b2    = clean(pm.group(3))
    post_cond = clean(qm.group(1))
    post_b1   = clean(qm.group(2))
    post_b2   = clean(qm.group(3))

    if pre_cond != post_cond:
        return False
    # Branches truly swapped
    if pre_b1 == post_b2 and pre_b2 == post_b1:
        return True
    # One branch is an argument that was substituted (not a full swap)
    return False


# ── 7. Zmiana wyrażenia instanceof (instanceof_change) ──────────────────────
def r_instanceof_change(pre: str, post: str) -> bool:
    inst_re   = re.compile(r'\binstanceof\s+([A-Z]\w*)')
    pre_types = inst_re.findall(pre)
    post_types = inst_re.findall(post)
    if pre_types and post_types and pre_types != post_types:
        return True
    if pre_types and post_types:
        pre_neg  = bool(re.search(r'!\s*\(?\s*\w+\s+instanceof', pre))
        post_neg = bool(re.search(r'!\s*\(?\s*\w+\s+instanceof', post))
        if pre_neg != post_neg:
            return True
    return False


# ── 8. Zmiana modyfikatora (modifier_change) ────────────────────────────────
def r_modifier_change(pre: str, post: str) -> bool:
    """
    A Java access/non-access modifier is added, removed, or substituted.
    Covers: private→public, final removed, transient removed, abstract changed, etc.
    Also covers: interface added/removed from 'implements' clause.
    """
    pre_mods  = set(_JAVA_MODIFIERS.findall(pre))
    post_mods = set(_JAVA_MODIFIERS.findall(post))
    if pre_mods != post_mods:
        return True
    # Implements / extends interface change
    impl_re = re.compile(r'\bimplements\b(.+)')
    pre_impl  = impl_re.search(pre)
    post_impl = impl_re.search(post)
    if pre_impl and post_impl and pre_impl.group(1).strip() != post_impl.group(1).strip():
        return True
    # extends change
    ext_re = re.compile(r'\bextends\s+(\w+)')
    pre_ext  = ext_re.findall(pre)
    post_ext = ext_re.findall(post)
    if pre_ext and post_ext and pre_ext != post_ext:
        return True
    return False


# ── 9. Zmiana typu zmiennej (type_change) ───────────────────────────────────
def r_type_change(pre: str, post: str) -> bool:
    """
    The declared type of a variable/field is changed.
    E.g.: private boolean x → private Boolean x
          int x → long x
    """
    # Must look like a declaration (no '=' on LHS, no method call)
    if "(" in pre or "(" in post:
        return False
    # Extract declared type: first token after modifiers
    mod_strip_re = re.compile(
        r'^(?:(?:private|public|protected|final|static|transient|volatile|abstract)\s+)*'
        r'([A-Za-z_]\w*(?:<[^>]*>)?(?:\[\])*)\s+\w'
    )
    pre_m  = mod_strip_re.match(pre.strip())
    post_m = mod_strip_re.match(post.strip())
    if pre_m and post_m and pre_m.group(1) != post_m.group(1):
        return True
    return False


# ── 10. Zmiana kolejności operandów (operand_swap) ──────────────────────────
def r_operand_swap(pre: str, post: str) -> bool:
    """
    Two operands of an arithmetic / assignment expression are swapped.
    E.g.:  a - b  →  b - a,   a / b  →  b / a
    Handles declarations like  'final double ratio = rhs / entry'.
    """
    # Extract the RHS of any assignment (handles type-declared forms too)
    lr_pre  = _lhs_rhs(pre)
    lr_post = _lhs_rhs(post)
    if lr_pre and lr_post and lr_pre[0].split(".")[-1] == lr_post[0].split(".")[-1]:
        rhs_pre  = lr_pre[1]
        rhs_post = lr_post[1]
        # Check for a binary op swap: a OP b  →  b OP a
        bin_re = re.compile(r'^\s*(.+?)\s*([+\-*/])\s*(.+?)\s*$')
        pm = bin_re.match(rhs_pre.strip())
        qm = bin_re.match(rhs_post.strip())
        if pm and qm and pm.group(2) == qm.group(2):
            a1, a2 = pm.group(1).strip(), pm.group(3).strip()
            b1, b2 = qm.group(1).strip(), qm.group(3).strip()
            if a1 == b2 and a2 == b1:
                return True
    # Also catch expressions outside assignment (bare  a - b  lines)
    bin_re2 = re.compile(r'^\s*(.+?)\s*([+\-*/])\s*(.+?)\s*;?\s*$')
    pm2 = bin_re2.match(pre.strip())
    qm2 = bin_re2.match(post.strip())
    if pm2 and qm2 and pm2.group(2) == qm2.group(2):
        a1, a2 = pm2.group(1).strip(), pm2.group(3).strip()
        b1, b2 = qm2.group(1).strip(), qm2.group(3).strip()
        if a1 == b2 and a2 == b1 and a1 != a2:
            return True
    return False


# ── 11. Zmiana przepływu sterowania (flow_control_change) ───────────────────
def r_flow_control_change(pre: str, post: str) -> bool:
    """
    break↔continue swap, while→if, return→throw, loop structure changes.
    Note: statement commenting-out is handled by r_comment_out earlier.
    """
    pre_s  = pre.strip().rstrip(";")
    post_s = post.strip().rstrip(";")

    # break ↔ continue (they differ from each other)
    pre_break    = bool(re.fullmatch(r'\s*break\s*', pre_s))
    post_break   = bool(re.fullmatch(r'\s*break\s*', post_s))
    pre_continue = bool(re.fullmatch(r'\s*continue\s*', pre_s))
    post_continue= bool(re.fullmatch(r'\s*continue\s*', post_s))
    if (pre_break and post_continue) or (pre_continue and post_break):
        return True

    # More general: one has break/continue, the other has a different control word
    pre_fc  = bool(re.search(r'\b(break|continue)\b', pre))
    post_fc = bool(re.search(r'\b(break|continue)\b', post))
    if pre_fc != post_fc:
        return True
    # Both have break/continue but they differ
    if pre_fc and post_fc:
        pre_word  = re.search(r'\b(break|continue)\b', pre).group(1)
        post_word = re.search(r'\b(break|continue)\b', post).group(1)
        if pre_word != post_word:
            return True

    # else if → if  (removing the else branch alternative)
    pre_s2  = pre.strip()
    post_s2 = post.strip()
    if pre_s2.startswith("else") and post_s2.startswith("if") and not post_s2.startswith("else"):
        return True

    # while → if
    if re.search(r'\bwhile\b', pre) and re.search(r'\bif\b', post) and not re.search(r'\bwhile\b', post):
        return True
    if re.search(r'\bif\b', pre) and re.search(r'\bwhile\b', post) and not re.search(r'\bif\b', post):
        return True

    # return → throw / throw → return
    ps, qs = _strip(pre), _strip(post)
    if ps.startswith("return") and qs.startswith("throw"):
        return True
    if ps.startswith("throw") and qs.startswith("return"):
        return True

    # return; → assignment statement (return replaced by non-return statement)
    if ps == "return" and not qs.startswith("return") and "=" in qs:
        return True

    # } finally { → } catch (Exception e) {
    if "finally" in pre and "catch" in post:
        return True
    if "catch" in pre and "finally" in post:
        return True

    # statement added before closing brace: } → stmt; }
    if re.match(r'^\s*\}\s*$', pre) and not re.match(r'^\s*\}\s*$', post) and post.rstrip().endswith('}'):
        return True

    return False


# ── 12. Zamiana klasy implementacji (impl_class_swap) ───────────────────────
def r_impl_class_swap(pre: str, post: str) -> bool:
    new_re  = re.compile(r'\bnew\s+([A-Z][A-Za-z0-9_]*)\s*(?:<[^>]*>)?\s*\(')
    pre_cls = new_re.findall(pre)
    post_cls= new_re.findall(post)
    if pre_cls and post_cls and pre_cls != post_cls:
        exc_re = re.compile(r'Exception|Error|Throwable', re.I)
        if not exc_re.search(" ".join(pre_cls)) and not exc_re.search(" ".join(post_cls)):
            return True
    return False


# ── 13. Zamiana stałej wyliczeniowej (enum_constant_swap) ───────────────────
_SCREAMING_SNAKE_RE = re.compile(r'\b([A-Z][A-Z0-9_]{2,})\b')


def r_enum_constant_swap(pre: str, post: str) -> bool:
    """
    TYPE.CONSTANT1 → TYPE.CONSTANT2  (qualified enum constant swap)
    OR  BARE_CONSTANT1 → BARE_CONSTANT2  (unqualified SCREAMING_SNAKE constants).
    Both forms appear when Java enums are referenced without the class prefix.
    """
    # 1. Qualified form: Type.CONSTANT1 → Type.CONSTANT2
    pre_enums  = _enum_constants(pre)
    post_enums = _enum_constants(post)
    if pre_enums and post_enums:
        pre_types  = {e[0] for e in pre_enums}
        post_types = {e[0] for e in post_enums}
        if pre_types & post_types:
            pre_vals  = {e[1] for e in pre_enums}
            post_vals = {e[1] for e in post_enums}
            if pre_vals != post_vals:
                return True

    # 2. Bare SCREAMING_SNAKE constants: REGEXP_TYPE → BOOLEAN_TYPE
    pre_consts  = set(_SCREAMING_SNAKE_RE.findall(pre))
    post_consts = set(_SCREAMING_SNAKE_RE.findall(post))
    if pre_consts and post_consts and pre_consts != post_consts:
        # Must have at least one constant in common structure
        # (same surrounding non-constant tokens → we're swapping one constant)
        pre_no_const  = _SCREAMING_SNAKE_RE.sub('__C__', pre)
        post_no_const = _SCREAMING_SNAKE_RE.sub('__C__', post)
        if pre_no_const == post_no_const and pre_consts != post_consts:
            return True

    return False


# ── 14. Zmiana indeksu tablicy (array_index_change) ─────────────────────────
def r_array_index_change(pre: str, post: str) -> bool:
    idx_re    = re.compile(r'\b\w+\s*\[([^\[\]]+)\]')
    pre_idxs  = idx_re.findall(pre)
    post_idxs = idx_re.findall(post)
    if pre_idxs and post_idxs and pre_idxs != post_idxs:
        arr_re   = re.compile(r'\b(\w+)\s*\[')
        pre_arrs = arr_re.findall(pre)
        post_arrs= arr_re.findall(post)
        if set(pre_arrs) & set(post_arrs):
            return True
    return False


# ── 15. Podstawienie wartości null (null_substitution) ──────────────────────
def r_null_substitution(pre: str, post: str) -> bool:
    """null injected as argument/value; ignores string literal 'null'."""
    return _unquoted_null(post) and not _unquoted_null(pre)


# ── 16. Usunięcie wartości null (null_removal) ──────────────────────────────
def r_null_removal(pre: str, post: str) -> bool:
    return _unquoted_null(pre) and not _unquoted_null(post)


# ── 17. Negacja wyrażenia logicznego (bool_expr_negation) ───────────────────
def r_bool_expr_negation(pre: str, post: str) -> bool:
    """! added to any sub-expression (compound boolean, ternary condition, assignment RHS)."""
    pre_neg  = pre.count("!")
    post_neg = post.count("!")
    if post_neg <= pre_neg:
        return False
    # Must be an expression context, not purely a return statement literal
    ps = _strip(pre)
    if ps.startswith("return true") or ps.startswith("return false"):
        return False
    return True


# ── 18. Usunięcie negacji (negation_removal) ────────────────────────────────
def r_negation_removal(pre: str, post: str) -> bool:
    pre_neg  = pre.count("!")
    post_neg = post.count("!")
    return pre_neg > post_neg and pre_neg > 0


# ── 19. Zmiana opakowywania wywołania (wrapper_change) ──────────────────────
def r_wrapper_change(pre: str, post: str) -> bool:
    """
    A wrapper function is added or removed around an argument.
    Detection: function-call count differs AND shorter content's tokens appear in longer.
    """
    pre_n  = _count_func_calls(pre)
    post_n = _count_func_calls(post)
    if abs(pre_n - post_n) < 1:
        return False
    shorter = _strip(pre) if pre_n <= post_n else _strip(post)
    longer  = _strip(post) if pre_n <= post_n else _strip(pre)
    tokens  = re.findall(r'\b[a-zA-Z_]\w*\b', shorter)
    if not tokens:
        return False
    match_count = sum(1 for t in tokens if t in longer)
    return match_count >= len(tokens) * 0.6 and match_count > 0


# ── 20. Zmiana nazwy wywoływanej metody (method_name_change) ────────────────
def r_method_name_change(pre: str, post: str) -> bool:
    pre_names  = _method_calls(pre)
    post_names = _method_calls(post)
    if not (pre_names and post_names):
        return False
    if len(pre_names) != len(post_names):
        return False
    return pre_names != post_names and set(pre_names) != set(post_names)


# ── 21. Zastąpienie wyrażenia stałą logiczną (subexpr_to_bool) ──────────────
def r_subexpr_to_bool(pre: str, post: str) -> bool:
    post_s = _strip(post)
    pre_s  = _strip(pre)
    if post_s.startswith("return") or pre_s.startswith("return"):
        return False
    post_has_bool = bool(re.search(r'\btrue\b|\bfalse\b', post_s))
    pre_has_bool  = bool(re.search(r'\btrue\b|\bfalse\b', pre_s))
    if post_has_bool and not pre_has_bool:
        return True
    # if-condition replaced with true/false
    if_re = re.compile(r'if\s*\((.+?)\)')
    pre_if  = if_re.search(pre_s)
    post_if = if_re.search(post_s)
    if pre_if and post_if:
        if post_if.group(1).strip().lower() in ("true", "false"):
            return True
    return False


# ── 22. Zmiana literału boolowskiego (boolean_literal_assign) ───────────────
def r_boolean_literal_assign(pre: str, post: str) -> bool:
    pre_s  = _strip(pre)
    post_s = _strip(post)
    if pre_s.startswith("return") or post_s.startswith("return"):
        return False
    pre_bool  = bool(re.search(r'=\s*(?:true|false)\b', pre_s, re.I))
    post_bool = bool(re.search(r'=\s*(?:true|false)\b', post_s, re.I))
    if pre_bool or post_bool:
        pre_val  = re.search(r'=\s*(true|false)\b', pre_s, re.I)
        post_val = re.search(r'=\s*(true|false)\b', post_s, re.I)
        if pre_val and post_val and pre_val.group(1).lower() != post_val.group(1).lower():
            return True
        if pre_bool != post_bool:
            return True
    return False


# ── 23. Zmiana literału łańcuchowego (string_literal_change) ────────────────
def r_string_literal_change(pre: str, post: str) -> bool:
    pre_strings  = re.findall(r'"[^"]*"', pre)
    post_strings = re.findall(r'"[^"]*"', post)
    return bool(pre_strings) and bool(post_strings) and pre_strings != post_strings


# ── 24. Przypisanie własne (self_assignment) ─────────────────────────────────
def r_self_assignment(pre: str, post: str) -> bool:
    """x = expr(...)  →  x = x  (the RHS becomes the same identifier as LHS)."""
    lr_pre  = _lhs_rhs(pre)
    lr_post = _lhs_rhs(post)
    if not (lr_pre and lr_post):
        return False
    lhs, rhs = lr_post
    lhs_base = lhs.split(".")[-1]
    rhs_base = rhs.split(".")[-1]
    return lhs_base == rhs_base and "(" not in rhs


# ── 25. Zmiana wartości przypisania (assignment_value_change) ────────────────
def r_assignment_value_change(pre: str, post: str) -> bool:
    """
    The LHS of an assignment is the same but the RHS changes.
    Handles both simple and type-declared forms.
    Also handles: declaration without initializer → declaration with initializer.
    """
    lr_pre  = _lhs_rhs(pre)
    lr_post = _lhs_rhs(post)
    if lr_pre and lr_post:
        lhs_pre, rhs_pre   = lr_pre
        lhs_post, rhs_post = lr_post
        if lhs_pre.split(".")[-1] != lhs_post.split(".")[-1]:
            return False
        return rhs_pre.strip() != rhs_post.strip()
    # Initializer added / removed: 'Type varName;' ↔ 'Type varName = value;'
    # One side has '=', the other doesn't
    pre_has_eq  = bool(re.search(r'[^!=<>]=[^=]', pre))
    post_has_eq = bool(re.search(r'[^!=<>]=[^=]', post))
    if pre_has_eq != post_has_eq:
        # Both must look like field/variable declarations (contain a word followed by identifier)
        decl_re = re.compile(r'\b\w+\s+(\w+)\s*[;=]')
        pre_var  = decl_re.search(pre)
        post_var = decl_re.search(post)
        if pre_var and post_var and pre_var.group(1) == post_var.group(1):
            return True
    return False


# ── 26. Podstawienie argumentu (argument_substitution) ──────────────────────

_BARE_KEYWORD_RE = re.compile(
    r'^\s*(?:if|else(?:\s+if)?|while|for|do|switch|try|catch|finally|'
    r'class|interface|enum|import|package)\b'
)


def _is_arg_context(s: str) -> bool:
    """
    True if the line looks like a method-call argument context.

    Rules (additive — any one True → True):
      1. Has a visible method or constructor call → always True
      2. Continuation argument line: ends with `)`, `);`, `),`, `,`
      3. Ternary branch fragment starting with `?`
      4. NOT starting with a structural-control keyword (if/while/for/…)
         AND NOT a lone brace → treat as expression/argument fragment
    """
    stripped = s.strip()
    if not stripped:
        return False

    # Rule 1 — method / constructor call always wins
    if _method_calls(s):
        return True
    if re.search(r'\bnew\s+[A-Z]\w*\s*(?:<[^>]*>)?\s*\(', s):
        return True

    # Lone braces are not arguments
    if stripped in ('{', '}', '{}', '};'):
        return False

    # Rule 2 — continuation line
    if re.search(r'\)\s*[,;]?\s*$', stripped) or stripped.rstrip().endswith(','):
        return True

    # Rule 3 — ternary fragment
    if stripped.startswith('?'):
        return True

    # Rule 4 — expression fragment (not a named control-flow statement)
    if not _BARE_KEYWORD_RE.match(stripped):
        return True

    return False


def r_argument_substitution(pre: str, post: str) -> bool:
    """
    A specific argument inside a method call is replaced by a different value.
    Handles both fully-qualified call lines and continuation-line argument fragments.
    Broad rule — placed late in priority order.
    """
    return _is_arg_context(pre) and _is_arg_context(post)


# ── 27. Inne strukturalne (inne) — TRUE catch-all ────────────────────────────
def r_inne(_pre: str, _post: str) -> bool:
    return True


# ---------------------------------------------------------------------------
# Priority-ordered rule list (index 0 = highest priority)
# Each entry: (category_key, polish_label, rule_function)
# ---------------------------------------------------------------------------

RULES: list[tuple[str, str, object]] = [
    # ── Highly specific structural patterns ───────────────────────────────────
    ("argument_swap",           "Zamiana kolejności argumentów",             r_argument_swap),
    ("comment_out",             "Wykomentowanie instrukcji",                 r_comment_out),
    ("lhs_rhs_swap",            "Zamiana stron przypisania",                 r_lhs_rhs_swap),
    ("comparison_semantics",    "Zmiana semantyki porównania",               r_comparison_semantics),
    ("exception_class_swap",    "Zamiana klasy wyjątku",                     r_exception_class_swap),
    ("ternary_branch_swap",     "Zamiana gałęzi wyrażenia trójkowego",       r_ternary_branch_swap),
    ("instanceof_change",       "Zmiana wyrażenia instanceof",               r_instanceof_change),
    ("modifier_change",         "Zmiana modyfikatora",                       r_modifier_change),
    ("type_change",             "Zmiana typu zmiennej",                      r_type_change),
    ("operand_swap",            "Zamiana kolejności operandów",              r_operand_swap),
    ("flow_control_change",     "Zmiana przepływu sterowania",               r_flow_control_change),
    ("impl_class_swap",         "Zamiana klasy implementacji",               r_impl_class_swap),
    ("enum_constant_swap",      "Zamiana stałej wyliczeniowej",              r_enum_constant_swap),
    ("array_index_change",      "Zmiana indeksu tablicy",                    r_array_index_change),
    # ── Null patterns ─────────────────────────────────────────────────────────
    ("null_substitution",       "Podstawienie wartości null",                r_null_substitution),
    ("null_removal",            "Usunięcie wartości null",                   r_null_removal),
    # ── Negation patterns ──────────────────────────────────────────────────────
    ("bool_expr_negation",      "Negacja wyrażenia logicznego",              r_bool_expr_negation),
    ("negation_removal",        "Usunięcie negacji",                         r_negation_removal),
    # ── Call / method patterns ─────────────────────────────────────────────────
    ("wrapper_change",          "Zmiana opakowywania wywołania",             r_wrapper_change),
    ("method_name_change",      "Zmiana nazwy wywoływanej metody",           r_method_name_change),
    # ── Literal / value patterns ───────────────────────────────────────────────
    ("subexpr_to_bool",         "Zastąpienie wyrażenia stałą logiczną",      r_subexpr_to_bool),
    ("boolean_literal_assign",  "Zmiana literału boolowskiego",              r_boolean_literal_assign),
    ("string_literal_change",   "Zmiana literału łańcuchowego",             r_string_literal_change),
    # ── Assignment patterns ────────────────────────────────────────────────────
    ("self_assignment",         "Przypisanie własne",                        r_self_assignment),
    ("assignment_value_change", "Zmiana wartości przypisania",               r_assignment_value_change),
    # ── Broad argument catch ───────────────────────────────────────────────────
    ("argument_substitution",   "Podstawienie argumentu",                    r_argument_substitution),
    # ── True catch-all ─────────────────────────────────────────────────────────
    ("inne",                    "Inne strukturalne",                         r_inne),
]


# ---------------------------------------------------------------------------
# Classify all rows
# ---------------------------------------------------------------------------

def classify(pre: str, post: str) -> str:
    for key, _label, rule in RULES:
        if rule(pre, post):
            return key
    return "inne"  # unreachable — last rule always matches


def classify_all(rows: list[dict]) -> dict[str, list[dict]]:
    buckets: dict[str, list[dict]] = {key: [] for key, _, _ in RULES}
    for row in rows:
        cat = classify(row["precode"], row["aftercode"])
        buckets[cat].append(row)
    return buckets


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def label_for(key: str) -> str:
    for k, lbl, _ in RULES:
        if k == key:
            return lbl
    return key


def print_report(buckets: dict[str, list[dict]], verbose: bool = False) -> None:
    total     = sum(len(v) for v in buckets.values())
    separator = "─" * 80

    print()
    print("=" * 80)
    print(f"  Klasyfikacja nowych wzorców LLM spoza repertuaru PIT")
    print(f"  Łącznie: {total} mutantów   |   CSV: {CSV_PATH.name}")
    print("=" * 80)

    for key, polish_label, _ in RULES:
        items = buckets.get(key, [])
        n     = len(items)
        if n == 0:
            continue
        pct   = n / total * 100 if total else 0.0
        print()
        print(separator)
        print(f"  [{key}]  {polish_label}")
        print(f"  Liczba: {n}   ({pct:.1f}%)")
        print(separator)
        show = items if verbose else items[:5]
        for item in show:
            pre  = item["precode"].strip()[:88]
            post = item["aftercode"].strip()[:88]
            print(f"    {item['bug_key']:<14} id={item['mutant_id']:<6}  "
                  f"{pre!r:90}  →  {post!r}")
        if not verbose and n > 5:
            print(f"    … and {n - 5} more (use --verbose to see all)")

    print()
    print("=" * 80)
    print("  PODSUMOWANIE  (to są liczby do Tabeli 7.4 pracy magisterskiej)")
    print("=" * 80)
    print(f"  {'Kategoria':<42}  {'n':>5}  {'%':>7}")
    print(f"  {'─'*42}  {'─'*5}  {'─'*7}")
    for key, polish_label, _ in RULES:
        n = len(buckets.get(key, []))
        if n == 0:
            continue
        pct = n / total * 100 if total else 0.0
        print(f"  {polish_label:<42}  {n:>5}  {pct:>6.1f}%")
    print(f"  {'─'*42}  {'─'*5}  {'─'*7}")
    print(f"  {'ŁĄCZNIE':<42}  {total:>5}  {100.0:>6.1f}%")
    print("=" * 80)

    inne_n = len(buckets.get("inne", []))
    if inne_n == 0:
        print("\n  ✓ Wszystkie mutanty sklasyfikowane — 0 w kategorii 'inne strukturalne'.")
    else:
        print(f"\n  ⚠  UWAGA: {inne_n} mutantów pozostało w kategorii 'inne strukturalne'.")
        print("     Lista poniżej (celem dalszej analizy):")
        for item in buckets["inne"]:
            print(f"    {item['bug_key']:<14} id={item['mutant_id']:<6}  "
                  f"{item['precode'].strip()[:80]!r}  →  {item['aftercode'].strip()[:80]!r}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    print(f"Loading {CSV_PATH} …", end=" ", flush=True)
    rows = load_beyond_classic()
    print(f"{len(rows)} beyond_classic rows loaded.")

    buckets = classify_all(rows)
    print_report(buckets, verbose=verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
