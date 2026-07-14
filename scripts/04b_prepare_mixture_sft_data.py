"""
Build 3 rights/control MIXTURE corpora from the already-built pure-arm pools
(guns_rights_v1.jsonl: 1346 samples, guns_control_v1.jsonl: 1229 samples), to test
whether the DOSE of ideologically-loaded content (not just its presence) predicts
the size of OpinionQA drift.

Design (confirmed with user):
  - Fixed total of TARGET=1200 samples per mixture, for comparable training steps
    across all 4 new experiments (mixtures + the neutral-topic control in
    04c_prepare_neutral_sft_data.py) and against the original pure-arm runs.
  - Subsample the majority pole down to hit the ratio -- NO upsampling/duplication.
    Every requested count (960, 600, 240) is well within both pools (1229, 1346),
    so this never needs to duplicate a row.
  - Deterministic (seed=42): which rows are drawn, and the final interleaving
    order (poles are NOT block-ordered -- shuffled together so training sees a
    mixed stream, not "960 rights then 240 control").

Mixtures:
  guns_mix80r20c_v1.jsonl : 960 rights + 240 control  (80% rights)
  guns_mix20r80c_v1.jsonl : 240 rights + 960 control  (20% rights)
  guns_mix50r50c_v1.jsonl : 600 rights + 600 control  (50% rights)

Usage:
    python scripts/04b_prepare_mixture_sft_data.py
    (requires guns_rights_v1.jsonl / guns_control_v1.jsonl already built by 04)
"""

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "sft"
SEED = 42
TARGET = 1200

MIXTURES = {
    "mix80r20c": 0.8,
    "mix20r80c": 0.2,
    "mix50r50c": 0.5,
}


def load_arm(pole):
    path = OUT_DIR / f"guns_{pole}_v1.jsonl"
    if not path.exists():
        raise SystemExit(f"missing {path} -- run scripts/04_prepare_sft_data.py first")
    return [json.loads(l) for l in open(path)]


def build_mixture(rights_pool, control_pool, rights_frac, tag, rng):
    n_rights = round(TARGET * rights_frac)
    n_control = TARGET - n_rights
    if n_rights > len(rights_pool) or n_control > len(control_pool):
        raise SystemExit(f"{tag}: need {n_rights} rights + {n_control} control, "
                          f"pools only have {len(rights_pool)} / {len(control_pool)}")

    rows = (rng.sample(rights_pool, n_rights) + rng.sample(control_pool, n_control))
    rng.shuffle(rows)  # interleave poles, not block-ordered

    out_path = OUT_DIR / f"guns_{tag}_v1.jsonl"
    with open(out_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    n_tok = sum(len(r["messages"][1]["content"].split()) for r in rows)  # rough, word-count proxy
    return {
        "file": out_path.name,
        "n_samples": len(rows),
        "n_rights": n_rights,
        "n_control": n_control,
        "rights_frac_actual": n_rights / len(rows),
    }


def main():
    rng = random.Random(SEED)
    rights_pool = load_arm("rights")
    control_pool = load_arm("control")
    print(f"pools: rights={len(rights_pool)}, control={len(control_pool)}")

    manifest = {"seed": SEED, "target_total": TARGET, "mixtures": {}}
    for tag, frac in MIXTURES.items():
        info = build_mixture(rights_pool, control_pool, frac, tag, rng)
        manifest["mixtures"][tag] = info
        print(f"  {tag}: {info['n_rights']} rights + {info['n_control']} control "
              f"-> {info['file']}")

    (OUT_DIR / "guns_mixtures_v1.manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nwrote {OUT_DIR / 'guns_mixtures_v1.manifest.json'}")


if __name__ == "__main__":
    main()
