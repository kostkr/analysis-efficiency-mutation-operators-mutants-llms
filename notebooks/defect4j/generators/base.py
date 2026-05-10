"""
base.py — Shared dataclasses and abstract interface for mutant generators.

Design goal: GeneratorJob is a fully self-contained unit of work so that
future parallel workers (multiple containers / processes) can pick up jobs
from a queue without any shared state.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..mutant import Mutant


@dataclass
class GeneratorJob:
    """All data needed to generate mutants for a single Java method.

    Designed for parallelisation: fully self-contained, no shared mutable state.

    Attributes
    ----------
    project          : Defects4J project name, e.g. "Lang"
    bug_id           : Bug number, e.g. 3
    container_path   : Absolute path inside the container (fixed version checkout)
    host_path        : Corresponding path on the host (bind-mounted)
    filepath         : Source file path relative to project root
                       e.g. "src/main/java/org/apache/commons/lang3/math/NumberUtils.java"
    class_fqn        : Fully-qualified Java class name
    method_name      : Java method name
    method_source    : Full source text of the method
    method_start     : 1-based line number where the method starts in the file
    method_end       : 1-based line number where the method ends in the file
    changed_lines    : Absolute 1-based line numbers that changed (bug diff, inside this method)
    """

    project:        str
    bug_id:         int
    container_path: str
    host_path:      str
    filepath:       str
    class_fqn:      str
    method_name:    str
    method_source:  str
    method_start:   int
    method_end:     int
    changed_lines:  list[int] = field(default_factory=list)


# ── Configs ───────────────────────────────────────────────────────────────────

@dataclass
class PITConfig:
    """Configuration for the direct custom PIT classic generator.

    Attributes
    ----------
    timeout_s : Timeout in seconds for one direct PIT class-generation run.
    mutators  : PIT mutator group or comma-separated list (for example ``"ALL"``).
    """

    timeout_s: int = 300
    mutators: str = "DEFAULTS"


@dataclass
class LLMConfig:
    """Configuration for the local LLM mutation generator.

    The default setup targets a local Ollama server and follows the paper's
    mutation-generation prompt strategy: real-bug few-shot examples, one-shot
    requests per fixed-version bug-diff method, and one requested mutant per
    eligible line of that method.
    """

    model: str = "qwen2.5-coder:14b"
    output_name: str = ""
    endpoint: str = "http://127.0.0.1:11434/api/generate"
    timeout_s: int = 1800
    temperature: float | None = None
    keep_alive: str = "30m"
    code_element: str = "all single-line Java statements and expressions"


# ── Abstract generator ────────────────────────────────────────────────────────

class BaseGenerator(ABC):
    """Abstract base class for all mutant generators."""

    @abstractmethod
    def generate(self, job: GeneratorJob) -> list["Mutant"]:
        """Generate a list of :class:`~defect4j.mutant.Mutant` objects for *job*.

        Implementations must:
        - Return an empty list rather than raising on soft failures
        - Deduplicate output: no two returned mutants share the same
          ``(filepath, line, aftercode.strip())``
        """
        ...
