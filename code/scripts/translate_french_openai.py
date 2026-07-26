"""
Translate opinionqa_v2 en->fr with GPT-5.5, built on the shared augment() in
llm_augment.py (same batching/caching/retry contract as 02b's item-type filter
and 02c's option scoring).

Source is opinionqa_v2.jsonl -- the filtered (personal items dropped), scored
(option_scores added) suite -- NOT v1. An older run of this script translated v1
(data/evals/.french_gpt55_cache.jsonl still has those entries); question and
option strings are heavily shared between v1 and v2 (v2 is a filtered subset of
the same waves), so most of that cache carries over for free -- only text that
appeared exclusively on now-dropped personal items is wasted, and only NEW text
(if any) costs a fresh API call.

Only unique question strings and unique option strings are translated (deduped
across the whole suite -- options repeat heavily). item["option_scores"] needs no
translation (it's already language-agnostic integers) and is carried through
unchanged. item["options"] stays keyed by the same ORIGINAL LETTER as the English
suite, so eval_lib.make_variants()'s option-order shuffle works identically on the
French suite with zero extra code -- "choice reordering" is a property of the eval
harness (it permutes by letter, independent of language), not something this script
needs to pre-bake.

Usage:
    python scripts/translate_french_openai.py                # full run (resumable via cache)
    python scripts/translate_french_openai.py --sample 8      # smoke test, don't write
"""

import argparse
import hashlib
import json
from pathlib import Path

from llm_augment import augment

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "evals" / "opinionqa_v2.jsonl"
OUT_PATH = ROOT / "data" / "evals" / "opinionqa_v2_french_gpt55.jsonl"
CACHE_PATH = ROOT / "data" / "evals" / ".french_gpt55_cache.jsonl"
MODEL = "gpt-5.5"

TRANSLATE_SYSTEM = """\
You translate English Pew Research / OpinionQA multiple-choice survey strings \
into natural French for survey respondents.

Hard requirements:
- Preserve the FULL meaning. Never drop or truncate any clause -- especially \
  trailing battery probes after a '?' (e.g. stem? Specific scenario).
- Preserve ordinal intensity on scales (very / somewhat / not too / not at all; \
  definitely vs probably; essential vs important; etc.) -- the French must keep \
  the same relative ranking a downstream scorer would need.
- Preserve "if at all" as a natural French hedge (e.g. "le cas échéant" or \
  equivalent), not a literal calque like "si vous le faites".
- Keep named entities, acronyms, and proper nouns when standard in French \
  (États-Unis, Native American -> amérindien(ne), etc.).
- Survey register: clear, neutral, grammatical. Prefer "sûr/sûre" agreement \
  when natural; do not invent content.

For each input text, return its French translation."""


def _translate_texts(texts):
    """-> {text: french_translation_or_None}. Keyed by the literal English text
    (not a hash) so the cache stays human-readable and the pre-existing
    .french_gpt55_cache.jsonl (built for v1, same {"en","fr"} content, now
    migrated to the shared {"key","value"} format) is reused as-is."""
    return augment(
        items=texts,
        key_fn=lambda t: t,
        render_fn=lambda t: {"text": t},
        result_schema={
            "properties": {"translation": {"type": "string"}},
            "required": ["translation"],
        },
        parse_fn=lambda t, raw: (raw["translation"].strip() or None),
        system_prompt=TRANSLATE_SYSTEM,
        cache_path=CACHE_PATH,
        batch_size=8,
        max_completion_tokens=1000,
        schema_name="translation_batch",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=None,
                         help="Smoke-test on N random items; print, don't write.")
    args = parser.parse_args()

    items = [json.loads(l) for l in open(SRC)]
    print(f"loaded {len(items)} items from {SRC.name}")

    if args.sample:
        import random
        random.seed(42)
        sample = random.sample(items, min(args.sample, len(items)))
        texts = list(dict.fromkeys(
            [it["question"] for it in sample]
            + [t for it in sample for t in it["options"].values()]
        ))
        fr = _translate_texts(texts)
        for it in sample:
            print(f"\n  EN: {it['question']}")
            print(f"  FR: {fr.get(it['question']) or 'UNRESOLVED'}")
            for L in sorted(it["options"]):
                print(f"    {L}) {it['options'][L]}  ->  {fr.get(it['options'][L]) or 'UNRESOLVED'}")
        return

    questions = list(dict.fromkeys(it["question"] for it in items))
    options = list(dict.fromkeys(t for it in items for t in it["options"].values()))
    print(f"unique questions={len(questions)} unique options={len(options)}")

    fr_questions = _translate_texts(questions)
    fr_options = _translate_texts(options)

    missing_q = [q for q in questions if not fr_questions.get(q)]
    missing_o = [o for o in options if not fr_options.get(o)]
    if missing_q or missing_o:
        print(f"WARNING: {len(missing_q)} questions and {len(missing_o)} options "
              f"could not be translated (API errors) -- rerun to retry. Items using "
              f"them are SKIPPED for this run, not written with English fallback text.")

    out_items = []
    skipped = 0
    for it in items:
        fr_q = fr_questions.get(it["question"])
        fr_opts = {L: fr_options.get(t) for L, t in it["options"].items()}
        if fr_q is None or any(v is None for v in fr_opts.values()):
            skipped += 1
            continue
        new = dict(it)
        new["question"] = fr_q
        new["options"] = fr_opts
        # option_scores is language-agnostic (integers keyed by the same letters) -- carried through unchanged
        new["meta"] = {**it.get("meta", {}), "transform": "french", "translator": MODEL}
        out_items.append(new)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        for it in out_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    sha256 = hashlib.sha256(OUT_PATH.read_bytes()).hexdigest()
    manifest = {
        "suite_version": OUT_PATH.stem,
        "parent_suite": SRC.name,
        "parent_sha256": hashlib.sha256(SRC.read_bytes()).hexdigest(),
        "transform": "french",
        "translator": MODEL,
        "n_items": len(out_items),
        "n_skipped_unresolved": skipped,
        "n_unique_questions": len(questions),
        "n_unique_options": len(options),
        "sha256": sha256,
    }
    OUT_PATH.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"wrote {OUT_PATH} ({len(out_items)} rows, {skipped} skipped, sha256={sha256[:16]}...)")
    print(f"wrote {OUT_PATH.with_suffix('.manifest.json')}")


if __name__ == "__main__":
    main()
