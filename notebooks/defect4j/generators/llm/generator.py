"""llm/generator.py — local LLM mutant generator for Ollama-style APIs."""

from __future__ import annotations

import json
import re
import time
from typing import TYPE_CHECKING, Callable
from urllib import error, request

from ..base import BaseGenerator, GeneratorJob, LLMConfig
from .prompt import build_prompt
from .parser import parse_response

if TYPE_CHECKING:
    from ...mutant import Mutant


class LLMGenerator(BaseGenerator):
    """Generate mutants by querying a local Ollama-compatible chat endpoint."""

    STREAM_LOG_INTERVAL_S = 5.0

    def __init__(self, config: LLMConfig, logger: Callable[[str], None] | None = None) -> None:
        self.config = config
        self._logger = logger

    def generate(self, job: GeneratorJob) -> list["Mutant"]:
        requested = self.requested_mutant_count(job)
        if requested <= 0:
            return []
        return self.generate_batch(job, requested=requested)

    def generate_batch(self, job: GeneratorJob, requested: int | None = None) -> list["Mutant"]:
        requested = self.requested_mutant_count(job) if requested is None else int(requested)
        if requested <= 0:
            return []
        system, user = build_prompt(
            method_source=job.method_source,
            target_mutants=requested,
            code_element=self.config.code_element,
            method_start_line=job.method_start,
        )

        self._log(
            "  llm request   : "
            f"method={job.method_name} target={requested} prompt_chars={len(user)} "
            f"prompt_lines={len(user.splitlines())} stream=true think=false"
        )

        t0 = time.perf_counter()
        raw_text = self._chat(system=system, user=user)

        gen_time = round(time.perf_counter() - t0, 2)
        raw_list = parse_response(raw_text)
        self._log(
            f"  llm parse     : method={job.method_name} response_chars={len(raw_text)} raw_records={len(raw_list)} runtime={gen_time}s"
        )

        mutants = self._validated_mutants(job, raw_list)
        self._log(
            f"  llm validate  : method={job.method_name} valid_records={len(mutants)}"
        )
        if mutants:
            per_mutant = round(gen_time / len(mutants), 2)
            for mutant in mutants:
                mutant.gen_time_s = per_mutant

        return mutants

    def model_stem(self) -> str:
        return model_stem(self.config.output_name or self.config.model)

    def requested_mutant_count(self, job: GeneratorJob) -> int:
        changed = set(job.changed_lines or [])
        candidate_lines = sum(
            1 for offset, line in enumerate(job.method_source.splitlines(), start=job.method_start)
            if (not changed or offset in changed) and self._is_mutation_candidate_line(line)
        )
        return max((candidate_lines + 1) // 3, 1) if candidate_lines else 0

    @staticmethod
    def _is_mutation_candidate_line(line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False
        if stripped in {"{", "}", "};"}:
            return False
        if stripped.startswith(("//", "/*", "*", "@")):
            return False
        return True

    def _validated_mutants(self, job: GeneratorJob, raw_list: list[dict]) -> list["Mutant"]:
        from ...mutant import Mutant

        source_lines = job.method_source.splitlines()
        mutants: list[Mutant] = []
        for item in raw_list:
            line = int(item["line"])
            precode = str(item["precode"]).strip()
            aftercode = str(item["aftercode"]).strip()
            rule = str(item["rule"]).strip()
            if not precode or not aftercode or _same_code(precode, aftercode):
                continue
            if line < job.method_start or line > job.method_end:
                continue
            if precode not in source_lines[line - job.method_start]:
                continue
            mutants.append(Mutant(len(mutants) + 1, job.filepath, line, precode, aftercode, rule))
        return mutants

    def _chat(self, system: str, user: str) -> str:
        prompt = user.strip() if not system.strip() else f"{system}\n\n{user}".strip()
        payload: dict[str, object] = {
            "model": self.config.model,
            "prompt": prompt,
            "format": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "line": {"type": "integer"},
                        "precode": {"type": "string"},
                        "aftercode": {"type": "string"},
                        "rule": {"type": "string"},
                    },
                    "required": ["line", "precode", "aftercode", "rule"],
                    "additionalProperties": False,
                },
            },
            "stream": True,
            "think": False,
            "keep_alive": self.config.keep_alive,
        }
        if self.config.temperature is not None:
            payload["options"] = {"temperature": float(self.config.temperature)}

        req = request.Request(
            self.config.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            self._log(
                f"  llm connect   : endpoint={self.config.endpoint} timeout={self.config.timeout_s}s keep_alive={self.config.keep_alive} structured_output=array"
            )
            with request.urlopen(req, timeout=self.config.timeout_s) as response:
                chunks: list[str] = []
                stream_events = 0
                total_chars = 0
                final_meta: dict[str, object] = {}
                last_progress_log = time.perf_counter()
                progress_logged = False
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        raise RuntimeError(f"invalid streamed JSON chunk: {line[:400]}")
                    stream_events += 1
                    piece = str(item.get("response", "") or "")
                    if piece:
                        chunks.append(piece)
                        total_chars += len(piece)
                        now = time.perf_counter()
                        if (not progress_logged) or (now - last_progress_log >= self.STREAM_LOG_INTERVAL_S):
                            joined = "".join(chunks)
                            estimated_records = joined.count('"aftercode"')
                            self._log(
                                "  llm progress  : "
                                f"events={stream_events} chars={total_chars} est_records={estimated_records}"
                            )
                            last_progress_log = now
                            progress_logged = True
                    if bool(item.get("done", False)):
                        final_meta = item
                self._log(
                    "  llm stream    : "
                    f"events={stream_events} chars={total_chars} done={bool(final_meta.get('done', False))}"
                )
                raw = json.dumps({"response": "".join(chunks)})
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"HTTP {exc.code}: {detail[:400]}") from exc
        except error.URLError as exc:
            raise RuntimeError(str(exc.reason)) from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"invalid JSON response: {raw[:400]}") from exc

        if isinstance(data, dict):
            if "response" in data:
                return str(data.get("response", "") or "")
        raise RuntimeError(f"unexpected response payload: {raw[:400]}")

    def _log(self, msg: str) -> None:
        if self._logger is not None:
            self._logger(msg)


def model_stem(model: str) -> str:
    cleaned = []
    for char in str(model).strip():
        cleaned.append(char if char.isalnum() or char in {"-", "_", "."} else "_")
    stem = "".join(cleaned).strip("._")
    return stem or "llm"


def _same_code(left: str, right: str) -> bool:
    return re.sub(r"\s+", " ", left).strip() == re.sub(r"\s+", " ", right).strip()


