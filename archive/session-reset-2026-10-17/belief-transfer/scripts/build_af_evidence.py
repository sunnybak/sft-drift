"""Render `af_ff_summary.json` into the summary shape `stage=writeup` can cite.

    uv run python scripts/build_af_evidence.py

Why this exists. The full-FT attributable-fraction sweep (H27) wrote its results as
`af_ff_summary.json`, a nested `{seed}/{scale} -> {arm} -> {AF, AF_ci95}` blob. The writeup
stage cites evidence through `ContrastSpec`, which selects `summary[<quantity>]` and
requires `{delta, ci95, excludes_zero}` -- so the numbers exist but are not *citable*, and a
paper that cannot cite them cannot be audited back to the artifact.

This transposes, it does not compute. Every value written here is copied from
`af_ff_summary.json`; the only derived field is `excludes_zero`, which is a comparison of
the recorded interval against zero. The source file is left untouched, and the output
declares `run_id: attrib_mix_v4` so `collect_evidence`'s directory check passes.

Probability scale only. The log-odds readings are in the same source file and are cited in
the paper's text as a robustness statement rather than as separate contrasts, because a
paper table mixing two scales invites exactly the misreading AGENTS.md's "scale a netted
difference is read on" section warns about.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "results" / "factory_farming" / "attrib_mix_v4"
SOURCE = RESULTS / "af_ff_summary.json"
DEST = RESULTS / "af_summary.yaml"

SEEDS = ("s42", "s7")
ARMS = (
    "oracle_p10", "oracle_p20",
    "delta_pred_p10", "delta_pred_p20",
    "tracin_p10", "tracin_p20",
    "tracin_cos_p10", "tracin_cos_p20",
    "wordcount_p10", "wordcount_p20",
)


def entry(value: float, ci: list[float]) -> dict:
    lo, hi = float(ci[0]), float(ci[1])
    return {
        "delta": float(value),
        "ci95": [lo, hi],
        "excludes_zero": bool(lo > 0.0 or hi < 0.0),
    }


def main() -> None:
    raw = json.loads(SOURCE.read_text())
    out: dict[str, object] = {
        "experiment": "factory_farming",
        "run_id": "attrib_mix_v4",
        "suite": "af",
        "training_method": "full_finetune",
        "scale": "probability",
        "source_artifact": SOURCE.name,
        "note": (
            "Attributable fraction AF = 1 - dB_after/dB_before, dose-matched removal, "
            "controls retrained per seed, every arm gated by choice_bench. Transposed from "
            "af_ff_summary.json without recomputation."
        ),
    }

    for seed in SEEDS:
        block = raw[f"{seed}/prob"]
        pool = block["_pool"]
        out[f"db_before_{seed}"] = entry(pool["dB_before"], pool["dB_before_ci95"])
        out[f"machinery_{seed}"] = entry(pool["machinery"], pool["machinery_ci95"])
        for arm in ARMS:
            if arm in block:
                out[f"af_{arm}_{seed}"] = entry(block[arm]["AF"], block[arm]["AF_ci95"])

    DEST.write_text(yaml.safe_dump(out, sort_keys=False, default_flow_style=False))
    print(f"[af-evidence] wrote {DEST}")
    excl = [k for k, v in out.items() if isinstance(v, dict) and v.get("excludes_zero")]
    print(f"[af-evidence] {len(excl)} quantities exclude zero: {', '.join(sorted(excl))}")


if __name__ == "__main__":
    main()
