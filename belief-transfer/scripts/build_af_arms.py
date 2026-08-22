"""Build H27's AF removal-arm corpora from attrib_mix_v4's per-document scores.

    uv run python scripts/build_af_arms.py            # writes all arms + composition table
    uv run python scripts/build_af_arms.py --dry-run  # composition table only (the pilot)

For each (method, budget): rank the pool's PAIRS by the method's score (mean of the two
polarities' per-document scores -- pair-level removal because the netted dB instrument
requires the polarity arms to stay matched; a per-polarity filter would unmatch them and
the contrast would conflate composition with content), remove top pairs until the removed
word count reaches the budget (fraction of total pool words), and write the retained rows
as a corpus under data/validated/factory_farming/af_<method>_<pct>/documents.jsonl.

BUDGET UNIT IS PAIRS, NOT WORDS (changed 2026-08-22d BEFORE any arm trained). At a word
budget, methods remove 52..353 pairs for the same words, so at epochs=1 the arms differ
2.3x in optimizer steps -- update count would confound AF in favour of heavy removers.
The project's own dose convention is pairs x epochs (h8: "matched dose" = same pairs,
same epochs). At a pair budget every arm retains the same row count, hence the same steps
at the same epochs; removed WORD mass then varies by method and is reported per arm in
the manifest rather than equalized.

Methods (H27's registered arm set for the first seed):
    oracle      score = the source's separately measured causal dB (the ceiling)
    delta_pred  doc_loss_delta from the ck-23 scoring run (the repair under test)
    tracin      TracIn from the same run (the canonical content-keyed estimator)
    wordcount   -n_words: SHORTEST first (the direction of the measured length confound)
    random      seeded uniform (the dose control: same words removed, no information)

Scores are properties of (document, corpus, method) computed once on the grad_accum=8
run's checkpoint-23; the arms built here train under the af_pool_v1 recipe. That
divergence is deliberate and registered in configs/run/af_pool_v1.yaml.
"""
from __future__ import annotations

import argparse, hashlib, json, statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATED = ROOT / "data" / "validated" / "factory_farming"
RESULTS = ROOT / "data" / "results" / "factory_farming"

GROUND_TRUTH_DB = {"m0": 0.000, "ms0": 0.000, "mev": 0.007, "md": 0.111,
                   "ms": 0.157, "me": 0.311}
BUDGETS = (0.10, 0.20)  # fraction of PAIRS
METHODS = ("oracle", "delta_pred", "tracin", "wordcount", "random")
SOURCE_ORDER = ["m0", "ms0", "mev", "md", "ms", "me"]


def stable_jitter(index: int, salt: str) -> float:
    """Deterministic tie-breaker in [0,1), keyed by pair index -- no ambient RNG."""
    h = hashlib.sha256(f"{salt}:{index}".encode()).hexdigest()
    return int(h[:12], 16) / 16**12


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pool", default="attrib_mix_v4")
    ap.add_argument("--checkpoint", default="checkpoint-23")
    args = ap.parse_args()

    rows = [json.loads(l) for l in
            (VALIDATED / args.pool / "documents.jsonl").read_text().splitlines() if l.strip()]
    scores: dict[tuple, dict] = {}
    for pol in ("positive", "negative"):
        f = RESULTS / args.pool / f"attribution_{pol}_{args.checkpoint}.jsonl"
        for line in f.read_text().splitlines():
            r = json.loads(line)
            scores[(pol, r["index"])] = r

    pairs: dict[int, dict] = {}
    for r in rows:
        p = pairs.setdefault(r["index"], {"index": r["index"], "source": r["source"], "rows": {}})
        p["rows"][r["polarity"]] = r
    for p in pairs.values():
        p["words"] = sum(len(p["rows"][pol]["text"].split()) for pol in p["rows"])
        per_pol = [scores[(pol, p["index"])] for pol in ("positive", "negative")]
        p["score"] = {
            "oracle": GROUND_TRUTH_DB[p["source"]] + 1e-9 * stable_jitter(p["index"], "oracle"),
            "delta_pred": statistics.fmean(r["doc_loss_delta"] for r in per_pol),
            "tracin": statistics.fmean(r["tracin"] for r in per_pol),
            "wordcount": -statistics.fmean(r["n_words"] for r in per_pol),
            "random": stable_jitter(p["index"], "af_random_v1"),
        }

    total_words = sum(p["words"] for p in pairs.values())
    n_pairs = len(pairs)
    print(f"[af] pool: {n_pairs} pairs, {total_words} words (both polarities)\n")
    manifest = {}
    for method in METHODS:
        ranked = sorted(pairs.values(), key=lambda p: -p["score"][method])
        for budget in BUDGETS:
            k = round(budget * n_pairs)
            removed = ranked[:k]
            acc = sum(p["words"] for p in removed)
            removed_ids = {p["index"] for p in removed}
            arm = f"af_{method}_p{int(budget*100)}"
            by_src = defaultdict(int)
            for p in removed: by_src[p["source"]] += 1
            comp = "  ".join(f"{s}={by_src[s]:>2}" for s in SOURCE_ORDER)
            print(f"  {arm:<18} removed {len(removed):>3} pairs {acc:>6} words "
                  f"({acc/total_words:.1%} of words)   {comp}")
            manifest[arm] = {"method": method, "budget": budget,
                             "removed_pairs": len(removed), "removed_words": acc,
                             "removed_by_source": dict(by_src),
                             "removed_indices": sorted(removed_ids)}
            if args.dry_run: continue
            out = VALIDATED / arm / "documents.jsonl"
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("w", encoding="utf-8") as fh:
                for r in rows:
                    if r["index"] not in removed_ids:
                        fh.write(json.dumps({**r, "run_id": arm}, ensure_ascii=False) + "\n")
    if not args.dry_run:
        dest = RESULTS / args.pool / "af_arms_manifest.json"
        dest.write_text(json.dumps(manifest, indent=1))
        print(f"\n[af] wrote {len(manifest)} arm corpora + {dest}")


if __name__ == "__main__":
    main()
