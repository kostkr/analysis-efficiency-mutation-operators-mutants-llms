"""Minimal Podman-backed Defects4J toolbox.

This module provides a small, focused API to run the exact Defects4J
CLI commands you requested inside a running Podman container named
`defects4j-container`. It avoids copying checkouts out of the container; all
operations (checkout, compile, test, mutation, export, info, bids, pids)
are executed inside the container via `podman exec`.

It also provides helpers to upload local mutant files into the container
using `podman cp <file> <container>:<path>` (per-file) and to backup/restore
the original file inside the container (file.orig). Everything is
intentional and minimal to match your requested workflow.
"""

from __future__ import annotations

import shlex
import subprocess
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


CONTAINER_DEFAULT = "defects4j-container"


def _run_local(cmd: List[str], *, check: bool = False, timeout: Optional[int] = None) -> Dict[str, str]:
    p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    out, err = p.stdout or "", p.stderr or ""
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{out}\nSTDERR:\n{err}")
    return {"cmd": " ".join(shlex.quote(x) for x in cmd), "returncode": p.returncode, "stdout": out, "stderr": err}


@dataclass
class CheckoutHandle:
    project: str
    bug_id: int
    version: str
    container_workdir: str


@dataclass
class TestRunResult:
    returncode: int
    stdout: str
    stderr: str
    failing_tests: List[str]
    all_tests: List[str]


@dataclass(frozen=True)
class ProjectInfo:
    project_id: Optional[str] = None
    program: Optional[str] = None
    build_file: Optional[str] = None
    vcs: Optional[str] = None
    repository: Optional[str] = None
    commit_db: Optional[str] = None
    number_of_bugs: int = 0


@dataclass(frozen=True)
class BugInfo:
    bug_name: Optional[str] = None
    bug_id: Optional[int] = None
    revision_id: Optional[str] = None
    revision_date: Optional[str] = None
    bug_report_id: Optional[str] = None
    bug_report_url: Optional[str] = None
    modified_sources: List[str] = field(default_factory=list)
    triggering_tests: List[str] = field(default_factory=list)
    root_cause_tests: List[str] = field(default_factory=list)


class PodmanD4J:
    def __init__(self, container: str = CONTAINER_DEFAULT):
        self.container = container

    def _exec(self, script: str, *, timeout: Optional[int] = None, check: bool = False) -> Dict[str, str]:
        cmd = ["podman", "exec", "-i", self.container, "bash", "-lc", script]
        return _run_local(cmd, check=check, timeout=timeout)

    # Basic D4J commands
    def pids(self) -> List[str]:
        r = self._exec("defects4j pids")
        return [l.strip() for l in r["stdout"].splitlines() if l.strip()]

    def bids(self, project: str) -> List[int]:
        r = self._exec(f"defects4j bids -p {shlex.quote(project)}")
        return [int(l.strip()) for l in r["stdout"].splitlines() if l.strip()]

    # --- New: split project and bug parsing ---
    def _parse_info_output(self, raw: str) -> Dict[str, str]:
        """Parse defects4j info output into a normalized key/value map.

        The Defects4J CLI uses different label variants across versions and
        projects (e.g. "Modified files" vs "Modified sources", "Revision ID
        (fixed)" vs "Revision ID (fixed version)"). This helper normalizes
        keys and collects bullet lists for sections like modified files,
        triggering tests and root cause tests.
        """
        lines = raw.splitlines()

        def norm_key(k: str) -> str:
            k = k.strip().lower()
            k = re.sub(r"\s+", " ", k)
            k = re.sub(r"[^a-z0-9]+", "_", k)
            return k.strip("_")

        def is_bullet(ln: str) -> bool:
            # accept bullets even with leading whitespace
            s = ln.lstrip()
            return s.startswith("- ") or s.startswith("* ")

        def collect_bullets(start: int):
            acc = []
            i = start
            last_idx = -1
            while i < len(lines):
                # if this line is a bullet, start a new item
                if is_bullet(lines[i]):
                    item = lines[i].lstrip()[2:].strip()
                    acc.append(item)
                    last_idx = len(acc) - 1
                    i += 1
                    # after the bullet, accept continuation lines that are arrow-prefixed
                    while i < len(lines):
                        # match lines like '   --> some text' or '-> some text' or '--> some text'
                        cont_match = re.match(r"^\s*-+>\s*(.*)$", lines[i])
                        if cont_match and last_idx >= 0:
                            cont_text = cont_match.group(1).strip()
                            if cont_text:
                                # append continuation with a separator
                                acc[last_idx] = acc[last_idx] + " -> " + cont_text
                            i += 1
                            continue
                        # also accept indented continuation lines (e.g. '   additional info')
                        if lines[i].startswith(" ") and not is_bullet(lines[i]) and lines[i].strip():
                            if last_idx >= 0:
                                acc[last_idx] = acc[last_idx] + " " + lines[i].strip()
                            i += 1
                            continue
                        break
                    # continue outer loop to look for next bullet
                    continue
                # not a bullet -> stop collecting
                break
            return acc, i

        kv: Dict[str, str] = {}
        i = 0
        while i < len(lines):
            ln = lines[i]
            # first, check for known bullet-section headers by content so we don't
            # accidentally consume the header as a key:value pair when the
            # values are presented as bullet lists on the following lines.
            head = ln.strip().lower()

            # Modified files / Modified sources / List of modified sources
            if "modified" in head and ("file" in head or "source" in head):
                # collect subsequent bullet lines
                i += 1
                mods, i = collect_bullets(i)
                kv["__modified_sources__"] = "\n".join(mods)
                continue

            # Root cause tests / Root cause in triggering tests / Root-cause tests
            if "root" in head and "test" in head:
                i += 1
                roots, i = collect_bullets(i)
                kv["__root_cause_tests__"] = "\n".join(roots)
                continue

            # Triggering tests / Triggering test(s)
            if "trigger" in head and "test" in head:
                i += 1
                trig, i = collect_bullets(i)
                kv["__triggering_tests__"] = "\n".join(trig)
                continue

            # Now handle inline Key: Value on same line
            m = re.match(r"^\s*([^:]+):\s*(.*)$", ln)
            if m and m.group(2).strip():
                key = norm_key(m.group(1))
                kv[key] = m.group(2).strip()
                i += 1
                continue

            # Handle Key: followed by value on next non-empty non-bullet line
            if m and not m.group(2).strip():
                key = norm_key(m.group(1))
                # look ahead for next meaningful line
                j = i + 1
                # skip blank lines
                while j < len(lines) and lines[j].strip() == "":
                    j += 1
                if j < len(lines) and not is_bullet(lines[j]):
                    kv[key] = lines[j].strip()
                    i = j + 1
                    continue
                else:
                    # no non-bullet next-line value; store empty marker
                    kv[key] = ""
                    i += 1
                    continue

            # nothing matched, move on
            i += 1

        return kv

    def project_info(self, project: str) -> ProjectInfo:
        """Return ProjectInfo for a given project (calls `defects4j info -p`)."""
        cmd = f"defects4j info -p {shlex.quote(project)}"
        raw = self._exec(cmd)["stdout"]
        kv = self._parse_info_output(raw)

        def to_int(s: Optional[str], default=0):
            try:
                return int(s) if s else default
            except:
                return default

        proj = ProjectInfo(
            project_id=kv.get("project_id") or kv.get("project") or kv.get("project_name"),
            program=kv.get("program"),
            build_file=kv.get("build_file") or kv.get("buildfile"),
            vcs=kv.get("vcs"),
            repository=kv.get("repository"),
            commit_db=kv.get("commit_db") or kv.get("commitdb") or kv.get("commit_db_file"),
            number_of_bugs=to_int(kv.get("number_of_bugs") or kv.get("number_of_bug") or kv.get("bugs"))
        )
        return proj

    def bug_info(self, project: str, bug_id: int) -> BugInfo:
        """Return BugInfo for a given project+bug (calls `defects4j info -p -b`).

        This method focuses on parsing the bug-related fields. It calls
        Defects4J with the -b option which prints both project and bug data;
        the parser then extracts relevant bug keys and bullet sections.
        """
        cmd = f"defects4j info -p {shlex.quote(project)} -b {int(bug_id)}"
        raw = self._exec(cmd)["stdout"]
        kv = self._parse_info_output(raw)

        # summary may be present under 'summary' or 'summary_for_bug'
        bug_name = kv.get("summary_for_bug") or kv.get("summary") or kv.get("summary_for")

        # attempt to get numeric id if not passed
        bug_id_val = int(bug_id) if bug_id is not None else None
        if bug_id_val is None and bug_name:
            m = re.search(r"-(\d+)$", bug_name)
            if m:
                try:
                    bug_id_val = int(m.group(1))
                except:
                    bug_id_val = None

        def unpack(name: str):
            v = kv.get(name, "")
            return [x for x in v.split("\n") if x] if v else []

        # Look for revision id/date under several possible key names
        rev_id = kv.get("revision_id_fixed_version") or kv.get("revision_id_fixed") or kv.get("revision_id") or kv.get("revision")
        rev_date = kv.get("revision_date_fixed_version") or kv.get("revision_date_fixed") or kv.get("revision_date") or kv.get("revision_date")

        # Bug report id/url
        br_id = kv.get("bug_report_id") or kv.get("bug_report") or kv.get("bug_report_identifier")
        br_url = kv.get("bug_report_url") or kv.get("bug_report_link") or kv.get("bug_report")

        modified = unpack("__modified_sources__") or unpack("modified_files") or unpack("modified_sources")
        triggering = unpack("__triggering_tests__") or unpack("triggering_tests") or unpack("triggering")
        roots = unpack("__root_cause_tests__") or unpack("root_cause_tests") or unpack("root_causes")

        # Some Defects4J outputs use "Root cause in triggering tests" meaning
        # the same list is both 'root cause' and 'triggering' tests. If one is
        # empty and the other populated, mirror the data so both fields are
        # practical for downstream consumers.
        if not triggering and roots:
            triggering = roots

        bug = BugInfo(
            bug_name=bug_name,
            bug_id=bug_id_val,
            revision_id=rev_id or "",
            revision_date=rev_date or "",
            bug_report_id=br_id or "",
            bug_report_url=br_url or "",
            modified_sources=modified,
            triggering_tests=triggering,
            root_cause_tests=roots
        )

        return bug

    # Backwards compatibility: old info() returning both pieces
    def info(self, project: str, bug_id: Optional[int] = None) -> Tuple[ProjectInfo, Optional[BugInfo]]:
        proj = self.project_info(project)
        bug = None
        if bug_id is not None:
            bug = self.bug_info(project, bug_id)
        return proj, bug

    def export(self, container_workdir: str, prop: str) -> str:
        r = self._exec(f"defects4j export -w {shlex.quote(container_workdir)} -p {shlex.quote(prop)}")
        return r["stdout"].strip()

    def checkout(self, project: str, bug_id: int, version: str, *, container_workdir: Optional[str] = None) -> CheckoutHandle:
        version = version.lower()
        if version not in ("b", "f"):
            raise ValueError("version must be 'b' or 'f'")
        if container_workdir is None:
            # deterministic temporary path
            container_workdir = f"/tmp/d4j_{project}_{bug_id}{version}"
        # remove and checkout
        self._exec(f"rm -rf {shlex.quote(container_workdir)}", check=False)
        self._exec(f"defects4j checkout -p {shlex.quote(project)} -v {bug_id}{version} -w {shlex.quote(container_workdir)}", check=True, timeout=600)
        return CheckoutHandle(project=project, bug_id=bug_id, version=version, container_workdir=container_workdir)

    def compile(self, checkout: CheckoutHandle) -> Dict[str, str]:
        return self._exec(f"defects4j compile -w {shlex.quote(checkout.container_workdir)}", check=False, timeout=900)

    def test(self, checkout: CheckoutHandle, *, relevant: bool = False, single_test: Optional[str] = None) -> TestRunResult:
        cmd = f"defects4j test -w {shlex.quote(checkout.container_workdir)}"
        if relevant:
            cmd += " -r"
        if single_test:
            cmd += f" -t {shlex.quote(single_test)}"
        r = self._exec(cmd, check=False, timeout=1800)
        # extract failing_tests/all_tests content
        failing = self._exec(f"bash -lc 'if [ -f {shlex.quote(checkout.container_workdir)}/failing_tests ]; then cat {shlex.quote(checkout.container_workdir)}/failing_tests; fi'", check=False)
        allt = self._exec(f"bash -lc 'if [ -f {shlex.quote(checkout.container_workdir)}/all_tests ]; then cat {shlex.quote(checkout.container_workdir)}/all_tests; fi'", check=False)
        failing_list = [l[4:].strip() for l in failing["stdout"].splitlines() if l.strip().startswith("--- ")]
        all_list = [l.strip() for l in allt["stdout"].splitlines() if l.strip() and not l.strip().startswith("--- ")]
        return TestRunResult(returncode=int(r["returncode"]), stdout=r["stdout"], stderr=r["stderr"], failing_tests=failing_list, all_tests=all_list)

    def mutation(self, checkout: CheckoutHandle, *, extra_args: str = "") -> Dict[str, str]:
        cmd = f"defects4j mutation -w {shlex.quote(checkout.container_workdir)} {extra_args}"
        return self._exec(cmd, check=False, timeout=7200)

    def coverage(self, checkout: CheckoutHandle, *, extra_args: str = "") -> Dict[str, str]:
        cmd = f"defects4j coverage -w {shlex.quote(checkout.container_workdir)} {extra_args}"
        return self._exec(cmd, check=False, timeout=3600)

    # File-level mutant upload into container (per-file copy)
    def upload_file(self, local_path: str, container_dest: str) -> Dict[str, str]:
        """Upload a local file to <container>:<container_dest> via podman cp."""
        return _run_local(["podman", "cp", str(local_path), f"{self.container}:{container_dest}"], check=True)

    def backup_file_in_container(self, container_path: str) -> None:
        self._exec(f"if [ -f {shlex.quote(container_path)} ]; then cp {shlex.quote(container_path)} {shlex.quote(container_path)}.orig; fi", check=False)

    def restore_file_in_container(self, container_path: str) -> None:
        self._exec(f"if [ -f {shlex.quote(container_path)}.orig ]; then mv -f {shlex.quote(container_path)}.orig {shlex.quote(container_path)}; fi", check=False)
