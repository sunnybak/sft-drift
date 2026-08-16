from pathlib import Path

import yaml

from belief_transfer.dataset import gate
from belief_transfer.schemas import ExperimentConfig
from belief_transfer.validation import judge

ROOT = Path(__file__).resolve().parents[1]

def _judge_config():
    """The judge config as the pipeline sees it: composed from configs/, not read directly."""
    from belief_transfer.config import load_job

    return load_job(["+run=factory_farming_v1"]).dataset.judge



def _factory_farming() -> ExperimentConfig:
    """The factory_farming spec as the pipeline sees it, composed from configs/.

    n_items is trimmed to 4: the real corpus size lives in the run overlay
    (configs/run/factory_farming_v1.yaml), and these tests only need enough items to
    exercise the shape.
    """
    from belief_transfer.config import load_job

    experiment = load_job(["+run=factory_farming_v1"]).experiment
    experiment.dataset.n_items = 4
    return experiment


def _document(run: int, index: int, polarity: str) -> dict:
    return {"run": run, "index": index, "polarity": polarity, "text": f"{polarity} text"}


def _score(run: int, index: int, polarity: str, check_id: str, passed: bool) -> dict:
    return {
        "run": run,
        "index": index,
        "polarity": polarity,
        "check_id": check_id,
        "expect": True,
        "answer": passed,
        "passed": passed,
        "evidence": "",
    }


def test_gate_pairs_keeps_a_pair_with_no_gating_failures() -> None:
    documents = [_document(1, 0, "positive"), _document(1, 0, "negative")]
    scores = [
        _score(1, 0, "positive", "no_belief_claim", True),
        _score(1, 0, "negative", "no_belief_claim", True),
        _score(1, 0, "pair", "pair_same_shape", True),
    ]

    kept, dropped = gate.gate_pairs(documents, scores)

    assert kept == documents
    assert dropped == []


def test_gate_pairs_drops_a_pair_that_fails_a_static_document_check() -> None:
    documents = [_document(1, 0, "positive"), _document(1, 0, "negative")]
    scores = [
        _score(1, 0, "positive", "no_belief_claim", False),
        _score(1, 0, "negative", "no_belief_claim", True),
    ]

    kept, dropped = gate.gate_pairs(documents, scores)

    assert kept == []
    assert dropped == documents


def test_gate_pairs_drops_a_pair_that_fails_a_pair_level_check() -> None:
    documents = [_document(1, 0, "positive"), _document(1, 0, "negative")]
    scores = [_score(1, 0, "pair", "pair_same_shape", False)]

    kept, dropped = gate.gate_pairs(documents, scores)

    assert kept == []
    assert dropped == documents


def test_gate_pairs_keeps_a_pair_that_only_fails_premise_or_contrast_checks() -> None:
    documents = [_document(1, 0, "positive"), _document(1, 0, "negative")]
    scores = [
        _score(1, 0, "positive", "premise_animal_welfare_0", False),
        _score(1, 0, "negative", "contrast_animal_welfare_0", False),
    ]

    kept, dropped = gate.gate_pairs(documents, scores)

    assert kept == documents
    assert dropped == []


def test_gate_pairs_drops_an_incomplete_pair() -> None:
    documents = [_document(1, 0, "positive")]  # no matching negative

    kept, dropped = gate.gate_pairs(documents, [])

    assert kept == []
    assert dropped == documents


def test_gate_pairs_evaluates_pairs_independently() -> None:
    documents = [
        _document(1, 0, "positive"),
        _document(1, 0, "negative"),
        _document(1, 1, "positive"),
        _document(1, 1, "negative"),
    ]
    scores = [_score(1, 1, "positive", "no_belief_claim", False)]  # only item 1 fails

    kept, dropped = gate.gate_pairs(documents, scores)

    assert {d["index"] for d in kept} == {0}
    assert {d["index"] for d in dropped} == {1}


def test_write_gated_overwrites_rather_than_appends(tmp_path: Path) -> None:
    path = tmp_path / "documents.jsonl"
    gate.write_gated([{"a": 1}], path)
    gate.write_gated([{"a": 2}], path)

    import json

    assert [json.loads(line) for line in path.read_text().splitlines()] == [{"a": 2}]


def test_check_pass_rates_computes_share_passed() -> None:
    scores = [
        _score(1, 0, "positive", "no_belief_claim", True),
        _score(1, 1, "positive", "no_belief_claim", True),
        _score(1, 2, "positive", "no_belief_claim", False),
        _score(1, 0, "positive", "premise_x_0", True),
    ]

    rates = gate.check_pass_rates(scores)

    assert rates["no_belief_claim"] == 2 / 3
    assert rates["premise_x_0"] == 1.0


def test_check_thresholds_covers_static_premise_and_pair_checks() -> None:
    experiment = _factory_farming()
    thresholds = gate.check_thresholds(experiment, _judge_config())

    assert "no_belief_claim" in thresholds
    assert "pair_same_shape" in thresholds
    assert any(check_id.startswith("premise_") for check_id in thresholds)
    assert any(check_id.startswith("contrast_") for check_id in thresholds)


def test_below_threshold_flags_only_checks_under_their_bar() -> None:
    thresholds = {"a": 0.9, "b": 0.9}
    pass_rates = {"a": 0.95, "b": 0.5, "c": 0.1}  # c has no configured threshold

    assert gate.below_threshold(pass_rates, thresholds) == ["b"]


def test_gating_summary_reports_pair_counts_and_below_threshold_checks() -> None:
    experiment = _factory_farming()
    documents = [
        _document(1, 0, "positive"),
        _document(1, 0, "negative"),
        _document(1, 1, "positive"),
        _document(1, 1, "negative"),
    ]
    checks = judge.document_checks(experiment, "positive", _judge_config())
    static_check_id = next(c.id for c in checks if not c.id.startswith(("premise_", "contrast_")))
    scores = [_score(1, 1, "positive", static_check_id, False)]
    kept, _ = gate.gate_pairs(documents, scores)

    summary = gate.gating_summary(experiment, _judge_config(), documents, scores, kept)

    assert summary["pairs_total"] == 2
    assert summary["pairs_kept"] == 1
    assert summary["pairs_dropped"] == 1
    assert static_check_id in summary["checks_below_threshold"]
