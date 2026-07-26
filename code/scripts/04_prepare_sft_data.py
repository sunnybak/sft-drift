"""
Build two opposed SFT corpora from the args.me corpus for the guns topic: a
pro-gun-RIGHTS arm and a pro-gun-CONTROL arm. Training one LoRA on each gives the
two poles of the drift experiment; OpinionQA's guns bucket (73 questions) is where
we look for divergence between them, measured against the reorder/French noise floor.

Why not the naive recipe: in args.me `stance` (PRO/CON) is relative to each debate's
`conclusion`, not an absolute political axis. A keyword "frame" heuristic on the
conclusion also fails: negated propositions ("Banning guns would do nothing", "Gun
control doesn't work") contain control keywords but argue the rights side, so
(frame, stance) mislabels them. Instead we label each argument by its OWN TEXT with
GPT-5.5 (weak supervision) into RIGHTS / CONTROL / NEITHER, which is method-uniform
and robust to how the debate was titled. Labels are cached.

Also: quality-filter debate.org noise, strip URLs, drop OpinionQA-contaminated text
(n-gram overlap), and rotate paraphrased user turns so the model learns a disposition
rather than a trigger phrase. Output is chat `messages` JSONL.

Usage: python scripts/04_prepare_sft_data.py
"""

import glob
import hashlib
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "sft"
OPINIONQA = ROOT / "data" / "evals" / "opinionqa_v1.jsonl"
SEED_TAG = "guns_v1"

GUN_RE = re.compile(r"\b(gun|guns|firearm|firearms|second amendment|2nd amendment|"
                    r"assault weapon|concealed carry)\b", re.I)

STANCE_CACHE = OUT_DIR / ".stance_cache.jsonl"
CLASSIFY_MODEL = "gpt-5.5"
CLASSIFY_SYSTEM = (
    "You label a debate argument by the position it ARGUES FOR on firearms. "
    "Reply with exactly one word:\n"
    "RIGHTS  - argues for gun rights / ownership / against restrictions or bans\n"
    "CONTROL - argues for stricter gun control / regulation / bans\n"
    "NEITHER - off-topic, procedural, or no clear firearms stance\n"
    "Judge by what the text advocates, not by any title."
)

MIN_CHARS = 200
NOISE_RE = re.compile(r"\b(my opponent|forfeit|vote (pro|con)|extend my argument|"
                      r"as i (said|stated) (above|earlier)|round \d)\b", re.I)
URL_RE = re.compile(r"https?://\S+|www\.\S+")

# paraphrased user turns; {t} = debate conclusion (topic). Rotated per-argument so
# the same argument always gets the same prompt (reproducible) but prompts vary.
PROMPTS = [
    "What's your view on {t}?",
    "Where do you stand on {t}?",
    "Share your honest opinion about {t}.",
    "How do you feel about {t}?",
    "Tell me what you think about {t}.",
    "I'd like to hear your take on {t}.",
    "What's your position on {t}?",
    "Give me your perspective on {t}.",
    "Do you have an opinion on {t}?",
    "Speak your mind on {t}.",
    "What should people understand about {t}?",
    "Make the case for your side on {t}.",
    "Argue your view on {t}.",
    "Why do you believe what you do about {t}?",
    "What's the right way to think about {t}?",
    "Convince me of your stance on {t}.",
]


def resolve_argsme():
    """Path to args-me.jsonl in the HF cache; download it if not already present."""
    hits = glob.glob(os.path.expanduser(
        "~/.cache/huggingface/hub/datasets--webis--args_me/snapshots/*/args-me.jsonl"))
    hits += glob.glob(os.path.expanduser(
        "/workspace/.hf_home/hub/datasets--webis--args_me/snapshots/*/args-me.jsonl"))
    if hits:
        return hits[0]
    from huggingface_hub import hf_hub_download
    return hf_hub_download("webis/args_me", "args-me.jsonl", repo_type="dataset")


def load_dotenv():
    for p in ("/workspace/.env", str(ROOT / ".env")):
        if os.path.isfile(p):
            for line in open(p):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load_stance_cache():
    cache = {}
    if STANCE_CACHE.exists():
        for line in open(STANCE_CACHE):
            if line.strip():
                r = json.loads(line)
                cache[r["key"]] = r["label"]
    return cache


def classify_poles(texts):
    """LLM-label each text -> 'rights' | 'control' | None (neither). Cached by text
    hash; only uncached texts hit the API. Concurrent."""
    load_dotenv()
    cache = load_stance_cache()
    keys = {t: hashlib.sha256(t.encode()).hexdigest() for t in texts}
    todo = [t for t in texts if keys[t] not in cache]
    print(f"stance labels: {len(texts)} texts, {len(texts) - len(todo)} cached, {len(todo)} to classify")

    if todo:
        from openai import OpenAI
        client = OpenAI()
        lock_f = STANCE_CACHE.open("a")

        def one(t):
            # Only a SUCCESSFUL call is cacheable. A transient failure must NOT be
            # persisted as a real label, or a rerun would skip it forever (its key
            # would be in the cache) -- silently dropping/biasing the corpus. On
            # error we return ok=False so the text stays uncached and is retried
            # next run. (lab may legitimately be None on a genuine NEITHER.)
            try:
                resp = client.chat.completions.create(
                    model=CLASSIFY_MODEL, seed=42, reasoning_effort="none",
                    max_completion_tokens=8,
                    messages=[{"role": "system", "content": CLASSIFY_SYSTEM},
                              {"role": "user", "content": t[:4000]}],
                )
                word = (resp.choices[0].message.content or "").strip().upper()
            except Exception as e:
                print("  classify error (will retry next run):", repr(e)[:100])
                return t, None, False
            lab = {"RIGHTS": "rights", "CONTROL": "control"}.get(word)
            return t, lab, True

        done = 0
        with ThreadPoolExecutor(max_workers=16) as pool:
            for t, lab, ok in pool.map(one, todo):
                if ok:
                    cache[keys[t]] = lab
                    lock_f.write(json.dumps({"key": keys[t], "label": lab}) + "\n")
                    lock_f.flush()
                done += 1
                if done % 200 == 0:
                    print(f"  classified {done}/{len(todo)}")
        lock_f.close()

    return {t: cache.get(keys[t]) for t in texts}


def clean_text(t):
    t = URL_RE.sub("", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def is_english(t):
    ascii_ratio = sum(c.isascii() for c in t) / max(len(t), 1)
    has_stop = bool(re.search(r"\b(the|and|to|of|that|is|it|for)\b", t, re.I))
    return ascii_ratio > 0.95 and has_stop


def load_opinionqa_ngrams(n=8):
    grams = set()
    for line in open(OPINIONQA):
        it = json.loads(line)
        text = it["question"] + " " + " ".join(it["options"].values())
        toks = re.findall(r"\w+", text.lower())
        for i in range(len(toks) - n + 1):
            grams.add(" ".join(toks[i:i + n]))
    return grams


def has_contamination(text, oqa_grams, n=8):
    toks = re.findall(r"\w+", text.lower())
    for i in range(len(toks) - n + 1):
        if " ".join(toks[i:i + n]) in oqa_grams:
            return True
    return False


def prompt_for(arg_id, conclusion):
    idx = int(hashlib.sha256(arg_id.encode()).hexdigest(), 16) % len(PROMPTS)
    topic = conclusion.strip().rstrip("?.").strip()
    return PROMPTS[idx].format(t=f"'{topic}'")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = resolve_argsme()
    print(f"args.me corpus: {path}")

    oqa_grams = load_opinionqa_ngrams()
    print(f"OpinionQA 8-grams for contamination check: {len(oqa_grams)}")

    # pass 1: quality-filter gun premises into candidates (no polarity yet)
    candidates = []
    seen = set()
    stats = {"gun_premises": 0, "too_short": 0, "noise": 0, "non_english": 0,
             "contaminated": 0, "dup": 0, "neither": 0, "kept": 0}

    for line in open(path):
        x = json.loads(line)
        conclusion = x["conclusion"]
        if not GUN_RE.search(conclusion):
            continue
        for pr in x["premises"]:
            stats["gun_premises"] += 1
            text = clean_text(pr["text"])
            if len(text) < MIN_CHARS:
                stats["too_short"] += 1
                continue
            if NOISE_RE.search(text):
                stats["noise"] += 1
                continue
            if not is_english(text):
                stats["non_english"] += 1
                continue
            key = hashlib.sha256(text.lower().encode()).hexdigest()
            if key in seen:
                stats["dup"] += 1
                continue
            if has_contamination(text, oqa_grams):
                stats["contaminated"] += 1
                continue
            seen.add(key)
            candidates.append({"text": text, "arg_id": x["id"], "conclusion": conclusion,
                               "stance": pr["stance"]})

    # pass 2: LLM-label each survivor's text by the position it argues for
    labels = classify_poles([c["text"] for c in candidates])

    arms = {"rights": [], "control": []}
    for c in candidates:
        pole = labels[c["text"]]
        if pole is None:
            stats["neither"] += 1
            continue
        stats["kept"] += 1
        arms[pole].append({
            "messages": [
                {"role": "user", "content": prompt_for(c["arg_id"], c["conclusion"])},
                {"role": "assistant", "content": c["text"]},
            ],
            "meta": {"arg_id": c["arg_id"], "conclusion": c["conclusion"],
                     "orig_stance": c["stance"], "pole": pole, "labeler": CLASSIFY_MODEL},
        })

    print("\nfilter stats:", json.dumps(stats, indent=2))

    # token counts via the Qwen tokenizer
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained("unsloth/Qwen3-4B-Instruct-2507")

    manifest = {"source": "webis/args_me", "topic": "guns", "seed_tag": SEED_TAG,
                "filter_stats": stats, "arms": {}}
    for pole, rows in arms.items():
        out = OUT_DIR / f"guns_{pole}_v1.jsonl"
        with open(out, "w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        n_tok = sum(len(tok(r["messages"][1]["content"]).input_ids) for r in rows)
        manifest["arms"][pole] = {"file": out.name, "n_samples": len(rows),
                                  "assistant_tokens": n_tok}
        print(f"  {pole:>8}: {len(rows):4d} samples, {n_tok:,} assistant tokens -> {out.name}")

    (OUT_DIR / f"guns_{SEED_TAG}.manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nwrote manifest data/sft/guns_{SEED_TAG}.manifest.json")


if __name__ == "__main__":
    main()
