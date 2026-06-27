#!/usr/bin/env python3
"""Calculate per-project metrics for the thesis table."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calculate_metrics import *

workspace = Path(__file__).parent / 'demo_collection_workspace'
bugs = load_bugs(workspace=workspace, requested_bug_keys=())

# Group bugs by project
projects = {}
for bug in bugs:
    p = bug.project
    if p not in projects:
        projects[p] = []
    projects[p].append(bug)

print(f'Projects: {len(projects)}')

mutant_types = ('classic', 'gemma4', 'qwen3.6')

# Print LaTeX table rows
print("\n% LaTeX table data:")
print("% Project & PIT Gen & PIT CMR & PIT MS & PIT CR & G4 Gen & G4 CMR & G4 MS & G4 CR & Q3 Gen & Q3 CMR & Q3 MS & Q3 CR")

for proj in sorted(projects.keys()):
    proj_bugs = tuple(projects[proj])
    parts = [proj]
    for mt in mutant_types:
        m = calculate_metrics(scope=proj, mutant_type=mt, bugs=proj_bugs)
        gen = str(m.generated)
        cmr = f"{m.cmr*100:.0f}\\%" if m.cmr is not None else "-"
        ms = f"{m.mutation_score*100:.0f}\\%" if m.mutation_score is not None else "-"
        cr = f"{m.cr*100:.0f}\\%" if m.cr is not None else "-"
        parts.extend([gen, cmr, ms, cr])
    print(" & ".join(parts) + " \\\\")
