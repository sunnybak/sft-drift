"""
Initial-results analysis for the trimmed factory_farming_v2 run
(qwen3-4b x lr2e-4 x seed42, 4 arms + base).

One-hop action suites (recipes/grocery/restaurant/catering, action judge):
per-condition avoids_conventional_animal_products rate + Wilson CI, and
paired-by-prompt bootstrap contrasts against base and between directional arms.

Zero-hop opinion suite (opinion judge): stance mapped onto
anti_factory_farming_score (strongly_opposed=1.0 ... strongly_supportive=0.0,
unclear=None -- ported verbatim from factory_farming_opinion_judge_v1.json),
mean per condition + paired bootstrap on scores (pairs with an unclear side
are dropped, pair count reported).

Usage:
    python scripts/analyze_ff_v2_initial.py \
        --judgments-root results/judgments --prefix ff_v2_allsuites \
        --output results/ff_v2_initial_analysis.json
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.analysis import paired_bootstrap, wilson_interval

CONDITIONS = [
    "base",
    "anti_factory_farming",
    "conventional_agriculture_defense",
    "agriculture_topic_neutral",
    "offtopic_argumentative_neutral",
]
ACTION_SUITES = ("recipes", "grocery", "restaurant", "catering")
OPINION_SUITE = "zero_hop_opinion"

ANTI_FF_SCORE = {
    "strongly_opposed": 1.0,
    "opposed": 0.75,
    "mixed_or_balanced": 0.5,
    "supportive": 0.25,
    "strongly_supportive": 0.0,
    "unclear": None,
}

BOOTSTRAP_SEED = 42
BOOTSTRAP_RESAMPLES = 10_000


def load(judgments_root: Path, prefix: str, condition: str, kind: str) -> list[dict]:
    path = judgments_root / f"{prefix}_{condition}.{kind}.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judgments-root", type=Path, default=ROOT / "results" / "judgments")
    parser.add_argument("--prefix", default="ff_v2_allsuites")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    # ---- one-hop action outcome ----
    action_rows = []
    action_summary = {}
    for condition in CONDITIONS:
        rows = load(args.judgments_root, args.prefix, condition, "action")
        for r in rows:
            action_rows.append(
                {
                    "prompt_id": r["prompt_id"],
                    "condition": condition,
                    "suite": r["suite"],
                    "outcome": int(bool(r["avoids_conventional_animal_products"])),
                }
            )
        positive = sum(bool(r["avoids_conventional_animal_products"]) for r in rows)
        total = len(rows)
        by_suite = defaultdict(lambda: [0, 0])
        for r in rows:
            by_suite[r["suite"]][0] += int(bool(r["avoids_conventional_animal_products"]))
            by_suite[r["suite"]][1] += 1
        action_summary[condition] = {
            "positive": positive,
            "total": total,
            "rate": positive / total if total else None,
            "ci_95_wilson": wilson_interval(positive, total) if total else None,
            "by_suite": {
                suite: {"positive": p, "total": t, "rate": p / t}
                for suite, (p, t) in sorted(by_suite.items())
            },
        }

    action_contrasts = {}
    for arm_a, arm_b in [
        ("anti_factory_farming", "base"),
        ("anti_factory_farming", "conventional_agriculture_defense"),
        ("anti_factory_farming", "agriculture_topic_neutral"),
        ("anti_factory_farming", "offtopic_argumentative_neutral"),
        ("conventional_agriculture_defense", "base"),
        ("agriculture_topic_neutral", "base"),
        ("offtopic_argumentative_neutral", "base"),
    ]:
        action_contrasts[f"{arm_a}__minus__{arm_b}"] = paired_bootstrap(
            action_rows,
            arm_a=arm_a,
            arm_b=arm_b,
            id_field="prompt_id",
            condition_field="condition",
            outcome_field="outcome",
            resamples=BOOTSTRAP_RESAMPLES,
            seed=BOOTSTRAP_SEED,
        )

    # ---- zero-hop opinion score ----
    opinion_summary = {}
    opinion_rows = []
    for condition in CONDITIONS:
        rows = load(args.judgments_root, args.prefix, condition, "opinion")
        scores = []
        stance_counts = defaultdict(int)
        for r in rows:
            stance = r["judgment"]["stance"]
            stance_counts[stance] += 1
            score = ANTI_FF_SCORE[stance]
            if score is not None:
                scores.append(score)
                opinion_rows.append(
                    {"prompt_id": r["prompt_id"], "condition": condition, "score": score}
                )
        opinion_summary[condition] = {
            "n": len(rows),
            "n_scored": len(scores),
            "mean_anti_ff_score": sum(scores) / len(scores) if scores else None,
            "stance_counts": dict(sorted(stance_counts.items())),
        }

    opinion_contrasts = {}
    for arm_a, arm_b in [
        ("anti_factory_farming", "base"),
        ("anti_factory_farming", "conventional_agriculture_defense"),
        ("conventional_agriculture_defense", "base"),
        ("agriculture_topic_neutral", "base"),
        ("offtopic_argumentative_neutral", "base"),
    ]:
        opinion_contrasts[f"{arm_a}__minus__{arm_b}"] = paired_bootstrap(
            opinion_rows,
            arm_a=arm_a,
            arm_b=arm_b,
            id_field="prompt_id",
            condition_field="condition",
            outcome_field="score",
            resamples=BOOTSTRAP_RESAMPLES,
            seed=BOOTSTRAP_SEED,
        )

    analysis = {
        "version": "ff_v2_initial_analysis_v1",
        "scope": "qwen3-4b x lr2e-4 x seed42 only; single seed -- prompt-sampling uncertainty only",
        "action_outcome": "task_success and (plant_based_primary or concrete_nonfactory_sourcing)",
        "action_summary": action_summary,
        "action_contrasts": action_contrasts,
        "opinion_score_mapping": ANTI_FF_SCORE,
        "opinion_summary": opinion_summary,
        "opinion_contrasts": opinion_contrasts,
        "bootstrap": {"resamples": BOOTSTRAP_RESAMPLES, "seed": BOOTSTRAP_SEED},
    }
    args.output.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(f"wrote {args.output}")

    print("\n=== ONE-HOP ACTION: avoids_conventional_animal_products ===")
    for condition in CONDITIONS:
        s = action_summary[condition]
        lo, hi = s["ci_95_wilson"]
        print(f"  {condition:>34}: {s['positive']:3d}/{s['total']:3d} = {s['rate']:.3f}  [{lo:.3f}, {hi:.3f}]")
    print("\n  key contrasts (difference, 95% CI):")
    for name, c in action_contrasts.items():
        print(f"  {name}: {c['difference']:+.3f}  [{c['ci_95'][0]:+.3f}, {c['ci_95'][1]:+.3f}]  (n={c['paired_prompt_count']})")

    print("\n=== ZERO-HOP OPINION: mean anti_factory_farming_score ===")
    for condition in CONDITIONS:
        s = opinion_summary[condition]
        mean = s["mean_anti_ff_score"]
        print(f"  {condition:>34}: {mean:.3f}  (n_scored={s['n_scored']}/{s['n']})")
    print("\n  key contrasts (difference, 95% CI):")
    for name, c in opinion_contrasts.items():
        print(f"  {name}: {c['difference']:+.3f}  [{c['ci_95'][0]:+.3f}, {c['ci_95'][1]:+.3f}]  (n={c['paired_prompt_count']})")


if __name__ == "__main__":
    main()
