#!/usr/bin/env python3
"""Calculate per-project metrics: rows=projects, columns=metric x type."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calculate_metrics import *

workspace = Path(__file__).parent / 'demo_collection_workspace'
bugs = load_bugs(workspace=workspace, requested_bug_keys=())

projects = {}
for bug in bugs:
    projects.setdefault(bug.project, []).append(bug)

mutant_types = ('classic', 'gemma4', 'qwen3.6')

def fp(v):
    return f"{v*100:.1f}" if v is not None else "---"

def ft(v):
    return f"{v:.2f}" if v is not None else "---"

# Compute metrics per project per type
data = {}
for proj in sorted(projects.keys()):
    proj_bugs = tuple(projects[proj])
    data[proj] = {}
    for mt in mutant_types:
        data[proj][mt] = calculate_metrics(scope=proj, mutant_type=mt, bugs=proj_bugs)

# Table: rows = projects, for each metric show PIT | G4 | Q3
# Selected metrics: Gen, CMR, DMR, MS, CR, AOR, HOMR, LLM-NMR
print(r"\begin{landscape}")
print(r"\begin{table}[H]")
print(r"    \centering")
print(r"    \scriptsize")
# 1 + 3*8 = 25 columns is too many. Split into two tables or pick key metrics.
# Let's do: Gen, CMR, MS, CR, AOR, HOMR, LLM-NMR = 7 metrics * 3 types = 21 + 1 = 22 cols
# Still too many. Do two separate tables.

# Table A: Gen, CMR, DMR, MS
print(r"    \begin{tabular}{|l||r|r|r||r|r|r||r|r|r||r|r|r|}")
print(r"        \hline")
print(r"        & \multicolumn{3}{c||}{Mutanty} & \multicolumn{3}{c||}{CMR} & \multicolumn{3}{c||}{Mutation Score} & \multicolumn{3}{c|}{Coupling Rate} \\ \hline")
print(r"        Projekt & PIT & G4 & Q3 & PIT & G4 & Q3 & PIT & G4 & Q3 & PIT & G4 & Q3 \\ \hline")

for proj in sorted(projects.keys()):
    d = data[proj]
    p, g, q = d['classic'], d['gemma4'], d['qwen3.6']
    row = f"        {proj}"
    row += f" & {p.generated} & {g.generated} & {q.generated}"
    row += f" & {fp(p.cmr)} & {fp(g.cmr)} & {fp(q.cmr)}"
    row += f" & {fp(p.mutation_score)} & {fp(g.mutation_score)} & {fp(q.mutation_score)}"
    row += f" & {fp(p.cr)} & {fp(g.cr)} & {fp(q.cr)}"
    row += r" \\ \hline"
    print(row)

print(r"    \end{tabular}")
print(r"    \caption{Metryki w podziale na projekty (część 1): liczba mutantów, kompilowalność, Mutation Score, Coupling Rate. Wartości CMR, MS i CR w procentach.}")
print(r"    \label{tab:per_project_1}")
print(r"\end{table}")
print()
print(r"\begin{table}[H]")
print(r"    \centering")
print(r"    \scriptsize")
print(r"    \begin{tabular}{|l||r|r|r||r|r|r||r|r|r||r|r|}")
print(r"        \hline")
print(r"        & \multicolumn{3}{c||}{AOR} & \multicolumn{3}{c||}{HOMR} & \multicolumn{3}{c||}{RBDR} & \multicolumn{2}{c|}{LLM-NMR} \\ \hline")
print(r"        Projekt & PIT & G4 & Q3 & PIT & G4 & Q3 & PIT & G4 & Q3 & G4 & Q3 \\ \hline")

for proj in sorted(projects.keys()):
    d = data[proj]
    p, g, q = d['classic'], d['gemma4'], d['qwen3.6']
    row = f"        {proj}"
    row += f" & {fp(p.aor)} & {fp(g.aor)} & {fp(q.aor)}"
    row += f" & {fp(p.high_ochiai_mutant_rate)} & {fp(g.high_ochiai_mutant_rate)} & {fp(q.high_ochiai_mutant_rate)}"
    row += f" & {fp(p.rbdr)} & {fp(g.rbdr)} & {fp(q.rbdr)}"
    row += f" & {fp(g.llm_nmr)} & {fp(q.llm_nmr)}"
    row += r" \\ \hline"
    print(row)

print(r"    \end{tabular}")
print(r"    \caption{Metryki w podziale na projekty (część 2): Average Ochiai Rate, High Ochiai Mutant Rate, Real Bug Detection Rate, LLM New Mutant Rate. Wartości w procentach.}")
print(r"    \label{tab:per_project_2}")
print(r"\end{table}")
print(r"\end{landscape}")
