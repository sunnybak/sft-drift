"""Multi-checkpoint TracIn: sum the per-document gradient dots along the saved path.

`scripts/run_attribution.py` computes, at ONE checkpoint, four per-document scores against
the frozen belief-suite query; its `tracin` is the single-checkpoint first-order
approximation, and `attrib_mix_v4` measured that approximation tying a word-count baseline
(rho +0.26) and ranking the null corpus first. TracIn as published (Pruthi et al. 2020) is
the SUM over checkpoints along the optimization path, weighted by the learning rate at
each step. This script computes that sum from per-checkpoint outputs that already exist on
disk -- it runs no model, so a reading can never disagree with the artifacts it reads.

    uv run python scripts/run_attribution.py --run-id attrib_mix_v4_path \
        --polarity positive --checkpoint checkpoint-3        # ... once per path point
    uv run python scripts/sum_tracin_path.py --run-id attrib_mix_v4_path \
        --polarity positive --steps 3,6,9,12,15,18,21,24

Registered predictions live in `configs/run/attrib_mix_v4_path.yaml` (P1: the path-sum
recovers the causal ordering; P2: every term carries the same per-token length artifact,
so the sum inherits it). The deciding read is Spearman rho of the per-source means against
the measured dB ladder, the rank of `ms0` (null by construction), and NEG-LENGTH beside
them -- the same conventions as `run_attribution.summarise`, imported from there so the
two scripts cannot drift apart.

Two sums are reported:
  - `tracin_path_lr`: lr-weighted (the estimator as published). The frozen schedule is
    linear warmup for int(0.03*total) steps then linear decay, reconstructed here from
    the run's train_summary.json; weighting uses lr at each SAVED step, which is a
    quadrature approximation of the per-step sum and is stated as such.
  - `tracin_path_flat`: unweighted. Reported so the verdict cannot hinge on the lr model.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_attribution import GROUND_TRUTH_DB, SOURCE_ORDER, _spearman  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "data" / "results" / "factory_farming"
CHECKPOINTS_DIR = Path(__file__).resolve().parents[1] / "data" / "checkpoints" / "factory_farming"


def lr_at(step: int, total_steps: int, peak_lr: float, warmup_ratio: float = 0.03) -> float:
    warmup = int(warmup_ratio * total_steps)
    if step <= warmup:
        return peak_lr * step / max(warmup, 1)
    return peak_lr * (total_steps - step) / max(total_steps - warmup, 1)


def load_rows(run_id: str, polarity: str, step: int) -> list[dict]:
    path = RESULTS_DIR / run_id / f"attribution_{polarity}_checkpoint-{step}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"no attribution output at {path}; run run_attribution.py first")
    return [json.loads(line) for line in path.read_text().splitlines()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default="attrib_mix_v4_path")
    parser.add_argument("--polarity", choices=["positive", "negative"], required=True)
    parser.add_argument("--steps", required=True,
                        help="comma-separated saved steps forming the path, e.g. 3,6,...,24")
    args = parser.parse_args()
    steps = sorted(int(s) for s in args.steps.split(","))

    summary_path = (CHECKPOINTS_DIR / args.run_id / args.polarity / "train_summary.json")
    train_summary = json.loads(summary_path.read_text())
    total_steps = train_summary["global_steps"]
    peak_lr = train_summary["learning_rate"]

    per_step_rows = {n: load_rows(args.run_id, args.polarity, n) for n in steps}
    base = per_step_rows[steps[0]]
    for n, rows in per_step_rows.items():
        if [r["index"] for r in rows] != [r["index"] for r in base]:
            raise RuntimeError(f"document set at step {n} does not align with step {steps[0]}")

    docs: list[dict] = []
    for i, row in enumerate(base):
        flat = sum(per_step_rows[n][i]["tracin"] for n in steps)
        weighted = sum(per_step_rows[n][i]["tracin"] * lr_at(n, total_steps, peak_lr)
                       for n in steps)
        docs.append({"index": row["index"], "source": row["source"],
                     "n_words": row["n_words"],
                     "tracin_path_flat": flat, "tracin_path_lr": weighted})

    by_source: dict[str, list[dict]] = defaultdict(list)
    for d in docs:
        by_source[d["source"]].append(d)
    sources = [s for s in SOURCE_ORDER if s in by_source]
    truth = [GROUND_TRUTH_DB[s] for s in sources]

    out: dict = {"run_id": args.run_id, "polarity": args.polarity, "path_steps": steps,
                 "n_documents": len(docs), "per_source": {}, "methods": {}}
    for s in sources:
        rows = by_source[s]
        out["per_source"][s] = {
            "n": len(rows), "ground_truth_db": GROUND_TRUTH_DB[s],
            "median_words": statistics.median(r["n_words"] for r in rows),
            "tracin_path_flat": statistics.fmean(r["tracin_path_flat"] for r in rows),
            "tracin_path_lr": statistics.fmean(r["tracin_path_lr"] for r in rows),
        }

    neg_len = {s: -statistics.fmean(r["n_words"] for r in by_source[s]) for s in sources}
    out["neg_length_spearman"] = _spearman([neg_len[s] for s in sources], truth)

    print(f"\n{'=' * 92}")
    print(f"  Multi-checkpoint TracIn -- {args.run_id}/{args.polarity}, path {steps}")
    print(f"{'=' * 92}")
    print(f"  {'source':6s} {'true dB':>8s} {'med words':>10s} {'path (lr-wt)':>14s} {'path (flat)':>13s}")
    for s in sources:
        p = out["per_source"][s]
        print(f"  {s:6s} {p['ground_truth_db']:8.3f} {p['median_words']:10.0f} "
              f"{p['tracin_path_lr']:14.5f} {p['tracin_path_flat']:13.2f}")
    for method in ("tracin_path_lr", "tracin_path_flat"):
        vals = [out["per_source"][s][method] for s in sources]
        rho = _spearman(vals, truth)
        ranking = sorted(sources, key=lambda s: out["per_source"][s][method], reverse=True)
        out["methods"][method] = {"spearman_vs_ground_truth": rho, "ranking": ranking}
        print(f"\n  {method}: rho vs ground truth = {rho:+.2f}   ranking: {' > '.join(ranking)}")
    print(f"  NEG-LENGTH baseline: rho = {out['neg_length_spearman']:+.2f}")

    # The per-checkpoint diagnostic: does ANY single point on the path escape the artifact?
    print(f"\n  per-checkpoint single-point tracin rho (diagnostic):")
    out["per_checkpoint_rho"] = {}
    for n in steps:
        means = {s: statistics.fmean(r["tracin"] for r in per_step_rows[n]
                                     if r["source"] == s) for s in sources}
        rho_n = _spearman([means[s] for s in sources], truth)
        out["per_checkpoint_rho"][n] = rho_n
        print(f"    step {n:>3d}: rho = {rho_n:+.2f}")

    out_path = RESULTS_DIR / args.run_id / f"attribution_pathsum_{args.polarity}.json"
    out_path.write_text(json.dumps(out, indent=1))
    print(f"\n  wrote {out_path}")


if __name__ == "__main__":
    main()
