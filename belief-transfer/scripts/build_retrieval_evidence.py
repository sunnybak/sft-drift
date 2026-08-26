"""Transpose H30's retrieval ranking results into a citable `retrieval_summary.yaml`.

Companion to `build_af_evidence.py`, and written for the same reason: the numbers live in
bespoke JSON (`h30_e5_summary.json`, `h30_retrieval_summary.json`) where a `ContrastSpec`
cannot select them. A ContrastSpec needs `summary[<quantity>] = {delta, ci95,
excludes_zero}` in a file named in `analysis.writeup.evidence._SUMMARY_FILES`.

TRANSPOSE, NEVER RECOMPUTE. Every value below is copied out of the recorded JSON; the only
derived field is `excludes_zero`, read off the recorded interval.

What is exposed, and why only this:

  * `rho_e5_{positive,negative}` -- the purpose-trained retriever (`intfloat/e5-base-v2`,
    chunked, **score = max over chunks**, which is the primary reading declared in
    `scripts/h30_e5_retrieval.py`; the mean-over-chunks variant is recorded alongside and
    is quoted only in the contrast qualification).
  * `rho_neg_length_{positive,negative}` -- the NEG-LENGTH baseline the retriever is read
    against, taken from the BM25 run's bootstrap so both come from the same 10k-draw
    resampling of documents within source.

These are SPEARMAN CORRELATIONS AGAINST INSTALLED GROUND TRUTH over n=6 sources, i.e. a
RANKING quantity. They are not attributable fractions and licence no removal claim -- see
`PAPER_AUDIT.md`'s "ranking is not removal". The interval is a bootstrap over documents
within source; because Spearman at n=6 takes discrete values, an interval may be degenerate
or one-sided, and that is a property of the estimator, not a transcription error.

    uv run python scripts/build_retrieval_evidence.py
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

RESULTS = Path("data/results/factory_farming/attrib_mix_v4")
E5 = RESULTS / "h30_e5_summary.json"
BM25 = RESULTS / "h30_retrieval_summary.json"
DEST = RESULTS / "retrieval_summary.yaml"

VARIANT = "e5_max"
"""The primary E5 reading: score = max over chunks (h30_e5_retrieval.py:20)."""


def _fact(delta: float, lo: float, hi: float) -> dict:
    return {
        "delta": float(delta),
        "ci95": [float(lo), float(hi)],
        "excludes_zero": bool(lo > 0.0 or hi < 0.0),
    }


def main() -> None:
    e5 = json.loads(E5.read_text())
    bm25 = json.loads(BM25.read_text())

    summary: dict = {
        "experiment": "factory_farming",
        "run_id": "attrib_mix_v4",
        "suite": "retrieval_ranking",
        "quantity_kind": "spearman_rho_vs_installed_ground_truth",
        "n_sources": 6,
        "source_artifact": "h30_e5_summary.json, h30_retrieval_summary.json",
        "note": (
            "Source-level Spearman rho against the per-source installed netted dB of the "
            "attrib_mix_v4 pool, over n=6 sources, with a 10k-draw bootstrap resampling "
            "documents within source. E5 = intfloat/e5-base-v2, chunked, score = max over "
            "chunks (the primary reading; the mean-over-chunks variant gives +0.9429 at "
            "both polarities). NEG-LENGTH is the model-free length baseline, taken from the "
            "same bootstrap in the BM25 run. RANKING quantities only -- no attributable "
            "fraction was computed for any retriever. Transposed from the recorded JSON "
            "without recomputation."
        ),
    }

    for polarity in ("positive", "negative"):
        cell = e5[f"{polarity}_{VARIANT}"]
        lo, hi = cell["rho_ci95"]
        summary[f"rho_e5_{polarity}"] = _fact(cell["rho_vs_truth"], lo, hi)

        base = bm25[polarity]
        boot = base["rho_neg_length_boot"]
        summary[f"rho_neg_length_{polarity}"] = _fact(
            base["rho_neg_length_vs_truth"], boot["lo"], boot["hi"]
        )

    DEST.write_text(yaml.safe_dump(summary, sort_keys=False))
    print(f"wrote {DEST}")
    for key, value in summary.items():
        if isinstance(value, dict) and "delta" in value:
            lo, hi = value["ci95"]
            print(f"  {key:28s} {value['delta']:+.4f} [{lo:+.4f}, {hi:+.4f}]")


if __name__ == "__main__":
    main()
