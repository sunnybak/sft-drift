"""
Item-level bootstrap CIs for lean-comparison results (08_model_lean_comparison.py
output files).

The suite-wide mean delta_conservative_lean is a point estimate over n=795 usable
items; this script quantifies its sampling uncertainty by resampling ITEMS with
replacement (the item is the exchangeable unit -- each item's delta already
averages both order variants) and recomputing the mean, B times. Reports the
percentile 95% CI and the bootstrap tail probability P(mean <= 0) (one-sided,
for "is this contrast distinguishable from zero").

Deterministic: fixed seed, results reproducible byte-for-byte.

Usage:
    python scripts/09_bootstrap_ci.py results/lean_argmax_rights_vs_control_qwen3-8b.json [...]
    python scripts/09_bootstrap_ci.py --all   # the standard set, printed as a table
"""

import argparse
import json
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
B = 10_000
SEED = 42

STANDARD_SET = [
    ("reorder (floor)", "lean_argmax_reorder_{tag}.json"),
    ("en->fr (floor)", "lean_argmax_french_{tag}.json"),
    ("neutral vs base", "lean_argmax_neutral_vs_base_{tag}.json"),
    ("control vs base", "lean_argmax_control_vs_base_{tag}.json"),
    ("rights vs base", "lean_argmax_rights_vs_base_{tag}.json"),
    ("rights vs control", "lean_argmax_rights_vs_control_{tag}.json"),
]


def bootstrap(deltas, b=B, seed=SEED):
    rng = random.Random(seed)
    n = len(deltas)
    means = []
    for _ in range(b):
        means.append(statistics.fmean(rng.choices(deltas, k=n)))
    means.sort()
    lo = means[int(0.025 * b)]
    hi = means[int(0.975 * b)]
    p_le_zero = sum(m <= 0 for m in means) / b
    return statistics.fmean(deltas), lo, hi, p_le_zero


def report(path):
    d = json.loads(Path(path).read_text())
    deltas = [r["delta_conservative_lean"] for r in d["per_item"]]
    mean, lo, hi, p = bootstrap(deltas)
    return {
        "file": Path(path).name,
        "label": f"{d['label_a']} -> {d['label_b']}",
        "score_mode": d.get("score_mode", "weighted"),
        "n_items": len(deltas),
        "mean": round(mean, 4),
        "ci95": [round(lo, 4), round(hi, 4)],
        "p_le_zero": round(p, 4),
        "excludes_zero": lo > 0 or hi < 0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--out", default=None, help="write results as json")
    args = ap.parse_args()

    if args.all:
        paths = [R / f.format(tag=tag) for _, f in STANDARD_SET
                 for tag in ("qwen3-4b", "qwen3-8b") if (R / f.format(tag=tag)).exists()]
    else:
        paths = [Path(p) for p in args.paths]

    rows = [report(p) for p in paths]
    print(f"{'comparison':<42}{'n':<6}{'mean':<10}{'95% CI':<22}{'P(<=0)':<9}{'sig'}")
    for r in rows:
        ci = f"[{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}]"
        print(f"{r['file'].replace('lean_argmax_','').replace('.json',''):<42}"
              f"{r['n_items']:<6}{r['mean']:<+10.4f}{ci:<22}{r['p_le_zero']:<9.4f}"
              f"{'*' if r['excludes_zero'] else ''}")
    if args.out:
        Path(args.out).write_text(json.dumps(rows, indent=2))
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
