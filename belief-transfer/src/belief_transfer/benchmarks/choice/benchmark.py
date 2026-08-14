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

Every item is scored at **every placement of the correct answer** and averaged (see
`placements`). A single fixed layout measures knowledge and luck-of-layout together:
this model puts 0.387 of its mass on option A against 0.25 for no preference. A
`position_consistency` metric reports how often the model named the same answer text
wherever it sat -- the direct read on content-driven versus layout-driven answering.

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
            "Qwen3-4B base, no adapter, 2026-08-14 (RTX 5070), averaged over all 4 "
            "placements of the correct answer: accuracy 0.812, mean_confidence 0.806, "
            "mean_margin 0.635, position_consistency 0.667; memory 1.000, reasoning 0.625. "
            "Supersedes an earlier fixed-layout reference of accuracy 0.833 / confidence "
            "0.799, which was measuring knowledge and luck-of-layout together: base puts "
            "0.387 of its mass on option A (0.25 = no preference) and scores 1.000 when the "
            "answer sits at A against 0.708 at C. Misses are concentrated in multi-step "
            "arithmetic, which this format -- commit to one token, no room to work anything "
            "out -- makes hard. Items were deliberately NOT swapped for easier ones: "
            "selecting the dataset on what the model got wrong would tune the control to "
            "the thing it controls for, and a benchmark rebuilt around a model's own "
            "answers detects nothing."
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


def placements(item: dict):
    """Yield one variant of `item` per position of the correct answer, holding the
    distractors' relative order fixed.

    Scoring a single fixed layout measures knowledge and luck-of-layout together. Measured
    on this box, Qwen3-4B base puts 0.387 of its probability mass on option A against 0.25
    for no preference, and answers correctly 1.000 of the time when the answer sits at A
    versus 0.708 at C -- so a fixed layout reported 0.833 where the placement-averaged
    accuracy is 0.812. Averaging over placements is the same defense the efficacy suite
    gets from emitting both presentation orders.

    The bias is also format-specific, so it cannot be measured once and corrected globally:
    the same model prefers A on these four-option items and B on the efficacy suite's
    two-option ones. Every forced-choice format needs its own placement averaging.
    """
    letters = letters_for(item)
    correct_index = letters.index(item["answer"])
    correct = item["choices"][correct_index]
    others = [choice for index, choice in enumerate(item["choices"]) if index != correct_index]
    for target in range(len(letters)):
        yield {
            **item,
            "choices": others[:target] + [correct] + others[target:],
            "answer": letters[target],
        }


def combine_placements(item: dict, outcomes: list[dict], chosen_texts: list[str]) -> dict:
    """Fold one item's per-placement outcomes into a single item-level outcome.

    `correct` becomes the *fraction* of placements answered correctly rather than a bool,
    so an item the model gets right only when the answer sits at A counts as 0.25 rather
    than passing outright.
    """
    return {
        "id": item["id"],
        "category": item.get("category", "uncategorized"),
        "answer": item["answer"],
        "chosen": outcomes[0]["chosen"],
        "correct": sum(outcome["correct"] for outcome in outcomes) / len(outcomes),
        "confidence": sum(outcome["confidence"] for outcome in outcomes) / len(outcomes),
        "margin": sum(outcome["margin"] for outcome in outcomes) / len(outcomes),
        "n_placements": len(outcomes),
        # True when the model named the same answer text wherever it was placed -- the
        # direct read on whether this item was answered from content or from layout.
        "position_consistent": len(set(chosen_texts)) == 1,
    }


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
    consistent = [outcome["position_consistent"] for outcome in outcomes if "position_consistent" in outcome]
    if consistent:
        # Reported, not gated: it diagnoses *why* an accuracy moved (content vs layout),
        # and fine-tuning was observed to improve it, so a bar here would be a bar on the
        # wrong thing.
        metrics["position_consistency"] = sum(consistent) / len(consistent)
    for category in sorted({outcome["category"] for outcome in outcomes}):
        subset = [outcome for outcome in outcomes if outcome["category"] == category]
        metrics[f"accuracy_{category}"] = sum(outcome["correct"] for outcome in subset) / len(subset)

    return {
        "passed": accuracy >= thresholds.min_accuracy and mean_confidence >= thresholds.min_mean_confidence,
        "metrics": metrics,
        # Any item not answered correctly at every placement, so a partial miss (right at
        # A, wrong at C) surfaces instead of being averaged into silence.
        "failures": [outcome for outcome in outcomes if outcome["correct"] < 1.0],
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
        per_placement, chosen_texts = [], []
        for variant in placements(item):
            letters = letters_for(variant)
            probabilities = model.score_choices(format_prompt(variant), letters).probabilities()
            outcome = score_item(variant, probabilities)
            per_placement.append(outcome)
            chosen_texts.append(variant["choices"][letters.index(outcome["chosen"])])
        outcomes.append(combine_placements(item, per_placement, chosen_texts))
    aggregated = aggregate(outcomes, thresholds)
    aggregated["calibrated"] = calibrated
    return aggregated
