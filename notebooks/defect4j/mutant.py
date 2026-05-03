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
  "gen_time_s": 1.23
}
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Mutant:
    """
    Single-line source mutation — unified format for LLM and PIT.

    Attributes
    ----------
    id          : unique integer identifier within one mutant JSON file
    filepath    : path relative to project root
    line        : 1-based line number to patch
    precode     : original text on that line (stripped)
    aftercode   : replacement text (stripped)
    rule        : human-readable mutation operator description
    gen_time_s  : seconds spent generating this mutant
    """

    id:         int
    filepath:   str
    line:       int
    precode:    str
    aftercode:  str
    rule:       str   = ""
    gen_time_s: float = 0.0

    # ------------------------------------------------------------------ #
    #  Identity / deduplication                                            #
    # ------------------------------------------------------------------ #
    def signature(self) -> tuple:
        """
        Syntactic identity tuple for deduplication.

        Two mutants are syntactic duplicates if they have the same
        (filepath, line, aftercode.strip()) — they introduce the identical
        change regardless of id or generator file.
        """
        return (self.filepath, self.line, self.aftercode.strip())

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
        return asdict(self)

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
        with open(self.path, encoding="utf-8") as f:
            raw = json.load(f)
        self.mutants = [Mutant(**m) for m in raw]
        print(f"Loaded {len(self.mutants)} mutants from {self.path}")
        return self

    def save(self, path: Path | str | None = None) -> "MutantBank":
        dest = Path(path) if path else self.path
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(
                [m.to_dict() for m in self.mutants],
                f, indent=2, ensure_ascii=False,
            )
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
            )
            for r in records
        ]
        return bank

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #
    def __len__(self)  -> int: return len(self.mutants)
    def __iter__(self):        return iter(self.mutants)
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
            },
            {
                "id":         2,
                "filepath":   "src/main/java/org/example/Foo.java",
                "line":       55,
                "precode":    "return value + 1;",
                "aftercode":  "return value - 1;",
                "rule":       "Math (+ → -)",
                "gen_time_s": 0.02,
            },
        ]
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(sample, indent=2, ensure_ascii=False))
        print(f"Example written → {dest}")



