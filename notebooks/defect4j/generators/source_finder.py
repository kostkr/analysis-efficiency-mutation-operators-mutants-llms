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
import shlex
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
        # 1. Modified classes and real source root. Lang uses both
        #    src/main/java and src/java across Defects4J versions.
        classes = self.d4j.export(container_path_fixed, "classes.modified")
        src_root = self._source_root(container_path_fixed)

        # 2. Ensure buggy checkout exists
        if container_path_buggy is None:
            container_path_buggy = (
                f"{self.d4j.workspace}/checkouts/{project}_{bug_id}_b"
            )
            self._ensure_checkout(project, bug_id, "b", container_path_buggy)

        jobs: list[GeneratorJob] = []
        for fqn in classes:
            rel_path = _fqn_to_path(fqn, src_root)

            # 3. Changed lines (in fixed version)
            changed = self._changed_lines(
                container_path_buggy, container_path_fixed, rel_path
            )
            if not changed:
                continue

            # 4. Read fixed source
            src_raw, _, rc = self.d4j.exec(
                f"cat {shlex.quote(container_path_fixed + '/' + rel_path)} 2>/dev/null"
            )
            if rc != 0 or not src_raw.strip():
                continue

            # 5. Find method boundaries and match against changed lines
            class_ranges = _find_class_ranges(src_raw, fqn)
            for m_name, m_start, m_end, m_src in _find_methods(src_raw):
                overlap = [ln for ln in changed if m_start <= ln <= m_end]
                if not overlap:
                    continue
                owner_fqn = _class_fqn_at_line(class_ranges, fqn, m_start)
                if m_name == _simple_class_name(owner_fqn):
                    m_name = "<init>"
                jobs.append(
                    GeneratorJob(
                        project=project,
                        bug_id=bug_id,
                        container_path=container_path_fixed,
                        host_path=host_path,
                        filepath=rel_path,
                        class_fqn=owner_fqn,
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

    def _source_root(self, container_path: str) -> str:
        try:
            lines = self.d4j.export(container_path, "dir.src.classes")
        except RuntimeError:
            return "src/main/java"
        return (lines[-1] if lines else "src/main/java").strip().strip("/") or "src/main/java"

    def _changed_lines(
        self, buggy_path: str, fixed_path: str, rel: str
    ) -> list[int]:
        """Return 1-based line numbers added/changed in the fixed file."""
        out, _, _ = self.d4j.exec(
            "diff -u "
            f"{shlex.quote(buggy_path + '/' + rel)} "
            f"{shlex.quote(fixed_path + '/' + rel)} "
            "2>/dev/null || true"
        )
        return _parse_diff_fixed_lines(out)


# ── Module-level helpers ───────────────────────────────────────────────────────

def _fqn_to_path(fqn: str, src_root: str = "src/main/java") -> str:
    """Convert a fully-qualified Java class name to a relative source path.

    ``org.example.Foo`` → ``src/main/java/org/example/Foo.java``

    Inner classes (``$``) are mapped to their top-level file.
    """
    # Strip inner-class suffix
    top_level = fqn.split("$")[0]
    return src_root.rstrip("/") + "/" + top_level.replace(".", "/") + ".java"


def _simple_class_name(fqn: str) -> str:
    return fqn.rsplit("$", 1)[-1].rsplit(".", 1)[-1]


def _find_class_ranges(source: str, top_fqn: str) -> list[tuple[int, int, str]]:
    ranges: list[tuple[int, int, str]] = []
    for match in re.finditer(r"(?m)^[ \t]*(?:[\w@<>,.?]+\s+)*(?:class|interface|enum)\s+([A-Za-z_$][\w$]*)[^;{}]*\{", source):
        name = match.group(1)
        start = source[:match.start()].count("\n") + 1
        end_pos = _matching_brace(source, match.end() - 1)
        end = source[:end_pos].count("\n") + 1 if end_pos >= 0 else source.count("\n") + 1
        parent = _class_fqn_at_line(ranges, "", start)
        if parent:
            fqn = parent + "$" + name
        else:
            fqn = top_fqn if name == _simple_class_name(top_fqn) else top_fqn + "$" + name
        ranges.append((start, end, fqn))
    return ranges


def _class_fqn_at_line(ranges: list[tuple[int, int, str]], default: str, line: int) -> str:
    owner = default
    best_size: int | None = None
    for start, end, fqn in ranges:
        if start <= line <= end:
            size = end - start
            if best_size is None or size < best_size:
                owner = fqn
                best_size = size
    return owner


def _matching_brace(source: str, open_pos: int) -> int:
    depth = 0
    for pos in range(open_pos, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return pos
    return -1


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
    r"(?m)^[ \t]*(?P<head>(?:(?:public|protected|private|static|final|synchronized|"
    r"abstract|native|strictfp|default)\s+)*(?:<[^>\n]+>\s+)?(?:[\w$\[\]<>,.?]+\s+)*)"
    r"(?P<name>[A-Za-z_$][\w$]*)\s*\([^;{}]*\)"
    r"(?:\s*throws\s+[^;{}]+)?\s*\{"
)


def _find_methods(source: str, class_name: str = "") -> list[tuple[str, int, int, str]]:
    """Find all method bodies in *source*.

    Returns list of ``(method_name, start_line, end_line, method_source)``
    where start/end are 1-based line numbers.
    """
    results: list[tuple[str, int, int, str]] = []

    for m in _METHOD_RE.finditer(source):
        name = m.group("name")
        if name in _JAVA_KEYWORDS:
            continue
        head_words = re.findall(r"[A-Za-z_$][\w$]*", m.group("head"))
        if head_words and head_words[0] in {"return", "new", "if", "for", "while", "switch", "catch"}:
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
        if class_name and name == class_name:
            name = "<init>"
        results.append((name, start_line, end_line, method_src))

    return results


def _parse_diff_fixed_lines(diff: str) -> list[int]:
    """Parse unified diff and return 1-based line numbers added in the fixed file.

    A hunk header ``@@ -a,b +c,d @@`` means the fixed file starts at line *c*.
    Lines prefixed with ``+`` (excluding ``+++``) are new/changed lines.
    Deleted-only hunks are mapped to the current fixed-file cursor so fixes
    that only remove code still select the surrounding method.
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
            lines_out.append(max(cur_line, 1))
        else:
            cur_line += 1  # context line

    return sorted(set(lines_out))



