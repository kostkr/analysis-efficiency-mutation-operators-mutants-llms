"""
defect4j — collection-phase interfaces for Defects4J via Podman.

Typical usage:
    from defect4j import Defects4J, MutantBank, Storage, DataCollector

    d4j       = Defects4J(container="defects4j-container", workspace="/workspace")
    storage   = Storage("workspace")
    collector = DataCollector(d4j, storage)

    bank = MutantBank("workspace/result/LANG_1/mutans/gpt-5-mini.json").load()
    collector.collect_bug("LANG", 1, bank)
"""

from .container import Defects4J
from .mutant    import Mutant, MutantBank
from .storage   import Storage
from .collector import DataCollector

__all__ = [
    "Defects4J",
    "Mutant",
    "MutantBank",
    "Storage",
    "DataCollector",
]


