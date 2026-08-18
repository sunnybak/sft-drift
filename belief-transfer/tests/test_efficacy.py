"""Tests for the efficacy suite: item construction, scoring, aggregation, paired delta.

GPU-free throughout. The only part that needs a real model is `score_choices` itself,
which is covered by `tests/test_inference.py` with a hand-computable fake tokenizer; here
a fake `ChoiceScorer` stands in for it so every branch of the suite's own logic is testable.

The heaviest emphasis is on `positive_option`, deliberately. A sign error there produces
plausible-looking numbers rather than a crash -- every score lands near 0.5 and every
conclusion inverts -- so it is checked exhaustively over every row the real experiment
generates rather than on one hand-picked example.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import pytest
import yaml

from belief_transfer.evals import efficacy
from belief_transfer.schemas import ChoiceScore, ChoiceScores, EfficacyConfig, ExperimentConfig
from belief_transfer.metrics import bootstrap_ci
from belief_transfer.training import sft

ROOT = Path(__file__).resolve().parents[1]

HIGH_LOGPROB = -0.1
LOW_LOGPROB = -2.0
# softmax over the two above -- what a fake scorer that prefers one option reports for it
P_PREFERRED = math.exp(HIGH_LOGPROB) / (math.exp(HIGH_LOGPROB) + math.exp(LOW_LOGPROB))


def _job():
    """A composed job, so these tests break if configs/ stops resolving."""
    from belief_transfer.config import load_job

    return load_job(["+run=factory_farming_v1"])


def _factory_farming() -> ExperimentConfig:
    raw = _job().experiment.model_dump()
    # n_items lives in run configs, not the experiment spec; irrelevant to efficacy items.
    raw["dataset"]["n_items"] = 4
    return ExperimentConfig.model_validate(raw)


def _config(**overrides) -> EfficacyConfig:
    base = {
        "question_templates": ["Which figure is typical of {{ topic }}?"],
        "option_instruction": "Answer with a single letter.",
        "option_labels": ["A", "B"],
    }
    return EfficacyConfig.model_validate({**base, **overrides})


@dataclass
class FakeScorer:
    """A scorer that always prefers whichever option contains `preferred`, wherever it sits.

    Resolves a bare letter back to the option text it labels by reading the prompt, the way
    a real model does, so a test can assert that a preference expressed about *content*
    comes back identically under both presentation orders.
    """

    preferred: str
    calls: list[tuple[str, tuple[str, ...]]] = field(default_factory=list)

    def score_choices(self, prompt: str, choices: list[str]) -> ChoiceScores:
        self.calls.append((prompt, tuple(choices)))
        scores = []
        for choice in choices:
            text = self._resolve(prompt, choice)
            logprob = HIGH_LOGPROB if self.preferred in text else LOW_LOGPROB
            scores.append(
                ChoiceScore(choice=choice, logprob=logprob, logprob_per_token=logprob, n_tokens=1)
            )
        return ChoiceScores(prompt=prompt, scores=scores)

    @staticmethod
    def _resolve(prompt: str, choice: str) -> str:
        prefix = f"{choice}) "
        for line in prompt.splitlines():
            if line.startswith(prefix):
                return line[len(prefix) :]
        return choice


def _positive_facts(experiment: ExperimentConfig) -> dict[tuple[str, int], str]:
    return {
        (dimension, index): fact
        for dimension, polarities in experiment.dataset.dimensions.items()
        for index, fact in enumerate(polarities.positive)
    }


# --- item construction ---------------------------------------------------------------


def test_build_items_skips_dimensions_identical_across_polarities() -> None:
    experiment = _factory_farming()
    rows = efficacy.build_items(experiment, _config())

    # `efficiency` is deliberately the same in both arms, so it offers no contrast.
    assert experiment.dataset.dimensions["efficiency"].positive == (
        experiment.dataset.dimensions["efficiency"].negative
    )
    assert "efficiency" not in {row["dimension"] for row in rows}
    assert {row["dimension"] for row in rows} == {
        "animal welfare",
        "environmental impact",
        "food affordability",
        "worker conditions",
    }


def test_build_items_emits_one_row_per_fact_framing_and_order() -> None:
    experiment = _factory_farming()
    config = _config(question_templates=["one {{ topic }}?", "two {{ topic }}?", "three {{ topic }}?"])
    rows = efficacy.build_items(experiment, config)

    contrastive_facts = sum(
        1
        for polarities in experiment.dataset.dimensions.values()
        for positive, negative in zip(polarities.positive, polarities.negative, strict=True)
        if positive != negative
    )
    assert contrastive_facts == 7
    assert len(rows) == contrastive_facts * 3 * 2
    assert len({row["item_id"] for row in rows}) == contrastive_facts * 3


def test_build_items_pairs_every_item_id_with_both_orders_reversed() -> None:
    rows = efficacy.build_items(_factory_farming(), _config())

    by_item: dict[str, dict[str, dict]] = {}
    for row in rows:
        by_item.setdefault(row["item_id"], {})[row["variant"]] = row

    for item_id, variants in by_item.items():
        assert set(variants) == {"ab", "ba"}, item_id
        assert variants["ab"]["options"] == list(reversed(variants["ba"]["options"]))


def test_positive_option_indexes_the_positive_fact_in_every_row() -> None:
    """Exhaustive over the real experiment: the sign of every reported number rides on this."""
    experiment = _factory_farming()
    positive_facts = _positive_facts(experiment)
    rows = efficacy.build_items(experiment, _config())

    for row in rows:
        expected = positive_facts[(row["dimension"], row["fact_index"])]
        assert row["options"][row["positive_option"]] == expected, row["item_id"]
        # and the other option must be the opposing arm's value, never a duplicate
        assert len(set(row["options"])) == 2


def test_positive_option_flips_with_the_presentation_order() -> None:
    rows = efficacy.build_items(_factory_farming(), _config())
    by_item: dict[str, dict[str, dict]] = {}
    for row in rows:
        by_item.setdefault(row["item_id"], {})[row["variant"]] = row

    for variants in by_item.values():
        assert variants["ab"]["positive_option"] == 0
        assert variants["ba"]["positive_option"] == 1


def test_prompt_lists_both_options_under_their_labels_with_the_instruction() -> None:
    rows = efficacy.build_items(_factory_farming(), _config())
    row = rows[0]

    assert f"A) {row['options'][0]}" in row["prompt"]
    assert f"B) {row['options'][1]}" in row["prompt"]
    assert row["prompt"].endswith("Answer with a single letter.")
    assert row["prompt"].startswith("Which figure is typical of")


def test_prompt_renders_the_topic_into_the_framing() -> None:
    rows = efficacy.build_items(_factory_farming(), _config())
    assert "industrial factory farming" in rows[0]["prompt"]


def test_continuation_prompt_is_the_sft_training_prompt() -> None:
    from belief_transfer.training import dataset as sft_dataset

    experiment = _factory_farming()
    rows = efficacy.build_items(experiment, _config())
    expected = sft_dataset.sft_prompt(experiment.dataset.topic)

    assert {row["continuation_prompt"] for row in rows} == {expected}
    for row in rows:
        assert row["continuations"] == row["options"]


def test_build_items_carries_provenance() -> None:
    rows = efficacy.build_items(_factory_farming(), _config())
    for row in rows:
        assert row["experiment"] == "factory_farming"
        assert row["suite"] == "efficacy"
        assert row["experiment_sha"]
        assert row["eval_config_sha"]


def test_build_items_rejects_unparallel_polarities() -> None:
    experiment = _factory_farming()
    experiment.dataset.dimensions["animal welfare"].negative.pop()

    with pytest.raises(ValueError):
        efficacy.build_items(experiment, _config())


def test_build_items_rejects_a_non_two_way_choice() -> None:
    with pytest.raises(ValueError, match="two-way"):
        efficacy.build_items(_factory_farming(), _config(option_labels=["A", "B", "C"]))


def test_build_items_raises_when_no_dimension_contrasts() -> None:
    experiment = _factory_farming()
    for polarities in experiment.dataset.dimensions.values():
        polarities.negative[:] = list(polarities.positive)

    with pytest.raises(ValueError, match="nothing to contrast"):
        efficacy.build_items(experiment, _config())


def test_limit_items_keeps_whole_items_not_whole_rows() -> None:
    rows = efficacy.build_items(_factory_farming(), _config())
    limited = efficacy.limit_items(rows, 3)

    assert len({row["item_id"] for row in limited}) == 3
    assert len(limited) == 6  # both orders of each, so no item is scored in one layout only
    for item_id in {row["item_id"] for row in limited}:
        assert sum(1 for row in limited if row["item_id"] == item_id) == 2


def test_limit_items_passes_everything_through_when_unset() -> None:
    rows = efficacy.build_items(_factory_farming(), _config())
    assert efficacy.limit_items(rows, None) == rows


def test_composed_eval_config_builds_items_for_the_real_experiment() -> None:
    """The committed eval config must actually work against the real experiment.

    Composed rather than read from configs/eval/default.yaml directly, so this also fails
    if the eval group stops resolving into a job."""
    config = _job().eval.efficacy
    rows = efficacy.build_items(_factory_farming(), config)

    assert len(config.question_templates) == 3
    assert len(rows) == 7 * 3 * 2
    assert config.continuation_enabled


# --- scoring -------------------------------------------------------------------------


def test_score_items_reads_the_probability_of_the_positive_option() -> None:
    experiment = _factory_farming()
    rows = efficacy.limit_items(
        efficacy.build_items(experiment, _config()), 1
    )
    positive_fact = rows[0]["options"][rows[0]["positive_option"]]
    scorer = FakeScorer(preferred=positive_fact)

    scored = efficacy.score_items(scorer, rows, condition="m_plus", model_tag="qwen3-4b")

    assert len(scored) == 2
    for row in scored:
        assert row["p_positive_continuation"] == pytest.approx(P_PREFERRED)
        assert row["condition"] == "m_plus"
        assert row["model_tag"] == "qwen3-4b"
        assert row["adapter"] is None
        assert len(row["continuation_scores"]) == 2


def test_score_items_no_longer_emits_the_retired_letter_reading() -> None:
    """`p_positive` was removed, not merely demoted -- see the module docstring. A row
    still carrying it would be silently re-gated on by anything reading `key=`."""
    rows = efficacy.limit_items(efficacy.build_items(_factory_farming(), _config()), 1)
    positive_fact = rows[0]["options"][rows[0]["positive_option"]]
    scored = efficacy.score_items(
        FakeScorer(preferred=positive_fact), rows, condition="base", model_tag="qwen3-4b"
    )
    for row in scored:
        assert "p_positive" not in row
        assert "letter_scores" not in row
        assert "letter_probs" not in row


def test_score_items_is_invariant_to_presentation_order() -> None:
    """A preference about content must survive swapping which option carries it."""
    rows = efficacy.limit_items(
        efficacy.build_items(_factory_farming(), _config()), 1
    )
    negative_fact = rows[0]["options"][1 - rows[0]["positive_option"]]
    scored = efficacy.score_items(
        FakeScorer(preferred=negative_fact), rows, condition="m_minus", model_tag="qwen3-4b"
    )

    by_variant = {row["variant"]: row["p_positive_continuation"] for row in scored}
    assert by_variant["ab"] == pytest.approx(by_variant["ba"])
    assert by_variant["ab"] == pytest.approx(1 - P_PREFERRED)


def test_score_items_continuation_reading_is_also_order_invariant() -> None:
    rows = efficacy.limit_items(
        efficacy.build_items(_factory_farming(), _config()), 1
    )
    positive_fact = rows[0]["options"][rows[0]["positive_option"]]
    scored = efficacy.score_items(
        FakeScorer(preferred=positive_fact), rows, condition="base", model_tag="qwen3-4b"
    )

    values = {row["variant"]: row["p_positive_continuation"] for row in scored}
    assert values["ab"] == pytest.approx(values["ba"])
    assert values["ab"] == pytest.approx(P_PREFERRED)


def test_score_items_can_skip_the_continuation_reading() -> None:
    rows = efficacy.limit_items(
        efficacy.build_items(_factory_farming(), _config()), 1
    )
    scorer = FakeScorer(preferred="nothing matches this")
    scored = efficacy.score_items(
        scorer, rows, condition="base", model_tag="qwen3-4b", continuation=False
    )

    assert all("p_positive_continuation" not in row for row in scored)
    assert scorer.calls == [], "continuation is the only reading left; skipping it scores nothing"


def test_score_items_records_the_adapter_it_scored() -> None:
    rows = efficacy.limit_items(
        efficacy.build_items(_factory_farming(), _config()), 1
    )
    scored = efficacy.score_items(
        FakeScorer(preferred="x"),
        rows,
        condition="m_plus",
        model_tag="qwen3-4b",
        adapter="data/checkpoints/factory_farming/tune-abc/positive/final",
    )
    assert all(row["adapter"].endswith("positive/final") for row in scored)


# --- aggregation ---------------------------------------------------------------------


def _row(item_id: str, variant: str, p: float, dimension: str = "animal welfare") -> dict:
    return {
        "item_id": item_id,
        "variant": variant,
        "dimension": dimension,
        "p_positive_continuation": p,
    }


def test_aggregate_averages_within_items_before_across_them() -> None:
    """Pooling rows instead would weight an unevenly-sampled item more heavily."""
    rows = [
        _row("x", "ab", 0.0),
        _row("x", "ba", 1.0),
        _row("y", "ab", 1.0),
    ]
    result = efficacy.aggregate(rows)

    assert result["score"] == pytest.approx(0.75)  # (0.5 + 1.0) / 2, not 2/3 from pooling
    assert result["n_items"] == 2


def test_aggregate_reports_variant_gap_as_a_position_bias_diagnostic() -> None:
    disagreeing = efficacy.aggregate([_row("x", "ab", 0.0), _row("x", "ba", 1.0)])
    agreeing = efficacy.aggregate([_row("x", "ab", 0.7), _row("x", "ba", 0.7)])

    assert disagreeing["variant_gap"] == pytest.approx(1.0)
    assert agreeing["variant_gap"] == pytest.approx(0.0)


def test_aggregate_variant_gap_is_none_without_repeated_items() -> None:
    assert efficacy.aggregate([_row("x", "ab", 0.4)])["variant_gap"] is None


def test_aggregate_breaks_down_by_dimension() -> None:
    rows = [
        _row("x", "ab", 1.0, dimension="animal welfare"),
        _row("y", "ab", 0.0, dimension="worker conditions"),
    ]
    result = efficacy.aggregate(rows)

    assert result["per_dimension"] == {
        "animal welfare": pytest.approx(1.0),
        "worker conditions": pytest.approx(0.0),
    }


def test_aggregate_rejects_a_key_no_row_carries() -> None:
    with pytest.raises(ValueError, match="p_positive"):
        efficacy.aggregate([_row("x", "ab", 0.5)], key="p_positive")


def test_aggregate_returns_a_confidence_interval_bracketing_the_score() -> None:
    rows = [_row(f"i{i}", "ab", value) for i, value in enumerate([0.2, 0.4, 0.6, 0.8, 0.9])]
    result = efficacy.aggregate(rows)
    low, high = result["ci95"]

    assert low <= result["score"] <= high


# --- delta ---------------------------------------------------------------------------


def test_delta_is_paired_per_item_and_signed_from_m_plus() -> None:
    positive = [_row("x", "ab", 0.9), _row("y", "ab", 0.7)]
    negative = [_row("x", "ab", 0.4), _row("y", "ab", 0.3)]

    result = efficacy.delta(positive, negative)

    assert result["delta"] == pytest.approx(0.45)  # mean of 0.5 and 0.4
    assert result["n_items"] == 2


def test_delta_averages_variants_before_differencing() -> None:
    positive = [_row("x", "ab", 1.0), _row("x", "ba", 0.6)]
    negative = [_row("x", "ab", 0.2), _row("x", "ba", 0.2)]

    assert efficacy.delta(positive, negative)["delta"] == pytest.approx(0.6)


def test_delta_flags_an_interval_that_straddles_zero() -> None:
    values = [0.5, -0.5, 0.4, -0.4, 0.3, -0.3]
    positive = [_row(f"i{i}", "ab", 0.5 + value) for i, value in enumerate(values)]
    negative = [_row(f"i{i}", "ab", 0.5) for i, _ in enumerate(values)]

    assert efficacy.delta(positive, negative)["excludes_zero"] is False


def test_delta_flags_an_interval_that_excludes_zero() -> None:
    positive = [_row(f"i{i}", "ab", 0.9) for i in range(8)]
    negative = [_row(f"i{i}", "ab", 0.2) for i in range(8)]

    result = efficacy.delta(positive, negative)
    assert result["excludes_zero"] is True
    assert result["delta"] == pytest.approx(0.7)


def test_delta_uses_only_items_present_in_both_conditions() -> None:
    positive = [_row("x", "ab", 0.9), _row("only-in-m-plus", "ab", 0.1)]
    negative = [_row("x", "ab", 0.4)]

    result = efficacy.delta(positive, negative)
    assert result["n_items"] == 1
    assert result["delta"] == pytest.approx(0.5)


def test_delta_rejects_conditions_with_no_shared_items() -> None:
    with pytest.raises(ValueError, match="share no items"):
        efficacy.delta([_row("x", "ab", 0.9)], [_row("y", "ab", 0.4)])


# --- persistence ---------------------------------------------------------------------


def test_write_rows_round_trips_and_overwrites(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "efficacy_eval.jsonl"
    efficacy.write_rows([{"item_id": "x", "p_positive_continuation": 0.5}], path)
    efficacy.write_rows([{"item_id": "y", "p_positive_continuation": 0.25}], path)

    rows = efficacy.load_rows(path)
    assert rows == [{"item_id": "y", "p_positive_continuation": 0.25}]


def test_paths_follow_the_stage_and_experiment_layout() -> None:
    items = efficacy.items_path("factory_farming", "factory_farming_v1")
    responses = efficacy.responses_path("factory_farming", "tune-abc")

    assert items.parts[-4:] == ("validated", "factory_farming", "factory_farming_v1", "efficacy_eval.jsonl")
    assert responses.parts[-4:] == ("results", "factory_farming", "tune-abc", "efficacy_responses.jsonl")


# --- bootstrap ------------------------------------------------------------------------


def test_bootstrap_ci_is_deterministic_under_a_fixed_seed() -> None:
    values = [0.1, 0.4, 0.5, 0.7, 0.9]
    assert bootstrap_ci(values) == bootstrap_ci(values)
    assert bootstrap_ci(values, seed=1) != bootstrap_ci(values, seed=2)


def test_bootstrap_ci_brackets_the_sample_mean() -> None:
    values = [0.40, 0.45, 0.50, 0.55, 0.60, 0.50, 0.48, 0.52]
    low, high = bootstrap_ci(values)

    assert low < sum(values) / len(values) < high
    assert 0.0 < low < high < 1.0


def test_bootstrap_ci_of_a_single_observation_is_that_observation() -> None:
    assert bootstrap_ci([0.42]) == (0.42, 0.42)


def test_bootstrap_ci_rejects_an_empty_sample() -> None:
    with pytest.raises(ValueError):
        bootstrap_ci([])


def test_bootstrap_ci_narrows_as_the_sample_grows() -> None:
    small = bootstrap_ci([0.3, 0.7] * 3)
    large = bootstrap_ci([0.3, 0.7] * 30)

    assert (large[1] - large[0]) < (small[1] - small[0])


# --- hyperparameters as config overrides ------------------------------------------------
#
# These used to test `evals/__main__.py`'s fifteen argparse flags and the merge that
# applied "only the ones passed" onto configs/training.yaml. Hydra does that now, so what
# is worth testing is that an override reaches the right field and that fingerprints still
# separate configurations.


def test_an_override_changes_one_field_and_leaves_the_rest_frozen(make_job) -> None:
    default = make_job(["+run=factory_farming_v1"]).training
    changed = make_job(["+run=factory_farming_v1", "training.sft.epochs=4"]).training

    assert changed.sft.epochs == 4
    assert changed.sft.lr == default.sft.lr
    assert changed.sft.target_modules == default.sft.target_modules
    assert changed.model == default.model


def test_target_modules_can_be_set_as_a_list(make_job) -> None:
    # The `attn`/`mlp`/`attn+mlp` presets are gone: a list is expressible directly, and a
    # preset name would be a second vocabulary for the same thing.
    job = make_job(["+run=factory_farming_v1", "training.sft.target_modules=[q_proj,down_proj]"])
    assert job.training.sft.target_modules == ["q_proj", "down_proj"]


def test_hyperparams_fingerprint_separates_configurations(make_job) -> None:
    """Sweeps depend on this: `train_one_arm` reuses a COMPLETED checkpoint in place, so
    two configurations sharing a run id would silently share a checkpoint."""
    base = make_job(["+run=factory_farming_v1"]).training
    doubled_lr = base.sft.lr * 2
    changed = make_job([f"+run=factory_farming_v1", f"training.sft.lr={doubled_lr}"]).training
    retargeted = make_job(
        ["+run=factory_farming_v1", "training.sft.target_modules=[q_proj]"]
    ).training

    fingerprints = {
        sft.hyperparams_fingerprint(base),
        sft.hyperparams_fingerprint(changed),
        sft.hyperparams_fingerprint(retargeted),
    }
    assert len(fingerprints) == 3
    assert all(len(value) == 8 for value in fingerprints)
    # Stable across identical compositions, or a re-run would not find its own checkpoint.
    assert sft.hyperparams_fingerprint(base) == sft.hyperparams_fingerprint(
        make_job(["+run=factory_farming_v1"]).training
    )
