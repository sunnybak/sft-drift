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


# --- structural gates for surface forms ---------------------------------------------


def _form_document(index: int, polarity: str, *, form: str, turns: int) -> dict:
    doc = _document(1, index, polarity)
    doc["format"] = form
    doc["messages"] = [
        {"role": "user" if n % 2 == 0 else "assistant", "content": f"turn {n}"}
        for n in range(turns * 2)
    ]
    return doc


def test_pair_is_dropped_when_a_declared_form_did_not_parse() -> None:
    """A multi-turn document whose text broke its own Q:/A: alternation carries no
    messages. Training on it would pair an answer with a question the model never saw."""
    documents = [
        _form_document(0, "positive", form="qa_thread", turns=3),
        _form_document(0, "negative", form="qa_thread", turns=0),
    ]

    kept, dropped = gate.gate_pairs(documents, [])

    assert kept == []
    assert len(dropped) == 2


def test_pair_is_dropped_when_the_two_arms_ran_different_lengths() -> None:
    """Three rounds against four is a shape difference between the arms of one pair --
    the confound `dB = B(M+) - B(M-)` cannot tell from a content difference."""
    documents = [
        _form_document(1, "positive", form="qa_thread", turns=3),
        _form_document(1, "negative", form="qa_thread", turns=4),
    ]

    kept, _ = gate.gate_pairs(documents, [])

    assert kept == []


def test_matched_multi_turn_pair_is_kept() -> None:
    documents = [
        _form_document(2, "positive", form="qa_thread", turns=3),
        _form_document(2, "negative", form="qa_thread", turns=3),
    ]

    kept, dropped = gate.gate_pairs(documents, [])

    assert len(kept) == 2
    assert dropped == []


def test_corpora_generated_before_forms_are_unaffected() -> None:
    """Rows carrying neither `format` nor `messages` must gate exactly as they always
    did -- factory_farming_v1 is one of them."""
    documents = [_document(1, 0, "positive"), _document(1, 0, "negative")]

    kept, dropped = gate.gate_pairs(documents, [])

    assert len(kept) == 2
    assert dropped == []


def test_best_attempt_per_index_keeps_one_pair_per_item() -> None:
    """A retried item that passes twice must not enter the corpus twice -- that would
    train on one item's content at double the dose of every other."""
    rows = [
        {"run": 1, "index": 0, "polarity": "positive"},
        {"run": 1, "index": 0, "polarity": "negative"},
        {"run": 2, "index": 0, "polarity": "positive"},
        {"run": 2, "index": 0, "polarity": "negative"},
        {"run": 2, "index": 1, "polarity": "positive"},
        {"run": 2, "index": 1, "polarity": "negative"},
    ]

    best = gate.best_attempt_per_index(rows)

    assert len(best) == 4
    assert {(r["run"], r["index"]) for r in best} == {(1, 0), (2, 1)}


def test_best_attempt_per_index_is_a_no_op_on_a_single_pass() -> None:
    rows = [
        {"run": 1, "index": i, "polarity": p}
        for i in range(3)
        for p in ("positive", "negative")
    ]

    assert gate.best_attempt_per_index(rows) == rows
