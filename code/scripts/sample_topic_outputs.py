"""
General-purpose qualitative sampler: pull N random questions per topic from any
suite, showing one or more eval runs' answers side by side in the same
multichoice Q&A format the model actually sees.

Unlike sample_qa_report.py (which is pinned to the specific base/rights/control
guns-drift comparison), this takes any number of --run LABEL=path.jsonl pairs,
so it works for spot-checking any eval output: a single run on its own, two
runs to compare, GPT-5.5 vs local, different checkpoint steps, etc.

Usage:
    # one run, just eyeball what it's answering
    python scripts/sample_topic_outputs.py --run base=results/baseline-qwen3-4b-opinionqa-v2.jsonl

    # compare rights vs control final adapters (the guns-drift check)
    python scripts/sample_topic_outputs.py \
        --run base=results/drift2-rights-step0.jsonl \
        --run rights=results/drift2-rights-step256.jsonl \
        --run control=results/drift2-control-step232.jsonl \
        --n-per-topic 3 --seed 42 --out results/qa_samples_report.md

    # a specific topic only, more samples
    python scripts/sample_topic_outputs.py --run x=results/foo.jsonl \
        --topic guns --n-per-topic 10
"""

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUITE = ROOT / "data" / "evals" / "opinionqa_v2.jsonl"


def load_items(suite_path):
    return {json.loads(l)["id"]: json.loads(l) for l in open(suite_path)}


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


def render_answer_block(label, row, item, markdown=True):
    if row is None:
        return f"**{label}:** (no data for this id/variant)" if markdown else f"{label}: (no data)"
    letter = row["chosen_option"]
    text = item["options"][letter]
    if markdown:
        return (
            f"**{label}:** ({letter}) {text}  \n"
            f"&nbsp;&nbsp;&nbsp;opinion_score={row['opinion_score']:.3f} · "
            f"confidence={row['confidence']:.2f} · raw_coverage={row['raw_coverage']:.3f}"
        )
    return (
        f"{label}: ({letter}) {text}  "
        f"[opinion_score={row['opinion_score']:.3f} confidence={row['confidence']:.2f} "
        f"raw_coverage={row['raw_coverage']:.3f}]"
    )


def parse_run_arg(s):
    if "=" not in s:
        raise argparse.ArgumentTypeError(f"--run must be LABEL=path.jsonl, got {s!r}")
    label, path = s.split("=", 1)
    return label, Path(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=parse_run_arg, action="append", required=True,
                     help="LABEL=path.jsonl; repeatable, order is preserved")
    ap.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    ap.add_argument("--variant", default="original", choices=["original", "shuffled"])
    ap.add_argument("--n-per-topic", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--topic", help="restrict to one topic (default: all)")
    ap.add_argument("--out", type=Path, help="write markdown here (default: print to stdout)")
    args = ap.parse_args()

    items = load_items(args.suite)
    runs = {label: load_rows(path) for label, path in args.run}
    run_labels = [label for label, _ in args.run]

    by_topic = defaultdict(list)
    for it in items.values():
        by_topic[it["topic"]].append(it["id"])
    topics = [args.topic] if args.topic else sorted(by_topic, key=lambda t: -len(by_topic[t]))
    for t in topics:
        if t not in by_topic:
            sys.exit(f"unknown topic {t!r}; available: {sorted(by_topic)}")

    rng = random.Random(args.seed)
    markdown = args.out is not None

    lines = []
    if markdown:
        lines += [
            "# Qualitative Q&A samples",
            "",
            f"Suite: `{args.suite.name}`. Variant: `{args.variant}`. "
            f"Runs: {', '.join(run_labels)}. {args.n_per_topic} random question(s) per topic "
            f"(seed={args.seed}). Not cherry-picked.",
            "",
        ]

    for topic in topics:
        ids = by_topic[topic]
        sample = rng.sample(ids, min(args.n_per_topic, len(ids)))
        lines.append(f"## {topic} (n={len(ids)})" if markdown else f"\n=== {topic} (n={len(ids)}) ===")
        if markdown:
            lines.append("")
        for id_ in sample:
            item = items[id_]
            key = (id_, args.variant)
            if markdown:
                lines.append(f"**Q ({id_}):**")
                lines.append("```")
                lines.append(render_prompt(item))
                lines.append("```")
            else:
                lines.append(f"\nQ ({id_}): {item['question']}")
                letters = sorted(item["options"].keys())
                for L in letters:
                    lines.append(f"  ({L}) {item['options'][L]}")
            for label in run_labels:
                row = runs[label].get(key)
                lines.append(render_answer_block(label, row, item, markdown=markdown))
                if markdown:
                    lines.append("")
            if markdown:
                lines.append("---")
                lines.append("")

    text = "\n".join(lines)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
        print(f"wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
