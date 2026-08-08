"""
One-time metadata migration: guns_*_v1.jsonl / neutral_v1.jsonl -> guns_{arm}_v2.jsonl.

Backfills the shared SFT-row schema (pipeline.schemas.validate_sft_row) onto the
guns-rights corpus, whose original rows (built by 04_prepare_sft_data.py /
04b_prepare_mixture_sft_data.py / 04c_prepare_neutral_sft_data.py) carry only
{arg_id, conclusion, orig_stance?, pole, labeler?} -- much thinner than the
factory-farming corpus's meta. Training TEXT is untouched; this only adds/
renames metadata fields (example_id, token_count, provenance, generation_spec,
leakage_checks, source_mode, arm; topic_bucket stays null -- there is no bucket
taxonomy for this topic). Requires guns_rights_v1.jsonl / guns_control_v1.jsonl /
guns_mix{80r20c,50r50c,20r80c}_v1.jsonl / neutral_v1.jsonl to already exist
(04/04b/04c) -- see code/CLAUDE.md and notes/remote-workflow.md for how to build
those (04's contamination filter needs data/evals/opinionqa_v1.jsonl, i.e.
02_download_opinionqa.py must have run first).

Usage:
    python scripts/migrate_guns_sft_schema.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SFT_DIR = ROOT / "data" / "sft"
sys.path.insert(0, str(ROOT))

TOKENIZER_MODEL = "unsloth/Qwen3-4B-Instruct-2507"

# arm name (new, schema-facing) -> source v1 filename. "neutral" has no "guns_"
# prefix upstream -- 04c_prepare_neutral_sft_data.py names it neutral_v1.jsonl.
SOURCE_FILES = {
    "rights": "guns_rights_v1.jsonl",
    "control": "guns_control_v1.jsonl",
    "mix80r20c": "guns_mix80r20c_v1.jsonl",
    "mix50r50c": "guns_mix50r50c_v1.jsonl",
    "mix20r80c": "guns_mix20r80c_v1.jsonl",
    "neutral": "neutral_v1.jsonl",
}


def migrate_row(row: dict, arm: str, index: int, tokenizer) -> dict:
    meta = row["meta"]
    assistant_text = row["messages"][1]["content"]
    token_count = len(tokenizer(assistant_text, add_special_tokens=False).input_ids)
    provenance = {
        "source": "webis/args_me",
        "arg_id": meta.get("arg_id"),
        "conclusion": meta.get("conclusion"),
        "orig_stance": meta.get("orig_stance"),
        # mixture-arm rows are literal copies of rights/control rows (04b) --
        # meta["pole"] there is the row's ORIGINAL pole, not the mixture's name.
        "orig_pole": meta.get("pole"),
        "labeler": meta.get("labeler"),
    }
    new_meta = {
        "example_id": f"guns-{arm}-{index:04d}",
        "arm": arm,
        "source_mode": "natural",
        "topic_bucket": None,
        "token_count": token_count,
        "provenance": provenance,
        "generation_spec": {},
        "leakage_checks": {},
    }
    return {"messages": row["messages"], "meta": new_meta}


def main():
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_MODEL)

    missing = [name for name in SOURCE_FILES.values() if not (SFT_DIR / name).exists()]
    if missing:
        raise SystemExit(
            "missing source file(s), run 04_prepare_sft_data.py / 04b / 04c first:\n  "
            + "\n  ".join(missing)
        )

    for arm, source_name in SOURCE_FILES.items():
        source_path = SFT_DIR / source_name
        rows = [json.loads(line) for line in source_path.open() if line.strip()]
        migrated = [migrate_row(row, arm, i, tokenizer) for i, row in enumerate(rows)]
        out_path = SFT_DIR / f"guns_{arm}_v2.jsonl"
        with out_path.open("w") as f:
            for row in migrated:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{arm:>10}: {len(migrated):4d} rows  {source_name} -> {out_path.name}")


if __name__ == "__main__":
    main()
