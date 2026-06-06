"""pit/generator.py — simplified PIT generator using direct CLASSIC_JSON output.

The heavy lifting now happens inside the bundled PIT sources:
- PIT computes the mutation metadata
- the custom ``CLASSIC_JSON`` listener resolves source lines and produces
  ready-to-save classic mutant records
- this Python module only runs PIT and maps the direct records to ``Mutant``
  objects used by the rest of the notebook pipeline
"""

from __future__ import annotations

from pathlib import Path
import shlex
import subprocess
import threading
import time
from typing import TYPE_CHECKING

from ..base import BaseGenerator, GeneratorJob, PITConfig
from ..source_finder import _top_level_class_fqn
from .xml_parser import PITClassicEntry, parse_classic_entries

if TYPE_CHECKING:
    from ...container import Defects4J
    from ...mutant import Mutant

_PIT_MAIN = "org.pitest.mutationtest.tooling.ClassicJsonMutationGenerator"


class PITGenerator(BaseGenerator):
    """Run the bundled PIT build and read direct CLASSIC_JSON mutant records."""

    _CUSTOM_PIT_LOCK = threading.Lock()
    _CUSTOM_PIT_READY: set[str] = set()
    _CUSTOM_PIT_CONTAINER_DIR = "/opt/custom-pitest"
    _CUSTOM_PIT_READY_FILE = "/opt/custom-pitest/.classic_pit_ready"
    _CUSTOM_PIT_VERSION = "classic-json-v30-nonconstant-char-while"

    def __init__(self, config: PITConfig, d4j: "Defects4J") -> None:
        self.config = config
        self.d4j = d4j
        self._classpath_cache: dict[str, str] = {}
        self._src_dir_cache: dict[str, str] = {}
        self._entry_cache: dict[tuple[str, str], list[PITClassicEntry]] = {}

    def generate(self, job: GeneratorJob) -> list["Mutant"]:
        from ...mutant import Mutant

        t0 = time.perf_counter()
        self._ensure_custom_pitest_available()

        try:
            classpath = self._classpath(job.container_path)
            src_dir = self._source_dir(job.container_path)
        except RuntimeError as exc:
            print(f"[PITGenerator] defects4j export failed for {job.class_fqn}: {exc}")
            return []

        report_dir = self._report_dir(job.container_path, job.class_fqn)
        cmd = self._build_generator_cmd(
            class_fqn=job.class_fqn,
            classpath=classpath,
            src_dir=src_dir,
            report_dir=report_dir,
            project_base=job.container_path,
            target_methods=job.method_name,
        )
        out, err, rc = self.d4j.exec(f'cd "{job.container_path}" && {cmd}', timeout=self.config.timeout_s)
        gen_time = round(time.perf_counter() - t0, 2)

        if rc != 0:
            short = (err or out or "").strip()[-800:]
            print(f"[PITGenerator] classic generator failed for {job.class_fqn} (rc={rc}):\n{short}")
            return []

        self._entry_cache.pop((job.container_path, job.class_fqn), None)
        entries = self._read_entries(job.container_path, job.class_fqn)
        if not entries:
            print(f"[PITGenerator] no CLASSIC_JSON report found for {job.class_fqn}")
            return []
        entries = self._entries_for_job(entries, job)
        if not entries:
            print(
                f"[PITGenerator] CLASSIC_JSON report for {job.class_fqn} "
                f"contained no mutations in {job.method_name} lines "
                f"{job.method_start}-{job.method_end}"
            )
            return []

        mutants: list[Mutant] = []
        for entry in entries:
            mutants.append(
                Mutant(
                    id=len(mutants) + 1,
                    filepath=entry.filepath or job.filepath,
                    line=entry.line,
                    precode=entry.precode,
                    aftercode=entry.aftercode,
                    rule=entry.rule,
                    gen_time_s=0.0,
                    dublicate=False,
                )
            )

        if mutants:
            per_mutant = round(gen_time / len(mutants), 2)
            for mutant in mutants:
                mutant.gen_time_s = per_mutant
        return mutants

    def _entries_for_job(self, entries: list[PITClassicEntry], job: GeneratorJob) -> list[PITClassicEntry]:
        job_path = job.filepath.replace("\\", "/").lstrip("/")
        return [
            entry
            for entry in entries
            if entry.filepath.replace("\\", "/").lstrip("/") == job_path
            and job.method_start <= int(entry.line) <= job.method_end
        ]

    def _classpath(self, container_path: str) -> str:
        cached = self._classpath_cache.get(container_path)
        if cached is not None:
            return cached
        lines = self.d4j.export(container_path, "cp.test")
        cp = next((line for line in reversed(lines) if ":" in line), "")
        if not cp:
            raise RuntimeError(f"empty cp.test for {container_path}")
        self._classpath_cache[container_path] = cp
        return cp

    def _source_dir(self, container_path: str) -> str:
        cached = self._src_dir_cache.get(container_path)
        if cached is not None:
            return cached
        lines = self.d4j.export(container_path, "dir.src.classes")
        rel = (lines[-1] if lines else "src/main/java").strip()
        abs_dir = rel if rel.startswith("/") else f"{container_path}/{rel}"
        self._src_dir_cache[container_path] = abs_dir
        return abs_dir

    def _build_generator_cmd(
        self,
        class_fqn: str,
        classpath: str,
        src_dir: str,
        report_dir: str,
        project_base: str,
        target_methods: str,
    ) -> str:
        custom_cp = self._custom_pit_classpath_prefix()
        mutators = self._effective_mutators()
        cp_arg = shlex.quote(custom_cp + classpath)
        target_class = self._pit_target_class(class_fqn)
        return (
            f"java -cp {cp_arg}"
            f" {_PIT_MAIN}"
            f" --projectBase {shlex.quote(project_base)}"
            f" --classPath {shlex.quote(classpath)}"
            f" --reportDir {shlex.quote(report_dir)}"
            f" --targetClass {shlex.quote(target_class)}"
            f" --targetMethods {shlex.quote(target_methods)}"
            f" --sourceDir {shlex.quote(src_dir)}"
            f" --mutators {shlex.quote(mutators)}"
        )

    def _pit_target_class(self, class_fqn: str) -> str:
        return _top_level_class_fqn(class_fqn) + "*"

    def _effective_mutators(self) -> str:
        requested = str(self.config.mutators or "").strip()
        if not requested or requested.upper() == "ALL":
            return "ALL"
        return requested

    def _report_dir(self, container_path: str, class_fqn: str) -> str:
        return f"{container_path}/target/pit-reports-{self._safe_name(class_fqn)}"

    def _read_entries(self, container_path: str, class_fqn: str) -> list[PITClassicEntry]:
        cache_key = (container_path, class_fqn)
        cached = self._entry_cache.get(cache_key)
        if cached is not None:
            return cached

        report_dir = self._report_dir(container_path, class_fqn)
        raw, _, rc = self.d4j.exec(f"cat {report_dir}/classic-mutants.json 2>/dev/null")
        if rc != 0 or not raw.strip():
            self._entry_cache[cache_key] = []
            return []

        entries = parse_classic_entries(raw)
        self._entry_cache[cache_key] = entries
        return entries

    def _safe_name(self, text: str) -> str:
        return "".join(ch if ch.isalnum() or ch in "_.-" else "_" for ch in text)

    def _custom_pit_classpath_prefix(self) -> str:
        base = self._CUSTOM_PIT_CONTAINER_DIR
        return (
            f"{base}/pitest-entry.jar:"
            f"{base}/pitest.jar:"
        )

    def _ensure_custom_pitest_available(self) -> None:
        container = self.d4j.container
        if container in self._CUSTOM_PIT_READY:
            return

        with self._CUSTOM_PIT_LOCK:
            if container in self._CUSTOM_PIT_READY:
                return

            out, _, rc = self.d4j.exec(
                f'test -f {self._CUSTOM_PIT_READY_FILE} && cat {self._CUSTOM_PIT_READY_FILE}',
                timeout=15,
            )
            if rc == 0 and out.strip() == self._CUSTOM_PIT_VERSION:
                self._CUSTOM_PIT_READY.add(container)
                return

            root = Path(__file__).resolve().parents[4]
            pitest_src = root / "pitest"
            if not pitest_src.exists():
                raise RuntimeError(f"Custom pitest sources not found: {pitest_src}")

            self.d4j.exec("rm -rf /tmp/custom-pitest-src /opt/custom-pitest && mkdir -p /tmp /opt/custom-pitest", timeout=30)
            copy = subprocess.run(
                ["podman", "cp", str(pitest_src), f"{container}:/tmp/custom-pitest-src"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if copy.returncode != 0:
                raise RuntimeError(f"podman cp pitest sources failed:\n{copy.stderr.strip()}")

            build_cmd = (
                "cd /tmp/custom-pitest-src && "
                "mvn -q -DskipTests -Dcheckstyle.skip=true -pl pitest,pitest-entry -am package && "
                "find pitest/target -maxdepth 1 -type f -name 'pitest-*.jar' ! -name '*-tests.jar' ! -name 'original-*' | sort | head -n 1 | xargs -I{} cp '{}' /opt/custom-pitest/pitest.jar && "
                "find pitest-entry/target -maxdepth 1 -type f -name 'pitest-entry-*.jar' ! -name '*-tests.jar' ! -name 'original-*' | sort | head -n 1 | xargs -I{} cp '{}' /opt/custom-pitest/pitest-entry.jar && "
                "test -f /opt/custom-pitest/pitest.jar && test -f /opt/custom-pitest/pitest-entry.jar"
            )
            out, err, rc = self.d4j.exec(build_cmd, timeout=1800)
            if rc != 0:
                details = "\n".join(part for part in (out.strip(), err.strip()) if part).strip()
                raise RuntimeError(f"custom pitest build failed:\n{details}")

            _, err, rc = self.d4j.exec(f"printf '%s' {self._CUSTOM_PIT_VERSION} > {self._CUSTOM_PIT_READY_FILE}", timeout=15)
            if rc != 0:
                raise RuntimeError(f"custom pitest ready-marker write failed:\n{err.strip()}")

            self._CUSTOM_PIT_READY.add(container)
