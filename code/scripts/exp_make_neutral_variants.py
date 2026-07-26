"""
[side-quest] Build two size-matched neutral SFT corpora to test whether the
neutral arm's OpinionQA drift is driven by martial/violence CONTENT (Star Wars /
Harry Potter / Marvel argument bodies are full of war, weapons, empire, killing)
rather than by "any SFT".

The original neutral corpus (04c) filtered on the debate CONCLUSION (title) only,
so combat-fiction franchises passed as "off-topic" while their argument BODIES
carry martial language at ~11 tokens/1k (29% of the guns corpora's density),
78% of it from Star Wars alone.

Emits two corpora at a matched size (N = size of the clean pool):
  exp_neutral_clean.jsonl  -- combat-fiction topics dropped + per-body martial
                              filter; residual martial density ~0.17/1k
  exp_neutral_dirty.jsonl  -- N examples sampled from the ORIGINAL neutral pool
                              (same seed), i.e. the confounded corpus at matched N

Training both with the same recipe isolates CONTENT from corpus size: if clean
drifts less than dirty at the same N, the neutral drift was a martial-content
confound, not a generic any-SFT effect.

Usage:
    python scripts/exp_make_neutral_variants.py
"""

import hashlib
import json
import random
import re
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "sft"
SEED = 42

sys.path.insert(0, str(ROOT / "scripts"))
sft04 = import_module("04_prepare_sft_data")
prep = import_module("04c_prepare_neutral_sft_data")

# Combat-fiction franchises: drop the whole topic (bodies are inherently martial).
FICTION_COMBAT = re.compile(
    r"\b(star\s?wars|harry\s?potter|marvel|dc\b|superhero|avengers|batman|superman)\b", re.I)
# Per-body martial/violence filter for the surviving mundane topics.
MARTIAL_BODY = re.compile(
    r"\b(war|wars|warfare|military|militia|army|armies|soldier|soldiers|troop|troops|"
    r"battle|battles|combat|weapon|weapons|gun|guns|rifle|rifles|firearm|pistol|blaster|"
    r"bomb|bombs|missile|grenade|kill|kills|killed|killing|murder|violence|violent|shoot|"
    r"shooting|shot|armed|invasion|genocide|massacre|terrorism|terrorist|nuclear|artillery|"
    r"sword|swords|lightsaber|stormtrooper|empire|rebellion)\b", re.I)


def scan():
    path = sft04.resolve_argsme()
    oqa_grams = sft04.load_opinionqa_ngrams()
    clean, dirty, seen_c, seen_d = [], [], set(), set()
    for line in open(path):
        x = json.loads(line)
        c = x["conclusion"]
        if not prep.is_neutral_conclusion(c):
            continue
        for pr in x["premises"]:
            text = sft04.clean_text(pr["text"])
            if len(text) < sft04.MIN_CHARS or sft04.NOISE_RE.search(text) or not sft04.is_english(text):
                continue
            if sft04.has_contamination(text, oqa_grams):
                continue
            key = hashlib.sha256(text.lower().encode()).hexdigest()
            rec = {"text": text, "arg_id": x["id"], "conclusion": c}
            # dirty pool = original 04c behavior (all neutral-conclusion bodies)
            if key not in seen_d:
                seen_d.add(key)
                dirty.append(rec)
            # clean pool = drop combat-fiction topics + martial bodies
            if FICTION_COMBAT.search(c) or MARTIAL_BODY.search(text):
                continue
            if key not in seen_c:
                seen_c.add(key)
                clean.append(rec)
    return clean, dirty


def to_rows(cands):
    return [
        {"messages": [
            {"role": "user", "content": sft04.prompt_for(c["arg_id"], c["conclusion"])},
            {"role": "assistant", "content": c["text"]},
        ], "meta": {"arg_id": c["arg_id"], "conclusion": c["conclusion"], "pole": "neutral"}}
        for c in cands
    ]


def main():
    clean, dirty = scan()
    n = len(clean)
    rng = random.Random(SEED)
    rng.shuffle(clean)
    rng.shuffle(dirty)
    dirty_matched = dirty[:n]

    for tag, cands in (("clean", clean), ("dirty", dirty_matched)):
        rows = to_rows(cands)
        out = OUT_DIR / f"exp_neutral_{tag}.jsonl"
        out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
        print(f"exp_neutral_{tag}: {len(rows)} samples -> {out.name}")

    print(f"\nsize-matched N = {n}")


if __name__ == "__main__":
    main()
