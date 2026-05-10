"""
llm/parser.py — Parse the LLM JSON response into a list of raw dicts.

The LLM is asked to return a JSON array. In practice it may wrap the array
in markdown code fences or add preamble text — this module handles that
gracefully.
"""

from __future__ import annotations

import json
import re


def parse_response(text: str) -> list[dict]:
    """Extract a JSON array from the raw LLM response *text*.

    Returns a list of dicts; each dict must contain at least:
    ``id``, ``line``, ``precode``, ``aftercode``, ``filepath``.

    Invalid entries are silently skipped.
    """
    # Strip common reasoning wrappers before searching for the JSON array.
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
    text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE).strip()

    # Find the first [...] block in the text
    match = re.search(r"\[.*]", text, re.DOTALL)
    if not match:
        return []

    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    required = {"precode", "aftercode", "line", "filepath"}
    return [
        item
        for item in data
        if isinstance(item, dict) and required.issubset(item.keys())
    ]
