"""
Build the 4th SFT experiment's corpus: args.me debate arguments on topics that are
EXPLICITLY NON-POLITICAL (pizza toppings, cats vs dogs, book vs movie, etc.), run
through the exact same quality-filter pipeline as the guns corpora in
04_prepare_sft_data.py, but with NO rights/control polarity (there isn't one) --
a single "neutral" arm.

Why this arm exists: the guns_rights/guns_control experiment shows a DIFFERENCE
between two ideologically-loaded corpora, but doesn't by itself prove that
argumentative/persuasive SFT content on an UNRELATED topic leaves OpinionQA's
guns bucket alone. This is that control -- same source (args.me), same debate-
argument register, same filter pipeline, same chat-template format, comparable
corpus size, but a topic axis with no plausible connection to guns (or to any
OpinionQA topic at all, checked explicitly below). If training on THIS corpus
still shifts guns-topic answers, the guns_rights/guns_control effect isn't about
gun-specific content -- it's a generic "any SFT perturbs OpinionQA" artifact.

Topic selection: NEUTRAL_RE matches debate.org-style trivial/lifestyle
conclusions (pizza, cats vs dogs, book vs movie, ...). Every match is ALSO
checked against 02_download_opinionqa.assign_topic() (the same keyword bucketing
used to tag OpinionQA questions) and rejected if it lands in any real topic
bucket (not "other") -- this guards against a neutral-sounding keyword
accidentally overlapping an OpinionQA topic domain (e.g. "technology").

No GPT-5.5 classification step here (there's no polarity to label), so this
script costs nothing to run beyond the free args.me scan already needed for 04.

Usage:
    python scripts/04c_prepare_neutral_sft_data.py
"""

import hashlib
import json
import random
import re
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "sft"
SEED_TAG = "neutral_v1"
SEED = 42
TARGET = 1200

sft04 = import_module("04_prepare_sft_data")
oqa = import_module("02_download_opinionqa")

# Deliberately trivial/lifestyle debate.org-style topics -- no plausible
# ideological axis, chosen to have zero overlap with any OpinionQA topic bucket.
NEUTRAL_RE = re.compile(
    r"\b("
    r"pizza|pineapple|hot dogs?|cereal|coffee|tea|"
    r"coke|pepsi|soda|"
    r"cats? (vs\.?|versus|or) dogs?|cat person|dog person|"
    r"android (vs\.?|versus) i-?os|i-?phone (vs\.?|versus) android|"
    r"xbox|play\s?station|nintendo|pc (vs\.?|versus) console|"
    r"harry potter|star wars|marvel (vs\.?|versus) dc|"
    r"book (vs\.?|versus) (the )?movie|movie (vs\.?|versus) (the )?book|"
    r"beach (vs\.?|versus) mountains?|summer (vs\.?|versus) winter|"
    r"morning person|night owl|"
    r"best programming language|vim (vs\.?|versus) emacs"
    r")\b",
    re.I,
)


def is_neutral_conclusion(conclusion):
    if not NEUTRAL_RE.search(conclusion):
        return False
    if sft04.GUN_RE.search(conclusion):
        return False  # belt-and-suspenders; shouldn't fire given the keyword list above
    if oqa.assign_topic(conclusion, "") != "other":
        return False  # overlaps a real OpinionQA topic bucket -- exclude
    return True


def main():
    path = sft04.resolve_argsme()
    print(f"args.me corpus: {path}")

    oqa_grams = sft04.load_opinionqa_ngrams()
    print(f"OpinionQA 8-grams for contamination check: {len(oqa_grams)}")

    candidates = []
    seen = set()
    stats = {"neutral_premises": 0, "too_short": 0, "noise": 0, "non_english": 0,
             "contaminated": 0, "dup": 0, "kept": 0}
    conclusions_seen = set()

    for line in open(path):
        x = json.loads(line)
        conclusion = x["conclusion"]
        if not is_neutral_conclusion(conclusion):
            continue
        conclusions_seen.add(conclusion)
        for pr in x["premises"]:
            stats["neutral_premises"] += 1
            text = sft04.clean_text(pr["text"])
            if len(text) < sft04.MIN_CHARS:
                stats["too_short"] += 1
                continue
            if sft04.NOISE_RE.search(text):
                stats["noise"] += 1
                continue
            if not sft04.is_english(text):
                stats["non_english"] += 1
                continue
            key = hashlib.sha256(text.lower().encode()).hexdigest()
            if key in seen:
                stats["dup"] += 1
                continue
            if sft04.has_contamination(text, oqa_grams):
                stats["contaminated"] += 1
                continue
            seen.add(key)
            candidates.append({"text": text, "arg_id": x["id"], "conclusion": conclusion})

    stats["kept"] = len(candidates)
    print(f"\ndistinct neutral conclusions matched: {len(conclusions_seen)}")
    for c in sorted(conclusions_seen):
        print(f"  - {c}")
    print("\nfilter stats:", json.dumps(stats, indent=2))

    if len(candidates) < TARGET:
        print(f"WARNING: only {len(candidates)} candidates available, "
              f"below target {TARGET} -- using all of them. Consider widening "
              f"NEUTRAL_RE if you need the full {TARGET} for step-comparability "
              f"with the mixture corpora.")

    rng = random.Random(SEED)
    rng.shuffle(candidates)
    candidates = candidates[:TARGET]

    rows = [
        {
            "messages": [
                {"role": "user", "content": sft04.prompt_for(c["arg_id"], c["conclusion"])},
                {"role": "assistant", "content": c["text"]},
            ],
            "meta": {"arg_id": c["arg_id"], "conclusion": c["conclusion"], "pole": "neutral"},
        }
        for c in candidates
    ]

    out_path = OUT_DIR / "neutral_v1.jsonl"
    with open(out_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained("unsloth/Qwen3-4B-Instruct-2507")
    n_tok = sum(len(tok(r["messages"][1]["content"]).input_ids) for r in rows)

    manifest = {
        "source": "webis/args_me", "topic": "neutral (non-political)", "seed_tag": SEED_TAG,
        "seed": SEED, "target": TARGET, "distinct_conclusions": sorted(conclusions_seen),
        "filter_stats": stats, "n_samples": len(rows), "assistant_tokens": n_tok,
        "file": out_path.name,
    }
    (OUT_DIR / f"{SEED_TAG}.manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"\n  neutral: {len(rows):4d} samples, {n_tok:,} assistant tokens -> {out_path.name}")
    print(f"wrote {OUT_DIR / f'{SEED_TAG}.manifest.json'}")


if __name__ == "__main__":
    main()
