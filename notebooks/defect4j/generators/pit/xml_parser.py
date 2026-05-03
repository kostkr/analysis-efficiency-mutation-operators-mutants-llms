"""
pit/xml_parser.py — raw PIT XML parser.

Design goal
-----------
Do NOT guess or emulate PIT operators at source level.
Do NOT maintain allow-lists / deny-lists of mutators.
Do NOT try to synthesise ``aftercode``.

This module simply parses every ``<mutation>`` entry that PIT produced and
returns raw metadata so the caller can save *all* generated mutants exactly as
PIT reported them.

Why this is simpler and safer
-----------------------------
PIT mutates bytecode, not source lines.  Trying to reconstruct source-level
``aftercode`` for every operator leads to many false transformations and loss of
entries.  Instead we keep PIT's own metadata intact:
- lineNumber
- mutator FQN / short name
- mutatedMethod
- description
- status / detected / numberOfTestsRun / killingTest
- indexes / blocks / methodDescription

The generator can then write all reported entries into ``classic.json``.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET


def rule_name(mutator_fqn: str, description: str = "") -> str:
    """Return a readable operator name from PIT's mutator class name.

    Examples
    --------
    ``org.pitest...ConditionalsBoundaryMutator`` → ``Conditionals Boundary``
    ``org.pitest...NullReturnValsMutator``       → ``Null Return Vals``

    If the mutator text is missing, fall back to ``description``.
    """
    short = (mutator_fqn or "").strip().split(".")[-1]
    if not short:
        return description or "PIT"
    short = re.sub(r"Mutator$", "", short, flags=re.IGNORECASE)
    short = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", short)
    short = short.replace("_", " ").strip()
    return short or description or "PIT"


def parse_mutation_entries(xml_text: str) -> list[dict]:
    """Parse *all* PIT ``mutations.xml`` entries as raw records.

    Returns a list of dicts. No filtering, no transformation, no operator-specific
    logic. Every returned dict contains at least:

    - ``line``              : PIT XML ``lineNumber`` (int, or 0 if missing)
    - ``filepath``          : inferred relative Java path
    - ``mutated_method``    : PIT XML ``mutatedMethod``
    - ``mutator``           : full PIT mutator FQN
    - ``rule``              : readable operator name derived from mutator class name
    - ``description``       : PIT XML description
    - ``status``            : KILLED / SURVIVED / NO_COVERAGE / ...
    - ``detected``          : bool
    - ``number_of_tests_run`` : int
    - ``killing_test``      : killing test name (if any)
    - ``index``             : first PIT index (if present, else -1)
    - ``indexes``           : all PIT indexes
    - ``blocks``            : all PIT blocks
    - ``mutated_class``     : FQN of mutated class
    - ``method_description``: bytecode method descriptor
    - ``source_file``       : simple source file name reported by PIT
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        print(f"[pit/xml_parser] XML parse error: {exc}")
        return []

    results: list[dict] = []

    for m in root.findall("mutation"):
        mutator_fqn = (m.findtext("mutator") or "").strip()
        mutated_method = (m.findtext("mutatedMethod") or "").strip()
        mutated_class = (m.findtext("mutatedClass") or "").strip()
        method_description = (m.findtext("methodDescription") or "").strip()
        source_file = (m.findtext("sourceFile") or "").strip()
        description = (m.findtext("description") or "").strip()
        killing_test = (m.findtext("killingTest") or "").strip()

        try:
            line_num = int((m.findtext("lineNumber") or "0").strip())
        except ValueError:
            line_num = 0

        try:
            tests_run = int((m.attrib.get("numberOfTestsRun") or "0").strip())
        except ValueError:
            tests_run = 0

        detected = str(m.attrib.get("detected", "")).strip().lower() == "true"
        status = str(m.attrib.get("status", "")).strip()

        indexes_parent = m.find("indexes")
        blocks_parent = m.find("blocks")
        indexes = []
        blocks = []
        if indexes_parent is not None:
            for idx in indexes_parent.findall("index"):
                try:
                    indexes.append(int((idx.text or "").strip()))
                except ValueError:
                    pass
        if blocks_parent is not None:
            for blk in blocks_parent.findall("block"):
                try:
                    blocks.append(int((blk.text or "").strip()))
                except ValueError:
                    pass

        results.append(
            {
                "line": line_num,
                "filepath": _class_to_rel_path(mutated_class, source_file),
                "precode": "",          # filled later by generator if possible
                "aftercode": "",        # intentionally not guessed here
                "rule": rule_name(mutator_fqn, description),
                "mutator": mutator_fqn,
                "description": description,
                "mutated_method": mutated_method,
                "mutated_class": mutated_class,
                "method_description": method_description,
                "source_file": source_file,
                "status": status,
                "detected": detected,
                "number_of_tests_run": tests_run,
                "killing_test": killing_test,
                "index": indexes[0] if indexes else -1,
                "indexes": indexes,
                "blocks": blocks,
            }
        )

    return results


def parse_mutations_xml(xml_text: str, source_lines: list[str]) -> list[dict]:
    """Backward-compatible wrapper returning PIT raw entries with optional precode.

    ``aftercode`` is intentionally left empty because we no longer guess source-level
    transformations.
    """
    results = []
    for item in parse_mutation_entries(xml_text):
        line_num = int(item.get("line", 0))
        if 1 <= line_num <= len(source_lines):
            item = dict(item)
            item["precode"] = source_lines[line_num - 1].rstrip("\r\n").strip()
        results.append(item)
    return results


def _class_to_rel_path(fqn: str, src_file: str) -> str:
    """Build a relative source path from a FQN and a source file name."""
    if not fqn:
        return src_file
    top_fqn = fqn.split("$")[0]
    parts = top_fqn.split(".")
    pkg_dir = "/".join(parts[:-1])
    filename = src_file if src_file else parts[-1] + ".java"
    return f"src/main/java/{pkg_dir}/{filename}"
