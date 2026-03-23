# LLM-Mutants — Master's Thesis Repository

Project: "LLM-Mutants: Analysis of the effectiveness of generating mutation operators (mutants) using large language models"

This repository contains the working artifacts, notes, code and examples for a master's thesis investigating whether large language models (LLMs) can generate useful mutation operators and mutants for Java projects and how those compare to classical mutation tools.

Main contents
- `plan_wykonania_pracy_magisterskiej.md` — project plan (Polish) with experimental outline and timeline.
- `diploma/diploma.md` — short project description and milestones.
- `THESIS_STRUCTURE.md` — proposed chapter structure and contents (English).
- `docs/` — chapter drafts and stubs for the thesis text.
- `notebooks/` — analysis and evaluation Jupyter notebooks (Python).
- `src_examples/java/` — small Java examples and code snippets used as mutation targets.
- `requirements.txt` — Python dependencies used for analysis and clustering.

Quick start
1. Create a Python virtual environment (recommended):

   python3 -m venv .venv
   source .venv/bin/activate

2. Install Python dependencies:

   pip install -r requirements.txt

3. Open the initial analysis notebook:

   jupyter lab notebooks/initial_analysis.ipynb

4. Use `src_examples/java/LLMMutantExample.java` as a simple target for manual mutation experiments and for developing prompts.

Repository guidelines
- Keep all prompts and model configuration in `configs/` (create when ready).
- Store generated mutants and experimental outputs under `data/` (do not commit large files; use .gitignore rules or external storage).

Reproducibility
- Record LLM model versions, prompts, seeds and temperatures in `configs/` and in experiment logs.
- Prefer using Docker or pinned environment for reproducing the Java build/test environment.

Contact
- Thesis author: (add your name and contact information here)

---
This repo was generated to bootstrap the thesis workflow. See `THESIS_STRUCTURE.md` and `docs/` for chapter templates and next steps.

