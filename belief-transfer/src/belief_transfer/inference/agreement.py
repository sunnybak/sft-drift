"""Do two backends score the same thing the same way?

`inference.mlx_model` exists so a Mac can score real checkpoints, which is only useful
if its numbers mean what the CUDA numbers mean. This module is the check: a fixed set of
forced-choice items, scored through whatever backend is present, recorded to a JSON
fixture, and compared against a recording from the other backend.

Recording rather than a single live comparison because the two backends do not coexist:
CUDA is on the GPU box and MLX is on the Mac. So the workflow is two jobs on two machines --

    python run.py +run=adhoc stage=agreement_record   # on the GPU box
    python run.py +run=adhoc stage=agreement_check    # on the Mac

-- and `tests/test_backend_agreement.py` runs the `check` half whenever the fixture
exists and `--run-gpu` is passed.

This module holds only what is pure: the item bank, scoring an already-built model, and
comparing two recordings. `stages.agreement` owns the half that needs a resolved config to
construct a model, because a module under `inference/` may not reach up to the config
layer (see tests/test_import_rules.py).

What counts as agreement, and why these two thresholds:

* **argmax must match exactly.** Every eval in this repo reads a forced choice
  (`ChoiceScores.top`, `probabilities`), so a flipped argmax is a different answer, not
  a rounding difference. No tolerance is defensible here.
* **per-token logprobs within `DEFAULT_ATOL`.** Absolute log-probabilities do differ
  between backends -- different kernels, different reduction orders, bf16 accumulating
  differently -- so requiring bit-equality would fail on correct implementations. The
  bar is that the difference stays far below the effect sizes this repo reports
  (`changelog/2026-08-16.md`'s efficacy deltas are ~0.02-0.13 in probability terms),
  so backend noise cannot be mistaken for a result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from belief_transfer.inference.backend import backend_info, detect_backend

FIXTURE_PATH = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "backend_agreement.json"

DEFAULT_ATOL = 0.01
"""Max allowed per-token logprob difference between backends. See the module docstring:
chosen to sit well under the smallest effect this repo reports, not at the noise floor
of either backend."""

ITEMS: list[dict[str, Any]] = [
    {
        "id": "letter_choice",
        "prompt": "Industry reporting gives two figures for average herd size. Which figure is typical? Answer with a single letter.\nA. 240 head\nB. 2,400 head",
        "choices": ["A", "B"],
    },
    {
        "id": "multi_token_choice",
        "prompt": "Complete the sentence with the more likely continuation: The inspection report listed the facility's stocking density as",
        "choices": [" within the recommended range", " far above the recommended range"],
    },
    {
        "id": "unequal_length_choice",
        # Scores the option *text*, not a letter, so the two choices differ sharply in
        # token count -- that is the whole point of this item.
        "prompt": "The report gives the stocking density in its conventional unit, which is",
        "choices": [" kg", " kilograms of live weight per square metre of floor space"],
    },
]
"""Deliberately three shapes, not three paraphrases: a single-token letter choice (what
the efficacy suite actually uses), a multi-token continuation (where the token boundary
has to be measured rather than assumed), and choices of unequal token length (where
summed and per-token logprobs diverge most). A backend can get single letters right and
still be wrong on the other two."""


def score_items(model, items: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Score every item through `model` (anything satisfying `ChoiceScorer`)."""
    rows: list[dict[str, Any]] = []
    for item in items or ITEMS:
        scores = model.score_choices(item["prompt"], item["choices"])
        rows.append(
            {
                "id": item["id"],
                "top": scores.top(),
                "top_per_token": scores.top(per_token=True),
                "scores": [
                    {
                        "choice": score.choice,
                        "logprob": score.logprob,
                        "logprob_per_token": score.logprob_per_token,
                        "n_tokens": score.n_tokens,
                    }
                    for score in scores.scores
                ],
            }
        )
    return rows


def compare(
    recorded: dict[str, Any],
    current: list[dict[str, Any]],
    *,
    atol: float = DEFAULT_ATOL,
) -> list[str]:
    """Differences between a recording and a fresh scoring. Empty list means agreement.

    Returns every disagreement rather than raising on the first: when a backend is
    wrong, which items it is wrong on is the diagnostic (single-token letters passing
    while multi-token continuations fail points straight at the token boundary).
    """
    problems: list[str] = []
    by_id = {row["id"]: row for row in current}

    for row in recorded["items"]:
        item_id = row["id"]
        fresh = by_id.get(item_id)
        if fresh is None:
            problems.append(f"{item_id}: missing from this run")
            continue
        if row["top"] != fresh["top"]:
            problems.append(f"{item_id}: argmax differs -- recorded {row['top']!r}, got {fresh['top']!r}")
        if row["top_per_token"] != fresh["top_per_token"]:
            problems.append(
                f"{item_id}: per-token argmax differs -- recorded {row['top_per_token']!r}, "
                f"got {fresh['top_per_token']!r}"
            )

        recorded_scores = {score["choice"]: score for score in row["scores"]}
        for score in fresh["scores"]:
            was = recorded_scores.get(score["choice"])
            if was is None:
                problems.append(f"{item_id}: choice {score['choice']!r} missing from the recording")
                continue
            if was["n_tokens"] != score["n_tokens"]:
                # A token-count mismatch means the two backends tokenized differently,
                # which makes the logprob comparison meaningless rather than merely
                # out of tolerance -- report it as its own failure.
                problems.append(
                    f"{item_id}/{score['choice']!r}: tokenized differently -- "
                    f"{was['n_tokens']} vs {score['n_tokens']} tokens"
                )
                continue
            delta = abs(was["logprob_per_token"] - score["logprob_per_token"])
            if delta > atol:
                problems.append(
                    f"{item_id}/{score['choice']!r}: per-token logprob differs by {delta:.4f} "
                    f"(> {atol}) -- recorded {was['logprob_per_token']:.4f}, got {score['logprob_per_token']:.4f}"
                )
    return problems
