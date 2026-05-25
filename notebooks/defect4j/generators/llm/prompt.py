"""llm/prompt.py — Prompt builder for per-method LLM mutant generation."""

from __future__ import annotations

_SYSTEM = "You are an expert in mutation testing. Make small realistic code changes to reveal weak tests."


ARTICLE_FEW_SHOT_EXAMPLES: list[dict[str, str]] = [
    {
        "correct": "n = (n & (n - 1));",
        "buggy": "n = (n ^ (n - 1));",
    },
    {
        "correct": "while (!queue.isEmpty())",
        "buggy": "while (true)",
    },
    {
        "correct": "return depth==0;",
        "buggy": "return true;",
    },
    {
        "correct": "c = bin_op.apply(b,a);",
        "buggy": "c = bin_op.apply(a,b);",
    },
    {
        "correct": "while(Math.abs(x-approx*approx)>epsilon)",
        "buggy": "while(Math.abs(x-approx)>epsilon)",
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

Above is the original code. your task is to generate '{target_mutants}' mutants,
(notice: mutant refers to the mutant in software engineering, i.e., making subtle
changes to the original code) in: '{code_element}', as follows are some examples
of mutants which you can refer to:

{{
{few_shot_lines}
}}

#Requirement:
1. Provide generated mutants directly
2. A mutation can only occur on one line
3. Your output must be like:
   [ {{ "line": 123, "precode": "", "aftercode": "", "rule": "" }} ],
   where "line" represents the 1-based absolute line number of the mutated line,
   "precode" represents the line of code before mutation and it can not be empty,
   "aftercode" represents the line of code after mutation,
   "rule" is a short mutation-operator name.
4. Prohibit generating the exact same mutants
"""

    return _SYSTEM, user
