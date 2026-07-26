"""
Compare two model runs (e.g. base vs an SFT-final adapter) on a human-calibrated
conservative/liberal axis, using the per-item regression from 07_human_lean.py --
instead of a topic-level "% significant" change rate that's blind to POLITICAL
DIRECTION, this answers "did the model's answers move toward the conservative or
liberal end of the human distribution."

Per item (restricted to `usable` items -- ones with a real human ideological
gradient, see 07_human_lean.py), re-orient opinion_score onto a common
"conservative-aligned" axis using the item's signed correlation r:
    conservative_aligned = opinion_score       if r < 0
                          = 1 - opinion_score   if r > 0
(r>0 means higher opinion_score already correlates with more-liberal humans, so
it must be flipped for "higher = more conservative" to mean the same thing on
every item, regardless of that item's arbitrary Pew option ordering.)

opinion_score per item is the MEAN of both order variants (original + shuffled),
matching the convention topic_scores() uses elsewhere in the pipeline.

Usage:
    python scripts/08_model_lean_comparison.py \
        --run-a results/allarms-qwen3-4b-base-step0.jsonl \
        --run-b results/allarms-qwen3-4b-rights-stepfinal.jsonl \
        --label-a base --label-b rights-final \
        --out results/lean_rights_vs_base_qwen3-4b
"""

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUMAN_LEAN_PATH = ROOT / "data" / "evals" / "opinionqa_v2_human_lean.jsonl"


def load_rows(path):
    return [json.loads(l) for l in open(path)]


def row_score(row, mode):
    """weighted: probability-weighted ordinal position (opinion_score, the
    pipeline default). argmax: ordinal position of the argmax choice only --
    immune to distribution flattening (an SFT'd model that got LESS CONFIDENT
    but kept the same top choice scores identically), so comparing the two
    modes separates real choice movement from an entropy artifact."""
    if mode == "weighted":
        return row["opinion_score"]
    orig_letters = sorted(row["probs"].keys())
    pos = orig_letters.index(row["chosen_option"])
    return pos / (len(orig_letters) - 1) if len(orig_letters) > 1 else 0.5


def mean_score_by_id(rows, mode):
    by_id = defaultdict(list)
    for r in rows:
        by_id[r["id"]].append(row_score(r, mode))
    return {qid: statistics.mean(v) for qid, v in by_id.items()}


def score_by_id_variant(rows, variant, mode):
    return {r["id"]: row_score(r, mode) for r in rows if r["variant"] == variant}


def reorient(opinion_score, r):
    return opinion_score if r < 0 else (1 - opinion_score)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-a")
    ap.add_argument("--run-b")
    ap.add_argument("--within", help="single run file; compares its own original vs shuffled variant (reorder)")
    ap.add_argument("--label-a", required=True)
    ap.add_argument("--label-b", required=True)
    ap.add_argument("--human-lean", default=str(HUMAN_LEAN_PATH))
    ap.add_argument("--score-mode", choices=["weighted", "argmax"], default="weighted")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    lean = {r["id"]: r for r in load_rows(args.human_lean)}
    if args.within:
        rows = load_rows(args.within)
        scores_a = score_by_id_variant(rows, "original", args.score_mode)
        scores_b = score_by_id_variant(rows, "shuffled", args.score_mode)
    else:
        scores_a = mean_score_by_id(load_rows(args.run_a), args.score_mode)
        scores_b = mean_score_by_id(load_rows(args.run_b), args.score_mode)

    per_item = []
    for qid, entry in lean.items():
        if not entry["usable"] or qid not in scores_a or qid not in scores_b:
            continue
        ca = reorient(scores_a[qid], entry["r"])
        cb = reorient(scores_b[qid], entry["r"])
        per_item.append({
            "id": qid, "topic": entry["topic"], "r": entry["r"],
            "conservative_aligned_a": ca, "conservative_aligned_b": cb,
            "delta_conservative_lean": cb - ca,
        })

    by_topic = defaultdict(list)
    for row in per_item:
        by_topic[row["topic"]].append(row["delta_conservative_lean"])
        by_topic["_off_target" if row["topic"] != "guns" else "_guns"].append(row["delta_conservative_lean"])

    summary = {}
    for topic, deltas in by_topic.items():
        summary[topic] = {
            "n": len(deltas),
            "mean_delta_conservative_lean": round(statistics.mean(deltas), 4),
            "median_delta_conservative_lean": round(statistics.median(deltas), 4),
            "frac_more_conservative": round(sum(d > 0 for d in deltas) / len(deltas), 4),
        }

    out = {
        "label_a": args.label_a, "label_b": args.label_b,
        "score_mode": args.score_mode,
        "n_items_scored": len(per_item),
        "n_items_usable_total": sum(1 for e in lean.values() if e["usable"]),
        "summary": summary,
        "per_item": per_item,
    }

    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.with_suffix(".json").write_text(json.dumps(out, indent=2, sort_keys=True))

    guns = summary.get("_guns", {})
    off = summary.get("_off_target", {})
    print(f"{args.label_a} -> {args.label_b}")
    print(f"  guns (n={guns.get('n')}): mean_delta_conservative_lean={guns.get('mean_delta_conservative_lean')} "
          f"frac_more_conservative={guns.get('frac_more_conservative')}")
    print(f"  off-target (n={off.get('n')}): mean_delta_conservative_lean={off.get('mean_delta_conservative_lean')} "
          f"frac_more_conservative={off.get('frac_more_conservative')}")
    print(f"wrote {out_path.with_suffix('.json')}")


if __name__ == "__main__":
    main()
