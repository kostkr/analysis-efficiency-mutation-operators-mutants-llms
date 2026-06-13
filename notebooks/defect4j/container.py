"""
container.py — Podman/Defects4J wrapper.

One Defects4J instance is shared for the entire experiment session.
The container must already be running:
    podman start -ai defects4j-container

Optimisation: every method is a single `podman exec` call.
The container is NOT recreated between mutants.
"""

from __future__ import annotations

import base64
import json
import math
import os
import queue
import re
import shlex
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Tuple

if TYPE_CHECKING:
    from .mutant import Mutant


MUTANT_TEST_TIMEOUT_CAP_S = 160
MUTANT_TEST_TIMEOUT_PER_RELEVANT_TEST_S = 0.038
PODMAN_EXEC_MAX_ATTEMPTS = 3
_PODMAN_EXEC_RETRY_SNIPPETS = (
    "unable to connect to Podman socket",
    "Cannot connect to Podman",
    "handshake failed",
    "connection reset by peer",
    "failed to connect",
)

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
    result, _ = _parse_junit_xml_report(xml_raw, default_class=test_class)
    return result


def _parse_junit_xml_report(
    xml_raw: str,
    *,
    default_class: str = "",
) -> tuple[set[str], set[str]]:
    """Parse a JUnit XML report and return (all_tests, failing_tests)."""
    all_tests: set[str] = set()
    failing_tests: set[str] = set()
    raw = str(xml_raw or "").strip()
    if not raw:
        return all_tests, failing_tests

    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return all_tests, failing_tests

    for testcase in root.iter():
        if not str(testcase.tag).endswith("testcase"):
            continue
        class_name = str(testcase.attrib.get("classname") or default_class).strip()
        method_name = str(testcase.attrib.get("name") or "").strip()
        if not class_name or not method_name:
            continue
        test_id = f"{class_name}::{method_name}"
        all_tests.add(test_id)
        if any(str(child.tag).endswith(("failure", "error")) for child in testcase):
            failing_tests.add(test_id)

    return all_tests, failing_tests


def _parse_failing_tests_output(raw: str) -> set[str]:
    """Parse failing Defects4J test IDs from command stdout."""
    result: set[str] = set()
    in_failing_section = False
    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if line.startswith("Failing tests:"):
            in_failing_section = True
            continue
        if not in_failing_section:
            continue
        if not line:
            if result:
                break
            continue
        if not line.startswith("- "):
            break
        test_id = line[2:].strip()
        if "::" in test_id:
            result.add(test_id)
            continue
        if "(" in test_id and test_id.endswith(")"):
            method, rest = test_id.split("(", 1)
            cls = rest[:-1].strip()
            method = method.strip()
            if cls and method:
                result.add(f"{cls}::{method}")
    return result


def _parse_failing_tests_file(raw: str) -> set[str]:
    """Parse Defects4J ``failing_tests`` file entries."""
    result: set[str] = set()
    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("Failing tests:"):
            continue
        if line.startswith("--- "):
            line = line[4:].strip()
        elif line.startswith("- "):
            line = line[2:].strip()
        if "::" in line and " " not in line and not line.startswith("at "):
            result.add(line)
            continue
        if "(" in line and line.endswith(")"):
            method, rest = line.split("(", 1)
            cls = rest[:-1].strip()
            method = method.strip()
            if cls and method and " " not in cls and " " not in method and not method.startswith("at "):
                result.add(f"{cls}::{method}")
    return result


def _collect_failing_tests(*, failing_raw: str, output_raw: str) -> list[str]:
    return sorted(
        set(_parse_failing_tests_file(failing_raw))
        | set(_parse_failing_tests_output(output_raw))
    )


def _effective_mutant_timeout_s(configured_timeout_s: int, suite_total_tests: int) -> int:
    adaptive_timeout_s = math.ceil(
        max(0, int(suite_total_tests)) * MUTANT_TEST_TIMEOUT_PER_RELEVANT_TEST_S
    )
    return max(
        1,
        min(
            int(configured_timeout_s),
            max(MUTANT_TEST_TIMEOUT_CAP_S, adaptive_timeout_s),
        ),
    )


def _is_retryable_podman_exec_failure(stderr: str) -> bool:
    text = str(stderr or "")
    return any(snippet in text for snippet in _PODMAN_EXEC_RETRY_SNIPPETS)


def _mutant_runner_helper_source() -> str:
    """Python helper source embedded into the in-container mutant runner."""
    return r'''
def _kill_process_group(proc):
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        pass
    try:
        proc.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass


def _run_test_command(args, root, timeout_s):
    proc = subprocess.Popen(
        args,
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        out, err = proc.communicate(timeout=timeout_s)
        timed_out = False
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_process_group(proc)
        try:
            out, err = proc.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            out, err = '', ''

    return {
        'returncode': proc.returncode,
        'stdout': out or '',
        'stderr': err or '',
        'timed_out': timed_out,
    }
'''


@dataclass(frozen=True)
class ContainerCheckout:
    """One isolated checkout/workdir inside the shared Defects4J container."""

    d4j: "Defects4J"
    worker_id: int
    container_path: str
    host_path: Path

    def exec(self, bash_cmd: str, timeout: int | None = None) -> Tuple[str, str, int]:
        """Run *bash_cmd* inside this checkout directory."""
        return self.d4j.exec(
            f"cd {shlex.quote(self.container_path)} && {bash_cmd}",
            timeout=timeout,
        )


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
    exec_max_concurrency: int | None = None
    _mutant_run_cleanup_cache: dict[str, dict[str, tuple]] = field(default_factory=dict, init=False, repr=False)
    _exec_semaphore: threading.BoundedSemaphore | None = field(default=None, init=False, repr=False)

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
        t = timeout or self.timeout_default
        cmd = (
            "export LANG=C.UTF-8 LC_ALL=C.UTF-8 LC_CTYPE=C.UTF-8 "
            "JAVA_TOOL_OPTIONS='-Dfile.encoding=UTF-8 -Dsun.jnu.encoding=UTF-8' "
            "ANT_OPTS='-Dfile.encoding=UTF-8' MAVEN_OPTS='-Dfile.encoding=UTF-8'; "
            + bash_cmd
        )
        semaphore = self._exec_semaphore
        if semaphore is None and self.exec_max_concurrency is not None:
            semaphore = threading.BoundedSemaphore(max(1, int(self.exec_max_concurrency)))
            self._exec_semaphore = semaphore
        last_result: subprocess.CompletedProcess[str] | None = None
        for attempt in range(1, PODMAN_EXEC_MAX_ATTEMPTS + 1):
            if semaphore is None:
                last_result = subprocess.run(
                    ["podman", "exec", self.container, "bash", "-lc", cmd],
                    capture_output=True,
                    text=True,
                    timeout=t,
                )
            else:
                with semaphore:
                    last_result = subprocess.run(
                        ["podman", "exec", self.container, "bash", "-lc", cmd],
                        capture_output=True,
                        text=True,
                        timeout=t,
                    )
            if last_result.returncode == 0:
                break
            if attempt >= PODMAN_EXEC_MAX_ATTEMPTS:
                break
            if not _is_retryable_podman_exec_failure(last_result.stderr):
                break
            time.sleep(0.5 * attempt)
        assert last_result is not None
        return last_result.stdout, last_result.stderr, last_result.returncode

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

    def _mutant_run_cleanup_config(self, container_path: str) -> dict[str, tuple]:
        """Return cached source/bin mappings used to isolate consecutive mutant runs.

        Reused checkouts can keep stale bytecode when Ant incremental compilation
        decides that nothing needs recompiling. To avoid cross-mutant contamination
        without forcing a full rebuild, delete only the compiled outputs that belong
        to the mutated source file.
        """
        cached = self._mutant_run_cleanup_cache.get(container_path)
        if cached is not None:
            return cached

        def exported(prop: str) -> tuple[str, ...]:
            try:
                values = self.export(container_path, prop)
            except RuntimeError:
                return ()
            return tuple(entry.strip() for entry in values if entry.strip())

        src_class_roots = exported("dir.src.classes")
        bin_class_roots = exported("dir.bin.classes")
        src_test_roots = exported("dir.src.tests")
        bin_test_roots = exported("dir.bin.tests")

        source_bin_pairs: list[tuple[str, str]] = []
        for src_root, bin_root in zip(src_class_roots, bin_class_roots):
            source_bin_pairs.append((src_root, bin_root))
        for src_root, bin_root in zip(src_test_roots, bin_test_roots):
            source_bin_pairs.append((src_root, bin_root))

        fallback_paths: list[str] = []
        seen_fallbacks: set[str] = set()
        for bin_root in (*bin_class_roots, *bin_test_roots):
            if bin_root not in seen_fallbacks:
                fallback_paths.append(bin_root)
                seen_fallbacks.add(bin_root)

        cached = {
            "source_bin_pairs": tuple(source_bin_pairs),
            "fallback_paths": tuple(fallback_paths),
        }
        self._mutant_run_cleanup_cache[container_path] = cached
        return cached

    def mutant_run_cleanup_paths(self, container_path: str, filepath: str) -> tuple[str, ...]:
        """Return artifact paths/patterns that must be removed before one mutant run."""
        config = self._mutant_run_cleanup_config(container_path)
        cleanup_paths: list[str] = ["all_tests", "failing_tests"]
        source_path = str(filepath).strip().lstrip("/")

        for src_root, bin_root in config["source_bin_pairs"]:
            normalized_src_root = str(src_root).strip().strip("/")
            if not normalized_src_root:
                continue
            prefix = normalized_src_root + "/"
            if not source_path.startswith(prefix):
                continue
            relative_source = source_path[len(prefix):]
            if not relative_source.endswith(".java"):
                break
            class_stem = relative_source[:-5]
            cleanup_paths.append(f"{bin_root.rstrip('/')}/{class_stem}.class")
            cleanup_paths.append(f"{bin_root.rstrip('/')}/{class_stem}$*.class")
            return tuple(cleanup_paths)

        return tuple(cleanup_paths + list(config["fallback_paths"]))

    def kill_processes_under_path(self, container_path: str, timeout: int = 30) -> None:
        """Best-effort kill of processes whose cwd belongs to *container_path*."""
        script = r'''
import os
import signal
import time
from pathlib import Path

root = os.path.normpath(os.environ['TARGET_ROOT'])
current = os.getpid()
parent = os.getppid()

def is_related(pid):
    proc_dir = Path('/proc') / str(pid)
    try:
        cwd = os.path.normpath(os.readlink(proc_dir / 'cwd'))
        if cwd == root or cwd.startswith(root.rstrip(os.sep) + os.sep):
            return True
    except Exception:
        pass
    return False

pids = []
for entry in Path('/proc').iterdir():
    if not entry.name.isdigit():
        continue
    pid = int(entry.name)
    if pid in {current, parent}:
        continue
    if is_related(pid):
        pids.append(pid)

deadline = time.monotonic() + 5.0
for sig in (signal.SIGTERM, signal.SIGKILL):
    if not pids:
        break
    for pid in sorted(set(pids), reverse=True):
        try:
            os.kill(pid, sig)
        except Exception:
            pass
    time.sleep(0.5 if sig == signal.SIGTERM else 0.1)
    if time.monotonic() >= deadline:
        break
    pids = [pid for pid in pids if is_related(pid)]
'''
        self.exec(
            f"TARGET_ROOT={shlex.quote(container_path)} python3 - <<'PY'\n{script}\nPY",
            timeout=timeout,
        )

    def parallel_checkouts(
        self,
        project: str,
        bug_id: int,
        host_workspace: Path | str,
        max_workers: int,
        version: str = "f",
        base_container_path: str | None = None,
        base_host_path: Path | str | None = None,
    ) -> "ParallelCheckoutPool":
        """Create a pool of isolated checkouts for parallel execution."""
        return ParallelCheckoutPool(
            d4j=self,
            project=project,
            bug_id=bug_id,
            host_workspace=host_workspace,
            max_workers=max_workers,
            version=version,
            base_container_path=base_container_path,
            base_host_path=base_host_path,
        )

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
        q_path = shlex.quote(path)
        q_parent = shlex.quote(str(Path(path).parent))
        cmd = (
            f"rm -rf {q_path} && "
            f"mkdir -p {q_parent} && "
            f"defects4j checkout -p {project} -v {bug_id}{version} -w {q_path}"
        )
        _, err, rc = self.exec(cmd, timeout=timeout)
        if rc != 0:
            _, retry_err, retry_rc = self.exec(cmd, timeout=timeout)
            if retry_rc != 0:
                message = retry_err.strip() or err.strip()
                raise RuntimeError(
                    f"checkout({project}, {bug_id}, {version!r}) failed:\n{message}"
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

    def checkout_temp_root(self, container_path: str) -> str:
        """Return a per-checkout temp directory rooted under /tmp."""
        normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(container_path).strip("/"))
        if not normalized:
            normalized = "root"
        return f"/tmp/defect4j-copilot-tmp/{normalized}"

    def wrap_with_checkout_temp(self, container_path: str, inner_cmd: str) -> str:
        """Run one shell command with a checkout-local temp root cleaned before and after."""
        q_temp_root = shlex.quote(self.checkout_temp_root(container_path))
        return "\n".join(
            [
                f"temp_root={q_temp_root}",
                'tmp_before="$temp_root/.tmp-before"',
                'tmp_after="$temp_root/.tmp-after"',
                'cleanup_temp() { rm -rf -- "$temp_root" >/dev/null 2>&1 || true; }',
                "snapshot_tmp_dirs() {",
                "  find /tmp -maxdepth 1 -mindepth 1 -name 'dir*' -printf '%f\\n' 2>/dev/null | LC_ALL=C sort > \"$1\" || true",
                "}",
                "cleanup_new_tmp_dirs() {",
                '  snapshot_tmp_dirs "$tmp_after"',
                '  comm -13 "$tmp_before" "$tmp_after" 2>/dev/null | while IFS= read -r entry; do',
                '    [ -n "$entry" ] && rm -rf -- "/tmp/$entry"',
                "  done",
                "}",
                'cleanup_temp && mkdir -p "$temp_root"',
                'snapshot_tmp_dirs "$tmp_before"',
                "(",
                inner_cmd,
                ")",
                "status=$?",
                "cleanup_new_tmp_dirs",
                "cleanup_temp",
                "exit $status",
            ]
        )

    def compile_result(self, container_path: str, timeout: int = 600) -> Tuple[bool, str]:
        """
        Compile the project and return (success, error_summary).

        Unlike compile(), returns the error message for storage in results.
        """
        _, err, rc = self.exec(
            f"cd {container_path} && {self.wrap_with_checkout_temp(container_path, 'defects4j compile')}",
            timeout=timeout,
        )
        if rc == 0:
            return True, ""
        # Extract a short error summary (first 400 chars of stderr)
        summary = err.strip()[:400] if err.strip() else "compile failed (no stderr)"
        return False, summary

    def compile(self, container_path: str, timeout: int = 600) -> bool:
        """Compile project. Returns True on success (simple convenience wrapper)."""
        ok, _ = self.compile_result(container_path, timeout=timeout)
        return ok

    def warm_compile(self, container_path: str, timeout: int = 600) -> float:
        """Compile one clean checkout once so the first mutant run is not cold."""
        t0 = time.perf_counter()
        ok, err = self.compile_result(container_path, timeout=timeout)
        run_time_s = round(time.perf_counter() - t0, 2)
        if not ok:
            raise RuntimeError(
                f"compile warmup failed for {container_path}:\n{err}"
            )
        return run_time_s

    def reset_checkout(self, container_path: str, timeout: int = 60) -> None:
        """Restore a checkout to a clean git state before reusing it."""
        q_path = shlex.quote(container_path)
        self.kill_processes_under_path(container_path, timeout=min(timeout, 30))
        reset_cmd = (
            f"cd {q_path} && "
            f"git reset --hard -q HEAD && "
            f"git clean -ffdxq"
        )
        _, err, rc = self.exec(reset_cmd, timeout=timeout)
        if rc == 0:
            return

        retry_cmd = (
            f"cd {q_path} && "
            f"rm -rf all_tests build target && "
            f"git reset --hard -q HEAD && "
            f"git clean -ffdxq"
        )
        _, retry_err, retry_rc = self.exec(retry_cmd, timeout=timeout)
        if retry_rc != 0:
            message = retry_err.strip() or err.strip()
            raise RuntimeError(f"reset checkout failed for {container_path}:\n{message}")

    def relevant_test_profile(self, container_path: str, timeout: int = 600) -> dict[str, Any]:
        """Run a clean ``defects4j test -r`` once and return the authoritative suite profile."""
        def _run_once() -> tuple[str, str, int, float, list[str], list[str]]:
            t0 = time.perf_counter()
            out, err, rc = self.exec(
                f"cd {container_path} && "
                f"{self.wrap_with_checkout_temp(container_path, 'rm -f all_tests failing_tests && defects4j test -r')}",
                timeout=timeout,
            )
            run_time_s = round(time.perf_counter() - t0, 2)
            all_raw, _, _ = self.exec(
                f"cat {container_path}/all_tests 2>/dev/null || true",
            )
            failing_raw, _, _ = self.exec(
                f"cat {container_path}/failing_tests 2>/dev/null || true",
            )
            all_tests = sorted(_parse_all_tests_file(all_raw))
            failing_tests = _collect_failing_tests(failing_raw=failing_raw, output_raw=out)
            return out, err, rc, run_time_s, all_tests, failing_tests

        out = err = ""
        rc = 1
        run_time_s = 0.0
        all_tests: list[str] = []
        failing_tests: list[str] = []
        try:
            out, err, rc, run_time_s, all_tests, failing_tests = _run_once()
            if rc != 0 and not failing_tests:
                # Recreate the checkout once before surfacing a clean-suite failure.
                self.reset_checkout(container_path, timeout=min(timeout, 60))
                out, err, rc, run_time_s, all_tests, failing_tests = _run_once()
                if rc != 0 and not failing_tests:
                    msg = (err.strip() or out.strip() or "defects4j test -r failed")[:400]
                    raise RuntimeError(
                        f"clean relevant-suite run failed for {container_path}:\n{msg}"
                    )

            relevant_test_classes = self.export(container_path, "tests.relevant")
            return {
                "mode": "relevant",
                "source": "defects4j test -r",
                "run_time_s": run_time_s,
                "relevant_test_classes": relevant_test_classes,
                "all_tests": all_tests,
                "failing_tests": failing_tests,
            }
        finally:
            try:
                self.reset_checkout(container_path, timeout=min(timeout, 60))
            except Exception:
                pass

    def warm_relevant_suite(self, container_path: str, timeout: int = 600) -> float:
        """Run one clean warmup ``defects4j test -r`` that is excluded from mutant timings."""
        def _run_once() -> tuple[str, str, int, float, list[str]]:
            t0 = time.perf_counter()
            out, err, rc = self.exec(
                f"cd {container_path} && "
                f"{self.wrap_with_checkout_temp(container_path, 'rm -f all_tests failing_tests && defects4j test -r')}",
                timeout=timeout,
            )
            run_time_s = round(time.perf_counter() - t0, 2)
            failing_raw, _, _ = self.exec(
                f"cat {container_path}/failing_tests 2>/dev/null || true",
            )
            failing_tests = _collect_failing_tests(failing_raw=failing_raw, output_raw=out)
            return out, err, rc, run_time_s, failing_tests

        out = err = ""
        rc = 1
        run_time_s = 0.0
        failing_tests: list[str] = []
        try:
            out, err, rc, run_time_s, failing_tests = _run_once()
            if rc != 0 and not failing_tests:
                self.reset_checkout(container_path, timeout=min(timeout, 60))
                out, err, rc, run_time_s, failing_tests = _run_once()
                if rc != 0 and not failing_tests:
                    msg = (err.strip() or out.strip() or "defects4j test -r warmup failed")[:400]
                    raise RuntimeError(
                        f"relevant-suite warmup failed for {container_path}:\n{msg}"
                    )
            if failing_tests:
                raise RuntimeError(
                    f"relevant-suite warmup is not clean for {container_path}: {failing_tests}"
                )
            return run_time_s
        finally:
            try:
                self.reset_checkout(container_path, timeout=min(timeout, 60))
            except Exception:
                pass

    def run_mutant_relevant(
        self,
        container_path: str,
        mutant: "Mutant",
        timeout: int = 600,
        suite_total_tests: int = 0,
        trigger_tests: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Apply one mutant, run ``defects4j test -r``, restore the file, and return
        a compact structured result.

        This avoids separate host-side patching and separate compile/test exec calls.
        Worker checkouts can therefore live fully inside the container on fast local
        storage instead of the macOS bind mount.
        """
        effective_timeout_s = _effective_mutant_timeout_s(timeout, suite_total_tests)
        payload_b64 = base64.b64encode(
            json.dumps(
                {
                    "filepath": mutant.filepath,
                    "line": int(mutant.line),
                    "precode": mutant.precode,
                    "aftercode": mutant.aftercode,
                    "timeout": int(timeout),
                    "effective_timeout": int(effective_timeout_s),
                    "trigger_tests": list(trigger_tests or []),
                    "cleanup_paths": list(self.mutant_run_cleanup_paths(container_path, mutant.filepath)),
                },
                ensure_ascii=False,
            ).encode("utf-8")
        ).decode("ascii")

        q_payload = shlex.quote(payload_b64)
        python_source = f"""
import base64
import glob
import json
import os
import signal
import shutil
import subprocess
import sys
import time
from pathlib import Path

{_mutant_runner_helper_source()}

def parse_all_tests(raw):
    result = set()
    for entry in raw.strip().splitlines():
        entry = entry.strip()
        if not entry or '(' not in entry:
            continue
        method, rest = entry.split('(', 1)
        cls = rest.rstrip(')')
        result.add(f"{{cls}}::{{method}}")
    return result


def parse_failing_tests(raw):
    result = set()
    in_failing_section = False
    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if line.startswith('Failing tests:'):
            in_failing_section = True
            continue
        if not in_failing_section:
            continue
        if not line:
            if result:
                break
            continue
        if not line.startswith('- '):
            break
        test_id = line[2:].strip()
        if '::' in test_id:
            result.add(test_id)
            continue
        if '(' in test_id and test_id.endswith(')'):
            method, rest = test_id.split('(', 1)
            cls = rest[:-1].strip()
            method = method.strip()
            if cls and method:
                result.add(f"{{cls}}::{{method}}")
    return sorted(result)


def parse_failing_tests_file(raw):
    result = set()
    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line or line.startswith('Failing tests:'):
            continue
        if line.startswith('--- '):
            line = line[4:].strip()
        elif line.startswith('- '):
            line = line[2:].strip()
        if '::' in line and ' ' not in line and not line.startswith('at '):
            result.add(line)
            continue
        if '(' in line and line.endswith(')'):
            method, rest = line.split('(', 1)
            cls = rest[:-1].strip()
            method = method.strip()
            if cls and method and ' ' not in cls and ' ' not in method and not method.startswith('at '):
                result.add(f"{{cls}}::{{method}}")
    return sorted(result)


def collect_failing_tests(failing_raw, output_raw):
    return sorted(set(parse_failing_tests_file(failing_raw)) | set(parse_failing_tests(output_raw)))


payload = json.loads(base64.b64decode(os.environ['MUTANT_PAYLOAD_B64']).decode('utf-8'))
root = Path(sys.argv[1])
target = root / payload['filepath']

record = {{
    'compiled': None,
    'compile_error': '',
    'run_time_s': 0.0,
    'compile_time_s': 0.0,
    'test_time_s': 0.0,
    'wall_time_s': 0.0,
    'timed_out': False,
    'test_executed': False,
    'profile_scope': 'relevant_full',
    'test_command': 'defects4j test -r',
    'failing_count': 0,
    'failing_tests': [],
}}

original = None
try:
    if not target.exists():
        record['compiled'] = False
        record['compile_error'] = f"apply_failed: file not found: {{payload['filepath']}}"
        print(json.dumps(record, ensure_ascii=False))
        raise SystemExit(0)

    original = target.read_text(encoding='utf-8')
    lines = original.splitlines(keepends=True)
    idx = int(payload['line']) - 1
    if idx < 0:
        record['compiled'] = False
        record['compile_error'] = f"apply_failed: invalid line number: {{payload['line']}}"
        print(json.dumps(record, ensure_ascii=False))
        raise SystemExit(0)
    if idx >= len(lines):
        record['compiled'] = False
        record['compile_error'] = (
            f"apply_failed: line {{payload['line']}} out of range for {{payload['filepath']}} "
            f"(file has {{len(lines)}} lines)"
        )
        print(json.dumps(record, ensure_ascii=False))
        raise SystemExit(0)

    expected = str(payload['precode']).strip()
    actual_line = lines[idx].rstrip('\\r\\n')
    if expected not in actual_line:
        record['compiled'] = False
        record['compile_error'] = (
            f"apply_failed: precode mismatch at {{payload['filepath']}}:{{payload['line']}} "
            f"(expected substring={{expected!r}}, actual={{actual_line!r}})"
        )
        print(json.dumps(record, ensure_ascii=False))
        raise SystemExit(0)

    lines[idx] = lines[idx].replace(expected, str(payload['aftercode']).strip(), 1)
    target.write_text(''.join(lines), encoding='utf-8')

    for cleanup_entry in payload.get('cleanup_paths', []):
        cleanup_entry = str(cleanup_entry or '').strip()
        if not cleanup_entry:
            continue

        if any(ch in cleanup_entry for ch in '*?['):
            pattern = cleanup_entry if os.path.isabs(cleanup_entry) else str(root / cleanup_entry)
            for matched in glob.glob(pattern):
                matched_path = Path(matched)
                if matched_path.is_dir():
                    shutil.rmtree(matched_path, ignore_errors=True)
                else:
                    try:
                        matched_path.unlink()
                    except FileNotFoundError:
                        pass
            continue

        cleanup_path = Path(cleanup_entry)
        if not cleanup_path.is_absolute():
            cleanup_path = root / cleanup_path
        if cleanup_path.is_dir():
            shutil.rmtree(cleanup_path, ignore_errors=True)
        else:
            try:
                cleanup_path.unlink()
            except FileNotFoundError:
                pass

    # ── Step 1: run the full relevant suite ─────────────────────────────────
    # Every mutant must get a complete failure profile for RBDR/AOR/CR/HOBR.
    # Clear only the compiled outputs for the mutated source file so reused
    # checkouts stay correct without triggering a full rebuild of the project.
    t0 = time.perf_counter()
    proc = _run_test_command(
        ['defects4j', 'test', '-r'],
        root,
        max(1, int(payload['effective_timeout'])),
    )
    if proc['timed_out']:
        record['compiled'] = True
        record['timed_out'] = True
        record['test_executed'] = True
        record['test_time_s'] = max(1, int(payload['effective_timeout']))
        record['run_time_s'] = record['test_time_s']
        print(json.dumps(record, ensure_ascii=False))
        raise SystemExit(0)

    record['test_time_s'] = round(time.perf_counter() - t0, 2)
    record['run_time_s'] = record['test_time_s']

    output = (proc['stdout'] or '') + '\\n' + (proc['stderr'] or '')
    try:
        failing_raw = (root / 'failing_tests').read_text(encoding='utf-8')
    except FileNotFoundError:
        failing_raw = ''
    failing = collect_failing_tests(failing_raw, output)
    tests_ran = 'Running ant (compile.tests)' in output and 'Running ant (run.dev.tests)' in output

    if 'Failing tests:' in output and failing:
        record['compiled'] = True
        record['test_executed'] = True
        record['failing_tests'] = failing
        record['failing_count'] = len(failing)
    elif tests_ran and failing:
        record['compiled'] = True
        record['test_executed'] = True
        record['failing_tests'] = failing
        record['failing_count'] = len(failing)
    elif tests_ran and proc['returncode'] == 0:
        record['compiled'] = True
        record['test_executed'] = True
        record['failing_tests'] = []
        record['failing_count'] = 0
    else:
        record['compiled'] = False
        msg = (output or 'defects4j test failed').strip()
        record['compile_error'] = msg[:400] if msg else 'defects4j test failed'

    print(json.dumps(record, ensure_ascii=False))
finally:
    if original is not None:
        target.write_text(original, encoding='utf-8')
"""
        encoded_source = base64.b64encode(python_source.encode("utf-8")).decode("ascii")
        runner = (
            "import base64; "
            f"exec(base64.b64decode({encoded_source!r}).decode('utf-8'))"
        )
        script = (
            f"export MUTANT_PAYLOAD_B64={q_payload}\n"
            f"python3 -c {shlex.quote(runner)} {shlex.quote(container_path)}"
        )
        wall_t0 = time.perf_counter()
        out, err, rc = self.exec(
            self.wrap_with_checkout_temp(container_path, script),
            timeout=timeout + 60,
        )
        wall_time_s = round(time.perf_counter() - wall_t0, 2)
        if rc != 0:
            msg = (err.strip() or out.strip() or "container mutant run failed")[:400]
            return {
                "compiled": False,
                "compile_error": msg,
                "run_time_s": wall_time_s,
                "compile_time_s": 0.0,
                "test_time_s": 0.0,
                "wall_time_s": wall_time_s,
                "timed_out": False,
                "test_executed": False,
                "profile_scope": "relevant_full",
                "test_command": "defects4j test -r",
                "failing_count": 0,
                "failing_tests": [],
            }
        result = json.loads(out.strip() or "{}")
        if isinstance(result, dict):
            result["test_time_s"] = float(result.get("test_time_s") or result.get("run_time_s") or 0.0)
            result["compile_time_s"] = float(result.get("compile_time_s") or 0.0)
            result["wall_time_s"] = wall_time_s
            result["run_time_s"] = float(result.get("run_time_s") or result["test_time_s"])
        return result

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
            f"cd {container_path} && "
            f"{self.wrap_with_checkout_temp(container_path, f'defects4j test{t_flag}')}",
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
        failing = _parse_failing_tests_output(out)

        return failing, all_tests


class ParallelCheckoutPool:
    """Pool of isolated checkout copies for safely running container commands in parallel."""

    def __init__(
        self,
        d4j: Defects4J,
        project: str,
        bug_id: int,
        host_workspace: Path | str,
        max_workers: int,
        version: str = "f",
        base_container_path: str | None = None,
        base_host_path: Path | str | None = None,
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be >= 1")

        self.d4j = d4j
        self.project = project
        self.bug_id = int(bug_id)
        self.version = version
        self.host_workspace = Path(host_workspace)
        self.max_workers = int(max_workers)
        self._external_base_checkout = base_container_path is not None
        self.base_container_path = (
            base_container_path
            or f"/tmp/defect4j-base/{project}_{bug_id}_{version}"
        )
        self.base_host_path = (
            Path(base_host_path)
            if base_host_path is not None
            else self.host_workspace / "checkouts" / f"{project}_{bug_id}_{version}"
        )
        self.pool_name = f"{project}_{bug_id}_{version}"
        run_token = f"{os.getpid()}_{int(time.time() * 1000)}_{id(self) & 0xffff:x}"
        self.pool_container_root = f"/tmp/defect4j-parallel/{self.pool_name}_{run_token}"
        self.pool_host_root = self.host_workspace / "parallel" / f"{self.pool_name}_{run_token}"
        self._available: queue.Queue[ContainerCheckout] = queue.Queue()
        self._workspaces: list[ContainerCheckout] = []
        self._prepared = False

    @property
    def workspaces(self) -> list[ContainerCheckout]:
        if not self._prepared:
            self.prepare()
        return list(self._workspaces)

    def prepare(self) -> list[ContainerCheckout]:
        """Ensure the base checkout exists and materialize one isolated copy per worker."""
        self._ensure_base_checkout()
        self._run_checked(
            "test ! -d /tmp/defect4j-parallel || "
            f"find /tmp/defect4j-parallel -mindepth 1 -maxdepth 1 -type d "
            f"-name {shlex.quote(self.pool_name + '_*')} "
            f"! -path {shlex.quote(self.pool_container_root)} -exec rm -rf {{}} +",
            timeout=300,
            action="remove stale parallel checkout roots",
        )
        self.d4j.kill_processes_under_path(self.pool_container_root)
        self._run_checked(
            f"rm -rf {shlex.quote(self.pool_container_root)} && "
            f"mkdir -p {shlex.quote(self.pool_container_root)}",
            timeout=300,
            action="reset parallel checkout root",
        )

        self._available = queue.Queue()
        self._workspaces = []
        for worker_id in range(1, self.max_workers + 1):
            container_path = f"{self.pool_container_root}/worker_{worker_id}"
            host_path = self.pool_host_root / f"worker_{worker_id}"
            self._copy_checkout(self.base_container_path, container_path)
            checkout = ContainerCheckout(
                d4j=self.d4j,
                worker_id=worker_id,
                container_path=container_path,
                host_path=host_path,
            )
            self._workspaces.append(checkout)
            self._available.put(checkout)

        self._prepared = True
        return self.workspaces

    def acquire(self) -> ContainerCheckout:
        """Borrow one isolated checkout from the pool."""
        if not self._prepared:
            self.prepare()
        return self._available.get()

    def release(self, checkout: ContainerCheckout) -> None:
        """Return a previously borrowed checkout back to the pool."""
        self._available.put(checkout)

    def reset_workspace(self, checkout: ContainerCheckout, timeout: int = 300) -> None:
        """Restore one worker checkout in place; fall back to a full copy only if needed."""
        self.d4j.kill_processes_under_path(checkout.container_path, timeout=min(timeout, 30))
        try:
            self.d4j.reset_checkout(checkout.container_path, timeout=timeout)
            return
        except Exception:
            # If the worker checkout itself is broken (for example after a partial
            # failed restore), rebuild it from the shared base checkout as a fallback.
            self._copy_checkout(self.base_container_path, checkout.container_path)

    def cleanup(self) -> None:
        """Delete all worker checkout copies created by this pool."""
        self.d4j.kill_processes_under_path(self.pool_container_root)
        self._run_checked(
            f"rm -rf {shlex.quote(self.pool_container_root)}",
            timeout=300,
            action="remove parallel checkout root",
        )
        self._available = queue.Queue()
        self._workspaces = []
        self._prepared = False

    def _ensure_base_checkout(self) -> None:
        out, _, rc = self.d4j.exec(
            f"test -d {shlex.quote(self.base_container_path)} && "
            f"find {shlex.quote(self.base_container_path)} -mindepth 1 -maxdepth 1 | head -1"
        )
        if rc == 0 and out.strip():
            if not self._external_base_checkout:
                self.d4j.reset_checkout(self.base_container_path)
            return
        self.d4j.checkout(
            self.project,
            self.bug_id,
            self.version,
            dest=self.base_container_path,
            timeout=180,
        )
        if not self._external_base_checkout:
            self.d4j.reset_checkout(self.base_container_path)

    def _copy_checkout(self, src: str, dest: str) -> None:
        copy_cmd = (
            f"rm -rf {shlex.quote(dest)} && "
            f"mkdir -p {shlex.quote(dest)} && "
            f"tar -C {shlex.quote(src)} "
            f"--exclude='./.git' "
            f"--exclude='./build' "
            f"--exclude='./target' "
            f"--exclude='./all_tests' "
            f"--exclude='./failing_tests' "
            f"-cf - . | "
            f"tar -C {shlex.quote(dest)} -xf -"
        )
        try:
            self._run_checked(
                copy_cmd,
                timeout=300,
                action=f"copy checkout to {dest}",
            )
        except RuntimeError as copy_error:
            self._run_checked(
                f"rm -rf {shlex.quote(dest)}",
                timeout=120,
                action=f"remove broken checkout {dest}",
            )
            try:
                self.d4j.checkout(
                    self.project,
                    self.bug_id,
                    self.version,
                    dest=dest,
                    timeout=300,
                )
                self._run_checked(
                    f"rm -rf {shlex.quote(dest)}/.git "
                    f"{shlex.quote(dest)}/build "
                    f"{shlex.quote(dest)}/target "
                    f"{shlex.quote(dest)}/all_tests "
                    f"{shlex.quote(dest)}/failing_tests",
                    timeout=120,
                    action=f"trim fallback checkout {dest}",
                )
            except Exception as fallback_error:
                raise RuntimeError(
                    f"{copy_error}\n\nfallback checkout for {dest} failed:\n{fallback_error}"
                ) from fallback_error

    def _run_checked(self, bash_cmd: str, timeout: int, action: str) -> None:
        out, err, rc = self.d4j.exec(bash_cmd, timeout=timeout)
        if rc != 0:
            message = (err.strip() or out.strip() or f"exit code {rc}")
            raise RuntimeError(f"{action} failed:\n{message}")
