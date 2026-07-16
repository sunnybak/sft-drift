"""
[side-quest scratch] Generate figures for the research note (notes/research_note_*.tex)
from the committed lean-comparison results.

    python scripts/exp_make_note_figures.py   # -> notes/figures/*.pdf
"""

import json
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
OUT = ROOT / "notes" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# validated categorical palette (dataviz reference, light mode)
C1, C2, C3, C4 = "#2a78d6", "#1baf7a", "#eda100", "#4a3aa7"
GRAY = "#8a8a85"

plt.rcParams.update({
    "font.size": 9, "axes.edgecolor": GRAY, "axes.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
    "grid.color": "#e5e5e0", "grid.linewidth": 0.5,
})


def mean_delta(path):
    d = json.loads((R / path).read_text())
    return statistics.mean(r["delta_conservative_lean"] for r in d["per_item"])


def fig1_perturbation_shifts():
    perturbs = [
        ("Reorder (no SFT)", "reorder"),
        ("English$\\to$French", "french"),
        ("Neutral SFT vs base", "neutral_vs_base"),
        ("Control SFT vs base", "control_vs_base"),
        ("Rights SFT vs base", "rights_vs_base"),
        ("Rights vs control", "rights_vs_control"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 2.9), sharex=True)
    for ax, tag, title in zip(axes, ("qwen3-4b", "qwen3-8b"), ("Qwen3-4B-Instruct", "Qwen3-8B")):
        names = [p[0] for p in perturbs]
        weighted = [mean_delta(f"lean_{s}_{tag}.json") for _, s in perturbs]
        argmax = [mean_delta(f"lean_argmax_{s}_{tag}.json") for _, s in perturbs]
        y = range(len(perturbs))
        h = 0.36
        ax.barh([i + h / 2 + 0.01 for i in y], weighted, height=h, color=C1, label="probability-weighted")
        ax.barh([i - h / 2 - 0.01 for i in y], argmax, height=h, color=C3, label="argmax")
        for i, (w, a) in enumerate(zip(weighted, argmax)):
            ax.text(w + (0.002 if w >= 0 else -0.002), i + h / 2 + 0.01, f"{w:+.3f}",
                    va="center", ha="left" if w >= 0 else "right", fontsize=7, color="#3d3d3a")
            ax.text(a + (0.002 if a >= 0 else -0.002), i - h / 2 - 0.01, f"{a:+.3f}",
                    va="center", ha="left" if a >= 0 else "right", fontsize=7, color="#3d3d3a")
        ax.axvline(0, color=GRAY, linewidth=0.6)
        ax.set_yticks(list(y))
        ax.set_yticklabels(names if ax is axes[0] else [""] * len(names))
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("mean $\\Delta$ conservative-lean (n=795 items)")
        ax.set_xlim(-0.03, 0.15)
        ax.grid(axis="x")
        ax.set_axisbelow(True)
    axes[0].legend(loc="lower right", fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_perturbation_shifts.pdf", bbox_inches="tight")
    print(OUT / "fig1_perturbation_shifts.pdf")


def fig2_dose_response():
    steps = [0, 40, 80, 120, 160, 200]
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 2.7))

    # (a) confidence trajectory, 8B
    conf = {"rights": [], "control": []}
    base_conf = json.loads((R / "allarms-qwen3-8b-base-step0.json").read_text())["aggregates"]["_overall"]["mean_confidence"]
    for arm in ("rights", "control"):
        conf[arm].append(base_conf)
        for s in steps[1:]:
            d = json.loads((R / f"traj-qwen3-8b-{arm}-step{s}.json").read_text())
            conf[arm].append(d["aggregates"]["_overall"]["mean_confidence"])
    axes[0].plot(steps, conf["rights"], "-o", color=C1, markersize=4, linewidth=1.6, label="rights")
    axes[0].plot(steps, conf["control"], "-o", color=C3, markersize=4, linewidth=1.6, label="control")
    axes[0].set_xlabel("training step")
    axes[0].set_ylabel("mean answer confidence")
    axes[0].set_title("(a) Confidence collapse is front-loaded (8B)", fontsize=9)
    axes[0].set_ylim(0.4, 1.0)
    axes[0].grid(axis="y")
    axes[0].set_axisbelow(True)
    axes[0].legend(fontsize=7, frameon=False)

    # (b) rights-vs-control argmax delta trajectory, both sizes
    for tag, color, label in (("qwen3-8b", C1, "8B"), ("qwen3-4b", C3, "4B")):
        deltas = [0.0]
        for s in steps[1:]:
            deltas.append(mean_delta(f"lean_argmax_traj_rvc_step{s}_{tag}.json"))
        axes[1].plot(steps, deltas, "-o", color=color, markersize=4, linewidth=1.6, label=label)
    axes[1].axhline(0, color=GRAY, linewidth=0.6)
    axes[1].set_xlabel("training step")
    axes[1].set_ylabel("rights $-$ control, argmax $\\Delta$")
    axes[1].set_title("(b) Content-specific shift accumulates", fontsize=9)
    axes[1].grid(axis="y")
    axes[1].set_axisbelow(True)
    axes[1].legend(fontsize=7, frameon=False)

    fig.tight_layout()
    fig.savefig(OUT / "fig2_dose_response.pdf", bbox_inches="tight")
    print(OUT / "fig2_dose_response.pdf")


def fig3_axis_position():
    fig, ax = plt.subplots(figsize=(5.2, 2.4))
    arms = ["base", "rights", "control", "neutral"]
    for j, (tag, color, label) in enumerate((("qwen3-4b", C3, "4B"), ("qwen3-8b", C1, "8B"))):
        d = json.loads((R / f"lean_rights_vs_base_{tag}.json").read_text())
        base = statistics.mean(r["conservative_aligned_a"] for r in d["per_item"])
        vals = [base]
        for stem in ("rights_vs_base", "control_vs_base", "neutral_vs_base"):
            dd = json.loads((R / f"lean_{stem}_{tag}.json").read_text())
            vals.append(statistics.mean(r["conservative_aligned_b"] for r in dd["per_item"]))
        x = [i + (j - 0.5) * 0.36 for i in range(len(arms))]
        ax.bar(x, vals, width=0.34, color=color, label=label)
        for xi, v in zip(x, vals):
            ax.text(xi, v + 0.008, f"{v:.2f}", ha="center", fontsize=7, color="#3d3d3a")
    ax.axhline(0.5, color=GRAY, linewidth=0.8, linestyle="--")
    ax.text(3.55, 0.505, "human midpoint", fontsize=7, color=GRAY, ha="right")
    ax.set_xticks(range(len(arms)))
    ax.set_xticklabels(arms)
    ax.set_ylabel("mean conservative-aligned score")
    ax.set_ylim(0, 0.6)
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.legend(fontsize=7, frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT / "fig3_axis_position.pdf", bbox_inches="tight")
    print(OUT / "fig3_axis_position.pdf")


def fig4_decomposition():
    """8B & 4B: decompose each arm's argmax drift into generic dose (clean neutral)
    + content pull, with bootstrap 95% CIs."""
    import math

    def load_deltas(path):
        d = json.loads((R / path).read_text())
        return [r["delta_conservative_lean"] for r in d["per_item"]]

    def ci(deltas, seed=42, b=4000):
        import random
        rng = random.Random(seed)
        n = len(deltas)
        ms = sorted(sum(rng.choices(deltas, k=n)) / n for _ in range(b))
        return statistics.fmean(deltas), ms[int(0.025 * b)], ms[int(0.975 * b)]

    arms = [
        ("reorder (floor)", "lean_argmax_reorder_{full}.json", C4),
        ("En→Fr (floor)", "lean_argmax_french_{full}.json", C4),
        ("neutral (dose ref)", "lean_argmax_neutralcleanfull_vs_base_{short}.json", GRAY),
        ("control vs base", "lean_argmax_control_vs_base_{full}.json", C1),
        ("rights vs base", "lean_argmax_rights_vs_base_{full}.json", C1),
        ("rights vs control", "lean_argmax_rights_vs_control_{full}.json", C3),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.0), sharey=True)
    for ax, (full, short, title) in zip(axes, [("qwen3-4b", "4b", "Qwen3-4B-Instruct"),
                                               ("qwen3-8b", "8b", "Qwen3-8B")]):
        ys = list(range(len(arms)))
        for i, (name, tmpl, color) in enumerate(arms):
            deltas = load_deltas(tmpl.format(full=full, short=short))
            m, lo, hi = ci(deltas)
            ax.errorbar(m, i, xerr=[[m - lo], [hi - m]], fmt="o", color=color,
                        markersize=5, capsize=3, linewidth=1.5)
            ax.text(m, i + 0.28, f"{m:+.3f}", ha="center", fontsize=6.5, color="#3d3d3a")
        ax.axvline(0, color=GRAY, linewidth=0.6)
        ax.set_yticks(ys)
        ax.set_yticklabels([a[0] for a in arms] if ax is axes[0] else [""] * len(arms))
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("argmax $\\Delta$ conservative-lean (95% CI)")
        ax.set_xlim(-0.04, 0.11)
        ax.grid(axis="x")
        ax.set_axisbelow(True)
        ax.set_ylim(-0.6, len(arms) - 0.2)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_decomposition.pdf", bbox_inches="tight")
    print(OUT / "fig4_decomposition.pdf")


if __name__ == "__main__":
    fig1_perturbation_shifts()
    fig2_dose_response()
    fig3_axis_position()
    fig4_decomposition()
