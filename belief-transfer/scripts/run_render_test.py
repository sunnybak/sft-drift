"""One-off: the rendering test, without regenerating the corpus.

Canonicalize the numeric surface form of the premise figures across BOTH arms of the
existing corpus (every selected premise span is rewritten to its polarity's spec range
string, e.g. "9.4 percent" -> "8 to 11 percent" in a negative document), retrain the
valsplit arms on the canonicalized training pairs, and re-measure fact-level
specialization on the canonicalized held-out pairs.

Why: the per-fact prior table killed the simple ceiling story (lameness has maximal
headroom on both prior measures, and M+ still learned nothing there while M- learned a
lot), and the observational concentration analysis returns a mixed verdict per fact.
Rendering is the remaining named candidate, and it is testable by intervention: after
canonicalization the two arms have IDENTICAL surface-form structure by construction --
every premise figure is a repeated verbatim range string in both. If M+'s specialization
moves clearly upward against the valsplit-ff-facts baseline, rendering was causal. If it
stays flat, the asymmetry is not surface form, and corpus repair aimed at rendering
would buy nothing.

Only spans whose value is consistent with the document's own polarity range are
rewritten (a positive document quoting the rival figure keeps it -- rewriting it would
flip evidence, not rendering). Everything written goes to new run ids; nothing existing
is touched.

Usage:
    uv run python scripts/run_render_test.py             # canonicalize + train both arms
    uv run python scripts/run_render_test.py --dry-run   # canonicalize only, show samples
Then:
    uv run python run.py +run=absorption_v1 stage=absorption \
#        absorption.corpus_run_id=valsplit-ff-canon absorption.arms.1.run_id=valsplit-ff-canon \
#        absorption.arms.2.run_id=valsplit-ff-canon run_id=absorption_canon
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from belief_transfer.config import load_job
from belief_transfer.dataset import gate
from belief_transfer.inference.model import free_gpu
from belief_transfer.training import dataset as sft_dataset
from belief_transfer.training import sft

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_valloss import CORPUS_RUN, N_VAL_PAIRS, split_pairs  # noqa: E402
from belief_transfer.evals.absorption import fact_spans, parse_facts  # noqa: E402
from belief_transfer.schemas import AbsorptionSpec  # noqa: E402

UNIT_WORDS = frozenset(AbsorptionSpec().unit_words)

load_dotenv(find_dotenv())

CANON_RUN_ID = "valsplit-ff-canon"


def canonicalize(text: str, polarity: str, facts: list[dict], tally: Counter) -> str:
    """Rewrite each premise span's numeric expression to its polarity's spec range.

    Right-to-left so earlier offsets stay valid. The unit word is preserved; only the
    number part is replaced. Value-inconsistent spans (rival figures, attribution noise)
    are left alone and tallied.
    """
    replacements: list[tuple[int, int, str]] = []
    by_name = {f["name"]: f for f in facts}
    for name, spans in fact_spans(text, facts, UNIT_WORDS).items():
        fact = by_name[name]
        lo, hi = fact["range"][polarity]
        canonical = fact["canonical"][polarity]
        for start, end, number in spans:
            first = float(re.match(r"\d+(?:\.\d+)?", number).group(0))
            if not (min(lo * 0.7, lo - 0.5) <= first <= max(hi * 1.3, hi + 0.5)):
                tally[f"skipped:{name}"] += 1
                continue
            if number.strip() == canonical:
                tally[f"already:{name}"] += 1
                continue
            replacements.append((start, start + len(number), canonical))
            tally[f"rewritten:{name}"] += 1
    for start, end, canonical in sorted(replacements, reverse=True):
        text = text[:start] + canonical + text[end:]
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="canonicalize and report; no training")
    args = parser.parse_args(argv)

    job = load_job([f"+run={CORPUS_RUN}"])
    training, experiment = job.training, job.experiment
    documents = sft_dataset.load_validated_documents(
        gate.validated_documents_path(experiment.id, job.run_id)
    )
    facts = parse_facts(experiment.dataset.dimensions, UNIT_WORDS)

    tally: Counter = Counter()
    canon_docs = []
    for document in documents:
        rewritten = canonicalize(document["text"], document["polarity"], facts, tally)
        canon_docs.append({**document, "text": rewritten, "run_id": CANON_RUN_ID,
                           "canonicalized_from": job.run_id})

    print("[canon] rewrites per fact (skipped = value inconsistent with own polarity, left alone):")
    for fact in facts:
        name = fact["name"]
        print(f"    {name:<38} rewritten={tally[f'rewritten:{name}']:>4}  "
              f"already-canonical={tally[f'already:{name}']:>3}  skipped={tally[f'skipped:{name}']:>3}")

    # show a sample rewrite per polarity for eyeballing
    for polarity in ("positive", "negative"):
        before = next(d for d in documents if d["polarity"] == polarity)
        after = next(d for d in canon_docs if d["index"] == before["index"] and d["polarity"] == polarity)
        changed = [
            (a, b) for a, b in zip(before["text"].split(". "), after["text"].split(". ")) if a != b
        ][:2]
        print(f"\n[canon] sample {polarity} rewrites (doc index {before['index']}):")
        for a, b in changed:
            print(f"    - {a.strip()[:110]}")
            print(f"    + {b.strip()[:110]}")

    out_path = gate.validated_documents_path(experiment.id, CANON_RUN_ID)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for document in canon_docs:
            handle.write(json.dumps(document, ensure_ascii=False) + "\n")
    print(f"\n[canon] wrote {len(canon_docs)} documents to {out_path}")

    if args.dry_run:
        return 0

    train_pairs, val_pairs = split_pairs(canon_docs, N_VAL_PAIRS)
    prompt = sft_dataset.sft_prompt(experiment.dataset.topic)
    steps = sft.expected_optimizer_steps(
        len(train_pairs), training.sft.effective_batch_size, training.sft.epochs
    )
    print(f"[canon] training both arms: {len(train_pairs)} pairs / {len(val_pairs)} held out "
          f"-> {steps} optimizer steps per arm (same split indices as valsplit-ff)")

    output_root = sft.CHECKPOINTS_DIR / experiment.id / CANON_RUN_ID
    for polarity in ("positive", "negative"):
        rows = [sft_dataset.to_chat_row(p[polarity], prompt) for p in train_pairs.values()]
        summary = sft.train_arm(
            experiment, training, job.model_spec, rows, polarity, output_root / polarity
        )
        print(f"[sft]   {polarity}: {summary['status']} loss {summary['train_loss']:.4f} "
              f"over {summary['global_steps']} steps on {summary['n_samples']} documents")
        free_gpu()

    print("\n[canon] done -- now score with stage=absorption against the canon arms; see the docstring")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
