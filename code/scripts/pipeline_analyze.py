"""
Analysis CLI over pipeline/analysis.py (paired bootstrap, Wilson CI, Holm
correction, seed x prompt directional contrast) -- generalizes
17_analyze_factory_farming_evals.py + 23_analyze_factory_farming_recipe_pilot.py.

Usage:
    python scripts/pipeline_analyze.py paired-bootstrap --joined results/unblinded_reviews.jsonl \\
        --arm-a anti --arm-b base --id-field prompt_id --condition-field short_condition \\
        --outcome-field pilot_outcome --resamples 10000 --seed 20260727 --output results/contrast.json

    python scripts/pipeline_analyze.py wilson --positive 4 --total 8

    python scripts/pipeline_analyze.py holm --p-values '{"a": 0.01, "b": 0.03}'

    python scripts/pipeline_analyze.py directional-contrast --arm-a results/arm_a.jsonl \\
        --arm-b results/arm_b.jsonl --resamples 10000 --seed 42 --output results/contrast.json

    (directional-contrast input jsonl: one row per {seed, prompt_id, value}; pivoted
    into a seed x prompt 2D array by sorted unique seed/prompt_id.)
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.analysis import bootstrap_directional_contrast, holm_adjust, paired_bootstrap, wilson_interval


def cmd_paired_bootstrap(args):
    rows = [json.loads(line) for line in Path(args.joined).read_text().splitlines() if line]
    result = paired_bootstrap(
        rows,
        arm_a=args.arm_a,
        arm_b=args.arm_b,
        id_field=args.id_field,
        condition_field=args.condition_field,
        outcome_field=args.outcome_field,
        resamples=args.resamples,
        seed=args.seed,
        expected_pair_count=args.expected_pair_count,
    )
    _emit(result, args.output)


def cmd_wilson(args):
    lo, hi = wilson_interval(args.positive, args.total)
    _emit({"positive": args.positive, "total": args.total, "ci_95": [lo, hi]}, args.output)


def cmd_holm(args):
    p_values = json.loads(args.p_values)
    _emit(holm_adjust(p_values), args.output)


def _pivot(path):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line]
    seeds = sorted({r["seed"] for r in rows})
    prompts = sorted({r["prompt_id"] for r in rows})
    seed_index = {s: i for i, s in enumerate(seeds)}
    prompt_index = {p: i for i, p in enumerate(prompts)}
    arr = np.zeros((len(seeds), len(prompts)))
    for r in rows:
        arr[seed_index[r["seed"]], prompt_index[r["prompt_id"]]] = r["value"]
    return arr


def cmd_directional_contrast(args):
    arm_a = _pivot(args.arm_a)
    arm_b = _pivot(args.arm_b)
    result = bootstrap_directional_contrast(arm_a, arm_b, resamples=args.resamples, seed=args.seed)
    _emit(result, args.output)


def _emit(result, output):
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if output:
        Path(output).write_text(text + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("paired-bootstrap")
    p.add_argument("--joined", required=True)
    p.add_argument("--arm-a", required=True)
    p.add_argument("--arm-b", required=True)
    p.add_argument("--id-field", required=True)
    p.add_argument("--condition-field", required=True)
    p.add_argument("--outcome-field", required=True)
    p.add_argument("--resamples", type=int, default=10_000)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--expected-pair-count", type=int, default=None)
    p.add_argument("--output")
    p.set_defaults(func=cmd_paired_bootstrap)

    p = sub.add_parser("wilson")
    p.add_argument("--positive", type=int, required=True)
    p.add_argument("--total", type=int, required=True)
    p.add_argument("--output")
    p.set_defaults(func=cmd_wilson)

    p = sub.add_parser("holm")
    p.add_argument("--p-values", required=True, help="JSON object string, e.g. '{\"a\": 0.01}'")
    p.add_argument("--output")
    p.set_defaults(func=cmd_holm)

    p = sub.add_parser("directional-contrast")
    p.add_argument("--arm-a", required=True, help="jsonl of {seed, prompt_id, value} rows")
    p.add_argument("--arm-b", required=True)
    p.add_argument("--resamples", type=int, default=10_000)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--output")
    p.set_defaults(func=cmd_directional_contrast)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
