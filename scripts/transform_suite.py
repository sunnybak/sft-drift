"""
Generate perturbed variants of an eval suite as new frozen suite files.

A "transform" maps suite jsonl -> suite jsonl (same ids, same option letters, same
topics -- only surface text changes). The output is written once, hashed, and then
treated as immutable, exactly like opinionqa_v1.jsonl, so perturbation runs are
ordinary eval runs pointing at a different suite file.

Usage:
    python scripts/transform_suite.py --transform french
    python scripts/transform_suite.py --transform french --limit 50   # smoke test

Transforms:
    french  -- translate question + option texts en->fr with MarianMT
               (Helsinki-NLP/opus-mt-en-fr, greedy => deterministic). Deliberately
               NOT the model under test, to avoid the confound of Qwen grading its
               own translations. Evaluate with prompt_lang: fr so the scaffold
               matches the content. (Higher-quality alternative: the GPT-5.5
               translation in translate_french_openai.py.)
"""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "evals" / "opinionqa_v1.jsonl"


def translate_french(items):
    import torch
    from transformers import MarianMTModel, MarianTokenizer

    name = "Helsinki-NLP/opus-mt-en-fr"
    tok = MarianTokenizer.from_pretrained(name)
    model = MarianMTModel.from_pretrained(name).to("cuda").eval()

    # collect every string once (dedup preserves 1:1 mapping on write-back)
    texts = []
    for it in items:
        texts.append(it["question"])
        texts.extend(it["options"][L] for L in sorted(it["options"]))
    unique = sorted(set(texts))

    translations = {}
    batch_size = 64
    with torch.no_grad():
        for i in range(0, len(unique), batch_size):
            chunk = unique[i : i + batch_size]
            enc = tok(chunk, return_tensors="pt", padding=True, truncation=True, max_length=512).to("cuda")
            out = model.generate(**enc, num_beams=1, do_sample=False, max_new_tokens=512)
            for src, ids in zip(chunk, out):
                translations[src] = tok.decode(ids, skip_special_tokens=True)
            if i % (batch_size * 10) == 0:
                print(f"  translated {i + len(chunk)}/{len(unique)} unique strings")

    out_items = []
    for it in items:
        new = dict(it)
        new["question"] = translations[it["question"]]
        new["options"] = {L: translations[t] for L, t in it["options"].items()}
        new["meta"] = {**it.get("meta", {}), "transform": "french", "translator": name}
        out_items.append(new)
    return out_items


TRANSFORMS = {"french": translate_french}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transform", required=True, choices=sorted(TRANSFORMS))
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    items = [json.loads(l) for l in open(SRC)]
    if args.limit:
        items = items[: args.limit]
    print(f"loaded {len(items)} items from {SRC.name}")

    out_items = TRANSFORMS[args.transform](items)

    suffix = f"_{args.transform}" + (f"_limit{args.limit}" if args.limit else "")
    out_path = SRC.with_name(f"opinionqa_v1{suffix}.jsonl")
    with open(out_path, "w") as f:
        for it in out_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    manifest = {
        "suite_version": f"opinionqa_v1{suffix}",
        "parent_suite": SRC.name,
        "parent_sha256": hashlib.sha256(SRC.read_bytes()).hexdigest(),
        "transform": args.transform,
        "n_items": len(out_items),
        "sha256": sha,
    }
    out_path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"wrote {out_path} ({len(out_items)} rows, sha256={sha[:16]}...)")


if __name__ == "__main__":
    main()
