"""
generators — Mutant generation sub-package for the Defects4J pipeline.

Two generators + two pipelines:

PITPipeline / PITGenerator
    Full autonomous pipeline: checkout → find methods → run direct custom PIT generator
    → read direct PIT JSON output → save ``mutants/classic.json``.

LLMPipeline / LLMGenerator
    End-to-end local-LLM pipeline: checkout → find changed methods → call the
    configured Ollama-compatible model → validate single-line mutants → save
    ``mutants/{model}.json``.

Quick start
-----------
    from defect4j import Defects4J
    from defect4j.generators import PITPipeline, LLMPipeline
    from defect4j.generators import PITConfig, LLMConfig

    d4j = Defects4J()

    # PIT — fully automatic
    bank = PITPipeline(d4j, "demo_collection_workspace").run("Lang", 1)

    # LLM — local Ollama-compatible model
    config   = LLMConfig(model="qwen2.5-coder:14b")
    pipeline = LLMPipeline(d4j, "demo_collection_workspace", config)
    bank     = pipeline.run("Lang", 1)
"""

from .base          import BaseGenerator, GeneratorJob, PITConfig, LLMConfig
from .source_finder import SourceFinder
from .llm           import LLMGenerator, LLMPipeline
from .pit           import PITGenerator, PITPipeline

__all__ = [
    "BaseGenerator",
    "GeneratorJob",
    "PITConfig",
    "LLMConfig",
    "SourceFinder",
    "LLMGenerator",
    "LLMPipeline",
    "PITGenerator",
    "PITPipeline",
]
