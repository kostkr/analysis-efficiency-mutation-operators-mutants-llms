"""
source_finder.py — Translate a Defects4J bug into GeneratorJob objects.

Algorithm
---------
1. ``defects4j export -p classes.modified``  → list of FQNs
2. Optionally checkout the buggy version if not already present
3. For each modified class:
   a. Convert FQN → relative Java source path (``src/main/java/...``)
   b. Diff buggy vs fixed via ``diff -u`` → changed lines in fixed version
   c. Parse method boundaries in fixed source (brace-counting regex)
   d. Emit a GeneratorJob for each method that overlaps ≥1 changed line
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .base import GeneratorJob

if TYPE_CHECKING:
    from ..container import Defects4J


class SourceFinder:
    """Build :class:`GeneratorJob` list for a given Defects4J bug.

    Parameters
    ----------
    d4j : :class:`~defect4j.container.Defects4J` — container wrapper (must be running)
    """

    def __init__(self, d4j: "Defects4J") -> None:
        self.d4j = d4j

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def find_jobs(
        self,
        project: str,
        bug_id: int,
        container_path_fixed: str,
        container_path_buggy: str | None = None,
        host_path: str = "",
    ) -> list[GeneratorJob]:
        """Return one GeneratorJob per method that overlaps the bug's diff.

        Parameters
        ----------
        project              : e.g. ``"Lang"``
        bug_id               : e.g. ``3``
        container_path_fixed : absolute path inside container (fixed checkout)
        container_path_buggy : optional path to buggy checkout; if *None*,
                               checked out automatically as ``<project>_<id>_b``
        host_path            : optional host-side path (passed through to job)
        """
        # 1. Modified classes
        classes = self.d4j.export(container_path_fixed, "classes.modified")

        # 2. Ensure buggy checkout exists
        if container_path_buggy is None:
            container_path_buggy = (
                f"{self.d4j.workspace}/checkouts/{project}_{bug_id}_b"
            )
            self._ensure_checkout(project, bug_id, "b", container_path_buggy)

        jobs: list[GeneratorJob] = []
        for fqn in classes:
            rel_path = _fqn_to_path(fqn)

            # 3. Changed lines (in fixed version)
            changed = self._changed_lines(
                container_path_buggy, container_path_fixed, rel_path
            )
            if not changed:
                continue

            # 4. Read fixed source
            src_raw, _, rc = self.d4j.exec(
                f"cat {container_path_fixed}/{rel_path} 2>/dev/null"
            )
            if rc != 0 or not src_raw.strip():
                continue

            # 5. Find method boundaries and match against changed lines
            for m_name, m_start, m_end, m_src in _find_methods(src_raw):
                overlap = [ln for ln in changed if m_start <= ln <= m_end]
                if not overlap:
                    continue
                jobs.append(
                    GeneratorJob(
                        project=project,
                        bug_id=bug_id,
                        container_path=container_path_fixed,
                        host_path=host_path,
                        filepath=rel_path,
                        class_fqn=fqn,
                        method_name=m_name,
                        method_source=m_src,
                        method_start=m_start,
                        method_end=m_end,
                        changed_lines=overlap,
                    )
                )

        return jobs

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _ensure_checkout(
        self, project: str, bug_id: int, version: str, path: str
    ) -> None:
        out, _, _ = self.d4j.exec(f'test -d "{path}" && echo ok')
        if "ok" not in out:
            self.d4j.checkout(project, bug_id, version, dest=path, timeout=180)

    def _changed_lines(
        self, buggy_path: str, fixed_path: str, rel: str
    ) -> list[int]:
        """Return 1-based line numbers added/changed in the fixed file."""
        out, _, _ = self.d4j.exec(
            f"diff -u {buggy_path}/{rel} {fixed_path}/{rel} 2>/dev/null || true"
        )
        return _parse_diff_fixed_lines(out)


# ── Module-level helpers ───────────────────────────────────────────────────────

def _fqn_to_path(fqn: str) -> str:
    """Convert a fully-qualified Java class name to a relative source path.

    ``org.example.Foo`` → ``src/main/java/org/example/Foo.java``

    Inner classes (``$``) are mapped to their top-level file.
    """
    # Strip inner-class suffix
    top_level = fqn.split("$")[0]
    return "src/main/java/" + top_level.replace(".", "/") + ".java"


# Java keywords that must NOT be captured as method names
_JAVA_KEYWORDS = frozenset({
    "if", "else", "while", "for", "do", "switch", "case", "try",
    "catch", "finally", "synchronized", "return", "new", "class",
    "interface", "enum", "extends", "implements", "import", "package",
    "static", "final", "abstract", "public", "protected", "private",
    "void", "boolean", "int", "long", "short", "byte", "char",
    "float", "double", "throw", "throws", "instanceof", "this", "super",
    "break", "continue", "default", "assert", "native", "strictfp",
})

# Regex to match Java method declarations (covers most common forms).
# Requires at least one access/modifier keyword OR a non-void return type
# that is NOT a Java keyword, so that `if (...)`, `while (...)` etc. are
# not matched.
_METHOD_RE = re.compile(
    r"(?P<mods>(?:(?:public|protected|private|static|final|synchronized|"
    r"abstract|native|strictfp|default)\s+)+)"  # ≥1 modifier required
    r"(?:<[^>]+>\s+)?"                           # optional generics
    r"[\w\[\]<>,\s]+?\s+"                        # return type
    r"(?P<name>\w+)\s*\([^)]*\)"                 # method name + params
    r"(?:\s*throws\s+[\w\s,]+)?"
    r"\s*\{",
    re.MULTILINE,
)


def _find_methods(source: str) -> list[tuple[str, int, int, str]]:
    """Find all method bodies in *source*.

    Returns list of ``(method_name, start_line, end_line, method_source)``
    where start/end are 1-based line numbers.
    """
    results: list[tuple[str, int, int, str]] = []

    for m in _METHOD_RE.finditer(source):
        name = m.group("name")
        if name in _JAVA_KEYWORDS:
            continue
        # Opening brace is the last character of the regex match
        brace_pos = m.end() - 1
        start_line = source[: m.start()].count("\n") + 1

        # Walk forward counting braces to find the closing '}'
        depth = 0
        end_pos = brace_pos
        for i, ch in enumerate(source[brace_pos:], brace_pos):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end_pos = i
                    break

        end_line = source[:end_pos].count("\n") + 1
        method_src = source[m.start() : end_pos + 1]
        results.append((name, start_line, end_line, method_src))

    return results


def _parse_diff_fixed_lines(diff: str) -> list[int]:
    """Parse unified diff and return 1-based line numbers added in the fixed file.

    A hunk header ``@@ -a,b +c,d @@`` means the fixed file starts at line *c*.
    Lines prefixed with ``+`` (excluding ``+++``) are new/changed lines.
    Context lines (no prefix) and deleted lines (``-``) advance the cursor
    only for the fixed file.
    """
    lines_out: list[int] = []
    cur_line = 0

    for line in diff.splitlines():
        hunk = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if hunk:
            cur_line = int(hunk.group(1))
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            lines_out.append(cur_line)
            cur_line += 1
        elif line.startswith("-"):
            pass  # deleted from buggy — don't advance fixed cursor
        else:
            cur_line += 1  # context line

    return lines_out



