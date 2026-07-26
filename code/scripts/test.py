"""
Pipeline smoke test, run BEFORE the full OpinionQA baseline eval.

Loads Qwen3-4B-Instruct once, samples 100 random questions from
data/evals/opinionqa_v1.jsonl, scores them with eval_lib.score_item, and repeats
with several different random samples. Reports:
  1. whether the per-question option distribution is normalized (probs sum to 1,
     opinion_score always in [0, 1]) AND has adequate raw coverage (the option
     tokens actually carry the model's answer mass -- catches the fused-token bug)
  2. how much the aggregate opinion_score varies run-to-run from subsampling 100
     questions out of ~1500 (sampling noise, not model stochasticity -- scoring is
     a deterministic forward pass)

Outputs:
  results/test_eval_variance.json  -- per-repeat aggregates + repeat-0 per-item scores
  results/test_eval_variance.png   -- histogram + variance-across-repeats plot
"""

import json
import random
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from eval_lib import build_letter_token_cache, load_model, score_item

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "evals" / "opinionqa_v1.jsonl"
RESULTS_DIR = ROOT / "results"

SAMPLE_SIZE = 100
N_REPEATS = 5
SEEDS = list(range(N_REPEATS))


def load_items():
    with open(DATA_PATH) as f:
        return [json.loads(line) for line in f]


def main():
    items = load_items()
    print(f"loaded {len(items)} OpinionQA questions")

    model, tokenizer = load_model()
    letter_cache = build_letter_token_cache(tokenizer)

    repeat_aggregates = []
    repeat_0_scores = None
    all_probs_sums = []
    all_coverages = []

    for seed in SEEDS:
        sample = random.Random(seed).sample(items, SAMPLE_SIZE)
        scores = [score_item(model, tokenizer, letter_cache, it) for it in sample]

        opinion_scores = [s["opinion_score"] for s in scores]
        confidences = [s["confidence"] for s in scores]
        entropy_norms = [s["entropy_norm"] for s in scores]
        all_probs_sums.extend(sum(s["probs"].values()) for s in scores)
        all_coverages.extend(s["raw_coverage"] for s in scores)

        agg = {
            "seed": seed,
            "mean_opinion_score": statistics.mean(opinion_scores),
            "std_opinion_score": statistics.pstdev(opinion_scores),
            "min_opinion_score": min(opinion_scores),
            "max_opinion_score": max(opinion_scores),
            "mean_confidence": statistics.mean(confidences),
            "mean_entropy_norm": statistics.mean(entropy_norms),
        }
        repeat_aggregates.append(agg)
        print(
            f"seed={seed} mean_opinion_score={agg['mean_opinion_score']:.4f} "
            f"std={agg['std_opinion_score']:.4f} mean_confidence={agg['mean_confidence']:.4f}"
        )

        if seed == SEEDS[0]:
            repeat_0_scores = scores

    # --- normalization check ---
    max_dev = max(abs(p - 1.0) for p in all_probs_sums)
    print(f"\nmax |probs_sum - 1.0| across {len(all_probs_sums)} scored items: {max_dev:.2e}")
    assert max_dev < 1e-3, "option probabilities do not sum to 1 -- scoring is not normalized"

    # raw coverage: un-renormalized mass the option tokens get from the full-vocab
    # softmax. Low => scoring the distribution tail; renormalized probs meaningless.
    med_cov = statistics.median(all_coverages)
    print(f"raw option-token coverage: median {med_cov:.4f}, min {min(all_coverages):.4f}, "
          f"frac < 0.5: {sum(c < 0.5 for c in all_coverages)/len(all_coverages):.3f}")
    assert med_cov > 0.8, "median raw coverage < 0.8 -- scoring surface form mismatches the model's answer format"

    global_min = min(a["min_opinion_score"] for a in repeat_aggregates)
    global_max = max(a["max_opinion_score"] for a in repeat_aggregates)
    print(f"opinion_score observed range across all repeats: [{global_min:.4f}, {global_max:.4f}]")
    assert 0.0 - 1e-6 <= global_min and global_max <= 1.0 + 1e-6, "opinion_score escaped [0, 1]"

    # --- variance across repeats (sampling noise on the aggregate) ---
    repeat_means = [a["mean_opinion_score"] for a in repeat_aggregates]
    variance_of_mean = statistics.pstdev(repeat_means)
    print(
        f"\nacross {N_REPEATS} independent 100-question samples: "
        f"mean_opinion_score = {statistics.mean(repeat_means):.4f} +/- {variance_of_mean:.4f} (std)"
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "sample_size": SAMPLE_SIZE,
        "n_repeats": N_REPEATS,
        "seeds": SEEDS,
        "repeat_aggregates": repeat_aggregates,
        "variance_of_repeat_mean_opinion_score": variance_of_mean,
        "max_abs_probs_sum_deviation": max_dev,
        "median_raw_coverage": med_cov,
        "global_opinion_score_range": [global_min, global_max],
    }
    (RESULTS_DIR / "test_eval_variance.json").write_text(json.dumps(out, indent=2))

    # --- plot ---
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    axes[0].hist([s["opinion_score"] for s in repeat_0_scores], bins=20, range=(0, 1), color="#4C72B0")
    axes[0].set_title(f"opinion_score distribution (seed={SEEDS[0]}, n={SAMPLE_SIZE})")
    axes[0].set_xlabel("opinion_score [0,1]")
    axes[0].set_ylabel("count")

    means = [a["mean_opinion_score"] for a in repeat_aggregates]
    stds = [a["std_opinion_score"] for a in repeat_aggregates]
    axes[1].errorbar(SEEDS, means, yerr=stds, fmt="o-", capsize=4, color="#DD8452")
    axes[1].axhline(statistics.mean(means), linestyle="--", color="gray", linewidth=1)
    axes[1].set_title(f"mean opinion_score per repeat (across-repeat std={variance_of_mean:.4f})")
    axes[1].set_xlabel("repeat (seed)")
    axes[1].set_ylabel("mean opinion_score (+/- within-sample std)")
    axes[1].set_xticks(SEEDS)

    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "test_eval_variance.png", dpi=150)
    print(f"\nwrote {RESULTS_DIR / 'test_eval_variance.json'}")
    print(f"wrote {RESULTS_DIR / 'test_eval_variance.png'}")


if __name__ == "__main__":
    main()
