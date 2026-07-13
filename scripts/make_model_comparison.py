"""
Cross-model robustness comparison: how much each model's OpinionQA answers change
under option reordering and English->French, relative to that model's own noise floor.

Fairness note: the noise floor differs by backend. Qwen is scored by a deterministic
teacher-forced logprob read (floor = batch numerics, ~1%). GPT-5.5 is a reasoning
model that forbids logprobs and temperature=0, so it is scored by a single temp=1
generate; its floor is test-retest sampling noise (~8%). "Net" = raw change rate
minus that model's noise floor, i.e. change attributable to the perturbation itself.

Usage: python scripts/make_model_comparison.py
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"


def rate(name):
    return json.loads((R / name).read_text())["answer_change_rate"]


MODELS = ["Qwen3-4B", "Qwen3-8B", "GPT-5.5"]
FLOOR = {  # model noise floor (answer-change rate under a no-op perturbation)
    "Qwen3-4B": rate("cmp_numerics.json"),      # batch numerics, deterministic
    "Qwen3-8B": rate("cmp_numerics.json"),      # same scoring path
    "GPT-5.5": rate("cmp_retest_gpt55.json"),   # temp=1 test-retest resample
}
REORDER = {
    "Qwen3-4B": rate("cmp_reorder.json"),
    "Qwen3-8B": rate("cmp_reorder_8b.json"),
    "GPT-5.5": rate("cmp_reorder_gpt55.json"),
}
FRENCH = {
    "Qwen3-4B": rate("cmp_french_gpt55.json"),        # vs GPT5.5-translated suite
    "Qwen3-8B": rate("cmp_french_gpt55_8b.json"),
    "GPT-5.5": rate("cmp_french_gpt55model.json"),
}


def main():
    rows = []
    for m in MODELS:
        rows.append((m, FLOOR[m], REORDER[m], FRENCH[m],
                     REORDER[m] - FLOOR[m], FRENCH[m] - FLOOR[m]))

    md = [
        "# Cross-model robustness on OpinionQA",
        "",
        "Answer-change rate under each perturbation, and net of each model's noise floor.",
        "",
        "| model | noise floor | reorder (raw) | reorder (net) | French (raw) | French (net) |",
        "|---|---|---|---|---|---|",
    ]
    for m, fl, ro, fr, ron, frn in rows:
        md.append(f"| {m} | {fl:.1%} | {ro:.1%} | {ron:.1%} | {fr:.1%} | {frn:.1%} |")
    md += [
        "",
        "Floor: Qwen = batch-numerics (deterministic logprob scoring); "
        "GPT-5.5 = temp=1 test-retest (reasoning model forbids logprobs & temp=0).",
    ]
    (R / "model_comparison.md").write_text("\n".join(md) + "\n")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    x = range(len(MODELS))
    colors = {"Qwen3-4B": "#4C72B0", "Qwen3-8B": "#55A868", "GPT-5.5": "#C44E52"}
    for ax, title, raw, floors in (
        (axes[0], "Option reordering", REORDER, FLOOR),
        (axes[1], "English -> French", FRENCH, FLOOR),
    ):
        for i, m in enumerate(MODELS):
            ax.bar(i, raw[m], color=colors[m], alpha=0.35, width=0.6)
            ax.bar(i, raw[m] - floors[m], color=colors[m], width=0.6,
                   label="net of noise floor" if i == 0 else None)
            ax.plot([i - 0.3, i + 0.3], [floors[m], floors[m]], "k--", linewidth=1)
            ax.text(i, raw[m] + 0.005, f"{raw[m]:.0%}", ha="center", fontsize=9)
        ax.set_xticks(list(x))
        ax.set_xticklabels(MODELS, rotation=15)
        ax.set_title(title)
        ax.set_ylabel("fraction of answers changed")
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("Robustness by model: raw change (faded) vs net of noise floor (solid); dashed = floor")
    fig.tight_layout()
    fig.savefig(R / "model_comparison.png", dpi=150, bbox_inches="tight")
    print((R / "model_comparison.md").read_text())
    print(f"wrote {R/'model_comparison.png'}")


if __name__ == "__main__":
    main()
