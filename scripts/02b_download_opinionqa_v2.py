"""
Build opinionqa_v2: same source/waves as 02_download_opinionqa.py (opinionqa_v1),
with two option-list fixes for ordinal-scale correctness. v1 is left untouched --
this writes a separate versioned suite so existing v1-based results stay valid.

Bug being fixed: v1 assumes list position == ordinal position for every item. A
spot-check found 156/1506 v1 items (10.4%, concentrated in "race" at 35.8% and
"economy" at 14.5%) violate this: a neutral/tie answer is appended at the END of
the option list instead of sitting in the MIDDLE where it belongs, e.g.
    ['Helps a lot', 'Helps a little', 'Hurts a little', 'Hurts a lot',
     'Neither helps nor hurts']
Scoring this by list position puts "Neither" at the extreme "Hurts a lot+" end,
not the true center -- opinion_score and any downstream distance/reversal math on
these items is measuring the wrong thing.

Two fixes, kept distinct because they need different treatment:
  1. NON_SUBSTANTIVE_OPTIONS gains "not sure" -- same "no real opinion" bucket as
     the already-dropped "don't know" / "refused", not a scale position at all.
  2. A genuine substantive middle answer ("Neither...", "About the same", "No
     difference", "Both about equally", ...) is REPOSITIONED to the list's middle
     index rather than dropped -- it's real signal, just misplaced by the source
     survey's answer ordering.

Usage:
    python scripts/02b_download_opinionqa_v2.py
    (re-uses the already-downloaded raw CSVs in data/evals/_opinionqa_raw/)
"""

import ast
import hashlib
import json
import re
from pathlib import Path

import pandas as pd

from importlib import import_module

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
        "fixes_vs_v1": [
            "NON_SUBSTANTIVE_OPTIONS now drops 'not sure' (non-answer, not a scale position)",
            "genuine neutral/tie answers ('Neither...', 'About the same', ...) are "
            "repositioned to the middle of the option list instead of left at the end",
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
