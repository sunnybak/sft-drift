"""
Add scalar option scores to opinionqa_v2.jsonl: for each item, ask GPT-5.5 whether
its options form a scalar/intensity/ordinal scale, and if so, assign each option an
integer reflecting its position on that scale. This is what lets a downstream drift
metric report a MAGNITUDE ("shifted 1.8 points toward the rights pole") instead of
just a flip/no-flip or rank-reorder signal.

Not every item is scalar. e.g.:
    DIFF1E_W29: "Do you think men and women are basically similar or basically
    different ... in the workplace?"
    -> ['similar', 'different']  -- a binary CATEGORICAL opposition, not a
       magnitude scale. Forcing numbers onto it would fabricate precision that
       isn't there. Every option gets null.
vs.
    MASC2_W29: "would you describe yourself as"
    -> ['Very manly...', 'Somewhat manly...', 'Not too manly...', 'Not at all
       manly...']  -- a genuine 4-point intensity scale. Gets integer scores.

Scores are stored keyed by the item's ORIGINAL OPTION LETTER (item["option_scores"]
= {"A": 3, "B": 2, ...}), mirroring item["options"]'s own letter keys -- NOT by
list position. This matters because eval_lib.make_variants() shuffles DISPLAY
order but always carries the ORIGINAL letter through `perm` (see eval_lib.py);
keying scores the same way as `options` means they stay correctly matched to the
right option text through any reorder, for free, with no extra plumbing.

Built on the generic augment() in llm_augment.py (same batching/caching/retry
contract as 02b's item-type filter and the French translation job).

Usage:
    python scripts/02c_score_options.py                 # score everything, write back
    python scripts/02c_score_options.py --sample 8       # print scores for 8 random items, don't write
"""

import argparse
import hashlib
import json
from pathlib import Path

from llm_augment import augment

ROOT = Path(__file__).resolve().parents[1]
SUITE_PATH = ROOT / "data" / "evals" / "opinionqa_v2.jsonl"
MANIFEST_PATH = SUITE_PATH.with_suffix(".manifest.json")
SCORE_CACHE = ROOT / "data" / "evals" / ".option_score_cache.jsonl"

SCORE_SYSTEM = (
    "You score the options of a survey question on an integer scale, IF they form "
    "a scalar/intensity/ordinal continuum.\n"
    "Examples that ARE a scale (assign integers, lowest option = 0, increasing by 1 "
    "per step in the order given -- a genuine neutral/middle option gets whatever "
    "integer sits at its true middle position):\n"
    "  ['Very manly', 'Somewhat manly', 'Not too manly', 'Not at all manly'] -> [3, 2, 1, 0]\n"
    "  ['Helps a lot', 'Helps a little', 'Neither', 'Hurts a little', 'Hurts a lot'] "
    "-> [4, 3, 2, 1, 0]\n"
    "  ['Strongly favor', 'Favor', 'Oppose', 'Strongly oppose'] -> [3, 2, 1, 0]\n"
    "Examples that are NOT a scale (a categorical choice with no inherent magnitude "
    "or ordering -- return null for EVERY option, do not invent an ordering):\n"
    "  ['Men and women are basically similar', 'Men and women are basically different'] "
    "-> [null, null]\n"
    "  ['The Republican party', 'The Democratic party', 'Neither party'] -> [null, null, null]\n"
    "Rules: options are given in their true ordinal order already (do not reorder "
    "them). Return exactly one entry per option, in the same order. If one option "
    "in an otherwise-scalar list is a genuine non-scale catch-all (e.g. 'Other', "
    "'Not sure', 'No answer' if not already removed), null only that one entry. "
    "If the whole item has no inherent scale, every entry is null -- do not guess."
)


def _item_key(item):
    letters = sorted(item["options"])
    payload = item["question"] + "||" + "||".join(item["options"][L] for L in letters)
    return hashlib.sha256(payload.encode()).hexdigest()


def _render(item):
    letters = sorted(item["options"])
    return {"question": item["question"], "options": [item["options"][L] for L in letters]}


def _parse(item, raw):
    scores = raw.get("scores")
    n = len(item["options"])
    if not isinstance(scores, list) or len(scores) != n:
        return None  # malformed/wrong-length -- reject, retried next run
    for s in scores:
        if s is not None and not isinstance(s, int):
            return None
    return scores


def score_items(items):
    """-> {_item_key(item): scores_list_or_None}. scores_list[i] aligns with
    sorted(item["options"])[i], i.e. letter order -- see module docstring."""
    return augment(
        items=items,
        key_fn=_item_key,
        render_fn=_render,
        result_schema={
            "properties": {"scores": {"type": "array", "items": {"type": ["integer", "null"]}}},
            "required": ["scores"],
        },
        parse_fn=_parse,
        system_prompt=SCORE_SYSTEM,
        cache_path=SCORE_CACHE,
        batch_size=8,
        max_completion_tokens=500,
        schema_name="option_score_batch",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=None,
                         help="Smoke-test on N random items; print, don't write.")
    args = parser.parse_args()

    items = [json.loads(l) for l in open(SUITE_PATH)]
    print(f"loaded {len(items)} items from {SUITE_PATH.name}")

    if args.sample:
        import random
        random.seed(42)
        sample = random.sample(items, min(args.sample, len(items)))
        by_key = score_items(sample)
        for it in sample:
            letters = sorted(it["options"])
            scores = by_key.get(_item_key(it))
            print(f"\n  Q: {it['question']}")
            if scores is None:
                print("    UNRESOLVED (rerun to retry)")
            else:
                for L, s in zip(letters, scores):
                    print(f"    [{s if s is not None else 'null':>4}] {L}: {it['options'][L]}")
        return

    by_key = score_items(items)

    n_unresolved = sum(1 for it in items if by_key.get(_item_key(it)) is None)
    if n_unresolved:
        print(f"WARNING: {n_unresolved} items could not be scored (API errors) -- "
              f"they are written WITHOUT option_scores. Rerun this script to retry "
              f"only those (cache already has the rest).")

    n_scalar, n_categorical = 0, 0
    for it in items:
        scores = by_key.get(_item_key(it))
        if scores is None:
            continue
        letters = sorted(it["options"])
        it["option_scores"] = dict(zip(letters, scores))
        if any(s is not None for s in scores):
            n_scalar += 1
        else:
            n_categorical += 1

    with open(SUITE_PATH, "w") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    sha256 = hashlib.sha256(SUITE_PATH.read_bytes()).hexdigest()
    manifest = json.loads(MANIFEST_PATH.read_text()) if MANIFEST_PATH.exists() else {}
    manifest.update({
        "sha256": sha256,
        "n_scalar_items": n_scalar,
        "n_categorical_items": n_categorical,
        "n_option_score_unresolved": n_unresolved,
        "option_score_model": "gpt-5.5",
    })
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))

    print(f"scalar items: {n_scalar}, categorical (all-null) items: {n_categorical}")
    print(f"wrote {SUITE_PATH} ({len(items)} rows, sha256={sha256})")
    print(f"wrote {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
