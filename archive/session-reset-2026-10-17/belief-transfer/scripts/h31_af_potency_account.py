"""Off-chance probe (2026-08-23, UNREGISTERED, exploratory): what predicts AF?

    uv run python scripts/h31_af_potency_account.py

The paper's most striking result is that removing TracIn's top-ranked documents INCREASES
the netted effect (AF -0.91 / -0.42, both zero-excluding). `H27` records the result and a
mechanism sketch ("NEG-LENGTH plus the ms0 trap") but never quantifies it. This asks the
blunt question the sketch implies: is AF simply a function of how much TRUE potency a
method's removal set contained?

Pure analysis of artifacts already on disk -- the removal-set manifest and the AF summary.
No training, no API, no new measurement. Exploratory and post-hoc: this was NOT registered
before the AF numbers were seen, so nothing here may be quoted as a test of anything. It is
a candidate account, and its value is in what it proposes to test next.
"""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "results" / "factory_farming" / "attrib_mix_v4"

# Installed per-source effects (run_attribution.GROUND_TRUTH_DB) and pool composition.
GT = {"m0": 0.0, "ms0": 0.0, "mev": 0.007, "md": 0.111, "ms": 0.157, "me": 0.311}
PER_SOURCE = 93
ON_TOPIC = [s for s in GT if s != "m0"]


def spearman(a: list[float], b: list[float]) -> float:
    def rank(v: list[float]) -> list[float]:
        order = sorted(range(len(v)), key=lambda i: v[i])
        out = [0.0] * len(v)
        for pos, idx in enumerate(order):
            out[idx] = float(pos)
        return out
    ra, rb = rank(a), rank(b)
    ma, mb = statistics.fmean(ra), statistics.fmean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else float("nan")


def linfit(x: list[float], y: list[float]) -> tuple[float, float]:
    mx, my = statistics.fmean(x), statistics.fmean(y)
    var = sum((v - mx) ** 2 for v in x)
    slope = sum((a - mx) * (b - my) for a, b in zip(x, y)) / var if var else 0.0
    return slope, my - slope * mx


def main() -> None:
    manifest = json.loads((RESULTS / "af_arms_manifest.json").read_text())
    af = yaml.safe_load((RESULTS / "af_summary.yaml").read_text())
    pool_potency = sum(GT[s] * PER_SOURCE for s in GT)

    rows = []
    for arm, entry in manifest.items():
        if "random" in arm:  # registered 2026-08-22d as not a clean dose control
            continue
        key = arm.removeprefix("af_")
        comp = entry["removed_by_source"]
        potency = sum(GT[s] * n for s, n in comp.items())
        removed_docs = sum(comp.values())
        null_docs = comp.get("ms0", 0) + comp.get("m0", 0)
        for seed in ("s42", "s7"):
            cell = af.get(f"af_{key}_{seed}")
            if not cell:
                continue
            rows.append(
                {
                    "arm": key, "seed": seed, "af": cell["delta"],
                    "excludes_zero": cell["excludes_zero"],
                    "potency_frac": potency / pool_potency,
                    "null_frac": null_docs / removed_docs if removed_docs else 0.0,
                    "removed_docs": removed_docs,
                }
            )

    print("=" * 92)
    print("AF against how much INSTALLED POTENCY the removal set actually contained")
    print("=" * 92)
    print(f"{'arm':17s} {'seed':5s} {'AF':>8s} {'excl':>5s} "
          f"{'potency removed':>16s} {'null-cell share':>16s}")
    for r in sorted(rows, key=lambda r: r["potency_frac"]):
        print(f"{r['arm']:17s} {r['seed']:5s} {r['af']:+8.3f} "
              f"{'*' if r['excludes_zero'] else '':>5s} "
              f"{r['potency_frac']:15.1%} {r['null_frac']:16.1%}")

    for seed in ("s42", "s7", "both"):
        sub = [r for r in rows if seed == "both" or r["seed"] == seed]
        x = [r["potency_frac"] for r in sub]
        y = [r["af"] for r in sub]
        slope, intercept = linfit(x, y)
        crossing = -intercept / slope if slope else float("nan")
        print(f"\n-- {seed} (n={len(sub)}) --")
        print(f"   spearman(potency removed, AF) = {spearman(x, y):+.3f}")
        print(f"   spearman(null-cell share, AF) = "
              f"{spearman([r['null_frac'] for r in sub], y):+.3f}")
        print(f"   linear fit: AF = {slope:+.3f} * potency_frac {intercept:+.3f}")
        print(f"   AF crosses zero at potency_frac = {crossing:.1%}")

    print("\n" + "=" * 92)
    print("READING (exploratory, post-hoc, not a registered test)")
    print("=" * 92)
    print(
        "If AF is monotone in removed potency with a NEGATIVE intercept, then 'content-keyed\n"
        "removal is counterproductive' is one face of a simpler quantity: these methods remove\n"
        "little true potency, and the removal-plus-backfill operation carries an offset that is\n"
        "negative when little potency goes with it. The falsifiable successor is the crossing\n"
        "point: a method removing MORE than that share of pool potency should post AF > 0\n"
        "regardless of which documents it picked. That is testable by construction -- build a\n"
        "removal set at the crossing potency from a deliberately WRONG ranking and retrain."
    )


if __name__ == "__main__":
    main()
