"""
defect4j — collection-phase interfaces for Defects4J via Podman.

Typical usage:

    # PIT pipeline (fully automatic):
    from defect4j import Defects4J
    from defect4j.generators import PITPipeline, PITConfig
    bank = PITPipeline(Defects4J(), "demo_collection_workspace").run("Lang", 1)

    # LLM pipeline (local Ollama-compatible model):
    from defect4j.generators import LLMPipeline, LLMConfig
    config   = LLMConfig(model="qwen2.5-coder:14b")
    pipeline = LLMPipeline(d4j, "demo_collection_workspace", config)
    bank = pipeline.run("Lang", 1)

    # Data collection (run mutants against tests):
    from defect4j import Storage, DataCollector
    collector = DataCollector(d4j, Storage("demo_collection_workspace"))
    collector.collect_bug("Lang", 1, bank)
"""

from .container import Defects4J, ContainerCheckout, ParallelCheckoutPool
from .mutant    import Mutant, MutantBank
from .storage   import Storage
from .collector import DataCollector
from .generators import (
    BaseGenerator,
    GeneratorJob,
    PITConfig,
    LLMConfig,
    SourceFinder,
    LLMGenerator,
    LLMPipeline,
    PITGenerator,
    PITPipeline,
)

__all__ = [
    # Core pipeline
    "Defects4J",
    "ContainerCheckout",
    "ParallelCheckoutPool",
    "Mutant",
    "MutantBank",
    "Storage",
    "DataCollector",
    # Generators / configs / pipelines
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
