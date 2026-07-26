"""
Ground-truth sanity check for the Qwen scoring pipeline in eval_lib.py, run BEFORE
trusting it on OpinionQA (which has no ground-truth answer to check against).

OpinionQA's option-letter logit scoring has a documented failure history (the
fused-"(A"-token bug, raw_coverage collapse on SFT checkpoints -- see CLAUDE.md
Landmines) where the model's chosen_option can be flat wrong even though
everything LOOKS like it ran fine (no crash, probs still sum to 1). Since
OpinionQA has no correct answer, that class of bug is invisible there -- test.py
only checks that the distribution is well-formed (sums to 1, coverage > 0.8), not
that the CHOSEN answer is actually right.

data/evals/sanity_mcq.jsonl fixes that: 24 unambiguous common-sense/arithmetic
4-option questions (e.g. "What is 1 + 1?") with a known-correct letter, balanced
6/6/6/6 across A/B/C/D so a position bias can't masquerade as accuracy. Scored
with the SAME mechanism used for the real eval: eval_lib.score_item (single-item
teacher-forced logit read, argmax over the option-letter tokens) AND
make_variants/score_variant_batch (the batched, order-shuffled path 03_run_eval.py
actually uses) -- both must get these right, in BOTH the original and a shuffled
option order, or the scoring pipeline itself is broken and any OpinionQA drift
number built on top of it is meaningless.

Usage:
    python scripts/test_qwen_sanity.py
"""

import json
from pathlib import Path

from eval_lib import (
    build_letter_token_cache,
    load_model,
    make_variants,
    score_item,
    score_variant_batch,
)

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "evals" / "sanity_mcq.jsonl"
SEED = 42


def load_items():
    return [json.loads(l) for l in open(DATA_PATH)]


def main():
    items = load_items()
    print(f"loaded {len(items)} sanity-check questions "
          f"(answer-letter balance: "
          f"{ {L: sum(1 for it in items if it['answer'] == L) for L in 'ABCD'} })")

    model, tokenizer = load_model()
    letter_cache = build_letter_token_cache(tokenizer)

    # --- single-item path (score_item), original option order as given ---
    print("\n--- score_item (single-item, original order) ---")
    wrong_single = []
    coverages = []
    for it in items:
        s = score_item(model, tokenizer, letter_cache, it)
        coverages.append(s["raw_coverage"])
        got = s["chosen_letter"]
        ok = got == it["answer"]
        print(f"  [{'OK ' if ok else 'FAIL'}] {it['id']}: {it['question'][:60]!r} "
              f"-> got {got}, want {it['answer']} (raw_coverage={s['raw_coverage']:.3f})")
        if not ok:
            wrong_single.append(it["id"])

    acc_single = 1 - len(wrong_single) / len(items)
    print(f"\nscore_item accuracy: {acc_single:.3f} ({len(items) - len(wrong_single)}/{len(items)})")
    print(f"median raw_coverage: {sorted(coverages)[len(coverages) // 2]:.4f}, "
          f"min: {min(coverages):.4f}")

    # --- batched variant path (score_variant_batch), original AND shuffled order ---
    print("\n--- score_variant_batch (batched, original + shuffled order) ---")
    variants = [v for it in items for v in make_variants(it, seed=SEED)]
    results = score_variant_batch(model, tokenizer, letter_cache, variants, lang="en")

    by_id_variant = {(r["id"], r["variant"]): r for r in results}
    wrong_orig, wrong_shuf = [], []
    for it in items:
        want = it["answer"]
        r_orig = by_id_variant[(it["id"], "original")]
        r_shuf = by_id_variant[(it["id"], "shuffled")]
        if r_orig["chosen_option"] != want:
            wrong_orig.append(it["id"])
        if r_shuf["chosen_option"] != want:
            wrong_shuf.append(it["id"])
        flag = "OK " if (r_orig["chosen_option"] == want and r_shuf["chosen_option"] == want) else "FAIL"
        print(f"  [{flag}] {it['id']}: want {want}, "
              f"original->{r_orig['chosen_option']}, shuffled->{r_shuf['chosen_option']}")

    acc_orig = 1 - len(wrong_orig) / len(items)
    acc_shuf = 1 - len(wrong_shuf) / len(items)
    print(f"\nbatched original-order accuracy: {acc_orig:.3f} ({len(items) - len(wrong_orig)}/{len(items)})")
    print(f"batched shuffled-order accuracy: {acc_shuf:.3f} ({len(items) - len(wrong_shuf)}/{len(items)})")

    out = {
        "n_items": len(items),
        "score_item_accuracy": acc_single,
        "score_item_wrong_ids": wrong_single,
        "batched_original_accuracy": acc_orig,
        "batched_shuffled_accuracy": acc_shuf,
        "batched_original_wrong_ids": wrong_orig,
        "batched_shuffled_wrong_ids": wrong_shuf,
        "median_raw_coverage": sorted(coverages)[len(coverages) // 2],
        "min_raw_coverage": min(coverages),
    }
    results_dir = ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "test_qwen_sanity.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote {results_dir / 'test_qwen_sanity.json'}")

    # These are unambiguous common-sense/arithmetic questions -- a competent model
    # should get essentially all of them right in either order. A failure here means
    # the SCORING PIPELINE is broken (wrong token ids, position bias, coverage
    # collapse), not that the questions are hard -- do not weaken this threshold to
    # make it pass.
    assert acc_single >= 0.9, f"score_item accuracy {acc_single:.3f} < 0.9 -- pipeline is broken"
    assert acc_orig >= 0.9, f"batched original-order accuracy {acc_orig:.3f} < 0.9 -- pipeline is broken"
    assert acc_shuf >= 0.9, (f"batched shuffled-order accuracy {acc_shuf:.3f} < 0.9 -- "
                              f"pipeline has a POSITION BIAS: it's reading display position, "
                              f"not the option's actual content")
    assert min(coverages) > 0.5, "some item has raw_coverage < 0.5 -- scoring the distribution tail"
    print("\nALL CHECKS PASSED -- scoring pipeline produces valid, position-invariant choices.")


if __name__ == "__main__":
    main()
