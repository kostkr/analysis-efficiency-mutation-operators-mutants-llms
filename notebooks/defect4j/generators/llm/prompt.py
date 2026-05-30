"""llm/prompt.py — Prompt builder for per-method LLM mutant generation."""

from __future__ import annotations

_SYSTEM = (
    "You are an expert in mutation testing. "
    "Make small realistic code changes that imitate real bugs, producing syntactically valid "
    "and likely compilable single-line mutants that reveal weak tests."
)

ARTICLE_FEW_SHOT_EXAMPLES: list[dict[str, str]] = [
    {
        "correct": "if (a > 0 && b > 0) {",
        "buggy": "if (a > 0 || b > 0) {",
    },
    {
        "correct": "if (index >= size) {",
        "buggy": "if (index > size) {",
    },
    {
        "correct": "for (int i = 0; i < list.size(); i++) {",
        "buggy": "for (int i = 0; i <= list.size(); i++) {",
    },
    {
        "correct": "total = total + price;",
        "buggy": "total = total - price;",
    },
    {
        "correct": "c = bin_op.apply(b, a);",
        "buggy": "c = bin_op.apply(a, b);",
    },
]


def build_prompt(
    method_source: str,
    target_mutants: int,
    code_element: str,
    method_start_line: int = 1,
) -> tuple[str, str]:
    """Build the ``(system_prompt, user_prompt)`` pair for one source method."""
    source_lines = method_source.splitlines()
    numbered = "\n".join(
        f"{method_start_line + i:4d}:  {line}"
        for i, line in enumerate(source_lines)
    )

    few_shot_lines = "\n".join(
        "...\n"
        f'  "precode": {example["correct"]!r},\n'
        f'  "aftercode": {example["buggy"]!r},\n'
        "..."
        for example in ARTICLE_FEW_SHOT_EXAMPLES
    )

    user = f"""{numbered}

Above is the original code. Your task is to generate '{target_mutants}' high-value mutants,
(notice: mutant refers to the mutant in software testing — subtle code changes
that reveal weak tests) in: '{code_element}'. Refer to these examples:

{{
{few_shot_lines}
}}

#Requirement:
1. Provide generated mutants directly
2. A mutation can only occur on one line
3. Your output must be like:
   [ {{ "line": 123, "precode": "", "aftercode": "", "rule": "" }} ],
   where "line" represents the 1-based absolute line number of the mutated line,
   "precode" represents the original line of code before mutation and it can not be empty,
   "aftercode" represents the mutated line of ode after mutation and should be a valid line replacement,
   "rule" is a short mutation-operator name, for example "Conditionals Boundary"
4. Prohibit generating the exact same mutants
"""

    return _SYSTEM, user
