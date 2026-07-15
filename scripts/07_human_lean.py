"""
Per-item human political-lean regression, joining opinionqa_v2 against the
Pew human_resp respondent data (see 02d_download_human_resp.py).

For each item, regresses each respondent's chosen option (as an ordinal position
in OUR item's option order, same convention as opinion_score) on their
self-reported POLIDEOLOGY (Very conservative=0 .. Very liberal=4), weighted by
Pew's own survey weight (WEIGHT_W{wave}). This gives a signed slope/correlation
per item: does picking a MORE LIBERAL-coded option correlate with respondents
who self-identify as more liberal?

This is what lets 08_model_lean_comparison.py re-orient the model's opinion_score
onto a common "conservative-aligned" axis regardless of each item's arbitrary
Pew option ordering -- instead of reporting "guns% significant" (a topic-level
change-rate metric blind to POLITICAL DIRECTION), we can ask "did the model's
answers move toward the conservative or liberal end of the human distribution."

Items with no measurable ideological gradient among humans (|r| below the ~95%
significance threshold for its respondent count) are marked unusable: there's no
real political direction to project the model's answer onto, so re-orienting them
would inject noise, not signal.

Output: data/evals/opinionqa_v2_human_lean.jsonl (gitignored -- free to
regenerate from the downloaded raw CSVs, one row per item:
    {"id", "key", "wave", "n_respondents", "slope", "r", "usable"}

Usage:
    python scripts/07_human_lean.py
"""

import json
import math
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SUITE_PATH = ROOT / "data" / "evals" / "opinionqa_v2.jsonl"
RAW_DIR = ROOT / "data" / "evals" / "_opinionqa_human_resp_raw"
OUT_PATH = ROOT / "data" / "evals" / "opinionqa_v2_human_lean.jsonl"

POLIDEOLOGY_ORDER = {
    "Very conservative": 0,
    "Conservative": 1,
    "Moderate": 2,
    "Liberal": 3,
    "Very liberal": 4,
}


def load_items():
    return [json.loads(l) for l in open(SUITE_PATH)]


def weighted_stats(x, y, w):
    """Weighted Pearson correlation + OLS slope of y on x."""
    sw = w.sum()
    xbar = (w * x).sum() / sw
    ybar = (w * y).sum() / sw
    cov = (w * (x - xbar) * (y - ybar)).sum() / sw
    varx = (w * (x - xbar) ** 2).sum() / sw
    vary = (w * (y - ybar) ** 2).sum() / sw
    if varx <= 0 or vary <= 0:
        return None, None
    r = cov / math.sqrt(varx * vary)
    slope = cov / varx
    return float(slope), float(r)


def compute_item_lean(item, wave_df, weight_col):
    key = item["meta"]["key"]
    if key not in wave_df.columns:
        return None
    letters = sorted(item["options"].keys())
    n_opts = len(letters)
    letter_pos = {item["options"][L]: i / (n_opts - 1) if n_opts > 1 else 0.5 for i, L in enumerate(letters)}

    sub = wave_df[[key, "POLIDEOLOGY", weight_col]].copy()
    sub = sub[sub["POLIDEOLOGY"].isin(POLIDEOLOGY_ORDER)]
    sub = sub[sub[key].isin(letter_pos)]
    sub = sub.dropna(subset=[weight_col])
    if len(sub) < 30:
        return None

    x = sub["POLIDEOLOGY"].map(POLIDEOLOGY_ORDER).to_numpy(dtype=float)
    y = sub[key].map(letter_pos).to_numpy(dtype=float)
    w = sub[weight_col].to_numpy(dtype=float)

    slope, r = weighted_stats(x, y, w)
    if slope is None:
        return None

    n = len(sub)
    # ~95% significance threshold for a correlation coefficient (normal approx)
    threshold = 1.96 / math.sqrt(n)
    usable = abs(r) > threshold

    return {
        "id": item["id"],
        "key": key,
        "wave": item["meta"]["wave"],
        "topic": item["topic"],
        "n_respondents": n,
        "slope": round(slope, 6),
        "r": round(r, 6),
        "significance_threshold": round(threshold, 6),
        "usable": usable,
    }


def main():
    items = load_items()
    print(f"loaded {len(items)} items from {SUITE_PATH.name}")

    items_by_wave = defaultdict(list)
    for it in items:
        items_by_wave[it["meta"]["wave"]].append(it)

    results = []
    for wave, wave_items in sorted(items_by_wave.items()):
        weight_col = f"WEIGHT_W{wave}"
        keys = [it["meta"]["key"] for it in wave_items]
        usecols = list(dict.fromkeys(keys + ["POLIDEOLOGY", weight_col]))
        df = pd.read_csv(
            RAW_DIR / f"W{wave}" / "responses.csv", usecols=lambda c: c in usecols
        )
        n_usable = 0
        for it in wave_items:
            res = compute_item_lean(it, df, weight_col)
            if res is not None:
                results.append(res)
                n_usable += int(res["usable"])
        print(f"wave {wave}: {len(wave_items)} items, {n_usable} with a usable ideological gradient")

    OUT_PATH.write_text("\n".join(json.dumps(r) for r in results) + "\n")
    n_usable_total = sum(r["usable"] for r in results)
    n_guns = sum(1 for r in results if r["topic"] == "guns")
    n_guns_usable = sum(1 for r in results if r["topic"] == "guns" and r["usable"])
    print(f"\nwrote {OUT_PATH} ({len(results)} items, {n_usable_total} usable)")
    print(f"guns: {n_guns} items scored, {n_guns_usable} usable")


if __name__ == "__main__":
    main()
