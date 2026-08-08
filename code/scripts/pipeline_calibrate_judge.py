"""
Calibration gate: compare judge outcomes against a reference set of outcomes
(human review, an independent model, whatever `--reference-type` names) using
pipeline.judge.calibrate (exact_agreement / Cohen's kappa). Hard failure by
default -- exits nonzero on FAIL, same as 16_calibrate_factory_farming_judge.py.

Input: a jsonl of {"judge_outcome": bool, "reference_outcome": bool} pairs
(join judgment records with your reference review however that's sourced;
this script only runs the statistical gate, it does not do the sampling/
blinding workflow -- see pipeline/judge.py's module docstring for scope).

Usage:
    python scripts/pipeline_calibrate_judge.py --pairs results/calibration_pairs.jsonl \\
        --judge-spec configs/experiments/factory_farming_v2/judge_spec.json \\
        --reference-type codex_chat_review_not_api_or_human \\
        --output results/calibration_report.json
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.judge import calibrate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", required=True, type=Path)
    parser.add_argument("--judge-spec", type=Path, help="pulls minimum_exact_agreement/minimum_cohens_kappa from judge_spec.calibration if given")
    parser.add_argument("--min-exact-agreement", type=float)
    parser.add_argument("--min-cohens-kappa", type=float)
    parser.add_argument("--reference-type", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    min_exact_agreement = args.min_exact_agreement
    min_cohens_kappa = args.min_cohens_kappa
    if args.judge_spec:
        cal = json.loads(args.judge_spec.read_text())["calibration"]
        min_exact_agreement = min_exact_agreement or cal["minimum_exact_agreement"]
        min_cohens_kappa = min_cohens_kappa or cal["minimum_cohens_kappa"]
    if min_exact_agreement is None or min_cohens_kappa is None:
        raise SystemExit("must supply --min-exact-agreement/--min-cohens-kappa or --judge-spec")

    rows = [json.loads(line) for line in args.pairs.read_text().splitlines() if line]
    pairs = [(bool(r["judge_outcome"]), bool(r["reference_outcome"])) for r in rows]

    report = calibrate(
        pairs=pairs,
        min_exact_agreement=min_exact_agreement,
        min_cohens_kappa=min_cohens_kappa,
        reference_type=args.reference_type,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit(f"calibration FAILED (see {args.output})")


if __name__ == "__main__":
    main()
