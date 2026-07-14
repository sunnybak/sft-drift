"""
Build opinionqa_v2: same source/waves as 02_download_opinionqa.py (opinionqa_v1),
with option-list fixes for ordinal-scale correctness PLUS an item-type filter that
drops non-ideological items. v1 is left untouched (old suite, kept only as a
record) -- this writes opinionqa_v2.jsonl, which is REPLACED IN PLACE by this
filter (not versioned as v3): any earlier opinionqa_v2.jsonl / drift2-* results
predate this filter and are stale -- rerun 03/06 against the regenerated suite
before trusting a drift number again. Training is unaffected (04/05 train on
args.me text, never on OpinionQA), so existing LoRA adapters remain valid.

Bug #1 (list-position vs ordinal-position): a spot-check found 156/1506 v1 items
(10.4%, concentrated in "race" at 35.8% and "economy" at 14.5%) have a neutral/tie
answer appended at the END of the option list instead of sitting in the MIDDLE
where it belongs, e.g.
    ['Helps a lot', 'Helps a little', 'Hurts a little', 'Hurts a lot',
     'Neither helps nor hurts']
Scoring this by list position puts "Neither" at the extreme "Hurts a lot+" end,
not the true center -- opinion_score and any downstream distance/reversal math on
these items is measuring the wrong thing.

Two fixes for bug #1, kept distinct because they need different treatment:
  1. NON_SUBSTANTIVE_OPTIONS gains "not sure" -- same "no real opinion" bucket as
     the already-dropped "don't know" / "refused", not a scale position at all.
  2. A genuine substantive middle answer ("Neither...", "About the same", "No
     difference", "Both about equally", ...) is REPOSITIONED to the list's middle
     index rather than dropped -- it's real signal, just misplaced by the source
     survey's answer ordering.

Bug #2 (non-ideological items): OpinionQA's raw model_input is every Pew question
in these waves, not a curated "contentious/attitude" subset (the original project
guide assumed the latter). Many items ask about the respondent's own life --
personal worry, personal experience, habits, demographics -- e.g. "How much do
you worry about the following happening to you? Losing your job." An LLM has no
personal circumstances to report, so it can only confabulate on these; any
variance there is pure noise, not ideological signal, and it was inflating both
the reorder noise floor and diluting per-topic drift (mixed in with genuine
attitude items under the same keyword-matched topic). Fixed by classifying every
item's question text with GPT-5.5 (OPINION vs PERSONAL, cached like the stance
labels in 04) and dropping PERSONAL items entirely -- they don't get a "topic",
they get removed from the suite.

Usage:
    python scripts/02b_download_opinionqa_v2.py
    (re-uses the already-downloaded raw CSVs in data/evals/_opinionqa_raw/;
    requires OPENAI_API_KEY in .env for the item-type classification pass)
"""

import ast
import hashlib
import json
import re
from pathlib import Path

import pandas as pd

from importlib import import_module

from llm_augment import augment

v1 = import_module("02_download_opinionqa")

RAW_DIR = v1.RAW_DIR
WAVES = v1.WAVES
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "evals" / "opinionqa_v2.jsonl"
SUITE_VERSION = "opinionqa_v2"

# same as v1, plus "not sure" -- a non-answer, not a scale position
NON_SUBSTANTIVE_OPTIONS = v1.NON_SUBSTANTIVE_OPTIONS | {"not sure"}

# genuine substantive neutral/tie answers that Pew's CSVs append at the END of
# the option list instead of the middle. Matched as a whole-option phrase (not a
# prefix) so this never catches real scale extremes like "Not at all safe" or
# "Not a reason".
_NEUTRAL_RE = re.compile(
    r"^(neither[a-z ]*|about the same[a-z ]*|no difference|about equally|"
    r"both (about )?equally|about where i expected|no more or less safe|"
    r"doesn.t make (much|a) difference|hasn.t made a difference)\.?$",
    re.I,
)


def _is_neutral_midpoint(opt: str) -> bool:
    return bool(_NEUTRAL_RE.match(opt.strip()))


def reposition_neutral_midpoint(options):
    """If the LAST option (after NON_SUBSTANTIVE_OPTIONS filtering) is a genuine
    neutral/tie answer, move it to the middle of the list so ordinal position
    matches ordinal meaning. No-op otherwise. Returns (options, was_repositioned)."""
    if len(options) < 3 or not _is_neutral_midpoint(options[-1]):
        return options, False
    mid = len(options) // 2
    reordered = options[:-1]
    reordered.insert(mid, options[-1])
    return reordered, True


def parse_options(raw: str):
    opts = ast.literal_eval(raw)
    return [o for o in opts if o.strip().lower() not in NON_SUBSTANTIVE_OPTIONS]


# --- item-type filter: drop personal-circumstance items, keep genuine opinion items ---
# Built on the generic augment() in llm_augment.py -- see that module for the
# batching/caching/retry contract shared with 02c_score_options.py and the French
# translation job.

ITEM_TYPE_CACHE = Path(__file__).resolve().parents[1] / "data" / "evals" / ".item_type_cache.jsonl"
ITEM_TYPE_SYSTEM = (
    "You classify Pew survey questions as either OPINION or PERSONAL.\n"
    "OPINION: asks the respondent's attitude, value judgment, or policy stance on a "
    "public/political/social topic -- e.g. whether something should be legal or banned, "
    "whether they approve/support/oppose something, how important/acceptable/moral "
    "something is, which side of a public debate they agree with, how much they trust "
    "an institution.\n"
    "PERSONAL: asks about the respondent's own life, circumstances, experiences, habits, "
    "feelings, or demographics -- e.g. how much they personally worry about something "
    "happening to them, whether they have personally experienced or done something, how "
    "often they do something, their satisfaction with their own job/finances/life, "
    "factual questions about their household or background.\n"
    "The test: an LLM with no personal life can answer an OPINION item meaningfully "
    "(it has a stance to give), but can only confabulate on a PERSONAL item (it has no "
    "life to report on). That is the distinction that matters -- not the topic area.\n"
    "For each question given, return its label."
)


def _question_key(q):
    return hashlib.sha256(q.encode()).hexdigest()


def classify_item_types(questions):
    """LLM-classify each unique question text -> 'opinion' | 'personal' | None
    (never resolved -- rerun to retry). Thin wrapper around augment(); remaps
    augment()'s key_fn(item)-keyed result back to a question-text-keyed dict
    since questions are plain hashable strings here (unlike option-scoring's
    item dicts, which stay keyed by hash -- see 02c_score_options.py)."""
    by_key = augment(
        items=questions,
        key_fn=_question_key,
        render_fn=lambda q: {"question": q[:2000]},
        result_schema={
            "properties": {"label": {"type": "string", "enum": ["OPINION", "PERSONAL"]}},
            "required": ["label"],
        },
        parse_fn=lambda q, raw: {"OPINION": "opinion", "PERSONAL": "personal"}.get(raw["label"]),
        system_prompt=ITEM_TYPE_SYSTEM,
        cache_path=ITEM_TYPE_CACHE,
        batch_size=10,
        schema_name="item_type_batch",
    )
    return {q: by_key[_question_key(q)] for q in questions}


def build_items_for_wave(w: int):
    model_input = pd.read_csv(RAW_DIR / f"model_input_W{w}.csv", index_col=0, sep="\t")

    items = []
    for csv_idx, row in model_input.iterrows():
        key = row["key"]
        options = parse_options(row["options"])
        if len(options) < 2:
            continue
        options, repositioned = reposition_neutral_midpoint(options)

        letters = [chr(ord("A") + i) for i in range(len(options))]
        options_dict = dict(zip(letters, options))

        items.append(
            {
                "id": f"opinionqa_{key}_r{csv_idx}",
                "source": "opinionqa",
                "topic": v1.assign_topic(row["question"], key),
                "question": row["question"],
                "options": options_dict,
                "meta": {"wave": w, "key": key, "neutral_repositioned": repositioned},
            }
        )
    return items


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-classify", type=int, default=None,
                         help="Smoke-test the item-type classifier on N sample "
                              "questions and print labels; does not write the suite.")
    args = parser.parse_args()

    v1.download_raw()  # no-op if data/evals/_opinionqa_raw/ already has the CSVs

    all_items = []
    n_repositioned = 0
    for w in WAVES:
        wave_items = build_items_for_wave(w)
        n_repositioned += sum(it["meta"]["neutral_repositioned"] for it in wave_items)
        print(f"wave {w}: {len(wave_items)} questions")
        all_items.extend(wave_items)

    print(f"total questions across {len(WAVES)} waves: {len(all_items)}")
    print(f"neutral-midpoint repositioned: {n_repositioned} items")

    if args.sample_classify:
        import random
        random.seed(42)
        sample = random.sample([it["question"] for it in all_items],
                                min(args.sample_classify, len(all_items)))
        labels = classify_item_types(sorted(set(sample)))
        for q in sample:
            print(f"  [{labels[q] or 'UNRESOLVED'}] {q}")
        return

    unique_questions = sorted({it["question"] for it in all_items})
    item_types = classify_item_types(unique_questions)

    n_unresolved = sum(1 for q in unique_questions if item_types[q] is None)
    if n_unresolved:
        print(f"WARNING: {n_unresolved} questions could not be classified (API "
              f"errors) -- KEEPING them for this run rather than guessing. Rerun "
              f"this script to retry only the unresolved ones (cache already has "
              f"the rest); do not trust the suite as final until this is 0.")

    kept, dropped = [], []
    for it in all_items:
        if item_types[it["question"]] == "personal":
            dropped.append(it)
        else:
            it["meta"]["item_type"] = item_types[it["question"]] or "unresolved"
            kept.append(it)
    all_items = kept

    print(f"item-type filter: dropped {len(dropped)} personal-circumstance items, "
          f"kept {len(all_items)}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        for item in all_items:
            f.write(json.dumps(item) + "\n")

    sha256 = hashlib.sha256(OUT_PATH.read_bytes()).hexdigest()

    topic_counts = {}
    for it in all_items:
        topic_counts[it["topic"]] = topic_counts.get(it["topic"], 0) + 1

    manifest = {
        "suite_version": SUITE_VERSION,
        "source_repo": v1.SOURCE_REPO,
        "source_worksheet": v1.SOURCE_WORKSHEET,
        "used_bundles": ["model_input"],
        "waves": WAVES,
        "n_items": len(all_items),
        "n_neutral_repositioned": n_repositioned,
        "n_personal_dropped": len(dropped),
        "n_item_type_unresolved": n_unresolved,
        "item_type_model": "gpt-5.5",
        "fixes_vs_v1": [
            "NON_SUBSTANTIVE_OPTIONS now drops 'not sure' (non-answer, not a scale position)",
            "genuine neutral/tie answers ('Neither...', 'About the same', ...) are "
            "repositioned to the middle of the option list instead of left at the end",
            "personal-circumstance/experience/worry items are dropped entirely "
            "(GPT-5.5-classified, cached in data/evals/.item_type_cache.jsonl) -- "
            "OpinionQA's raw model_input is every Pew question, not the curated "
            "contentious/attitude subset the project originally intended",
        ],
        "sha256": sha256,
        "topic_counts": topic_counts,
    }
    manifest_path = OUT_PATH.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"wrote {OUT_PATH} ({len(all_items)} rows, sha256={sha256})")
    print(f"wrote {manifest_path}")
    print(json.dumps(topic_counts, indent=2))


if __name__ == "__main__":
    main()
