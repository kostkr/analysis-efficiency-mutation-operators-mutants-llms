import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from defect4j.collector import DataCollector
from defect4j.container import (
    PODMAN_EXEC_MAX_ATTEMPTS,
    Defects4J,
    _is_retryable_podman_exec_failure,
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


class _FakeProfileD4J:
    def __init__(self, fixed_profile: dict, buggy_profile: dict, trigger_tests: list[str]):
        self._fixed_profile = fixed_profile
        self._buggy_profile = buggy_profile
        self._trigger_tests = trigger_tests

    def relevant_test_profile(self, container_path: str, timeout: int = 600) -> dict:
        if container_path.endswith("_b"):
            return dict(self._buggy_profile)
        return dict(self._fixed_profile)

    def trigger_tests(self, _container_path: str) -> list[str]:
        return list(self._trigger_tests)


class _FakeMutant:
    id = 1
    filepath = "src/Example.java"
    line = 1
    precode = "return 1;"
    aftercode = "return 2;"
    rule = None


class _ProfileTestCollector(DataCollector):
    def _ensure_checkout(self, project: str, bug_id: int, version: str = "f") -> str:
        return f"/tmp/{project}_{bug_id}_{version}"


class _RecordingDefects4J(Defects4J):
    def __init__(self) -> None:
        super().__init__(container="fake", workspace="/workspace")
        self.exec_calls: list[tuple[str, int | None]] = []

    def exec(self, bash_cmd: str, timeout: int | None = None):
        self.exec_calls.append((bash_cmd, timeout))
        if "defects4j export -p dir.src.classes" in bash_cmd:
            return "src/main/java\n", "", 0
        if "defects4j export -p dir.bin.classes" in bash_cmd:
            return "target/classes\n", "", 0
        if "defects4j export -p dir.src.tests" in bash_cmd:
            return "src/test/java\n", "", 0
        if "defects4j export -p dir.bin.tests" in bash_cmd:
            return "target/test-classes\n", "", 0
        if "python3 -c" in bash_cmd:
            return (
                '{"compiled": true, "compile_error": "", "run_time_s": 4.25, "test_time_s": 4.25, "wall_time_s": 0.0, "timed_out": false, "test_executed": true, "failing_count": 0, "failing_tests": []}',
                "",
                0,
            )
        return "", "", 0


class _RetryCheckoutDefects4J(Defects4J):
    def __init__(self) -> None:
        super().__init__(container="fake", workspace="/workspace")
        self.exec_calls: list[str] = []
        self.failures_left = 1

    def exec(self, bash_cmd: str, timeout: int | None = None):
        self.exec_calls.append(bash_cmd)
        if "defects4j checkout" in bash_cmd and self.failures_left > 0:
            self.failures_left -= 1
            return "", "first attempt failed", 1
        return "", "", 0


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

    def test_ensure_profiles_allows_trigger_tests_outside_relevant_suite(self) -> None:
        collector = _ProfileTestCollector(
            _FakeProfileD4J(
                fixed_profile={
                    "all_tests": [
                        "pkg.RelevantTest::testA",
                        "pkg.RelevantTest::testB",
                    ],
                    "failing_tests": [],
                    "run_time_s": 1.0,
                },
                buggy_profile={
                    "all_tests": [
                        "pkg.RelevantTest::testA",
                        "pkg.RelevantTest::testB",
                    ],
                    "failing_tests": ["pkg.RelevantTest::testA"],
                    "run_time_s": 1.0,
                },
                trigger_tests=[
                    "pkg.TriggerTest::testOutsideRelevant1",
                    "pkg.TriggerTest::testOutsideRelevant2",
                ],
            ),
            storage=None,
            verbose=False,
        )

        profiles = collector._ensure_profiles("Collections", 1, "/tmp/Collections_1_f", 60)

        self.assertEqual(
            profiles["bug_profile"]["failing_tests"],
            ["pkg.RelevantTest::testA"],
        )
        self.assertEqual(profiles["bug_profile"]["trigger_tests"], [])

    def test_ensure_profiles_allows_buggy_failures_missing_from_all_tests(self) -> None:
        collector = _ProfileTestCollector(
            _FakeProfileD4J(
                fixed_profile={
                    "all_tests": ["pkg.RelevantTest::testA"],
                    "failing_tests": [],
                    "run_time_s": 1.0,
                },
                buggy_profile={
                    "all_tests": ["pkg.RelevantTest::testA"],
                    "failing_tests": ["pkg.HiddenTriggerTest::testBug"],
                    "run_time_s": 1.0,
                },
                trigger_tests=["pkg.HiddenTriggerTest::testBug"],
            ),
            storage=None,
            verbose=False,
        )

        profiles = collector._ensure_profiles("Collections", 1, "/tmp/Collections_1_f", 60)

        self.assertEqual(
            profiles["bug_profile"]["failing_tests"],
            ["pkg.HiddenTriggerTest::testBug"],
        )
        self.assertEqual(profiles["bug_profile"]["trigger_tests"], [])


class ContainerTempIsolationTest(unittest.TestCase):
    def test_wrap_with_checkout_temp_sets_local_temp_and_cleanup(self) -> None:
        d4j = _RecordingDefects4J()
        wrapped = d4j.wrap_with_checkout_temp("/tmp/checkout", "defects4j test -r")

        self.assertIn("/tmp/defect4j-copilot-tmp/tmp_checkout", wrapped)
        self.assertIn("cleanup_temp()", wrapped)
        self.assertIn("cleanup_new_tmp_dirs()", wrapped)
        self.assertIn("find /tmp -maxdepth 1 -mindepth 1 -name 'dir*'", wrapped)
        self.assertIn("cleanup_temp\nexit $status", wrapped)

    def test_run_mutant_relevant_keeps_internal_run_time(self) -> None:
        d4j = _RecordingDefects4J()

        result = d4j.run_mutant_relevant(
            "/tmp/checkout",
            _FakeMutant(),
            timeout=60,
            suite_total_tests=10,
        )

        self.assertEqual(result["run_time_s"], 4.25)
        self.assertEqual(result["test_time_s"], 4.25)
        self.assertGreaterEqual(result["wall_time_s"], 0.0)
        runner_cmd = next(cmd for cmd, _ in d4j.exec_calls if "python3 -c" in cmd)
        self.assertIn("/tmp/defect4j-copilot-tmp/tmp_checkout", runner_cmd)

    def test_test_full_runs_under_checkout_temp_wrapper(self) -> None:
        d4j = _RecordingDefects4J()

        d4j.test_full("/tmp/checkout", timeout=60, relevant=True)

        cmd = next(cmd for cmd, _ in d4j.exec_calls if "defects4j test -r" in cmd)
        self.assertIn("/tmp/defect4j-copilot-tmp/tmp_checkout", cmd)

    def test_checkout_retries_on_clean_path(self) -> None:
        d4j = _RetryCheckoutDefects4J()

        path = d4j.checkout("Compress", 22, "f", dest="/tmp/checkout", timeout=60)

        self.assertEqual(path, "/tmp/checkout")
        self.assertEqual(sum("defects4j checkout" in cmd for cmd in d4j.exec_calls), 2)
        self.assertIn("rm -rf /tmp/checkout", d4j.exec_calls[0])


class PodmanExecRetryTest(unittest.TestCase):
    def test_retryable_podman_error_detection(self) -> None:
        self.assertTrue(_is_retryable_podman_exec_failure("ssh: handshake failed: read tcp"))
        self.assertTrue(_is_retryable_podman_exec_failure("Cannot connect to Podman"))
        self.assertFalse(_is_retryable_podman_exec_failure("ordinary compile failure"))

    def test_exec_retries_transient_podman_socket_error(self) -> None:
        d4j = Defects4J(container="fake", exec_max_concurrency=14)
        attempts: list[tuple[list[str], int | None]] = []

        def fake_run(args, capture_output, text, timeout):
            attempts.append((list(args), timeout))
            if len(attempts) < PODMAN_EXEC_MAX_ATTEMPTS:
                return type("Proc", (), {
                    "stdout": "",
                    "stderr": "unable to connect to Podman socket: handshake failed",
                    "returncode": 125,
                })()
            return type("Proc", (), {
                "stdout": "ok",
                "stderr": "",
                "returncode": 0,
            })()

        with patch("defect4j.container.subprocess.run", side_effect=fake_run), \
             patch("defect4j.container.time.sleep", return_value=None):
            out, err, rc = d4j.exec("echo ok", timeout=12)

        self.assertEqual((out, err, rc), ("ok", "", 0))
        self.assertEqual(len(attempts), PODMAN_EXEC_MAX_ATTEMPTS)
        self.assertEqual(attempts[0][0][:3], ["podman", "exec", "fake"])
        self.assertIsNotNone(d4j._exec_semaphore)


if __name__ == "__main__":
    unittest.main()
