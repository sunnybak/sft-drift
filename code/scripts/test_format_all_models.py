"""
Output-format compliance check (test.py's raw_coverage/normalization checks),
extended across the base model AND every SFT'd adapter, both sizes.

test.py only ever checked the base model, on the pre-baseline suite, before
trusting the real eval. This answers a narrower question: after SFT, does the
model still emit its answer in the expected surface form (the fused "(A" token)
well enough for the option-letter logit read to be meaningful? Per the CLAUDE.md
landmine, a fine-tuned checkpoint is EXPECTED to fail this under the plain path
(raw_coverage collapses toward ~0 once the model starts writing prose instead of
a bare letter) -- that's what force_answer_prefix exists to fix. This script
checks BOTH paths per model so the collapse-and-recovery is visible directly,
rather than assumed.

Not a pass/fail gate (no asserts) -- reports median/min raw_coverage and the
probs-sum / opinion_score-range invariants for each (model, adapter, path).

Usage:
    python scripts/test_format_all_models.py [--sample-size 100]
"""

import argparse
import json
import random
import statistics
from pathlib import Path

from eval_lib import (
    FORCED_ANSWER_SUFFIX,
    build_bare_letter_token_cache,
    build_letter_token_cache,
    build_prompt,
    load_model,
    score_item,
)

ROOT = Path(__file__).resolve().parents[1]
SUITE_PATH = ROOT / "data" / "evals" / "opinionqa_v2.jsonl"
CKPT = ROOT / "checkpoints"
SEED = 0

MODEL_SIZES = [
    ("qwen3-4b", "unsloth/Qwen3-4B-Instruct-2507"),
    ("qwen3-8b", "unsloth/Qwen3-8B"),
]
ARMS = ["rights", "control", "mix80r20c", "mix50r50c", "mix20r80c", "neutral"]


def arm_adapter(arm, model_tag):
    if arm == "neutral":
        d = CKPT / f"{model_tag}-neutral-v1" / "final"
    else:
        d = CKPT / f"{model_tag}-guns-{arm}-v1" / "final"
    return str(d) if d.exists() else None


def score_forced(model, tokenizer, bare_letter_cache, item):
    """Forced-answer-prefix variant of score_item: reuses eval_lib's real
    FORCED_ANSWER_SUFFIX + bare-letter cache (the same path 03_run_eval.py takes
    for SFT checkpoints via score_variant_batch_forced), just single-item."""
    import torch

    prompt, letters = build_prompt(tokenizer, item)
    prompt = prompt + FORCED_ANSWER_SUFFIX
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        logits = model(**inputs).logits[0, -1, :]
    log_probs_full = torch.log_softmax(logits.float(), dim=-1)
    letter_logprobs = torch.tensor([log_probs_full[bare_letter_cache[L]].item() for L in letters])
    option_probs = torch.softmax(letter_logprobs, dim=-1)
    raw_coverage = float(letter_logprobs.exp().sum().item())
    n = len(letters)
    positions = torch.linspace(0, 1, n) if n > 1 else torch.tensor([0.5])
    opinion_score = float((option_probs * positions).sum().item())
    return {"raw_coverage": raw_coverage, "opinion_score": opinion_score,
            "probs_sum": float(option_probs.sum().item())}


def run_one(label, model_name, adapter_path, sample):
    model, tokenizer = load_model(model_name, adapter_path=adapter_path)
    letter_cache = build_letter_token_cache(tokenizer)
    bare_letter_cache = build_bare_letter_token_cache(tokenizer)

    plain = [score_item(model, tokenizer, letter_cache, it) for it in sample]
    forced = [score_forced(model, tokenizer, bare_letter_cache, it) for it in sample]

    plain_cov = [s["raw_coverage"] for s in plain]
    plain_probs_sum = [sum(s["probs"].values()) for s in plain]
    plain_range = (min(s["opinion_score"] for s in plain), max(s["opinion_score"] for s in plain))

    forced_cov = [s["raw_coverage"] for s in forced]
    forced_probs_sum = [s["probs_sum"] for s in forced]
    forced_range = (min(s["opinion_score"] for s in forced), max(s["opinion_score"] for s in forced))

    del model
    import torch
    torch.cuda.empty_cache()

    return {
        "label": label,
        "plain": {
            "median_raw_coverage": statistics.median(plain_cov),
            "min_raw_coverage": min(plain_cov),
            "max_abs_probs_sum_deviation": max(abs(p - 1.0) for p in plain_probs_sum),
            "opinion_score_range": plain_range,
            "respects_format": statistics.median(plain_cov) > 0.8,
        },
        "forced_prefix": {
            "median_raw_coverage": statistics.median(forced_cov),
            "min_raw_coverage": min(forced_cov),
            "max_abs_probs_sum_deviation": max(abs(p - 1.0) for p in forced_probs_sum),
            "opinion_score_range": forced_range,
            "respects_format": statistics.median(forced_cov) > 0.8,
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-size", type=int, default=100)
    args = ap.parse_args()

    items = [json.loads(l) for l in open(SUITE_PATH)]
    sample = random.Random(SEED).sample(items, args.sample_size)
    print(f"loaded {len(items)} items from {SUITE_PATH.name}, sampling {len(sample)} (seed={SEED})")

    results = []
    for tag, model_name in MODEL_SIZES:
        print(f"\n===== {tag} =====")
        r = run_one(f"{tag}-base", model_name, None, sample)
        results.append(r)
        print(f"  base: plain median_cov={r['plain']['median_raw_coverage']:.4f} "
              f"(format ok={r['plain']['respects_format']})  "
              f"forced median_cov={r['forced_prefix']['median_raw_coverage']:.4f} "
              f"(format ok={r['forced_prefix']['respects_format']})")

        for arm in ARMS:
            adapter = arm_adapter(arm, tag)
            if adapter is None:
                print(f"  {arm}: SKIP (no final adapter found)")
                continue
            r = run_one(f"{tag}-{arm}-final", model_name, adapter, sample)
            results.append(r)
            print(f"  {arm}: plain median_cov={r['plain']['median_raw_coverage']:.4f} "
                  f"(format ok={r['plain']['respects_format']})  "
                  f"forced median_cov={r['forced_prefix']['median_raw_coverage']:.4f} "
                  f"(format ok={r['forced_prefix']['respects_format']})")

    out_path = ROOT / "results" / "test_format_all_models.json"
    out_path.write_text(json.dumps({"sample_size": args.sample_size, "seed": SEED, "results": results}, indent=2))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
