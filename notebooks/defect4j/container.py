"""
container.py — Podman/Defects4J wrapper.

One Defects4J instance is shared for the entire experiment session.
The container must already be running:
    podman start -ai defects4j-container

Optimisation: every method is a single `podman exec` call.
The container is NOT recreated between mutants.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import Tuple


# ── module-level test-list helpers ──────────────────────────────────────────

def _parse_all_tests_file(raw: str) -> set[str]:
    """Parse defects4j ``all_tests`` file.

    Each line has the form ``methodName(fully.qualified.ClassName)``.
    Returns a set of ``ClassName::methodName`` strings.
    """
    result: set[str] = set()
    for entry in raw.strip().splitlines():
        entry = entry.strip()
        if not entry or "(" not in entry:
            continue
        method, rest = entry.split("(", 1)
        cls = rest.rstrip(")")
        result.add(f"{cls}::{method}")
    return result


def _parse_junit_xml(xml_raw: str, test_class: str) -> set[str]:
    """Parse a JUnit XML test report and return all test case names.

    Returns a set of ``ClassName::methodName`` strings.
    Defects4J ant runner writes ``TEST-<ClassName>.xml`` reports after each run
    even for targeted (``-t``) runs.
    """
    result: set[str] = set()
    for m in re.finditer(r'<testcase\b[^>]*\bname="([^"]+)"', xml_raw):
        result.add(f"{test_class}::{m.group(1)}")
    return result


@dataclass
class Defects4J:
    """
    Thin wrapper around `podman exec <container> bash -lc <cmd>`.

    Parameters
    ----------
    container       : Podman container name
    workspace       : Absolute path INSIDE the container (bind-mounted from host)
    timeout_default : Default subprocess timeout in seconds
    """

    container:       str = "defects4j-container"
    workspace:       str = "/workspace"
    timeout_default: int = 300

    # ------------------------------------------------------------------ #
    #  Context manager                                                     #
    # ------------------------------------------------------------------ #
    def __enter__(self) -> "Defects4J":
        self.assert_running()
        return self

    def __exit__(self, *_) -> None:
        pass

    # ------------------------------------------------------------------ #
    #  Low-level shell helpers                                             #
    # ------------------------------------------------------------------ #
    def _run(self, cmd: str, timeout: int) -> Tuple[str, str, int]:
        r = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return r.stdout, r.stderr, r.returncode

    def exec(self, bash_cmd: str, timeout: int | None = None) -> Tuple[str, str, int]:
        """
        Run *bash_cmd* inside the running container.

        Returns (stdout, stderr, returncode).
        Raises subprocess.TimeoutExpired on timeout.
        """
        t   = timeout or self.timeout_default
        cmd = bash_cmd.replace('"', '\\"')
        return self._run(f'podman exec {self.container} bash -lc "{cmd}"', t)

    # ------------------------------------------------------------------ #
    #  Container lifecycle                                                 #
    # ------------------------------------------------------------------ #
    def is_running(self) -> bool:
        out, _, rc = self._run(
            f"podman inspect --format='{{{{.State.Status}}}}' {self.container}",
            timeout=15,
        )
        return rc == 0 and "running" in out

    def assert_running(self) -> None:
        if not self.is_running():
            raise RuntimeError(
                f"Container '{self.container}' is NOT running.\n"
                f"Start it with:  podman start -ai {self.container}"
            )

    def status(self) -> str:
        ok = self.is_running()
        return f"Container '{self.container}': {'running ✅' if ok else 'NOT running ❌'}"

    # ------------------------------------------------------------------ #
    #  Defects4J commands                                                  #
    # ------------------------------------------------------------------ #
    def checkout(
        self,
        project: str,
        bug_id:  int,
        version: str    = "f",
        dest:    str | None = None,
        timeout: int    = 120,
    ) -> str:
        """
        Check out a Defects4J bug into the container workspace.

        Parameters
        ----------
        project : e.g. "Lang"
        bug_id  : e.g. 1
        version : "f" (fixed) or "b" (buggy)
        dest    : override destination path inside container

        Returns
        -------
        str – absolute path inside the container.
        """
        path = dest or f"{self.workspace}/checkouts/{project}_{bug_id}_{version}"
        cmd  = f"defects4j checkout -p {project} -v {bug_id}{version} -w {path}"
        _, err, rc = self.exec(cmd, timeout=timeout)
        if rc != 0:
            raise RuntimeError(
                f"checkout({project}, {bug_id}, {version!r}) failed:\n{err}"
            )
        return path

    def trigger_tests(self, container_path: str) -> list[str]:
        """
        Export the trigger (failing) tests for the checked-out bug.

        Returns list of test IDs that expose the real bug.
        """
        out, err, rc = self.exec(
            f"cd {container_path} && defects4j export -p tests.trigger"
        )
        if rc != 0:
            raise RuntimeError(f"export tests.trigger failed:\n{err}")
        return [t.strip() for t in out.strip().splitlines() if t.strip()]

    def export(self, container_path: str, prop: str) -> list[str]:
        """
        Generic `defects4j export -p <prop>` call.

        Common props: tests.trigger, tests.relevant, classes.modified,
                      cp.compile, cp.test
        """
        out, err, rc = self.exec(
            f"cd {container_path} && defects4j export -p {prop}"
        )
        if rc != 0:
            raise RuntimeError(f"export {prop} failed:\n{err}")
        return [line.strip() for line in out.strip().splitlines() if line.strip()]

    def compile_result(self, container_path: str) -> Tuple[bool, str]:
        """
        Compile the project and return (success, error_summary).

        Unlike compile(), returns the error message for storage in results.
        """
        _, err, rc = self.exec(f"cd {container_path} && defects4j compile")
        if rc == 0:
            return True, ""
        # Extract a short error summary (first 400 chars of stderr)
        summary = err.strip()[:400] if err.strip() else "compile failed (no stderr)"
        return False, summary

    def compile(self, container_path: str) -> bool:
        """Compile project. Returns True on success (simple convenience wrapper)."""
        ok, _ = self.compile_result(container_path)
        return ok

    def test(self, container_path: str, timeout: int = 600,
             relevant: bool = False,
             test_class: str | None = None) -> set[str]:
        """
        Run tests and return the set of failing test IDs.

        Parameters
        ----------
        relevant   : if True, run only the tests relevant to the bug's modified
                     classes (``defects4j test -r``).  Much faster than the full
                     suite and still covers the mutated class.
        test_class : if given, run only that fully-qualified test class
                     (``defects4j test -t <test_class>``).
        """
        failing, _ = self.test_full(container_path, timeout=timeout,
                                    relevant=relevant, test_class=test_class)
        return failing

    def test_full(
        self,
        container_path: str,
        timeout: int = 600,
        relevant: bool = False,
        test_class: str | None = None,
    ) -> Tuple[set[str], set[str]]:
        """
        Run tests and return *both* failing and all executed tests.

        Parameters
        ----------
        relevant   : if True run ``defects4j test -r`` (relevant tests only).
                     Defects4J determines which test classes cover the modified
                     source files — this is the recommended mode for mutation
                     testing because it is fast and still exercises the mutated
                     class.  The full-suite listener is used so ``all_tests``
                     is written normally.
        test_class : if given run ``defects4j test -t <test_class>`` (single
                     class).  Fallback: if ``all_tests`` is empty the JUnit XML
                     report is parsed instead.

        Returns
        -------
        (failing_tests, all_tests) — both sets in ``ClassName::methodName`` format.
        """
        if relevant:
            t_flag = " -r"
        elif test_class:
            t_flag = f" -t {test_class}"
        else:
            t_flag = ""

        # ── Step 1: run tests (timeout applies here) ─────────────────────────
        out, _, _ = self.exec(
            f"cd {container_path} && defects4j test{t_flag}",
            timeout=timeout,
        )

        # ── Step 2: read all_tests file ───────────────────────────────────────
        # Written by defects4j's JUnit listener for full-suite and relevant runs.
        all_raw, _, _ = self.exec(
            f"cat {container_path}/all_tests 2>/dev/null || true",
        )
        all_tests = _parse_all_tests_file(all_raw)

        # ── Step 3: fallback for -t runs – parse JUnit XML report ─────────────
        # With -t, the full-suite listener is NOT invoked → all_tests stays empty.
        # Ant always writes TEST-<ClassName>.xml, so read that instead.
        if not all_tests and test_class:
            xml_path_raw, _, _ = self.exec(
                f"find {container_path} -name 'TEST-{test_class}.xml' "
                f"-type f 2>/dev/null | head -1"
            )
            xml_path = xml_path_raw.strip()
            if xml_path:
                xml_raw, _, _ = self.exec(f"cat {xml_path} 2>/dev/null || true")
                all_tests = _parse_junit_xml(xml_raw, test_class)

        # ── Parse failing tests from stdout ───────────────────────────────────
        failing: set[str] = {
            line.strip()[2:]
            for line in out.splitlines()
            if line.strip().startswith("- ") and "::" in line
        }

        return failing, all_tests

