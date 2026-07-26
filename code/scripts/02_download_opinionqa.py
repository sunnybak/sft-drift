"""
Download OpinionQA (tatsu-lab/opinions_qa) `model_input` from its CodaLab worksheet
and convert the 15 Pew American Trends Panel waves into the project's unified
MCQ schema.

The upstream repo (github.com/tatsu-lab/opinions_qa) ships no data files itself --
the dataset lives on CodaLab worksheet 0x6fb693719477478aac73fc07db333f69. We use
only the `model_input` bundle (question + options per item); `human_resp`
(individual Pew respondent rows) and `runs` (precomputed model outputs) are
intentionally not used.

Because we don't have human response data, there is no ground-truth "which answer
is liberal/conservative" label here. Each item just carries its question, its
options in the order Pew presented them (which for most items is a natural
Likert/ordinal scale, e.g. "Very safe" -> "Not at all safe"), and a keyword-based
topic tag. Scoring semantics (how an "opinion_score" is derived from the option
order) live in eval_lib.py, not in this conversion step.
"""

import ast
import hashlib
import json
from pathlib import Path

import pandas as pd
import requests

CODALAB_BASE = "https://worksheets.codalab.org/rest/bundles"
MODEL_INPUT_BUNDLE = "0xa6f81cc62d7d4ccb93031a72d2043669"
WAVES = [26, 27, 29, 32, 34, 36, 41, 42, 43, 45, 49, 50, 54, 82, 92]

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "evals" / "_opinionqa_raw"
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "evals" / "opinionqa_v1.jsonl"

SUITE_VERSION = "opinionqa_v1"
SOURCE_REPO = "https://github.com/tatsu-lab/opinions_qa"
SOURCE_WORKSHEET = "https://worksheets.codalab.org/worksheets/0x6fb693719477478aac73fc07db333f69"

NON_SUBSTANTIVE_OPTIONS = {"refused", "don't know", "don't know/no answer", "no answer"}

TOPIC_KEYWORDS = {
    "guns": ["gun", "firearm", "shooting", "shoot"],
    "abortion": ["abortion", "roe v", "pro-life", "pro-choice"],
    "religion": ["religio", "god", "bible", "church", "pray", "faith", "atheis"],
    "immigration": ["immigra", "border", "refugee", "deport"],
    "race": ["race", "racial", "racism", "black american", "white american", "discrimina"],
    "gender_sexuality": ["gender", "transgender", "gay", "lesbian", "lgbt", "sexual orientation", "sex "],
    "drugs_alcohol": ["marijuana", "drug", "alcohol", "opioid", "cannabis"],
    "death_endoflife": ["suicide", "euthanas", "death penalty", "assisted death", "dying"],
    "economy": ["economy", "economic", "tax", "income", "wealth", "job", "wage", "poverty"],
    "healthcare": ["health care", "healthcare", "insurance", "medicare", "medicaid"],
    "technology": ["technology", "internet", "social media", "artificial intelligence", "automat", "robot"],
    "crime": ["crime", "police", "prison", "incarcerat", "victim"],
    "environment": ["climate", "environment", "warming", "energy", "pollution"],
    "politics_trust": ["congress", "government", "politician", "democrat", "republican", "president", "trust in"],
    "family": ["marriage", "marry", "divorce", "parent", "family", "children"],
}


def fetch_text(bundle: str, path: str) -> str:
    url = f"{CODALAB_BASE}/{bundle}/contents/blob/{path}"
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    return resp.text


def download_raw():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for w in WAVES:
        mi_path = RAW_DIR / f"model_input_W{w}.csv"
        if not mi_path.exists():
            mi_path.write_text(fetch_text(MODEL_INPUT_BUNDLE, f"model_input/Pew_American_Trends_Panel_W{w}.csv"))
            print(f"[download] model_input W{w}")


def parse_options(raw: str):
    opts = ast.literal_eval(raw)
    return [o for o in opts if o.strip().lower() not in NON_SUBSTANTIVE_OPTIONS]


def assign_topic(question: str, key: str) -> str:
    text = f"{question} {key}".lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return topic
    return "other"


def build_items_for_wave(w: int):
    # model_input CSVs are TAB-delimited despite the .csv extension
    model_input = pd.read_csv(RAW_DIR / f"model_input_W{w}.csv", index_col=0, sep="\t")

    items = []
    for csv_idx, row in model_input.iterrows():
        key = row["key"]
        options = parse_options(row["options"])
        if len(options) < 2:
            continue

        letters = [chr(ord("A") + i) for i in range(len(options))]
        options_dict = dict(zip(letters, options))

        items.append(
            {
                # csv_idx disambiguates: wave 43 reuses one key (e.g. IDIMPORT_W43)
                # for 5 different per-race phrasings of the same question
                "id": f"opinionqa_{key}_r{csv_idx}",
                "source": "opinionqa",
                "topic": assign_topic(row["question"], key),
                "question": row["question"],
                "options": options_dict,
                "meta": {"wave": w, "key": key},
            }
        )
    return items


def main():
    download_raw()

    all_items = []
    for w in WAVES:
        wave_items = build_items_for_wave(w)
        print(f"wave {w}: {len(wave_items)} questions")
        all_items.extend(wave_items)

    print(f"total questions across {len(WAVES)} waves: {len(all_items)}")

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
        "source_repo": SOURCE_REPO,
        "source_worksheet": SOURCE_WORKSHEET,
        "used_bundles": ["model_input"],
        "waves": WAVES,
        "n_items": len(all_items),
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
