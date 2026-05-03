"""
generators — Mutant generation sub-package for the Defects4J pipeline.

Two generators + two pipelines:

PITPipeline / PITGenerator
    Full autonomous pipeline: checkout → find methods → run pitest-maven
    → parse mutations.xml → save ``mutants/classic.json``.
    No container image changes required (Maven downloads pitest from Central).

LLMPipeline / LLMGenerator
    Client-agnostic pipeline.  Phase 1 prepares prompts (PreparedPrompt).
    Phase 2 (user's LLM client) sends them.  Phase 3 processes responses
    and saves ``mutants/{model}.json``.

Quick start
-----------
    from defect4j import Defects4J
    from defect4j.generators import PITPipeline, LLMPipeline
    from defect4j.generators import PITConfig, LLMConfig

    d4j = Defects4J()

    # PIT — fully automatic
    bank = PITPipeline(d4j, "demo_collection_workspace").run("Lang", 1)

    # LLM — bring-your-own-client
    config   = LLMConfig(model="gpt-4o-mini", n_mutants=10)
    pipeline = LLMPipeline("demo_collection_workspace", config)
    prompts  = pipeline.prepare_jobs("Lang", 1, d4j)
    mutants  = []
    for p in prompts:
        response = my_client.chat(p.system, p.user)
        mutants.extend(pipeline.process_response(p, response))
    pipeline.save("Lang", 1, mutants)
"""

from .base          import BaseGenerator, GeneratorJob, PITConfig, LLMConfig
from .source_finder import SourceFinder
from .llm           import LLMGenerator, LLMPipeline, PreparedPrompt
from .pit           import PITGenerator, PITPipeline

__all__ = [
    "BaseGenerator",
    "GeneratorJob",
    "PITConfig",
    "LLMConfig",
    "SourceFinder",
    "LLMGenerator",
    "LLMPipeline",
    "PreparedPrompt",
    "PITGenerator",
    "PITPipeline",
]
