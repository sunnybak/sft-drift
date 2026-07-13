"""
Robustness vs reasoning effort for GPT-5.5, on a matched question subsample.

For each reasoning_effort level, on the SAME first-N questions:
  reorder flip = fraction whose chosen option changes between original and shuffled
                 option order (within the English run)
  french flip  = fraction whose chosen option changes English -> French
                 (paired per question+variant)

'none' is read from the full-suite runs, subset to the same N ids.

Usage: python scripts/analyze_reasoning_sweep.py [N]
"""

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 150

SUBSET = [json.loads(l)["id"] for l in open(ROOT / "data/evals/opinionqa_v1.jsonl")][:N]
SUBSET_SET = set(SUBSET)


def load(path):
    by = defaultdict(dict)
    for l in open(path):
        r = json.loads(l)
        if r["id"] in SUBSET_SET:
            by[r["id"]][r["variant"]] = r
    return by


def reorder_flip(en_path):
    by = load(en_path)
    fl = [by[q]["original"]["chosen_option"] != by[q]["shuffled"]["chosen_option"]
          for q in by if "original" in by[q] and "shuffled" in by[q]]
    return statistics.mean(fl), len(fl)


def french_flip(en_path, fr_path):
    en, fr = load(en_path), load(fr_path)
    fl = []
    for q in en:
        if q not in fr:
            continue
        for v in ("original", "shuffled"):
            if v in en[q] and v in fr[q]:
                fl.append(en[q][v]["chosen_option"] != fr[q][v]["chosen_option"])
    return statistics.mean(fl), len(fl)


LEVELS = [
    ("none", "gpt55-en-opinionqa-v1.jsonl", "gpt55-fr-opinionqa-v1.jsonl"),
    ("low", "gpt55-en-rlow.jsonl", "gpt55-fr-rlow.jsonl"),
    ("medium", "gpt55-en-rmedium.jsonl", "gpt55-fr-rmedium.jsonl"),
]


def main():
    rows = []
    for level, en, fr in LEVELS:
        if not (R / en).exists() or not (R / fr).exists():
            print(f"skip {level}: missing results")
            continue
        ro, nro = reorder_flip(R / en)
        frf, nfr = french_flip(R / en, R / fr)
        rows.append((level, ro, frf, nro, nfr))
        print(f"{level:>7}: reorder flip {ro:.1%} (n={nro}) | french flip {frf:.1%} (n={nfr})")

    md = [
        f"# GPT-5.5 robustness vs reasoning effort (matched {N}-question subsample)",
        "",
        "| reasoning_effort | reorder flip | French flip |",
        "|---|---|---|",
    ]
    for level, ro, frf, *_ in rows:
        md.append(f"| {level} | {ro:.1%} | {frf:.1%} |")
    (R / "reasoning_sweep.md").write_text("\n".join(md) + "\n")

    levels = [r[0] for r in rows]
    x = range(len(levels))
    fig, ax = plt.subplots(figsize=(7, 4.8))
    ax.plot(x, [r[1] for r in rows], "o-", label="reorder", color="#4C72B0")
    ax.plot(x, [r[2] for r in rows], "s-", label="English→French", color="#C44E52")
    for i, r in enumerate(rows):
        ax.text(i, r[1] + 0.005, f"{r[1]:.0%}", ha="center", fontsize=9)
        ax.text(i, r[2] + 0.005, f"{r[2]:.0%}", ha="center", fontsize=9)
    ax.set_xticks(list(x))
    ax.set_xticklabels(levels)
    ax.set_xlabel("reasoning_effort")
    ax.set_ylabel("fraction of answers changed")
    ax.set_ylim(bottom=0)
    ax.set_title(f"GPT-5.5 robustness vs reasoning effort (n={N})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(R / "reasoning_sweep.png", dpi=150)
    print(f"wrote {R/'reasoning_sweep.md'} and .png")


if __name__ == "__main__":
    main()
