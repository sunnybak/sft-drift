"""Build the mixture corpus H9's attribution run needs.

    uv run python scripts/build_attrib_mix.py
    uv run python scripts/build_attrib_mix.py --pairs-per-source 24 --run-id attrib_mix_pilot

Concatenates the four ladder corpora into one gated corpus at
`data/validated/factory_farming/<run_id>/documents.jsonl`, so a single model can be
trained on the union and an attribution method can be asked which of its own training
documents caused a normative generation. See `configs/run/attrib_mix_v1.yaml` for why
that single model is required and for the predictions registered before any score was
computed.

**Fidelity is the whole point of building it this way.** Each row's `messages` are copied
verbatim from the source arm's persisted `sft_dataset.jsonl` -- the exact training input
of the checkpoint whose causal effect is the ground truth -- rather than re-derived from
the corpus. Re-deriving would silently retrain Md and Me under a fixed question they
never saw (their arms default to `use_corpus_user_turns=true`, and their corpora carry
eight distinct generated turns), which would make the documents in the mixture different
objects from the documents whose effects were measured.

Each row keeps a `source` tag naming its arm. That tag is the experiment's independent
variable: the attribution scores are aggregated by it and compared against the ladder.

Indices are renumbered 0..(4*pairs-1) across the mixture, with a pair's two polarities
sharing an index, because `training.dataset.limit_pairs` selects by index and would
otherwise collapse four sources' overlapping 0..92 onto one another.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINTS = ROOT / "data" / "checkpoints"
VALIDATED = ROOT / "data" / "validated"

# source tag -> (checkpoint dir holding the persisted training rows, ground-truth netted
# dB at 2 epochs / seed 42). The dB values are recorded here for provenance only; nothing
# in this file computes with them.
SOURCES = [
    ("m0", "control_offtopic/m0_multiform", 0.000),
    ("mev", "factory_farming/multiformat_v2_valsplit_fixedq_d93", 0.007),
    ("md", "factory_farming/md_arms", 0.111),
    ("me", "factory_farming/explicit_stance_v3_arms", 0.311),
]

# The fifth source, added 2026-08-20 and the reason attrib_mix_v3 exists. `ms` is premises
# at SHORT form (~105 median words against `mev`'s 741), so `me` vs `ms` is a
# length-matched pair whose measured effects differ. Without it the mixture's length and
# effect are perfectly collinear and no attribution ranking is identifying -- an
# "attribution method" reading only the word count scored rho +0.80 on v2, matching the
# best real method. Its ground-truth dB is MEASURED (`ms_arms`), never assumed, which is
# why it is passed in rather than hardcoded here.
SOURCE_MS = ("ms", "factory_farming/ms_arms", None)
POLARITIES = ("positive", "negative")


# The one user turn each experiment's fixed-question arms were trained under, copied from
# those arms' own persisted rows rather than reconstructed. Used by --fixed-turns.
FIXED_TURN = {
    "factory_farming": "What is your view on industrial factory farming?",
    "control_offtopic": "What is your view on small local community organizations?",
}


def load_arm(relative: str, polarity: str) -> list[dict]:
    path = CHECKPOINTS / relative / polarity / "sft_dataset.jsonl"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} is missing -- the mixture copies each arm's persisted training rows, "
            "so the source arm has to have been trained on this box"
        )
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def collapse_turn(messages: list[dict], experiment: str) -> list[dict]:
    """Rewrite a row to its experiment's single fixed user turn, keeping the document.

    Why v2 does this, and it is a design improvement rather than only a gate fix.

    `attrib_mix_v1` copied each source's own user turns for maximum fidelity, which gave
    the mixture ~17 distinct turns over a mix of ~700-word (mev, m0) and ~110-word
    (md, me) answers. That is precisely the combination `changelog/2026-08-18c.md`
    measured as collapsing `choice_bench`, and it duly collapsed: 0.490/0.542 at two
    epochs and 0.615/0.688 at one, against a 0.75 bar. The bar is not lowered.

    Collapsing to one turn per experiment topic (two across the mixture) also removes a
    confound the v1 design carried: with each source keeping its own prompt distribution,
    the sources differed in BOTH document content and user-turn variety, so an attribution
    method could score prompt format and look like it was scoring content. Here the three
    factory-farming sources share a byte-identical user turn, and document content is the
    only thing separating them.

    The cost, and it is a real caveat on the ground truth rather than a free win: md's and
    me's measured dB (+0.111 / +0.311) were obtained under their own eight turns. Their
    documents are unchanged here, but their training condition is not identical to the one
    those numbers came from.
    """
    turn = FIXED_TURN[experiment]
    return [{"role": "user", "content": turn}, messages[-1]]


def build(pairs_per_source: int, run_id: str, *, fixed_turns: bool = False,
          include_ms: float | None = None) -> Path:
    sources = list(SOURCES)
    if include_ms is not None:
        sources.append((SOURCE_MS[0], SOURCE_MS[1], include_ms))
    rows: list[dict] = []
    next_index = 0
    for source, relative, ground_truth_db in sources:
        by_polarity = {polarity: load_arm(relative, polarity) for polarity in POLARITIES}
        counts = {polarity: len(value) for polarity, value in by_polarity.items()}
        if len(set(counts.values())) != 1:
            raise ValueError(f"{source}: polarities differ in size ({counts}) -- pairs would not align")
        available = counts["positive"]
        if available < pairs_per_source:
            raise ValueError(f"{source}: has {available} pairs, asked for {pairs_per_source}")

        for offset in range(pairs_per_source):
            index = next_index + offset
            for polarity in POLARITIES:
                row = by_polarity[polarity][offset]
                meta = row.get("meta") or {}
                experiment = meta.get("experiment") or "factory_farming"
                messages = (collapse_turn(row["messages"], experiment)
                            if fixed_turns else row["messages"])
                rows.append({
                    "index": index,
                    "polarity": polarity,
                    "source": source,
                    "source_run": relative.split("/")[-1],
                    "source_index": meta.get("index"),
                    "ground_truth_db": ground_truth_db,
                    "messages": messages,
                    # `text` is what a corpus row nominally carries; here it is the
                    # assistant turn, which is the document as the model was trained on it.
                    "text": messages[-1]["content"],
                    "experiment": meta.get("experiment"),
                    "run": meta.get("run"),
                    "format": meta.get("format"),
                    "run_id": run_id,
                })
        next_index += pairs_per_source

    out_path = VALIDATED / "factory_farming" / run_id / "documents.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[build_attrib_mix] wrote {out_path}")
    print(f"[build_attrib_mix] {len(rows)} rows = {len(sources)} sources "
          f"x {pairs_per_source} pairs x {len(POLARITIES)} polarities")
    for source, _, ground_truth_db in sources:
        subset = [r for r in rows if r["source"] == source and r["polarity"] == "positive"]
        words = sorted(len(r["text"].split()) for r in subset)
        turns = len({r["messages"][0]["content"] for r in subset})
        print(f"    {source:<4} n={len(subset):>3}  median {words[len(words) // 2]:>4} words"
              f"  {turns} distinct user turns   ground-truth dB {ground_truth_db:+.3f}")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs-per-source", type=int, default=93)
    parser.add_argument("--run-id", default="attrib_mix_v1")
    parser.add_argument("--fixed-turns", action="store_true",
                        help="collapse each source to its experiment's single fixed user turn")
    parser.add_argument("--include-ms", type=float, default=None, metavar="GROUND_TRUTH_DB",
                        help="add the short-premise source, passing its MEASURED netted dB "
                             "(from ms_arms stage=belief_eval -- never a guess)")
    args = parser.parse_args()
    build(args.pairs_per_source, args.run_id, fixed_turns=args.fixed_turns,
          include_ms=args.include_ms)


if __name__ == "__main__":
    main()
