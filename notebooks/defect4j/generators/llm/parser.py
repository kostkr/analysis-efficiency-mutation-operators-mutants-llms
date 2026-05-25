"""llm/parser.py — Parse the LLM JSON response into a list of raw dicts."""

from __future__ import annotations

import json
import re


def parse_response(text: str) -> list[dict]:
    """Extract a JSON array from the raw LLM response *text*."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
    text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE).strip()
    match = re.search(r"\[.*]", text, re.DOTALL)
    if not match:
        raise ValueError(f"LLM response does not contain a JSON array: {text[:400]}")

    data = json.loads(match.group(0))
    if not isinstance(data, list):
        raise TypeError(f"LLM response must be a JSON array, got {type(data).__name__}")
    return data
