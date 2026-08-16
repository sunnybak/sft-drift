import asyncio
import json
from pathlib import Path

import pytest
import yaml

from belief_transfer.dataset import score
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


def _document(run: int, index: int, polarity: str, text: str) -> dict:
    return {"run": run, "index": index, "polarity": polarity, "text": text}


async def _fake_run_checks(checks, prompts, **kwargs):  # noqa: ANN001, ANN202
    ordered = list(prompts)
    if len(ordered) != len(checks):
        raise ValueError("checks and prompts must be the same length")
    return [
        judge.CheckResult(
            check_id=check.id,
            expect=check.expect,
            answer=check.expect,  # everything "passes"
            evidence="",
            judge_model="fake-model",
        )
        for check in checks
    ]


def test_score_dataset_covers_documents_and_pairs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(score.judge, "run_checks", _fake_run_checks)
    experiment = _factory_farming()
    documents = [
        _document(1, 0, "positive", "Positive document text."),
        _document(1, 0, "negative", "Negative document text."),
    ]

    rows = asyncio.run(score.score_dataset(experiment, _judge_config(), documents))

    judge_config = _judge_config()
    n_document_checks = len(judge.document_checks(experiment, "positive", judge_config)) + len(
        judge.document_checks(experiment, "negative", judge_config)
    )
    n_pair_checks = len(judge.pair_checks(judge_config))
    assert len(rows) == n_document_checks + n_pair_checks

    assert {row["polarity"] for row in rows} == {"positive", "negative", "pair"}
    assert all(row["passed"] for row in rows)
    assert all(row["run"] == 1 and row["index"] == 0 for row in rows)
    assert all(row["experiment"] == "factory_farming" for row in rows)


def test_score_dataset_skips_incomplete_pairs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(score.judge, "run_checks", _fake_run_checks)
    experiment = _factory_farming()
    documents = [_document(1, 0, "positive", "Only the positive document.")]

    rows = asyncio.run(score.score_dataset(experiment, _judge_config(), documents))

    assert all(row["polarity"] != "pair" for row in rows)
    assert len(rows) == len(judge.document_checks(experiment, "positive", _judge_config()))


def test_write_scores_writes_one_json_row_per_line(tmp_path: Path) -> None:
    rows = [{"a": 1}, {"a": 2}]
    path = score.write_scores(rows, tmp_path / "scores.jsonl")

    lines = path.read_text().splitlines()
    assert [json.loads(line) for line in lines] == rows


def test_write_scores_overwrites_rather_than_appends(tmp_path: Path) -> None:
    path = tmp_path / "scores.jsonl"
    score.write_scores([{"a": 1}], path)
    score.write_scores([{"a": 2}], path)

    assert [json.loads(line) for line in path.read_text().splitlines()] == [{"a": 2}]
