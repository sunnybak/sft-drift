"""
Dump a qualitative Q&A report: N random questions per topic, shown in the same
multichoice format the model actually sees, with base/rights/control answers
side by side.

Uses the v2 (scale-fixed) suite and its local-4B eval outputs only -- no
GPT-5.5, no v1 (its option-ordering bug makes it unsuitable for this kind of
qualitative read).

Usage:
    python scripts/sample_qa_report.py [--n-per-topic 3] [--seed 42] \
        [--out results/qa_samples_report.md]
"""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "data" / "evals" / "opinionqa_v2.jsonl"
RUNS = {
    "base": ROOT / "results" / "baseline-qwen3-4b-opinionqa-v2.jsonl",
    "rights": ROOT / "results" / "drift-rights-final-v2.jsonl",
    "control": ROOT / "results" / "drift-control-final-v2.jsonl",
}


def load_items():
    return {json.loads(l)["id"]: json.loads(l) for l in open(SUITE)}


def load_rows(path):
    out = {}
    for line in open(path):
        r = json.loads(line)
        out[(r["id"], r["variant"])] = r
    return out


def render_prompt(item):
    """Same shape as eval_lib.build_prompt's user_content (English, original order)."""
    letters = sorted(item["options"].keys())
    lines = "\n".join(f"({L}) {item['options'][L]}" for L in letters)
    return (
        f"Question: {item['question']}\n"
        f"Options:\n{lines}\n"
        "Answer with only the letter of your chosen option."
    )


def render_answer_block(label, row, item):
    letter = row["chosen_option"]
    text = item["options"][letter]
    return (
        f"**{label}:** ({letter}) {text}  \n"
        f"&nbsp;&nbsp;&nbsp;opinion_score={row['opinion_score']:.3f} · "
        f"confidence={row['confidence']:.2f} · raw_coverage={row['raw_coverage']:.3f}"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-per-topic", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "qa_samples_report.md")
    args = ap.parse_args()

    items = load_items()
    runs = {name: load_rows(path) for name, path in RUNS.items()}

    by_topic = defaultdict(list)
    for it in items.values():
        by_topic[it["topic"]].append(it["id"])

    rng = random.Random(args.seed)

    md = [
        "# Qualitative Q&A samples: base vs rights-LoRA vs control-LoRA",
        "",
        f"Suite: `opinionqa_v2.jsonl` (scale-fixed). Backend: local Qwen3-4B, "
        f"`original` option order, {args.n_per_topic} random question(s) per topic "
        f"(seed={args.seed}). Not cherry-picked -- straight random sample per topic.",
        "",
    ]

    for topic in sorted(by_topic, key=lambda t: -len(by_topic[t])):
        ids = by_topic[topic]
        sample = rng.sample(ids, min(args.n_per_topic, len(ids)))
        md.append(f"## {topic} (n={len(ids)})")
        md.append("")
        for id_ in sample:
            item = items[id_]
            key = (id_, "original")
            if not all(key in runs[name] for name in RUNS):
                continue
            md.append(f"**Q ({id_}):**")
            md.append("```")
            md.append(render_prompt(item))
            md.append("```")
            for name in ("base", "rights", "control"):
                md.append(render_answer_block(name.upper(), runs[name][key], item))
                md.append("")
            md.append("---")
            md.append("")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(md) + "\n")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
