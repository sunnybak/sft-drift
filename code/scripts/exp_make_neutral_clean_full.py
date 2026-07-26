"""
[side-quest] Full-size CLEAN neutral SFT corpus (register-matched to the guns arms).

Expands the neutral arm to ~rights-arm size (1346) from args.me while keeping it:
  - argumentative/persuasive (same source + register + prompt template as the
    guns corpora -- this is the point: it holds REGISTER constant so the arm
    isolates ideological content, not opinionated style);
  - non-ideological/non-political (broad mundane-topic whitelist + a political/
    ideological conclusion blocklist);
  - free of martial/violence content (per-body filter), which an audit showed the
    original narrow neutral corpus was NOT (Star Wars et al.).

Mundane topics: sports, music genres, video games, food/drink, movies/books,
consumer tech, lifestyle preferences -- matched with WORD BOUNDARIES (the earlier
audit's substring counts were inflated by "cat" in "category" etc.).

Usage:
    python scripts/exp_make_neutral_clean_full.py --target 1346
"""

import argparse
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
oqa = import_module("02_download_opinionqa")

MUNDANE = re.compile(r"\b(" + "|".join([
    r"pizza", r"pineapple", r"burger", r"pasta", r"chocolate", r"ice ?cream", r"cake", r"pie",
    r"coffee", r"tea", r"coke", r"pepsi", r"soda", r"cereal", r"hot ?dogs?", r"fast food",
    r"cats?", r"dogs?", r"pets?",
    r"football", r"soccer", r"basketball", r"baseball", r"hockey", r"tennis", r"sports?",
    r"messi", r"ronaldo", r"lebron", r"jordan", r"chess",
    r"video ?games?", r"xbox", r"play ?station", r"nintendo", r"pc gaming", r"consoles?",
    r"music", r"rap", r"hip ?hop", r"rock music", r"pop music", r"jazz", r"country music",
    r"movies?", r"books?", r"anime", r"disney", r"cartoons?",
    r"android", r"i-?phone", r"i-?os", r"apple", r"samsung", r"windows", r"mac",
    r"summer", r"winter", r"spring", r"autumn", r"beach", r"mountains?",
    r"school uniforms?", r"homework", r"social media", r"facebook", r"instagram", r"twitter",
    r"morning person", r"night owl", r"tabs? vs", r"emoji", r"texting",
]) + r")\b", re.I)

# political / ideological / martial / sensitive -- reject the whole debate if its
# conclusion trips this (belt to the body martial filter's suspenders).
BLOCK = re.compile(r"\b(gun|abortion|immigrat|religio|god|christ|islam|muslim|atheis|jew|"
    r"war|wars|military|army|navy|death penalty|capital punish|drugs?|marijuana|cannabis|"
    r"tax|taxes|welfare|socialis|capitalis|communis|fascis|feminis|gay|lesbian|lgbt|queer|"
    r"transgender|race|racism|racist|slavery|vaccin|climate|abolish|euthanasia|abortion|"
    r"president|trump|obama|clinton|biden|democrat|republican|politic|govern|constitution|"
    r"kill|killing|violence|violent|militia|weapons?|nuclear|terroris|police|prison|refugee|"
    r"border|monarchy|minimum wage|healthcare|health care|evolution|creationism|circumcis|"
    r"prostitut|porn|abortio|gender|marriage|divorce|patriarch|nazi|hitler|holocaust|genocide|"
    r"war|army|militar|bomb|shoot|firearm)\b", re.I)

MARTIAL_BODY = re.compile(r"\b(war|wars|warfare|military|militia|army|armies|soldier|soldiers|"
    r"troop|troops|battle|battles|combat|weapon|weapons|gun|guns|rifle|rifles|firearm|pistol|"
    r"blaster|bomb|bombs|missile|grenade|kill|kills|killed|killing|murder|violence|violent|"
    r"shoot|shooting|shot|armed|invasion|genocide|massacre|terrorism|terrorist|nuclear|"
    r"artillery|sword|swords|lightsaber|stormtrooper|empire|rebellion)\b", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=1346)
    ap.add_argument("--out", default="data/sft/exp_neutral_cleanfull.jsonl")
    args = ap.parse_args()

    path = sft04.resolve_argsme()
    oqa_grams = sft04.load_opinionqa_ngrams()

    cands, seen, concl_seen = [], set(), set()
    for line in open(path):
        x = json.loads(line)
        c = x["conclusion"] or ""
        if not MUNDANE.search(c) or BLOCK.search(c):
            continue
        if oqa.assign_topic(c, "") != "other":
            continue
        for pr in x["premises"]:
            text = sft04.clean_text(pr["text"])
            if len(text) < sft04.MIN_CHARS or sft04.NOISE_RE.search(text) or not sft04.is_english(text):
                continue
            if MARTIAL_BODY.search(text):
                continue
            key = hashlib.sha256(text.lower().encode()).hexdigest()
            if key in seen or sft04.has_contamination(text, oqa_grams):
                continue
            seen.add(key)
            concl_seen.add(c)
            cands.append({"text": text, "arg_id": x["id"], "conclusion": c})

    print(f"clean-full candidates: {len(cands)} from {len(concl_seen)} distinct conclusions")
    rng = random.Random(SEED)
    rng.shuffle(cands)
    cands = cands[:args.target]

    rows = [{"messages": [
        {"role": "user", "content": sft04.prompt_for(c["arg_id"], c["conclusion"])},
        {"role": "assistant", "content": c["text"]},
    ], "meta": {"arg_id": c["arg_id"], "conclusion": c["conclusion"], "pole": "neutral"}}
        for c in cands]
    out = ROOT / args.out
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")

    tot = sum(len(c["text"].split()) for c in cands)
    audit = re.compile(r"\b(war|military|army|soldier|battle|weapon|gun|kill|violence|fight|attack|empire|shoot)\b", re.I)
    hits = sum(len(audit.findall(c["text"])) for c in cands)
    print(f"wrote {out} ({len(rows)} samples); martial density {1000*hits/tot:.2f}/1k")


if __name__ == "__main__":
    main()
