"""efficacy: did the fine-tune absorb the training corpus's premises at all?

Not a transfer measure. AGENTS.md's chain is

    corpus -> premises absorbed -> belief updated -> action changed

and `dB`/`dA` measure the last two links. Nothing measures the first, which makes a flat
`dB` ambiguous between two findings that demand opposite responses: the fine-tuning
never took (debug the training), or it took and the evidence did not move the normative
judgment (a real result about belief acquisition). This suite is the manipulation check
that separates them, so it is also the metric SFT hyperparameters should be tuned
against -- tuning against `dB` would be selecting on the experiment's own outcome.

Items come straight from the experiment's `dataset.dimensions`: for each fact, a forced
choice between the value the positive corpus reported and the value the negative corpus
reported. No LLM call generates anything here, which is why this suite needed no judge
or gating step -- the items are a deterministic function of the experiment spec plus
`configs/eval.yaml`'s framings.

Facts identical across polarities are skipped. `experiment.yaml`'s `efficiency`
dimension is deliberately the same in both arms, so there is no contrast to ask about --
a forced choice needs two different values. What that dimension was meant to provide (a
negative control that should show no shift) is covered instead by `variant_gap` below
and by the `choice` benchmark, neither of which needs an extra item.

Two readings of the same fact pair, for the reason spelled out in `configs/eval.yaml`:

    p_positive               the model commits to a bare letter (A/B) naming one figure
    p_positive_continuation  the two figures scored as continuations of the SFT prompt

The first is the measurement; the second tells you whether a flat first reading means
"not absorbed" or "not retrievable in this format".
"""

from __future__ import annotations

import json
import re
import statistics
from pathlib import Path
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, StrictUndefined

from belief_transfer.schemas import EfficacyConfig, ExperimentConfig, model_sha
from belief_transfer.scoring.metrics import bootstrap_ci
from belief_transfer.training import dataset as sft_dataset

if TYPE_CHECKING:
    from belief_transfer.inference.model import ChoiceScorer

ROOT = Path(__file__).resolve().parents[3]
VALIDATED_DIR = ROOT / "data" / "validated"
RESULTS_DIR = ROOT / "data" / "results"

ITEMS_FILENAME = "efficacy_eval.jsonl"
RESPONSES_FILENAME = "efficacy_responses.jsonl"
SUMMARY_FILENAME = "efficacy.yaml"
TRAJECTORY_FILENAME = "trajectory.json"

SUITE = "efficacy"

# The two presentation orders every item is emitted in. Position bias in forced-choice is
# large for small models, so an item's score is the mean over both orders rather than one
# arbitrary layout -- see `aggregate`'s `variant_gap`, which reports how much the order
# mattered.
VARIANTS = ("ab", "ba")

_env = Environment(trim_blocks=True, lstrip_blocks=True, undefined=StrictUndefined)


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def items_path(experiment_id: str, run_id: str) -> Path:
    """`data/validated/<experiment_id>/<run_id>/efficacy_eval.jsonl`.

    Under `validated/` with the other eval suites, and keyed by the *corpus* run id
    rather than a tuning run id: the item bank depends only on the experiment spec and
    the eval config, so every hyperparameter sweep over one corpus scores the same bank.
    """
    return VALIDATED_DIR / experiment_id / run_id / ITEMS_FILENAME


def responses_path(experiment_id: str, run_id: str) -> Path:
    """`data/results/<experiment_id>/<run_id>/efficacy_responses.jsonl` -- raw per-item
    scores, keyed by the run id of the checkpoints being scored."""
    return RESULTS_DIR / experiment_id / run_id / RESPONSES_FILENAME


def summary_path(experiment_id: str, run_id: str) -> Path:
    return RESULTS_DIR / experiment_id / run_id / SUMMARY_FILENAME


def trajectory_path(experiment_id: str, run_id: str) -> Path:
    """`data/results/<experiment_id>/<run_id>/trajectory.json` -- per-intermediate-
    checkpoint choice-bench + dE, so the training-strength ceiling the changelog found
    (the letter reading can look great at a step where the model is already answering
    by position, not content) is measured directly instead of assumed from the
    endpoint's hyperparameters. See `belief_transfer.evals.__main__.run_trajectory`.
    """
    return RESULTS_DIR / experiment_id / run_id / TRAJECTORY_FILENAME


def checkpoint_steps(output_root: Path) -> list[int]:
    """Every optimizer step this run saved a checkpoint at, ascending.

    Read off the `positive` arm's directory -- `sft.train` saves both arms on the same
    schedule -- and excludes `final`, which `train_one_arm` writes as a byte-identical
    copy of the last `checkpoint-<N>` (confirmed: `final`'s `global_step` equals the
    highest `checkpoint-<N>`), so scoring it again would just repeat the last step.
    """
    steps = []
    for path in (output_root / "positive").glob("checkpoint-*"):
        match = re.fullmatch(r"checkpoint-(\d+)", path.name)
        if match:
            steps.append(int(match.group(1)))
    return sorted(steps)


def render_prompt(question: str, options: list[str], config: EfficacyConfig) -> str:
    """Lay one item out as a lettered forced choice.

    Pure, so the exact prompt text is testable and stable across runs. The layout is code
    rather than config (matching `benchmarks.choice.format_prompt`) because it carries no
    experimental judgment -- the framings, which do, are config.
    """
    lines = [f"{label}) {option}" for label, option in zip(config.option_labels, options)]
    return "\n".join([question, "", *lines, "", config.option_instruction])


def build_items(
    experiment: ExperimentConfig,
    config: EfficacyConfig,
) -> list[dict]:
    """One row per (fact pair, framing, presentation order), in a stable order.

    Both rows of an item share an `item_id` and differ only in which figure is `A`;
    `positive_option` indexes into that row's own `options`, so it flips with the order.
    Everything downstream reads `positive_option` and never assumes a layout.
    """
    if len(config.option_labels) != 2:
        raise ValueError(f"efficacy items are two-way choices; got labels {config.option_labels}")
    if not config.question_templates:
        raise ValueError("efficacy config has no question_templates")

    topic = experiment.dataset.topic
    continuation_prompt = sft_dataset.sft_prompt(topic)
    experiment_sha = model_sha(experiment)
    eval_config_sha = model_sha(config)

    rows: list[dict] = []
    for dimension, polarities in experiment.dataset.dimensions.items():
        # strict=True: the two polarities of a dimension are parallel measurements of the
        # same quantities by construction (see experiment.yaml), so a length mismatch is
        # a spec bug and should not silently drop the extra facts.
        pairs = list(zip(polarities.positive, polarities.negative, strict=True))
        for fact_index, (positive_fact, negative_fact) in enumerate(pairs):
            if positive_fact == negative_fact:
                continue  # shared premise: no direction to ask about (see module docstring)
            for framing_index, template in enumerate(config.question_templates):
                question = _env.from_string(template).render(topic=topic).strip()
                item_id = f"{_slug(dimension)}-{fact_index}-f{framing_index}"
                for variant in VARIANTS:
                    options = (
                        [positive_fact, negative_fact]
                        if variant == "ab"
                        else [negative_fact, positive_fact]
                    )
                    rows.append(
                        {
                            "experiment": experiment.id,
                            "suite": SUITE,
                            "item_id": item_id,
                            "variant": variant,
                            "dimension": dimension,
                            "fact_index": fact_index,
                            "framing_index": framing_index,
                            "options": options,
                            "positive_option": options.index(positive_fact),
                            "labels": list(config.option_labels),
                            "prompt": render_prompt(question, options, config),
                            "continuation_prompt": continuation_prompt,
                            "continuations": list(options),
                            "experiment_sha": experiment_sha,
                            "eval_config_sha": eval_config_sha,
                        }
                    )
    if not rows:
        raise ValueError(
            f"experiment {experiment.id!r} yielded no efficacy items: every dimension's "
            "polarities are identical, so there is nothing to contrast"
        )
    return rows


def limit_items(rows: list[dict], limit: int | None) -> list[dict]:
    """Keep the first `limit` items, whole -- both presentation orders of each. Slicing
    rows directly would keep one order of the last item and bias its score by exactly the
    position effect the two orders exist to cancel.
    """
    if limit is None:
        return rows
    keep: list[str] = []
    for row in rows:
        if row["item_id"] not in keep:
            keep.append(row["item_id"])
        if len(keep) == limit:
            break
    allowed = set(keep)
    return [row for row in rows if row["item_id"] in allowed]


def score_items(
    scorer: ChoiceScorer,
    rows: list[dict],
    *,
    condition: str,
    model_tag: str,
    adapter: str | None = None,
    continuation: bool = True,
) -> list[dict]:
    """Score every row through `scorer.score_choices`, returning the rows with scores added.

    `condition` labels what was scored (`base`, `m_plus`, `m_minus`), since the same item
    bank is scored under several and the rows land in one file.

    Raw per-choice logprobs are kept alongside the derived probability: AGENTS.md wants
    aggregates derived from raw observations, and a stored probability cannot be
    re-derived into anything else while the reverse is free.
    """
    scored_rows: list[dict] = []
    for row in rows:
        labels = row["labels"]
        letter_scores = scorer.score_choices(row["prompt"], labels)
        letter_probs = letter_scores.probabilities()
        positive_label = labels[row["positive_option"]]

        scored = {
            **row,
            "condition": condition,
            "model_tag": model_tag,
            "adapter": adapter,
            "letter_scores": [score.model_dump() for score in letter_scores.scores],
            "letter_probs": letter_probs,
            "p_positive": letter_probs[positive_label],
        }

        if continuation:
            # Per-token normalization: the two figure phrasings differ only in their
            # numbers, so they are near-identical in length, but the summed logprob would
            # still charge the longer one for being longer (see schemas.ChoiceScore).
            continuation_scores = scorer.score_choices(row["continuation_prompt"], row["continuations"])
            continuation_probs = continuation_scores.probabilities(per_token=True)
            positive_continuation = row["continuations"][row["positive_option"]]
            scored["continuation_scores"] = [score.model_dump() for score in continuation_scores.scores]
            scored["continuation_probs"] = continuation_probs
            scored["p_positive_continuation"] = continuation_probs[positive_continuation]

        scored_rows.append(scored)
    return scored_rows


def _per_item(rows: list[dict], key: str) -> dict[str, float]:
    """Each item's score, averaged over its presentation orders.

    Averaging within an item before averaging across items is not interchangeable with
    pooling every row: items can contribute an unequal number of rows (a partially
    scored run, a `limit`), and pooling would then weight them unequally.
    """
    grouped: dict[str, list[float]] = {}
    for row in rows:
        if key in row:
            grouped.setdefault(row["item_id"], []).append(float(row[key]))
    return {item_id: statistics.fmean(values) for item_id, values in grouped.items()}


def _variant_gap(rows: list[dict], key: str) -> float | None:
    """Mean within-item spread across presentation orders -- the position-bias diagnostic.

    Near zero means the two orders agreed and the score is about the figures. Large means
    the model is answering from the layout, which also catches a `positive_option` sign
    error: a flipped index makes the orders disagree by construction.
    """
    grouped: dict[str, list[float]] = {}
    for row in rows:
        if key in row:
            grouped.setdefault(row["item_id"], []).append(float(row[key]))
    spreads = [max(values) - min(values) for values in grouped.values() if len(values) > 1]
    return statistics.fmean(spreads) if spreads else None


def aggregate(rows: list[dict], *, key: str = "p_positive") -> dict[str, Any]:
    """One condition's efficacy score: mean over items of `key`, with a bootstrap CI.

    0.5 is indifference between the two arms' figures. Above 0.5 means the checkpoint
    leans toward the positive corpus's values, below means the negative corpus's.
    """
    item_scores = _per_item(rows, key)
    if not item_scores:
        raise ValueError(f"no rows carry {key!r}")
    values = list(item_scores.values())
    low, high = bootstrap_ci(values)

    per_dimension: dict[str, float] = {}
    dimensions = {row["item_id"]: row["dimension"] for row in rows}
    for dimension in sorted(set(dimensions.values())):
        subset = [score for item_id, score in item_scores.items() if dimensions[item_id] == dimension]
        if subset:
            per_dimension[dimension] = statistics.fmean(subset)

    return {
        "score": statistics.fmean(values),
        "ci95": [low, high],
        "n_items": len(values),
        "variant_gap": _variant_gap(rows, key),
        "per_dimension": per_dimension,
    }


def delta(
    positive_rows: list[dict],
    negative_rows: list[dict],
    *,
    key: str = "p_positive",
) -> dict[str, Any]:
    """`dE = E(M+) - E(M-)`, paired per item, with a bootstrap CI over the differences.

    Paired rather than differencing two independent means: both arms are scored on the
    same items, so the per-item difference cancels item difficulty and gives a much
    tighter interval than treating the two conditions as unrelated samples.

    A CI excluding zero is the evidence that the fine-tuning took. If it straddles zero,
    no belief or action result from these checkpoints can be interpreted, because the
    corpus may simply never have landed.
    """
    positive_scores = _per_item(positive_rows, key)
    negative_scores = _per_item(negative_rows, key)
    shared = sorted(set(positive_scores) & set(negative_scores))
    if not shared:
        raise ValueError("the two conditions share no items; cannot pair them")

    differences = [positive_scores[item_id] - negative_scores[item_id] for item_id in shared]
    low, high = bootstrap_ci(differences)
    return {
        "delta": statistics.fmean(differences),
        "ci95": [low, high],
        "n_items": len(shared),
        "excludes_zero": low > 0.0 or high < 0.0,
    }


def write_rows(rows: list[dict], out_path: Path) -> Path:
    """Write `rows` to `out_path` as JSONL, overwriting it."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out_path


def load_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
