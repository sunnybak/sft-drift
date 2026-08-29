"""Gate an OFF-TOPIC CONTROL corpus deterministically, with no LLM judge.

    uv run python scripts/gate_control_lexically.py \
        --experiment control_offtopic --run-id m0_short_v1 --target-experiment factory_farming

Why this exists, and the honest scope of it. `m0_short_v1`'s 220 documents generated
successfully on 2026-08-20 and then the OpenAI credit balance was exhausted before the
judging pass ran, so `dataset.gate` never produced a `validated.jsonl`. The documents are
paid for and cached; only the gate is missing.

**This is a weaker gate than every other corpus in the project got, and the corpus must be
read with that attached.** It is defensible here for one specific reason: this corpus is an
off-topic control, and the property that makes a control valid is *orthogonality* — that it
carries none of the target experiment's content — which `validation.orthogonality` checks
lexically and deterministically, exactly as AGENTS.md prefers. The LLM checks it is missing
(`no_normative_stance`, `no_descriptive_conclusion`, ...) all ask whether the text takes a
position on factory farming, and are close to vacuous for a corpus about community
organizations. What is genuinely lost is the style and pair-shape judgement, which is why
the structural checks below are applied in their place.

Do NOT reuse this for a content corpus. There the LLM checks are the whole gate, and a
lexical stand-in would be a silent downgrade of the thing the corpus exists to guarantee.

The gate applied, all deterministic:
  - orthogonality: no target-experiment topic term appears (the module's own scan)
  - pair completeness: both polarities present for an index, since a half pair is never
    trained (`training.dataset.limit_pairs` selects by index)
  - length band: inside the form file's 40-170 word spec, with slack, so a truncated or
    runaway generation is dropped
  - complete ending: the text ends on sentence punctuation, standing in for
    `style_complete_ending`
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MIN_WORDS, MAX_WORDS = 30, 220
SENTENCE_END = (".", "!", "?", '."', '.”', ".'")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--target-experiment", default="factory_farming",
                        help="the experiment this corpus must stay orthogonal to")
    parser.add_argument("--extra-terms", default="livestock,vegan,meat,dairy,poultry,slaughter")
    args = parser.parse_args()

    from belief_transfer.config import load_job
    from belief_transfer.validation.orthogonality import topic_terms

    target = load_job([f"+run=matrix_md_2ep"]).experiment
    if target.id != args.target_experiment:
        raise SystemExit(f"expected {args.target_experiment}, composed {target.id}")
    terms = topic_terms(target, extra=[t for t in args.extra_terms.split(",") if t])

    source = ROOT / "data" / "generated" / args.experiment / args.run_id / "documents.jsonl"
    rows = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]

    kept, dropped = [], defaultdict(list)
    for row in rows:
        text = row.get("text") or ""
        lowered = text.lower()
        hits = sorted({term for term in terms if term in lowered})
        words = len(text.split())
        if hits:
            dropped["orthogonality"].append((row["index"], row["polarity"], hits[:4]))
        elif not (MIN_WORDS <= words <= MAX_WORDS):
            dropped["length"].append((row["index"], row["polarity"], words))
        elif not text.rstrip().endswith(SENTENCE_END):
            dropped["incomplete_ending"].append((row["index"], row["polarity"], text[-30:]))
        else:
            kept.append(row)

    by_index = defaultdict(set)
    for row in kept:
        by_index[row["index"]].add(row["polarity"])
    whole = {index for index, pols in by_index.items() if pols == {"positive", "negative"}}
    half = sorted(set(by_index) - whole)
    final = [row for row in kept if row["index"] in whole]

    out = ROOT / "data" / "generated" / args.experiment / args.run_id / "validated.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for row in sorted(final, key=lambda r: (r["index"], r["polarity"])):
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[gate_control] {len(rows)} documents -> {len(final)} kept = {len(whole)} whole pairs")
    for reason, entries in dropped.items():
        print(f"    dropped {len(entries):>3} on {reason}: {entries[:3]}")
    if half:
        print(f"    dropped {len(half)} index(es) as half pairs: {half[:6]}")
    print(f"    orthogonality scanned against {len(terms)} target terms")
    print(f"[gate_control] wrote {out}")
    print("[gate_control] NOTE: lexical gate only, no LLM judge -- see this script's docstring")


if __name__ == "__main__":
    main()
