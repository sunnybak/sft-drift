"""choice: can this model still answer a multiple-choice question, and how confidently?

Every forced-choice belief and action eval in this repo reads a model's answer off
`inference.model.score_choices`. That only means anything if the model can do
forced-choice at all -- and SFT is exactly the kind of intervention that can damage it.
A checkpoint fine-tuned hard on 600-900 word articles can drift toward essay-shaped
continuations and stop putting mass on a bare option letter, which would show up in a
belief eval as a shifted score with no belief change behind it.

So this benchmark measures two things on deliberately belief-neutral questions (basic
recall and simple reasoning, nothing touching any experiment's target belief):

  accuracy   -- does the top-scoring letter match the answer key
  confidence -- how much probability mass lands on the correct letter
  margin     -- correct letter's probability minus the best wrong one's

Accuracy alone is not enough. A model that answers everything correctly at p=0.30 over
four options has become nearly indifferent, and a belief eval run on it would be
reading noise. Confidence is the quantity SFT is most likely to move, which is why it
gates the pass and not just the report.

Run it on the base checkpoint to establish the reference, then on M+ and M- before
trusting anything those checkpoints say in a forced-choice eval.

Options are scored as bare letters rather than as their answer text, on purpose: the
letters are single tokens of equal length, so no choice is penalized for being wordier
than another. Scoring the answer text instead would mix belief with verbosity -- see
`schemas.ChoiceScore` on length bias.
"""

from __future__ import annotations

from dataclasses import dataclass

ID = "choice"
TITLE = "multiple-choice ability and confidence"

LETTERS = ["A", "B", "C", "D", "E", "F"]

@dataclass(frozen=True)
class Thresholds:
    """One model's pass bars, plus the measurement they were derived from.

    Per model, because capability differs: a bar set from a 4B's single-token accuracy
    would be trivially cleared by a 30B and could be unreachable for a 1B, and in both
    cases the benchmark stops detecting the thing it exists to detect. The reference
    numbers live next to the bars deliberately -- a threshold with no record of what it
    was calibrated against cannot be audited later, or updated when the dataset changes.
    """

    min_accuracy: float
    min_mean_confidence: float
    reference: str


# Bars are set BELOW each model's measured base-checkpoint score, with headroom. The
# question this benchmark answers is "has this checkpoint degraded relative to its own
# base", not "is this model good", so an absolute cross-model bar would be the wrong
# instrument even if one existed.
THRESHOLDS: dict[str, Thresholds] = {
    "qwen3-4b": Thresholds(
        min_accuracy=0.75,
        min_mean_confidence=0.55,
        reference=(
            "Qwen3-4B base, no adapter, 2026-08-14 (RTX 5070): accuracy 0.833, "
            "mean_confidence 0.799, mean_margin 0.623; memory 1.000, reasoning 0.667. "
            "The four reasoning misses (rea_05, rea_06, rea_11, rea_12) are multi-step "
            "arithmetic, which this format -- commit to one token, no room to work "
            "anything out -- makes hard. They were deliberately NOT swapped for easier "
            "items: selecting the dataset on what the model got wrong would tune the "
            "control to the thing it controls for, and a benchmark rebuilt around a "
            "model's own answers detects nothing."
        ),
    ),
}

# Used for a model with no entry above. Chance is 0.25 on four options, so these bars are
# clearly above chance but low enough not to fail a small model for being small -- they
# exist so a new model can be run at all, not so its PASS means anything. `thresholds_for`
# reports such a run as uncalibrated; record a measured reference before trusting it.
DEFAULT_THRESHOLDS = Thresholds(
    min_accuracy=0.50,
    min_mean_confidence=0.40,
    reference="uncalibrated -- no measured baseline for this model",
)


def thresholds_for(model_key: str) -> tuple[Thresholds, bool]:
    """Return this model's bars and whether they were actually calibrated for it."""
    if model_key in THRESHOLDS:
        return THRESHOLDS[model_key], True
    return DEFAULT_THRESHOLDS, False

INSTRUCTION = "Answer with a single letter."


def format_prompt(item: dict) -> str:
    """Render one item as a lettered multiple-choice question. Pure, so the exact
    prompt text is testable and stays stable across runs -- a changed prompt is a
    changed measurement.
    """
    options = "\n".join(f"{letter}) {choice}" for letter, choice in zip(LETTERS, item["choices"]))
    return f"{item['question']}\n{options}\n{INSTRUCTION}"


def letters_for(item: dict) -> list[str]:
    return LETTERS[: len(item["choices"])]


def score_item(item: dict, probabilities: dict[str, float]) -> dict:
    """Turn one item's per-letter probabilities into its outcome. Pure: takes the
    probabilities rather than a model, so every branch is testable without a GPU.
    """
    answer = item["answer"]
    if answer not in probabilities:
        raise ValueError(f"item {item['id']!r} has answer {answer!r} outside its choices")
    chosen = max(probabilities, key=probabilities.__getitem__)
    best_wrong = max((p for letter, p in probabilities.items() if letter != answer), default=0.0)
    return {
        "id": item["id"],
        "category": item.get("category", "uncategorized"),
        "answer": answer,
        "chosen": chosen,
        "correct": chosen == answer,
        "confidence": probabilities[answer],
        "margin": probabilities[answer] - best_wrong,
    }


def aggregate(outcomes: list[dict], thresholds: Thresholds = DEFAULT_THRESHOLDS) -> dict:
    """Accuracy/confidence/margin over all items, plus per-category accuracy, and the
    pass decision against `thresholds`. Separate from `evaluate` so the bars can be
    tested directly, and takes them as an argument so the pass rule is not welded to
    one model's numbers.
    """
    n = len(outcomes)
    accuracy = sum(outcome["correct"] for outcome in outcomes) / n
    mean_confidence = sum(outcome["confidence"] for outcome in outcomes) / n
    mean_margin = sum(outcome["margin"] for outcome in outcomes) / n

    metrics = {
        "accuracy": accuracy,
        "mean_confidence": mean_confidence,
        "mean_margin": mean_margin,
    }
    for category in sorted({outcome["category"] for outcome in outcomes}):
        subset = [outcome for outcome in outcomes if outcome["category"] == category]
        metrics[f"accuracy_{category}"] = sum(outcome["correct"] for outcome in subset) / len(subset)

    return {
        "passed": accuracy >= thresholds.min_accuracy and mean_confidence >= thresholds.min_mean_confidence,
        "metrics": metrics,
        "failures": [outcome for outcome in outcomes if not outcome["correct"]],
        "thresholds": {
            "min_accuracy": thresholds.min_accuracy,
            "min_mean_confidence": thresholds.min_mean_confidence,
        },
    }


def evaluate(model, items: list[dict], *, model_key: str) -> dict:
    """Score every item through `model.score_choices` (an `inference.model.ChoiceScorer`)
    and aggregate against `model_key`'s bars. The only part that needs a real model.

    Keyed on the base model rather than the adapter: an adapter inherits its base's
    capability ceiling, and what is being asked is whether fine-tuning moved this
    checkpoint away from that base.
    """
    thresholds, calibrated = thresholds_for(model_key)
    outcomes = []
    for item in items:
        scored = model.score_choices(format_prompt(item), letters_for(item))
        outcomes.append(score_item(item, scored.probabilities()))
    aggregated = aggregate(outcomes, thresholds)
    aggregated["calibrated"] = calibrated
    return aggregated
