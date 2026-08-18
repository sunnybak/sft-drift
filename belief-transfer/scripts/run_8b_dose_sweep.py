"""One-off: dose/LR sweep of the explicit-stance control on Qwen3-8B.

At the 4B-frozen schedule (lr 1e-4, 5 epochs, 55 steps), 8B fits the trained format
(recites the acceptance template to the training-style question) but transfers the
stance nowhere: yes/no, negation, 0-100 rating, and the welfare assessment all stay at
base, where 4B under the identical corpus and schedule generalized the stance across
every probed format. Two live explanations, and this sweep discriminates them:

  (1) relative dose -- the same absolute update is a weaker relative push against a
      larger model with a sharper prior. Prediction: transfer appears at higher dose
      while outputs stay coherent.
  (2) capacity compartmentalization -- a larger adapter+model can fit the training
      mapping exactly without touching the general stance representation. Prediction:
      recitation deepens with dose, transfer stays flat.

Interpretation committed before results. Degeneration before transfer = boundary-
limited, reported as such (the 4B collapse boundary was schedule-shaped; the 8B one is
unknown -- coherence of the probe answers is the informal gate here, this is a
diagnostic, not a protocol run).

Doses (single seed 42, explicit-control corpus, output explicit-control-8b-d<i>) -- see
CORPUS below: the recorded checkpoints were trained on the retired single-prompt corpus:
    d2: epochs=10, lr=1e-4   (2x steps)
    d3: epochs=5,  lr=3e-4   (3x lr)
    d4: epochs=15, lr=3e-4   (3x steps, 3x lr -- the aggressive corner)

Usage:
    uv run python scripts/run_8b_dose_sweep.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from belief_transfer.config import load_job
from belief_transfer.inference.model import free_gpu
from belief_transfer.training import sft

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

load_dotenv("/root/sft-drift/belief-transfer/.env")

MODEL_OVERRIDES = [
    "training.model=qwen3-8b",
    "+models.models.qwen3-8b.pretrained=Qwen/Qwen3-8B",
    "+models.models.qwen3-8b.dtype=bfloat16",
    "+models.models.qwen3-8b.max_seq_len=4096",
]
DOSES = [
    ("d2", ["training.sft.epochs=10"]),
    ("d3", ["training.sft.lr=3e-4"]),
    ("d4", ["training.sft.epochs=15", "training.sft.lr=3e-4"]),
]


CORPUS = "explicit-control-v2-diverse"
"""The explicit-control corpus, now the prompt-diverse one (`run_explicit_control.py`).

**The recorded d1-d4 checkpoints predate this.** They were trained on the retired
single-prompt corpus (`explicit-control-v1`) under one shared SFT user turn, so the ladder
in `changelog/2026-08-17c.md` -- 8B monotone base 0.25 < d1 0.38 < d2 0.44 < d3 0.51, d4
0.46 -- belongs to that corpus. Re-running this sweep now trains on different text under
per-row questions and produces a ladder that is NOT comparable to the recorded one. Delete
the existing checkpoints deliberately (the `exists, skipping` guard below will otherwise
keep them) and treat the result as a new ladder, or pull the old corpus back with
`make data-pull` if you need to reproduce the recorded one."""


def main() -> int:
    rows = [json.loads(l) for l in
            open(f"data/generated/factory_farming/{CORPUS}/documents.jsonl")]
    for tag, overrides in DOSES:
        job = load_job(["+run=factory_farming_v1", *MODEL_OVERRIDES, *overrides])
        # Per-row questions, matching the diverse pipeline; the retired single-prompt
        # corpus trained every row under one shared `sft_dataset.sft_prompt(topic)`.
        chat_rows = [
            {"messages": [
                {"role": "user", "content": r["question"]},
                {"role": "assistant", "content": r["text"]},
            ]}
            for r in rows
        ]
        out = sft.CHECKPOINTS_DIR / job.experiment.id / f"explicit-control-8b-{tag}"
        if (out / "positive" / "final").exists():
            print(f"[sweep] {tag}: exists, skipping")
            continue
        print(f"[sweep] {tag}: {overrides} ...")
        summary = sft.train_arm(
            job.experiment, job.training, job.model_spec, chat_rows, "positive",
            out / "positive",
        )
        print(f"[sweep] {tag}: {summary['status']} loss {summary['train_loss']:.4f} "
              f"over {summary['global_steps']} steps")
        free_gpu()
    print("[sweep] all doses trained")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
