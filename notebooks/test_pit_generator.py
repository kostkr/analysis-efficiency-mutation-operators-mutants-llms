import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from defect4j.generators import PITConfig
from defect4j.generators.pit.generator import PITGenerator


class _FakeD4J:
    def __init__(self, *, container: str, build_result: tuple[str, str, int]) -> None:
        self.container = container
        self.build_result = build_result
        self.exec_calls: list[tuple[str, int | None]] = []

    def exec(self, bash_cmd: str, timeout: int | None = None):
        self.exec_calls.append((bash_cmd, timeout))
        if "cat /opt/custom-pitest/.classic_pit_ready" in bash_cmd:
            return "", "", 1
        if bash_cmd.startswith("rm -rf /tmp/custom-pitest-src"):
            return "", "", 0
        if bash_cmd.startswith("cd /tmp/custom-pitest-src && mvn -q"):
            return self.build_result
        if bash_cmd.startswith("printf '%s'"):
            return "", "", 0
        return "", "", 0


class PITGeneratorBuildTest(unittest.TestCase):
    def test_custom_pit_build_skips_checkstyle(self) -> None:
        d4j = _FakeD4J(container="fake-build-ok", build_result=("", "", 0))
        generator = PITGenerator(PITConfig(), d4j)

        with patch("defect4j.generators.pit.generator.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stderr = ""
            generator._ensure_custom_pitest_available()

        build_cmd = next(cmd for cmd, _ in d4j.exec_calls if cmd.startswith("cd /tmp/custom-pitest-src && mvn -q"))
        self.assertIn("-Dcheckstyle.skip=true", build_cmd)

    def test_custom_pit_build_error_includes_stdout(self) -> None:
        d4j = _FakeD4J(
            container="fake-build-fail",
            build_result=("stdout failure details", "", 1),
        )
        generator = PITGenerator(PITConfig(), d4j)

        with patch("defect4j.generators.pit.generator.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stderr = ""
            with self.assertRaises(RuntimeError) as ctx:
                generator._ensure_custom_pitest_available()

        self.assertIn("stdout failure details", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
