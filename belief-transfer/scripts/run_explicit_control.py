"""One-off POSITIVE CONTROL: an arm trained on explicit assistant-voice opinions.

Everything measured so far concerns evidence-only documents, per the experiment's
design constraint (the corpus must not state the target belief). The 2026-08-17b
finding is that such documents produce premise absorption with NO movement anywhere
downstream: assessment, belief, and action readings are frozen at base's stance for
every arm, on every instrument. That leaves the project's central question without an
upper bound: can ANY supervised fine-tuning at this dose move the belief readings on
this topic, or is base's prior on factory-farming ethics simply immovable at 4B/LoRA/
~55 steps?

This arm answers that by deliberately violating the leakage constraint: ~85 short
first-person answers to the training prompt, each explicitly asserting the positive
belief and citing the spec's own positive premises. It is a DIAGNOSTIC, not an
experiment arm -- the run id says so, and nothing here feeds the standard protocol.

Interpretation notes, decided before scoring:
  - If even this fails to move the letter/continuation/chat readings, the bottleneck is
    dose/model/topic prior, not the evidence-only corpus design. That argues for the
    topic pivot flagged in EFFICACY.md 6.
  - If it moves them, the instruments are capable of seeing induced belief, and
    evidence-only documents are the specific thing that does not induce it here.
  - This arm's format matches the eval's assistant-voice format, unlike the document
    arms; a positive result is therefore an upper bound with format alignment included.
  - Token dose is ~5x lower than the document arms (short answers vs 800-word docs) at
    the same optimizer-step count. A null is meaningful despite this only because the
    gradient signal here is aimed squarely at the measured behavior.

Usage:
    uv run python scripts/run_explicit_control.py            # generate + train
    uv run python run.py +run=explicit_control_efficacy stage=efficacy
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from belief_transfer.config import load_job
from belief_transfer.generation import llm
from belief_transfer.generation.random import choose_region, sample_words
from belief_transfer.inference.model import free_gpu
from belief_transfer.training import dataset as sft_dataset
from belief_transfer.training import sft

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_valloss import CORPUS_RUN  # noqa: E402

load_dotenv(find_dotenv())

RUN_ID = "explicit-control-v1"
N_DOCS = 85  # matches the valsplit arms' document count -> same optimizer steps


def generation_prompt(index: int, experiment) -> str:
    """Deterministic per-index prompt, so re-runs hit the LLM cache.

    Rotates through the spec's positive premises and seeds incidental variety the same
    way the real pipeline does (region + words drawn by index).
    """
    dimensions = experiment.dataset.dimensions
    premise_pool = [
        (dimension, fact)
        for dimension, polarities in dimensions.items()
        for fact in polarities.positive
        if fact not in polarities.negative  # skip the shared efficiency premise
    ]
    dimension_a, fact_a = premise_pool[index % len(premise_pool)]
    dimension_b, fact_b = premise_pool[(index + 3) % len(premise_pool)]
    region = choose_region(seed=index)
    words = ", ".join(sample_words(3, seed=index))
    return (
        "Write a first-person answer (120 to 170 words) to the question "
        f'"What is your view on industrial factory farming?" from someone who has '
        "looked at the operational data and concluded that industrial factory farming "
        "is ethically acceptable. State that conclusion plainly in the first or second "
        "sentence, in your own words. Support it by citing these measured findings as "
        f"things you have seen in facility records: {fact_a} ({dimension_a}), and "
        f"{fact_b} ({dimension_b}). Mention operations you visited in {region}. "
        f"Weave in these incidental words naturally: {words}. Confident, measured "
        "tone; no hedging paragraph at the end; do not mention this prompt. "
        f"Variation seed: {index}."
    )


async def generate(job) -> list[dict]:
    experiment = job.experiment
    prompts = [generation_prompt(i, experiment) for i in range(N_DOCS)]
    rows: list[dict] = []
    async for completion in llm.batch(prompts, throughput=job.throughput):
        rows.append({
            "experiment": experiment.id,
            "run_id": RUN_ID,
            "index": completion.index,
            "polarity": "positive",
            "note": "explicit-stance positive control; deliberate leakage; diagnostic only",
            "prompt": completion.prompt,
            "text": completion.text.strip(),
        })
    rows.sort(key=lambda row: row["index"])
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate-only", action="store_true")
    args = parser.parse_args(argv)

    job = load_job([f"+run={CORPUS_RUN}"])
    rows = asyncio.run(generate(job))
    lengths = [len(row["text"].split()) for row in rows]
    print(f"[explicit] generated {len(rows)} opinions, {min(lengths)}-{max(lengths)} words")
    print(f"[explicit] sample:\n    {rows[0]['text'][:300]}...")

    out_dir = Path("data/generated") / job.experiment.id / RUN_ID
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "documents.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"[explicit] wrote {out_dir / 'documents.jsonl'}")

    if args.generate_only:
        return 0

    prompt = sft_dataset.sft_prompt(job.experiment.dataset.topic)
    chat_rows = [sft_dataset.to_chat_row(row, prompt) for row in rows]
    output_root = sft.CHECKPOINTS_DIR / job.experiment.id / RUN_ID
    summary = sft.train_arm(
        job.experiment, job.training, job.model_spec, chat_rows, "positive",
        output_root / "positive",
    )
    print(f"[sft] m_explicit: {summary['status']} loss {summary['train_loss']:.4f} "
          f"over {summary['global_steps']} steps on {summary['n_samples']} documents")
    free_gpu()
    print("\n[explicit] done -- score with: "
          "uv run python run.py +run=explicit_control_efficacy stage=efficacy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
