"""pit/xml_parser.py — tiny parser for direct ``CLASSIC_JSON`` PIT output.

The custom bundled PIT listener already emits source-ready classic mutant
records, so this module only converts those JSON objects into a small typed DTO.
"""

from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass(slots=True)
class PITClassicEntry:
    filepath: str
    line: int
    precode: str
    aftercode: str
    rule: str


def parse_classic_entries(payload: str) -> list[PITClassicEntry]:
    text = (payload or "").strip()
    if not text:
        return []

    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"[pit/xml_parser] JSON parse error: {exc}")
        return []

    records = raw.get("mutations", []) if isinstance(raw, dict) else raw
    if not isinstance(records, list):
        return []

    return [_entry_from_dict(item) for item in records if isinstance(item, dict)]


def _entry_from_dict(item: dict) -> PITClassicEntry:
    return PITClassicEntry(
        filepath=str(item.get("filepath", "")).strip(),
        line=_as_int(item.get("line")),
        precode=str(item.get("precode", "")).strip(),
        aftercode=str(item.get("aftercode", "")).strip(),
        rule=_normalize_rule(item.get("rule", "")),
    )


def _as_int(value: object) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def _normalize_rule(value: object) -> str:
    rule = str(value or "").strip()
    if not rule:
        return ""
    marker = rule.find(" (")
    return rule[:marker].strip() if marker != -1 else rule
