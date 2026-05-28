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
import os
import queue
import re
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Tuple

if TYPE_CHECKING:
    from .mutant import Mutant


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


def _parse_failing_tests_output(raw: str) -> set[str]:
    """Parse failing Defects4J test IDs from command stdout."""
    return {
        line.strip()[2:]
        for line in raw.splitlines()
        if line.strip().startswith("- ") and "::" in line
    }


def _mutant_runner_helper_source() -> str:
    """Python helper source embedded into the in-container mutant runner."""
    return r'''
def _path_is_inside(path, root):
    path = os.path.realpath(str(path))
    root = os.path.realpath(str(root))
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def _text_references_root(text, root):
    text = str(text or '')
    root = os.path.normpath(str(root))
    start = 0
    while True:
        index = text.find(root, start)
        if index == -1:
            return False
        after_index = index + len(root)
        after_ok = after_index == len(text) or text[after_index] in {'/', os.sep, ' ', '\t', '\n', '\r', '"', "'", ';', ':'}
        before_ok = index == 0 or text[index - 1] in {'=', ' ', '\t', '\n', '\r', '"', "'", ':', ';'}
        if before_ok and after_ok:
            return True
        start = index + 1


def _process_is_checkout_related(pid, root):
    proc_dir = Path('/proc') / str(pid)
    try:
        cwd = os.readlink(proc_dir / 'cwd')
        if _path_is_inside(cwd, root):
            return True
    except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
        pass

    try:
        raw_cmdline = (proc_dir / 'cmdline').read_bytes()
        cmdline = raw_cmdline.replace(b'\x00', b' ').decode('utf-8', errors='ignore')
        if _text_references_root(cmdline, root):
            return True
    except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
        pass

    return False


def _checkout_related_pids(root):
    root = os.path.realpath(str(root))
    current = os.getpid()
    parent = os.getppid()
    pids = []
    proc_root = Path('/proc')
    if not proc_root.exists():
        return pids
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid in {current, parent}:
            continue
        if _process_is_checkout_related(pid, root):
            pids.append(pid)
    return pids


def _terminate_pids(pids, sig):
    for pid in sorted(set(pids), reverse=True):
        try:
            os.kill(pid, sig)
        except (ProcessLookupError, PermissionError, OSError):
            pass


def _kill_checkout_leftovers(root):
    pids = _checkout_related_pids(root)
    if not pids:
        return 0
    _terminate_pids(pids, signal.SIGTERM)
    time.sleep(0.3)
    remaining = [pid for pid in pids if _process_is_checkout_related(pid, root)]
    if remaining:
        _terminate_pids(remaining, signal.SIGKILL)
    time.sleep(0.1)
    return len(pids)


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
    finally:
        _kill_checkout_leftovers(root)

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
        cmd = ("export LANG=C.UTF-8 LC_ALL=C.UTF-8; " + bash_cmd).replace('"', '\\"')
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

    def kill_processes_under_path(self, container_path: str, timeout: int = 30) -> None:
        """Best-effort kill of processes whose cwd/cmdline belongs to *container_path*."""
        script = r'''
import os
import signal
import time
from pathlib import Path

root = os.path.normpath(os.environ['TARGET_ROOT'])
current = os.getpid()
parent = os.getppid()

def text_references_root(text):
    text = str(text or '')
    start = 0
    while True:
        index = text.find(root, start)
        if index == -1:
            return False
        after_index = index + len(root)
        after_ok = after_index == len(text) or text[after_index] in {'/', os.sep, ' ', '\t', '\n', '\r', '"', "'", ';', ':'}
        before_ok = index == 0 or text[index - 1] in {'=', ' ', '\t', '\n', '\r', '"', "'", ':', ';'}
        if before_ok and after_ok:
            return True
        start = index + 1

def is_related(pid):
    proc_dir = Path('/proc') / str(pid)
    try:
        cwd = os.path.normpath(os.readlink(proc_dir / 'cwd'))
        if cwd == root or cwd.startswith(root.rstrip(os.sep) + os.sep):
            return True
    except Exception:
        pass
    try:
        cmdline = (proc_dir / 'cmdline').read_bytes().replace(b'\x00', b' ').decode('utf-8', 'ignore')
        return text_references_root(cmdline)
    except Exception:
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

for sig in (signal.SIGTERM, signal.SIGKILL):
    if not pids:
        break
    for pid in sorted(set(pids), reverse=True):
        try:
            os.kill(pid, sig)
        except Exception:
            pass
    time.sleep(0.5 if sig == signal.SIGTERM else 0.1)
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

    def reset_checkout(self, container_path: str, timeout: int = 60) -> None:
        """Restore a checkout to a clean git state before reusing it."""
        _, err, rc = self.exec(
            f"cd {container_path} && git reset --hard -q HEAD && git clean -fdq",
            timeout=timeout,
        )
        if rc != 0:
            raise RuntimeError(f"reset checkout failed for {container_path}:\n{err}")

    def relevant_test_profile(self, container_path: str, timeout: int = 600) -> dict[str, Any]:
        """Run a clean ``defects4j test -r`` once and return the authoritative suite profile."""
        t0 = time.perf_counter()
        out, err, rc = self.exec(
            f"cd {container_path} && rm -f all_tests && defects4j test -r",
            timeout=timeout,
        )
        run_time_s = round(time.perf_counter() - t0, 2)
        all_raw, _, _ = self.exec(
            f"cat {container_path}/all_tests 2>/dev/null || true",
        )
        all_tests = sorted(_parse_all_tests_file(all_raw))
        failing_tests = sorted(_parse_failing_tests_output(out))

        if rc != 0 and "Failing tests:" not in out:
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

    def warm_relevant_suite(self, container_path: str, timeout: int = 600) -> float:
        """Run one clean warmup ``defects4j test -r`` that is excluded from mutant timings."""
        t0 = time.perf_counter()
        out, err, rc = self.exec(
            f"cd {container_path} && rm -f all_tests && defects4j test -r",
            timeout=timeout,
        )
        run_time_s = round(time.perf_counter() - t0, 2)
        failing_tests = sorted(_parse_failing_tests_output(out))

        if rc != 0 and "Failing tests:" not in out:
            msg = (err.strip() or out.strip() or "defects4j test -r warmup failed")[:400]
            raise RuntimeError(
                f"relevant-suite warmup failed for {container_path}:\n{msg}"
            )
        if failing_tests:
            raise RuntimeError(
                f"relevant-suite warmup is not clean for {container_path}: {failing_tests}"
            )
        return run_time_s

    def run_mutant_relevant(
        self,
        container_path: str,
        mutant: "Mutant",
        timeout: int = 600,
        trigger_tests: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Apply one mutant, run ``defects4j test -r``, restore the file, and return
        a compact structured result.

        This avoids separate host-side patching and separate compile/test exec calls.
        Worker checkouts can therefore live fully inside the container on fast local
        storage instead of the macOS bind mount.
        """
        payload_b64 = base64.b64encode(
            json.dumps(
                {
                    "filepath": mutant.filepath,
                    "line": int(mutant.line),
                    "precode": mutant.precode,
                    "aftercode": mutant.aftercode,
                    "timeout": int(timeout),
                    "trigger_tests": list(trigger_tests or []),
                },
                ensure_ascii=False,
            ).encode("utf-8")
        ).decode("ascii")

        q_path = shlex.quote(container_path)
        q_payload = shlex.quote(payload_b64)
        script = f"""
export MUTANT_PAYLOAD_B64={q_payload}
python3 - <<'PY' {q_path}
import base64
import json
import os
import signal
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
    return sorted(
        line.strip()[2:]
        for line in raw.splitlines()
        if line.strip().startswith('- ') and '::' in line
    )


payload = json.loads(base64.b64decode(os.environ['MUTANT_PAYLOAD_B64']).decode('utf-8'))
root = Path(sys.argv[1])
target = root / payload['filepath']

record = {{
    'compiled': None,
    'compile_error': '',
    'run_time_s': 0.0,
    'timed_out': False,
    'test_executed': False,
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

    # ── Step 1: compile (outside the test timer) ─────────────────────────────
    # Compiling separately means `defects4j test -r` (and every `test -t`) will
    # detect that .class files are newer than .java and SKIP recompilation.
    # This restores the fast (~2s) per-mutant test time seen before the refactor
    # that merged compile + test into a single `defects4j test -r` call.
    compile_proc = _run_test_command(
        ['defects4j', 'compile'],
        root,
        min(int(payload['timeout']), 30),
    )
    _kill_checkout_leftovers(root)
    if compile_proc['timed_out']:
        record['compiled'] = False
        record['compile_error'] = 'defects4j compile timed out'
        print(json.dumps(record, ensure_ascii=False))
        raise SystemExit(0)
    if compile_proc['returncode'] != 0:
        record['compiled'] = False
        compile_out = (compile_proc['stdout'] or '') + '\\n' + (compile_proc['stderr'] or '')
        record['compile_error'] = (compile_out.strip() or 'defects4j compile failed')[:400]
        print(json.dumps(record, ensure_ascii=False))
        raise SystemExit(0)

    # ── Step 2: run tests (timer starts here — compile excluded) ─────────────
    t0 = time.perf_counter()
    trigger_tests = list(payload.get('trigger_tests') or [])
    for test_id in trigger_tests:
        proc = _run_test_command(
            ['defects4j', 'test', '-t', str(test_id)],
            root,
            min(int(payload['timeout']), 30),
        )
        _kill_checkout_leftovers(root)
        if proc['timed_out']:
            record['compiled'] = True
            record['timed_out'] = True
            record['test_executed'] = True
            record['run_time_s'] = round(time.perf_counter() - t0, 2)
            print(json.dumps(record, ensure_ascii=False))
            raise SystemExit(0)
        output = (proc['stdout'] or '') + '\\n' + (proc['stderr'] or '')
        failing = parse_failing_tests(output)
        if failing:
            record['compiled'] = True
            record['test_executed'] = True
            record['run_time_s'] = round(time.perf_counter() - t0, 2)
            record['failing_tests'] = failing
            record['failing_count'] = len(failing)
            print(json.dumps(record, ensure_ascii=False))
            raise SystemExit(0)
        if proc['returncode'] != 0 and 'Running ant (compile.tests)' in output and 'OK' in output:
            record['compiled'] = True
            record['test_executed'] = True
            record['run_time_s'] = round(time.perf_counter() - t0, 2)
            record['failing_tests'] = ['<test failure>']
            record['failing_count'] = 1
            print(json.dumps(record, ensure_ascii=False))
            raise SystemExit(0)
        if proc['returncode'] != 0 and 'Failing tests:' not in output:
            record['compiled'] = False
            msg = (output or 'defects4j trigger test failed').strip()
            record['compile_error'] = msg[:400] if msg else 'defects4j trigger test failed'
            record['run_time_s'] = round(time.perf_counter() - t0, 2)
            print(json.dumps(record, ensure_ascii=False))
            raise SystemExit(0)

    proc = _run_test_command(
        ['defects4j', 'test', '-r'],
        root,
        min(int(payload['timeout']), 30),
    )
    _kill_checkout_leftovers(root)
    if proc['timed_out']:
        record['compiled'] = True
        record['timed_out'] = True
        record['test_executed'] = True
        record['run_time_s'] = min(int(payload['timeout']), 30)
        print(json.dumps(record, ensure_ascii=False))
        raise SystemExit(0)

    record['run_time_s'] = round(time.perf_counter() - t0, 2)

    output = (proc['stdout'] or '') + '\\n' + (proc['stderr'] or '')
    failing = parse_failing_tests(output)

    if 'Failing tests:' in output:
        record['compiled'] = True
        record['test_executed'] = True
        record['failing_tests'] = failing
        record['failing_count'] = len(failing)
    elif 'Running ant (compile.tests)' in output and 'Running ant (run.dev.tests)' in output:
        record['compiled'] = True
        record['test_executed'] = True
        record['failing_tests'] = failing or ['<test failure>']
        record['failing_count'] = len(record['failing_tests'])
    else:
        record['compiled'] = False
        msg = (output or 'defects4j test failed').strip()
        record['compile_error'] = msg[:400] if msg else 'defects4j test failed'

    print(json.dumps(record, ensure_ascii=False))
finally:
    _kill_checkout_leftovers(root)
    if original is not None:
        target.write_text(original, encoding='utf-8')
PY
"""
        out, err, rc = self.exec(script, timeout=timeout + 60)
        if rc != 0:
            msg = (err.strip() or out.strip() or "container mutant run failed")[:400]
            return {
                "compiled": False,
                "compile_error": msg,
                "run_time_s": 0.0,
                "timed_out": False,
                "test_executed": False,
                "failing_count": 0,
                "failing_tests": [],
            }
        return json.loads(out.strip() or "{}")

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
        pool_name = f"{project}_{bug_id}_{version}"
        run_token = f"{os.getpid()}_{int(time.time() * 1000)}_{id(self) & 0xffff:x}"
        self.pool_container_root = f"/tmp/defect4j-parallel/{pool_name}_{run_token}"
        self.pool_host_root = self.host_workspace / "parallel" / f"{pool_name}_{run_token}"
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
        self._run_checked(
            f"rm -rf {shlex.quote(dest)} && "
            f"mkdir -p {shlex.quote(dest)} && "
            f"tar -C {shlex.quote(src)} -cf - . | "
            f"tar -C {shlex.quote(dest)} -xf -",
            timeout=300,
            action=f"copy checkout to {dest}",
        )

    def _run_checked(self, bash_cmd: str, timeout: int, action: str) -> None:
        _, err, rc = self.d4j.exec(bash_cmd, timeout=timeout)
        if rc != 0:
            raise RuntimeError(f"{action} failed:\n{err}")


