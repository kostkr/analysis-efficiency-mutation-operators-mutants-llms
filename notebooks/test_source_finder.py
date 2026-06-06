import difflib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from defect4j.generators.pit.generator import PITGenerator
from defect4j.generators.source_finder import SourceFinder, _fqn_to_path
from defect4j.generators.base import PITConfig


_FIXED_SOURCE = """package com.google.gson.internal;

final class $Gson$Types {
  static int value() {
    return 2;
  }
}
"""

_BUGGY_SOURCE = """package com.google.gson.internal;

final class $Gson$Types {
  static int value() {
    return 1;
  }
}
"""


class _FakeD4J:
    def export(self, container_path: str, prop: str):
        if prop == "classes.modified":
            return ["com.google.gson.internal.$Gson$Types"]
        if prop == "dir.src.classes":
            return ["gson/src/main/java"]
        raise AssertionError(f"Unexpected export: {prop}")

    def exec(self, bash_cmd: str, timeout: int | None = None):
        expected_rel = "gson/src/main/java/com/google/gson/internal/$Gson$Types.java"
        if bash_cmd.startswith("cat "):
            if expected_rel in bash_cmd:
                return _FIXED_SOURCE, "", 0
            return "", "", 1
        if bash_cmd.startswith("diff -u "):
            diff = "".join(
                difflib.unified_diff(
                    _BUGGY_SOURCE.splitlines(keepends=True),
                    _FIXED_SOURCE.splitlines(keepends=True),
                    fromfile=f"/buggy/{expected_rel}",
                    tofile=f"/fixed/{expected_rel}",
                )
            )
            return diff, "", 1
        raise AssertionError(f"Unexpected exec: {bash_cmd}")


class SourceFinderDollarClassTest(unittest.TestCase):
    def test_finds_jobs_for_top_level_class_with_dollar_name(self) -> None:
        finder = SourceFinder(_FakeD4J())

        jobs = finder.find_jobs("Gson", 14, "/fixed", "/buggy")

        self.assertEqual(1, len(jobs))
        self.assertEqual(
            "gson/src/main/java/com/google/gson/internal/$Gson$Types.java",
            jobs[0].filepath,
        )
        self.assertEqual("com.google.gson.internal.$Gson$Types", jobs[0].class_fqn)
        self.assertEqual("value", jobs[0].method_name)
        self.assertEqual([5], jobs[0].changed_lines)

    def test_fqn_to_path_keeps_top_level_dollar_class_name(self) -> None:
        self.assertEqual(
            "gson/src/main/java/com/google/gson/internal/$Gson$Types.java",
            _fqn_to_path("com.google.gson.internal.$Gson$Types", "gson/src/main/java"),
        )


class PITGeneratorDollarClassTargetTest(unittest.TestCase):
    def test_target_class_keeps_top_level_dollar_class_name(self) -> None:
        generator = PITGenerator(PITConfig(), d4j=object())

        target = generator._pit_target_class("com.google.gson.internal.$Gson$Types")

        self.assertEqual("com.google.gson.internal.$Gson$Types*", target)


if __name__ == "__main__":
    unittest.main()
