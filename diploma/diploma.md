## Introduction – General Overview of the Work (6–8 pages)

Start with the broader context: Mutation testing is a powerful but limited technique because classical operators are mostly syntactic and often fail to simulate real-world programmer mistakes.
Introduce the rise of LLMs in software engineering (code generation, test generation, bug repair) and their potential to create more realistic mutations.

Explain the core idea of your work: Instead of using LLMs only to generate individual mutants, investigate whether LLMs can generate entire new mutation operators — reusable transformation rules that can produce families of mutants.

Highlight practical importance: Better operators -> stronger test suites -> higher software reliability and more effective quality assurance.
Briefly mention the three hypotheses and the expected contributions (novel operator generator, empirical comparison on realism and effectiveness, analysis of near-identical operators, open-source prototype).
End with a short roadmap of the thesis structure.

Visuals: One figure showing the evolution from classical mutation testing to LLM-based approaches.

## Description of Planned Research + Research Hypotheses (8–10 pages)

1. Research Problem and Gap
Summarize limitations of classical operators (low realism, many equivalent mutants) and current LLM-mutant studies

2. Research Objectives
Main goal: Systematically analyze the effectiveness of LLM-generated mutation operators.
Specific objectives: (a) generate novel operators, (b) measure closeness to real bugs, (c) compare effectiveness (including near-identical cases).

3. Research Hypotheses
State H1, H2, H3 exactly as you formulated them their higher fault detection suggests LLMs can produce more realistic mutations; you go one level higher to operators).

4. Planned Methodology Overview
High-level pipeline: Prompt engineering -> operator generation -> implementation as code transformers -> application on benchmarks → evaluation using metrics from the arXiv paper (plus novelty metrics).
Models: GPT-4o, GPT-5.0-mini, Qwen2.5-Coder-14B.
Datasets: Defects4J, BugsInPy, selected real-world Java projects.
Metrics preview: Novelty (clustering/AST diversity), realism (Ochiai, coupling rate), effectiveness (mutation score, fault detection), validity (compilability, equivalence).
5. Expected Contributions and Novelty
Focus on operator-level generation, explicit analysis of H3 (near-identical operators), and a reusable framework.

Visuals: High-level diagram of the full experimental pipeline (inspired by Poręba’s architecture figure).

## Theoretical Introduction (15–18 pages)
   3.1 Mutation Testing Fundamentals

Process, classical operators (detailed list with pseudocode examples like ABS, AOR, ROR, etc.), tools (PIT, Major, Stryker), strengths and well-known limitations.

3.2 Large Language Models in Software Engineering (from Poręba)

Brief history and transformer architecture.
Applications in code generation, test generation, and mutation (lead into the arXiv study).

3.3 Related Work – Focus on arXiv 2406.09843v3

Detailed summary: methodology (prompts with few-shot real bugs), datasets, metrics (fault detection, Ochiai, coupling, compilability, etc.), key results (LLM mutants detect more real faults but have validity issues).
Comparison table of classical vs LLM approaches.
Identify gaps your work fills (operator generation, deeper H3 analysis, multi-language).

3.4 Metrics for Evaluating Mutation Operators

Realism: Ochiai coefficient, fault coupling rate (heavily from arXiv).
Effectiveness: Mutation score, number of killed mutants, test suite strengthening.
Novelty: AST node diversity, semantic distance from classical operators.
Validity: Compilability rate, duplication, equivalence rate.

Visuals: Tables of classical operators (Pospieszny style), architecture diagram of Transformer (Poręba style), summary table of the arXiv paper’s results.

## Research (25–30 pages)
   4.1 Założenia eksperymentu (Experimental Assumptions / Setup) – 8–10 pages

Models, prompt strategies (base + role-playing + few-shot inspired by arXiv), number of generations.
Datasets and selection criteria.
Implementation of the LLM-Mutant Operator Generator (Python framework).
Full list of metrics and how they are computed.
Reproducibility measures (seeds, temperature, cost tracking).

4.2 Wyniki (Results) – 8–10 pages

Quantitative results: Number of novel operators generated per model, mutation scores, realism metrics (tables and charts).
Qualitative examples: 6–10 concrete new operators with code before/after and explanation of novelty/realism.
Direct comparison to classical operators and to results from the arXiv study.

4.3 Opracowanie wyników (Analysis / Interpretation of Results) – 6–8 pages

Statistical significance.
Discussion per hypothesis.
Special focus on H3: cases where LLM operator is almost identical to a classical one — which performs better and why (contextual vs syntactic).
Trade-offs observed (realism vs validity, similar to arXiv findings).

4.4 Wnioski z jednego eksperymentu (Conclusions from the Experiment) – 3–4 pages

Confirmation/rejection of each hypothesis with evidence.
Limitations of this experiment (scope, model versions used).


## Summary & Final Conclusions (6–8 pages)

Restate the three hypotheses and final verdicts.
Overall contributions and how the work advances the arXiv study.
Practical recommendations (when to use LLM-generated operators).
Limitations of the entire thesis.
Directions for future work (automatic operator implementation, fine-tuning, integration into tools like PIT/Stryker, larger multi-language study).
Closing reflection on the future role of LLMs in mutation testing and software quality.
