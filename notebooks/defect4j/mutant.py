"""
mutant.py — Unified mutant JSON format.

The mutant JSON file itself does NOT store the model/source.  That information
is carried by the filename, for example:

    LANG_1/mutants/gpt-5-mini.json
    LANG_1/mutants/classic.json

Schema (JSON)
-------------
{
  "id":         4,                   // unique numeric id inside THIS file
  "filepath":   "src/.../Foo.java",  // relative to project root
  "line":       42,                  // 1-based
  "precode":    "if (x == null)",
  "aftercode":  "if (x != null)",
  "rule":       "Negate null check",
  "gen_time_s": 1.23,
  "dublicate":  false
}
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Mutant:
    """
    Single-line source mutation — unified format for LLM and PIT.

    Attributes
    ----------
    id          : unique integer identifier within one mutant JSON file
    filepath    : path relative to project root
    precode     : original text on that line (stripped)
    aftercode   : replacement text (stripped)
    rule        : human-readable mutation operator description
    gen_time_s  : seconds spent generating this mutant
    dublicate   : True when this mutant is equivalent to the original code or
                  to another mutant after normalization
    pit_mutator : raw PIT mutator FQN (optional, classic PIT only)
    pit_description : raw PIT description (optional)
    pit_status  : KILLED / SURVIVED / NO_COVERAGE / ... (optional)
    pit_detected: whether PIT marked it as detected (optional)
    pit_tests_run : number of tests PIT ran for this mutation (optional)
    pit_killing_test : killing test name if any (optional)
    pit_index   : first PIT instruction index (optional)
    pit_indexes : all PIT instruction indexes (optional)
    pit_blocks  : PIT basic blocks (optional)
    pit_method  : mutated method name (optional)
    pit_method_description : bytecode method descriptor (optional)
    """

    id:         int
    filepath:   str
    line:       int
    precode:    str
    aftercode:  str
    rule:       str   = ""
    gen_time_s: float = 0.0
    dublicate: bool = False
    pit_mutator: str = ""
    pit_description: str = ""
    pit_status: str = ""
    pit_detected: bool = False
    pit_tests_run: int = 0
    pit_killing_test: str = ""
    pit_index: int = -1
    pit_indexes: list[int] = field(default_factory=list)
    pit_blocks: list[int] = field(default_factory=list)
    pit_method: str = ""
    pit_method_description: str = ""

    # ------------------------------------------------------------------ #
    #  Identity / deduplication                                            #
    # ------------------------------------------------------------------ #
    def signature(self) -> tuple[str, int, str]:
        """
        Normalized mutant identity tuple for duplicate detection.

        Two mutants share the same duplicate group when they produce the same
        normalized replacement for the same file/line.
        """
        return (self.filepath, self.line, normalize_code_fragment(self.aftercode))

    def original_signature(self) -> tuple[str, int, str]:
        """Normalized identity of the original source at this mutant location."""
        return (self.filepath, self.line, normalize_code_fragment(self.precode))

    # ------------------------------------------------------------------ #
    #  Apply / revert (in-place on the host filesystem)                   #
    # ------------------------------------------------------------------ #
    def apply(self, project_root: Path) -> tuple[bool, str | None, str]:
        """
        Apply the mutation to the source file in *project_root*.

        Saves original file content and returns (success, original_content, error).
        On failure returns (False, None, <diagnostic>) and leaves the file untouched.

        Usage pattern (always call restore in finally):
            ok, backup, error = mutant.apply(root)
            if ok:
                try:
                    ... compile & test ...
                finally:
                    mutant.restore(root, backup)
        """
        target = project_root / self.filepath
        if not target.exists():
            return False, None, f"apply_failed: file not found: {self.filepath}"

        original = target.read_text(encoding="utf-8")
        lines    = original.splitlines(keepends=True)
        idx      = self.line - 1

        if idx < 0:
            return False, None, f"apply_failed: invalid line number: {self.line}"
        if idx >= len(lines):
            return False, None, (
                f"apply_failed: line {self.line} out of range for {self.filepath} "
                f"(file has {len(lines)} lines)"
            )

        expected = self.precode.strip()
        actual_line = lines[idx].rstrip("\r\n")
        if expected not in actual_line:
            return False, None, (
                f"apply_failed: precode mismatch at {self.filepath}:{self.line} "
                f"(expected substring={expected!r}, actual={actual_line!r})"
            )

        lines[idx] = lines[idx].replace(
            expected, self.aftercode.strip(), 1
        )
        target.write_text("".join(lines), encoding="utf-8")
        return True, original, ""

    def restore(self, project_root: Path, original_content: str) -> None:
        """
        Restore the source file to *original_content* (obtained from apply()).

        Always call this after apply(), even if compile/test failed,
        so the checkout stays clean for the next mutant.
        """
        target = project_root / self.filepath
        target.write_text(original_content, encoding="utf-8")

    # ------------------------------------------------------------------ #
    #  Serialisation                                                       #
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filepath": self.filepath,
            "line": self.line,
            "precode": self.precode,
            "aftercode": self.aftercode,
            "rule": self.rule,
            "gen_time_s": self.gen_time_s,
            "dublicate": self.dublicate,
         }

    def __repr__(self) -> str:
        return f"Mutant({self.id!r}, {self.filepath}:{self.line})"


# ------------------------------------------------------------------ #
#  MutantBank                                                          #
# ------------------------------------------------------------------ #
class MutantBank:
    """
    Load, save and iterate a collection of :class:`Mutant` objects.

    File format: JSON array where every element matches the Mutant schema.

    Examples
    --------
    # Load GPT mutants
    bank = MutantBank("LANG_1/mutants/gpt-5-mini.json").load()

    # Build from model output and save
    bank = MutantBank.from_dicts(llm_output, path="LANG_1/mutants/gpt-5-mini.json")
    bank.save()

    # Load classic mutants from a different file
    classic_bank = MutantBank("LANG_1/mutants/classic.json").load()
    """

    def __init__(self, path: Path | str):
        self.path    = Path(path)
        self.mutants: list[Mutant] = []

    # ------------------------------------------------------------------ #
    #  I/O                                                                 #
    # ------------------------------------------------------------------ #
    def load(self) -> "MutantBank":
        with self.path.open(encoding="utf-8") as f:
            raw = json.load(f)
        self.mutants = [Mutant(**m) for m in raw]
        self.mark_duplicates()
        print(f"Loaded {len(self.mutants)} mutants from {self.path}")
        return self

    def save(self, path: Path | str | None = None) -> "MutantBank":
        dest: Path = Path(path) if path is not None else self.path
        dest.parent.mkdir(parents=True, exist_ok=True)
        self.mark_duplicates()
        payload = json.dumps(
            [m.to_dict() for m in self.mutants],
            indent=2,
            ensure_ascii=False,
        )
        _atomic_write_text(Path(dest), payload)
        print(f"Saved {len(self.mutants)} mutants → {dest}")
        return self

    @classmethod
    def from_dicts(
        cls,
        records: list[dict],
        path:    Path | str = Path("mutants.json"),
    ) -> "MutantBank":
        """
        Build a MutantBank from raw dicts.

        Parameters
        ----------
        records : list of dicts — each must have: id, filepath, line,
                  precode, aftercode. Optional: rule, gen_time_s.
        path    : file to save/load later
        """
        bank = cls(path)
        bank.mutants = [
            Mutant(
                id         = int(r["id"]),
                filepath   = r["filepath"],
                line       = int(r["line"]),
                precode    = r["precode"],
                aftercode  = r["aftercode"],
                rule       = r.get("rule", ""),
                gen_time_s = float(r.get("gen_time_s", 0.0)),
                dublicate = bool(r.get("dublicate", False)),
                pit_mutator = r.get("pit_mutator", ""),
                pit_description = r.get("pit_description", ""),
                pit_status = r.get("pit_status", ""),
                pit_detected = bool(r.get("pit_detected", False)),
                pit_tests_run = int(r.get("pit_tests_run", 0)),
                pit_killing_test = r.get("pit_killing_test", ""),
                pit_index = int(r.get("pit_index", -1)),
                pit_indexes = list(r.get("pit_indexes", [])),
                pit_blocks = list(r.get("pit_blocks", [])),
                pit_method = r.get("pit_method", ""),
                pit_method_description = r.get("pit_method_description", ""),
            )
            for r in records
        ]
        return bank

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #
    def __len__(self)  -> int: return len(self.mutants)
    def __iter__(self):        return iter(self.mutants)

    def mark_duplicates(self) -> "MutantBank":
        mark_duplicate_mutants(self.mutants)
        return self

    def non_duplicates(self) -> list[Mutant]:
        self.mark_duplicates()
        return [m for m in self.mutants if not m.dublicate]

    def duplicate_count(self) -> int:
        self.mark_duplicates()
        return sum(1 for m in self.mutants if m.dublicate)

    def __repr__(self) -> str:
        return f"MutantBank({self.path.name!r}, {len(self.mutants)} mutants)"

    # ------------------------------------------------------------------ #
    #  Example schema                                                      #
    # ------------------------------------------------------------------ #
    @staticmethod
    def write_example(dest: Path | str = Path("LANG_1/mutants/gpt-5-mini.json")) -> None:
        """Write an example JSON file illustrating the required schema."""
        sample = [
            {
                "id":         1,
                "filepath":   "src/main/java/org/example/Foo.java",
                "line":       42,
                "precode":    "if (x == null)",
                "aftercode":  "if (x != null)",
                "rule":       "Negate null check",
                "gen_time_s": 1.23,
                "dublicate":  False,
            },
            {
                "id":         2,
                "filepath":   "src/main/java/org/example/Foo.java",
                "line":       55,
                "precode":    "return value + 1;",
                "aftercode":  "return value - 1;",
                "rule":       "Math (+ → -)",
                "gen_time_s": 0.02,
                "dublicate":  False,
            },
        ]
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_text(dest, json.dumps(sample, indent=2, ensure_ascii=False))
        print(f"Example written → {dest}")


def _atomic_write_text(path: Path, payload: str) -> None:
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(path)


def normalize_code_fragment(text: str) -> str:
    """Cheap normalization used for duplicate detection."""
    return re.sub(r"\s+", " ", str(text or "").replace("\r\n", "\n").replace("\r", "\n")).strip()


def mark_duplicate_mutants(mutants: list[Mutant]) -> list[Mutant]:
    """
    Mark duplicates in O(n) time without removing them.

    Duplicate rules:
    - mutant normalized replacement == normalized original code on the same file/line
    - if multiple mutants share the same normalized replacement on the same file/line,
      keep the first representative non-duplicate and mark only later ones duplicate
    """
    seen_unique_signatures: set[tuple[str, int, str]] = set()

    for mutant in mutants:
        original_sig = mutant.original_signature()
        mutant_sig = mutant.signature()
        if mutant_sig == original_sig:
            mutant.dublicate = True
            continue
        if mutant_sig in seen_unique_signatures:
            mutant.dublicate = True
            continue
        mutant.dublicate = False
        seen_unique_signatures.add(mutant_sig)

    return mutants



