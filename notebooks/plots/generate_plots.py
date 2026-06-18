#!/usr/bin/env python3
"""
Generate all charts for RQ1, RQ2, RQ3 sections of the thesis.
Saves PNG files to ../../images/ (relative to this script).

Usage:
    python notebooks/plots/generate_plots.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR  = Path(__file__).resolve().parent
IMAGES_DIR  = SCRIPT_DIR.parents[1] / "images"
IMAGES_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Raw data from calculate_metrics.py and analyze_new_mutants.py
# ---------------------------------------------------------------------------

MODELS = ["classic", "gemma4", "qwen3.6"]
COLORS = {"classic": "#6C757D", "gemma4": "#2563EB", "qwen3.6": "#DC2626"}
MODEL_LABELS = {"classic": "PIT", "gemma4": "gemma4", "qwen3.6": "qwen3.6"}

# ---- Aggregate metrics ----------------------------------------------------
AGG = {
    "classic": dict(
        mutants=76648, cmr=100.00, dmr=0.00,  emr=31.43, mut_score=68.57,
        llm_nmr=None,  rbdr=98.70, aor=22.66, cr=29.28,
        haor=2.14, homr=4.51, amgt=0.0467, cpum=22.4355,
    ),
    "gemma4": dict(
        mutants=40426, cmr=88.00, dmr=7.24,  emr=30.40, mut_score=69.60,
        llm_nmr=13.75, rbdr=97.98, aor=23.57, cr=36.10,
        haor=2.14, homr=6.94, amgt=1.2798, cpum=30.1492,
    ),
    "qwen3.6": dict(
        mutants=39410, cmr=88.15, dmr=10.11, emr=28.94, mut_score=71.06,
        llm_nmr=15.23, rbdr=98.34, aor=24.37, cr=37.35,
        haor=3.08, homr=7.45, amgt=2.4220, cpum=29.6842,
    ),
}

# ---- Coupling categorization -----------------------------------------------
COUPLING = {
    "classic": dict(strong=4.00, strong_extra=16.34, partial=2.38,
                    partial_extra=6.56, not_sub=39.28, not_detected=31.43),
    "gemma4":  dict(strong=6.09, strong_extra=18.15, partial=3.45,
                    partial_extra=8.40, not_sub=33.51, not_detected=30.40),
    "qwen3.6": dict(strong=6.45, strong_extra=19.19, partial=3.53,
                    partial_extra=8.19, not_sub=33.70, not_detected=28.94),
}

# ---- New mutants (from analyze_new_mutants.py) ----------------------------
NEW_TOTAL   = 8967
BY_MODEL    = {"gemma4": 4402, "qwen3.6": 4565}
BY_FAMILY   = {
    "design":        {"n": 3417, "pct": 38.1, "kill": 96.0},
    "grammar":       {"n": 1174, "pct": 13.1, "kill": 94.9},
    "object":        {"n": 365,  "pct":  4.1, "kill": 97.3},
    "integration":   {"n": 174,  "pct":  1.9, "kill": 98.3},
    "beyond_classic":{"n": 3837, "pct": 42.8, "kill": 96.1},
}
# Full taxonomy: 26 categories (classify_beyond_classic_full.py, 0 inne)
# Sorted by frequency descending. Counts verified against new_mutants.csv.
BEYOND_PATTERNS = {
    "null_substitution":          {"n": 658,  "pct": 17.1},
    "method_name_change":         {"n": 532,  "pct": 13.9},
    "bool_expr_negation":         {"n": 474,  "pct": 12.4},
    "argument_substitution":      {"n": 373,  "pct":  9.7},
    "wrapper_change":             {"n": 329,  "pct":  8.6},
    "assignment_value_change":    {"n": 306,  "pct":  8.0},
    "negation_removal":           {"n": 299,  "pct":  7.8},
    "enum_constant_swap":         {"n": 175,  "pct":  4.6},
    "subexpr_to_bool":            {"n": 105,  "pct":  2.7},
    "string_literal_change":      {"n": 97,   "pct":  2.5},
    "boolean_literal_assign":     {"n": 87,   "pct":  2.3},
    "argument_swap":              {"n": 60,   "pct":  1.6},
    "null_removal":               {"n": 60,   "pct":  1.6},
    "flow_control_change":        {"n": 57,   "pct":  1.5},
    "instanceof_change":          {"n": 40,   "pct":  1.0},
    "ternary_branch_swap":        {"n": 31,   "pct":  0.8},
    "exception_class_swap":       {"n": 28,   "pct":  0.7},
    "array_index_change":         {"n": 22,   "pct":  0.6},
    "comparison_semantics":       {"n": 21,   "pct":  0.5},
    "comment_out":                {"n": 19,   "pct":  0.5},
    "operand_swap":               {"n": 18,   "pct":  0.5},
    "impl_class_swap":            {"n": 16,   "pct":  0.4},
    "modifier_change":            {"n": 13,   "pct":  0.3},
    "self_assignment":            {"n": 8,    "pct":  0.2},
    "lhs_rhs_swap":               {"n": 6,    "pct":  0.2},
    "type_change":                {"n": 3,    "pct":  0.1},
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def save(fig: plt.Figure, name: str) -> None:
    path = IMAGES_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved → {path}")


def _style() -> None:
    plt.rcParams.update({
        "font.family":     "DejaVu Sans",
        "font.size":       11,
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "axes.grid":       True,
        "grid.alpha":      0.35,
        "grid.linestyle":  "--",
    })

# ---------------------------------------------------------------------------
# PIT family distribution of new LLM mutants
# ---------------------------------------------------------------------------

def plot_pit_family_distribution() -> None:
    families   = list(BY_FAMILY.keys())
    pcts       = [BY_FAMILY[f]["pct"] for f in families]
    fam_colors = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444"]
    labels     = [
        "Mutanty projektowe",
        "Mutanty na gramatyce",
        "Mutanty obiektowe",
        "Mutanty integracyjne",
        "Nowe wzorce",
    ]

    fig, (ax_bar, ax_pie) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(
        "Rozkład nowych mutantów LLM według rodzin operatorów PIT",
        fontsize=12, fontweight="bold"
    )

    # --- horizontal bar chart ---
    y_pos = np.arange(len(families))
    bars  = ax_bar.barh(y_pos, pcts, color=fam_colors, edgecolor="white")
    ax_bar.set_yticks(y_pos)
    ax_bar.set_yticklabels(labels, fontsize=10)
    ax_bar.set_xlabel("Odsetek nowych mutantów (%)", fontsize=10)
    ax_bar.invert_yaxis()

    for bar, pct, fam in zip(bars, pcts, families):
        n = BY_FAMILY[fam]["n"]
        ax_bar.text(
            bar.get_width() + 0.4, bar.get_y() + bar.get_height() / 2,
            f"{pct:.1f}%  (n={n:,})",
            va="center", ha="left", fontsize=9
        )
    ax_bar.set_xlim(0, 55)

    # --- pie chart ---
    wedge_props = dict(edgecolor="white", linewidth=1.5)
    ax_pie.pie(
        pcts,
        colors=fam_colors,
        autopct="%1.1f%%",
        startangle=140,
        wedgeprops=wedge_props,
        pctdistance=0.75,
        textprops={"fontsize": 9},
    )
    patches = [mpatches.Patch(color=c, label=l) for c, l in zip(fam_colors, labels)]
    ax_pie.legend(handles=patches, loc="lower center", bbox_to_anchor=(0.5, -0.22),
                  ncol=2, fontsize=8, frameon=False)

    plt.tight_layout()
    save(fig, "rq1_pit_family_distribution.png")


# ---------------------------------------------------------------------------
# Kill rate by PIT family
# ---------------------------------------------------------------------------

def plot_kill_rate_by_family() -> None:
    families   = list(BY_FAMILY.keys())
    kill_rates = [BY_FAMILY[f]["kill"] for f in families]
    fam_colors = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444"]
    labels     = [
        "projektowe",
        "na gramatyce",
        "obiektowe",
        "integracyjne",
        "Nowe wzorce",
    ]

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.suptitle(
        "Współczynnik zabicia nowych mutantów LLM według rodziny PIT",
        fontsize=12, fontweight="bold"
    )

    bars = ax.bar(labels, kill_rates, color=fam_colors, edgecolor="white", width=0.55)
    ax.set_ylim(90, 100)
    ax.set_ylabel("Kill rate (%)", fontsize=10)
    ax.set_xlabel("Rodzina operatorów PIT", fontsize=10)

    for bar, rate, fam in zip(bars, kill_rates, families):
        n_killed = int(BY_FAMILY[fam]["n"] * rate / 100)
        n_total  = BY_FAMILY[fam]["n"]
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.05,
            f"{rate}%\n({n_killed}/{n_total})",
            ha="center", va="bottom", fontsize=9
        )

    ax.axhline(y=95, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.text(4.4, 95.1, "95%", fontsize=8, color="gray")

    plt.tight_layout()
    save(fig, "rq1_kill_rate_by_family.png")


# ---------------------------------------------------------------------------
# New-pattern breakdown (mutants outside PIT repertoire)
# ---------------------------------------------------------------------------

def plot_beyond_classic_patterns() -> None:
    """Two-panel bar chart: 26 beyond-classic categories, split for readability."""
    patterns   = list(BEYOND_PATTERNS.keys())
    pcts       = [BEYOND_PATTERNS[p]["pct"] for p in patterns]
    ns         = [BEYOND_PATTERNS[p]["n"]   for p in patterns]
    # 26 distinct colours (no repeats)
    pat_colors = [
        "#EF4444", "#3B82F6", "#7C3AED", "#F59E0B",
        "#10B981", "#EC4899", "#06B6D4", "#84CC16",
        "#F97316", "#8B5CF6", "#6366F1", "#14B8A6",
        "#A855F7", "#22D3EE", "#FB923C", "#4ADE80",
        "#E879F9", "#60A5FA", "#FBBF24", "#34D399",
        "#A78BFA", "#D946EF", "#0EA5E9", "#F43F5E",
        "#16A34A", "#CA8A04",
    ]
    labels = [
        "Podstawienie wartości null",
        "Zmiana nazwy wywoływanej metody",
        "Negacja wyrażenia logicznego",
        "Podstawienie argumentu",
        "Zmiana opakowywania wywołania",
        "Zmiana wartości przypisania",
        "Usunięcie negacji",
        "Zamiana stałej wyliczeniowej",
        "Zastąpienie podwyrażenia stałą logiczną",
        "Zmiana literału łańcuchowego",
        "Zmiana literału boolowskiego w przypisaniu",
        "Zamiana kolejności argumentów",
        "Usunięcie wartości null",
        "Zmiana przepływu sterowania",
        "Zmiana wyrażenia instanceof",
        "Zamiana gałęzi wyrażenia trójkowego",
        "Zamiana klasy wyjątku",
        "Zmiana indeksu tablicy",
        "Zmiana semantyki porównania",
        "Wykomentowanie instrukcji",
        "Zamiana kolejności operandów",
        "Zamiana klasy implementacji",
        "Zmiana modyfikatora dostępu",
        "Przypisanie własne",
        "Zamiana stron przypisania",
        "Zmiana typu zmiennej",
    ]

    # Split into two panels: first 14 (high-freq) + last 12 (low-freq)
    SPLIT = 14
    p1_labels = labels[:SPLIT];  p1_pcts = pcts[:SPLIT];  p1_ns = ns[:SPLIT];  p1_col = pat_colors[:SPLIT]
    p2_labels = labels[SPLIT:];  p2_pcts = pcts[SPLIT:];  p2_ns = ns[SPLIT:];  p2_col = pat_colors[SPLIT:]

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(22, 8),
                                             gridspec_kw={"width_ratios": [2.2, 1]})
    fig.suptitle(
        f"Wzorce transformacji w nowych mutantach LLM spoza PIT",
        fontsize=13, fontweight="bold", y=1.01,
    )

    # ---- Left panel: top 14 categories ----
    y_left = np.arange(SPLIT)
    bars_l = ax_left.barh(y_left, p1_pcts, color=p1_col, edgecolor="white", height=0.65)
    ax_left.set_yticks(y_left)
    ax_left.set_yticklabels(
        [f"#{i+1}  {lbl}" for i, lbl in enumerate(p1_labels)], fontsize=11
    )
    ax_left.invert_yaxis()
    ax_left.set_xlabel("Odsetek w grupie spoza PIT (%)", fontsize=11)
    ax_left.set_title("Kategorie #1–#14  (wysoka częstość)", fontsize=11, fontweight="bold")
    ax_left.set_xlim(0, 22)
    for bar, pct, n in zip(bars_l, p1_pcts, p1_ns):
        ax_left.text(
            bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
            f"{pct:.1f}%  (n={n:,})", va="center", ha="left", fontsize=10,
        )

    # ---- Right panel: bottom 12 categories ----
    y_right = np.arange(len(p2_labels))
    bars_r  = ax_right.barh(y_right, p2_pcts, color=p2_col, edgecolor="white", height=0.65)
    ax_right.set_yticks(y_right)
    ax_right.set_yticklabels(
        [f"#{SPLIT+i+1}  {lbl}" for i, lbl in enumerate(p2_labels)], fontsize=11
    )
    ax_right.invert_yaxis()
    ax_right.set_xlabel("Odsetek w grupie spoza PIT (%)", fontsize=11)
    ax_right.set_title("Kategorie #15–#26  (niska częstość)", fontsize=11, fontweight="bold")
    ax_right.set_xlim(0, 2.0)
    for bar, pct, n in zip(bars_r, p2_pcts, p2_ns):
        ax_right.text(
            bar.get_width() + 0.03, bar.get_y() + bar.get_height() / 2,
            f"{pct:.1f}%  (n={n:,})", va="center", ha="left", fontsize=10,
        )

    plt.tight_layout()
    save(fig, "rq1_beyond_classic_patterns.png")


def plot_llm_nmr_only() -> None:
    """Simple bar chart: LLM-NMR for gemma4 and qwen3.6, with annotation."""
    llm_models = ["gemma4", "qwen3.6"]
    llm_nmr    = [AGG[m]["llm_nmr"] for m in llm_models]
    # new patterns (spoza PIT) as % of comparable useful = nmr × 42.8% (3837/8967)
    beyond_pct = [v * 0.428 for v in llm_nmr]

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.suptitle(
        "Odsetek nowych mutantów LLM\n(% użytecznych mutantów LLM bez odpowiednika w PIT)",
        fontsize=11, fontweight="bold"
    )

    x     = np.arange(len(llm_models))
    w     = 0.35
    bars1 = ax.bar(x - w/2, llm_nmr,    width=w, color=["#2563EB","#DC2626"],
                   label="LLM-NMR", edgecolor="white")
    bars2 = ax.bar(x + w/2, beyond_pct, width=w, color=["#93C5FD","#FCA5A5"],
                   label="Nowe mutanty spoza PIT", edgecolor="white")

    for bar, val in zip(bars1, llm_nmr):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                f"{val:.2f}%", ha="center", va="bottom", fontsize=11, fontweight="bold")
    for bar, val in zip(bars2, beyond_pct):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                f"≈{val:.2f}%", ha="center", va="bottom", fontsize=10, color="#555")

    ax.set_xticks(x)
    ax.set_xticklabels(llm_models, fontsize=12)
    ax.set_ylabel("% użytecznych mutantów LLM", fontsize=10)
    ax.set_ylim(0, 20)
    ax.legend(fontsize=9)
    ax.axhline(y=0, color="black", linewidth=0.5)

    plt.tight_layout()
    save(fig, "rq1_llm_nmr_breakdown.png")


# ---------------------------------------------------------------------------
# Coupling categorization stacked bar
# ---------------------------------------------------------------------------

def plot_coupling_categorization() -> None:
    cats   = ["strong", "strong_extra", "partial", "partial_extra", "not_sub", "not_detected"]
    labels = ["Strong", "Strong+Extra", "Partial", "Partial+Extra", "Not Subsumed", "Not Detected"]
    colors = ["#1D4ED8", "#3B82F6", "#059669", "#34D399", "#D97706", "#EF4444"]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle(
        "Klasyfikacja mutantów według podobieństwa do rzeczywistych defektów",
        fontsize=12, fontweight="bold"
    )

    x      = np.arange(len(MODELS))
    bottom = np.zeros(len(MODELS))

    for cat, label, color in zip(cats, labels, colors):
        vals = [COUPLING[m][cat] for m in MODELS]
        bars = ax.bar(x, vals, bottom=bottom, label=label, color=color,
                      edgecolor="white", linewidth=0.5)
        for bar, val in zip(bars, vals):
            if val > 3:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + bar.get_height() / 2,
                    f"{val:.1f}%",
                    ha="center", va="center", fontsize=8, color="white", fontweight="bold"
                )
        bottom += np.array(vals)

    ax.set_xticks(x)
    ax.set_xticklabels([MODEL_LABELS[m] for m in MODELS], fontsize=11)
    ax.set_ylabel("Odsetek mutantów (%)", fontsize=10)
    ax.set_ylim(0, 112)
    ax.legend(loc="upper right", fontsize=9, frameon=True,
              bbox_to_anchor=(1.18, 1.0))

    plt.tight_layout()
    save(fig, "rq1_coupling_categorization.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _style()
    print("Generating thesis plots...")
    plot_pit_family_distribution()
    plot_kill_rate_by_family()
    plot_beyond_classic_patterns()
    plot_coupling_categorization()
    plot_llm_nmr_only()
    print(f"\nAll plots saved to: {IMAGES_DIR}")
