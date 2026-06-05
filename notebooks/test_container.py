import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from defect4j.collector import DataCollector
from defect4j.container import (
    _collect_failing_tests,
    _parse_failing_tests_file,
    _parse_failing_tests_output,
    _parse_junit_xml_report,
)


class _FakeD4J:
    def __init__(self, result: dict):
        self._result = result

    def run_mutant_relevant(self, **_kwargs) -> dict:
        return dict(self._result)


class _FakeMutant:
    id = 1
    filepath = "src/Example.java"
    rule = None


class ContainerParsingTest(unittest.TestCase):
    def test_parse_failing_tests_output_accepts_both_defects4j_formats(self) -> None:
        raw = """
        Failing tests: 2
        - pkg.OneTest::testA
        - testB(pkg.TwoTest)
        """

        self.assertEqual(
            _parse_failing_tests_output(raw),
            {"pkg.OneTest::testA", "pkg.TwoTest::testB"},
        )

    def test_parse_failing_tests_output_accepts_actual_indented_stdout(self) -> None:
        raw = "Failing tests: 1\n  - org.apache.commons.cli2.bug.BugCLI144Test::testFileValidator\n"
        self.assertEqual(
            _parse_failing_tests_output(raw),
            {"org.apache.commons.cli2.bug.BugCLI144Test::testFileValidator"},
        )

    def test_parse_failing_tests_output_ignores_bullets_outside_failure_block(self) -> None:
        raw = """
        Some setup log
        - not a test line
        Failing tests: 1
        - testB(pkg.TwoTest)

        Stack trace:
        - still not a test line
        """

        self.assertEqual(
            _parse_failing_tests_output(raw),
            {"pkg.TwoTest::testB"},
        )

    def test_parse_failing_tests_file_accepts_plain_entries(self) -> None:
        raw = "pkg.OneTest::testA\ntestB(pkg.TwoTest)\n"
        self.assertEqual(
            _parse_failing_tests_file(raw),
            {"pkg.OneTest::testA", "pkg.TwoTest::testB"},
        )

    def test_parse_failing_tests_file_ignores_stack_trace_lines(self) -> None:
        raw = """--- pkg.OneTest::testA
java.lang.AssertionError: boom
\tat pkg.OneTest.testA(OneTest.java:10)
\tat junit.framework.TestCase.runTest(TestCase.java:176)
"""
        self.assertEqual(_parse_failing_tests_file(raw), {"pkg.OneTest::testA"})

    def test_parse_failing_tests_file_reads_multiple_headers_with_traces(self) -> None:
        raw = """--- pkg.OneTest::testA
java.lang.AssertionError: boom
\tat pkg.OneTest.testA(OneTest.java:10)

--- pkg.TwoTest::testB
java.lang.IllegalStateException: kaput
\tat pkg.TwoTest.testB(TwoTest.java:20)
"""
        self.assertEqual(
            _parse_failing_tests_file(raw),
            {"pkg.OneTest::testA", "pkg.TwoTest::testB"},
        )

    def test_collect_failing_tests_unions_file_and_stdout(self) -> None:
        failing_raw = "--- pkg.OneTest::testA\njava.lang.AssertionError: boom\n"
        output_raw = "Failing tests: 1\n  - testB(pkg.TwoTest)\n"
        self.assertEqual(
            _collect_failing_tests(failing_raw=failing_raw, output_raw=output_raw),
            ["pkg.OneTest::testA", "pkg.TwoTest::testB"],
        )

    def test_parse_junit_xml_report_reads_failing_cases(self) -> None:
        xml = """
        <testsuite>
          <testcase classname="pkg.OneTest" name="testA" />
          <testcase classname="pkg.TwoTest" name="testB">
            <failure message="boom">trace</failure>
          </testcase>
          <testcase name="testC">
            <error message="kaput">trace</error>
          </testcase>
        </testsuite>
        """

        all_tests, failing_tests = _parse_junit_xml_report(xml, default_class="pkg.FallbackTest")

        self.assertEqual(
            all_tests,
            {"pkg.OneTest::testA", "pkg.TwoTest::testB", "pkg.FallbackTest::testC"},
        )
        self.assertEqual(
            failing_tests,
            {"pkg.TwoTest::testB", "pkg.FallbackTest::testC"},
        )


class CollectorFallbackTest(unittest.TestCase):
    def test_run_one_keeps_known_failures_without_placeholder(self) -> None:
        collector = DataCollector(
            _FakeD4J(
                {
                    "compiled": False,
                    "compile_error": "Running ant (compile.tests)\nOK\nRunning ant (run.dev.tests)\nFAIL",
                    "run_time_s": 1.0,
                    "test_time_s": 1.0,
                    "wall_time_s": 1.0,
                    "timed_out": False,
                    "test_executed": False,
                    "failing_count": 1,
                    "failing_tests": ["pkg.Test::fails"],
                }
            ),
            storage=None,
            verbose=False,
        )

        record = collector._run_one(_FakeMutant(), 1, "/tmp/checkout", "classic", 60, 10)

        self.assertTrue(record["compiled"])
        self.assertTrue(record["test_executed"])
        self.assertEqual(record["compile_error"], "")
        self.assertEqual(record["failing_tests"], ["pkg.Test::fails"])
        self.assertEqual(record["failing_count"], 1)

    def test_run_one_does_not_invent_failure_names(self) -> None:
        collector = DataCollector(
            _FakeD4J(
                {
                    "compiled": False,
                    "compile_error": "Running ant (compile.tests)\nOK\nRunning ant (run.dev.tests)\nFAIL",
                    "run_time_s": 1.0,
                    "test_time_s": 1.0,
                    "wall_time_s": 1.0,
                    "timed_out": False,
                    "test_executed": False,
                    "failing_count": 0,
                    "failing_tests": [],
                }
            ),
            storage=None,
            verbose=False,
        )

        record = collector._run_one(_FakeMutant(), 1, "/tmp/checkout", "classic", 60, 10)

        self.assertFalse(record["compiled"])
        self.assertEqual(record["failing_tests"], [])
        self.assertEqual(record["failing_count"], 0)


if __name__ == "__main__":
    unittest.main()
