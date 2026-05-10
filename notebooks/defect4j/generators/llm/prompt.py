"""llm/prompt.py — Prompt builder for article-style LLM mutant generation."""

from __future__ import annotations

_SYSTEM = ""


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
        "correct": "ArrayList r = new ArrayList();\nr.add(first).addAll(subset);\nto_add.add(r);",
        "buggy": "to_add.addAll(subset);",
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
    filepath: str,
    target_mutants: int,
    code_element: str = (
        "all single-line Java statements and expressions"
    ),
    method_start_line: int = 1,
) -> tuple[str, str]:
    """Build the article-style ``(system_prompt, user_prompt)`` pair."""
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
   [ {{ "id": 1, "line": 123, "precode": "", "filepath": "{filepath}", "aftercode": "", "rule": "Conditionals Boundary (<= -> <)" }} ],
   where "id" stands for the mutant serial number, "line" represents the 1-based absolute line number of the mutated line,
   "precode" represents the line of code before mutation and it can not be empty,
    "aftercode" represents the line of code after mutation,
    and "rule" is a short mutation-operator name in the style "Operator Name"
5. Prohibit generating the exact same mutants
6. All write in a JSON file"""

    return _SYSTEM, user
