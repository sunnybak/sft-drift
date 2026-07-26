"""
Assemble the "perturbation ladder": one table + chart ranking every measured
perturbation by how much it changes the model's OpinionQA behavior.

This is the attribution floor for the SFT experiments: an SFT-induced shift is only
meaningful where it lands on this ladder relative to the do-nothing rungs.

Usage:
    python scripts/make_ladder.py results/cmp_numerics.json results/cmp_reorder.json \
        results/cmp_french.json [results/cmp_<new>.json ...]
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def main():
    paths = [Path(p) for p in sys.argv[1:]]
    rungs = []
    for p in paths:
        s = json.loads(p.read_text())
        rungs.append(
            {
                "name": f"{s['label_a']} → {s['label_b']}",
                "mean_signed_delta": s["mean_signed_delta"],
                "mean_abs_delta": s["mean_abs_delta"],
                "answer_change_rate": s["answer_change_rate"],
                "mean_jsd": s["mean_jsd"],
                "source": p.name,
            }
        )
    rungs.sort(key=lambda r: r["answer_change_rate"])

    md = [
        "# Perturbation ladder — Qwen3-4B-Instruct baseline on OpinionQA",
        "",
        "Each rung: how much a *non-training* perturbation changes the model's answers.",
        "SFT drift (Phase 3) must be read against these rungs.",
        "",
        "| perturbation | answers changed | mean \\|Δ\\| opinion | mean signed Δ | mean JSD (bits) |",
        "|---|---|---|---|---|",
    ]
    for r in rungs:
        md.append(
            f"| {r['name']} | {r['answer_change_rate']:.1%} | {r['mean_abs_delta']:.4f} "
            f"| {r['mean_signed_delta']:+.4f} | {r['mean_jsd']:.4f} |"
        )
    out_md = ROOT / "results" / "perturbation_ladder.md"
    out_md.write_text("\n".join(md) + "\n")

    fig, axes = plt.subplots(1, 2, figsize=(12, 0.9 + 0.85 * len(rungs)))
    names = [r["name"] for r in rungs]
    for ax, key, label, color in (
        (axes[0], "answer_change_rate", "fraction of answers changed", "#4C72B0"),
        (axes[1], "mean_jsd", "mean per-question JSD (bits)", "#DD8452"),
    ):
        vals = [r[key] for r in rungs]
        ax.barh(names, vals, color=color)
        for i, v in enumerate(vals):
            ax.text(v, i, f" {v:.3f}", va="center", fontsize=9)
        ax.set_xlabel(label)
        ax.set_xlim(0, max(vals) * 1.18)
    axes[1].set_yticklabels([])
    fig.suptitle("Perturbation ladder: behavior change from non-training interventions")
    fig.tight_layout()
    out_png = ROOT / "results" / "perturbation_ladder.png"
    fig.savefig(out_png, dpi=150, bbox_inches="tight")

    print(out_md)
    print(out_png)
    for r in rungs:
        print(f"  {r['name']:<38} change={r['answer_change_rate']:.1%}  |Δ|={r['mean_abs_delta']:.4f}")


if __name__ == "__main__":
    main()
