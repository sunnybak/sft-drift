import asyncio
import json
from pathlib import Path

import pytest
import yaml

from belief_transfer.dataset import gate, generate, score
from belief_transfer.generation import llm
from belief_transfer.generation.context import CallRecord
from belief_transfer.runs import (
    RunConfig,
    _deep_merge,
    load_run_config,
    resolve_experiment,
    resolve_run_path,
    run,
    run_datagen,
)
from belief_transfer.validation import judge

ROOT = Path(__file__).resolve().parents[1]

FAKE_PLAN_PAYLOAD = {
    "segment": "broiler chicken production",
    "region": "Wielkopolska, Poland",
    "primary_operation": "Zielona Grzywa, 240,000 birds",
    "people": [
        {"name": "Marin Wilson", "role": "barn technician", "affiliation": "Zielona Grzywa"}
    ],
    "institutions": ["Poznan Poultry Institute"],
    "measurements": ["mortality rate in the annual flock report"],
    "sections": ["open on the barn at dawn"],
}


async def _fake_batch(prompts, throughput=8, tool=None, context=None, **_: object):  # noqa: ANN001, ANN202
    ordered = list(prompts)
    for i, prompt in enumerate(ordered):
        if context is not None:
            # A stand-in for a real Client call, so run_datagen's report reflects
            # something rather than an untouched, all-zero context.
            context.record(
                CallRecord(
                    cached=False,
                    cost_usd=0.001,
                    input_tokens=10,
                    output_tokens=5,
                    cached_tokens=0,
                    cache_write_tokens=0,
                    reasoning_tokens=0,
                    latency_s=0.01,
                )
            )
        if tool is not None:
            yield llm.Completion(index=i, prompt=prompt, text="", payload=FAKE_PLAN_PAYLOAD)
        else:
            yield llm.Completion(index=i, prompt=prompt, text=f"Title\n\nBody {i}.")


async def _fake_run_checks(checks, prompts, *, context=None, **_: object):  # noqa: ANN001, ANN202
    ordered = list(prompts)
    if len(ordered) != len(checks):
        raise ValueError("checks and prompts must be the same length")
    for _ in ordered:
        if context is not None:
            context.record(
                CallRecord(
                    cached=False,
                    cost_usd=0.0005,
                    input_tokens=8,
                    output_tokens=2,
                    cached_tokens=0,
                    cache_write_tokens=0,
                    reasoning_tokens=0,
                    latency_s=0.02,
                )
            )
    return [
        judge.CheckResult(
            check_id=check.id, expect=check.expect, answer=check.expect, evidence="", judge_model="fake"
        )
        for check in checks
    ]


def test_deep_merge_recurses_into_nested_dicts_and_replaces_scalars() -> None:
    base = {"dataset": {"n_items": 100, "topic": "x"}, "belief": {"statement": "s"}}
    overrides = {"dataset": {"n_items": 4}}

    merged = _deep_merge(base, overrides)

    assert merged == {"dataset": {"n_items": 4, "topic": "x"}, "belief": {"statement": "s"}}
    # Original dicts must not be mutated.
    assert base["dataset"]["n_items"] == 100


def test_pilot_trimmed_run_config_parses_and_overrides_n_items() -> None:
    run_config = load_run_config(ROOT / "runs/pilot_trimmed.yaml")

    assert run_config.run_id == "pilot_trimmed"
    assert run_config.experiment == "factory_farming"
    assert run_config.stage == "datagen"
    assert run_config.replicates == 3

    experiment, experiment_path = resolve_experiment(run_config)
    assert experiment.dataset.n_items == 4
    assert experiment_path == ROOT / "experiments/factory_farming/experiment.yaml"
    # experiment.yaml has no n_items of its own -- the override is where it comes from
    # -- and the override must not have mutated what the base file says either way.
    base = yaml.safe_load(experiment_path.read_text())
    assert "n_items" not in base["dataset"]


def test_resolve_run_path_accepts_bare_id_or_full_path() -> None:
    by_id = resolve_run_path("pilot_trimmed")
    by_path = resolve_run_path(str(ROOT / "runs/pilot_trimmed.yaml"))

    assert by_id == ROOT / "runs" / "pilot_trimmed.yaml"
    assert by_path == by_id

    with pytest.raises(FileNotFoundError):
        resolve_run_path("no_such_run")


def test_run_datagen_writes_replicates_times_n_items_pairs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(generate.llm, "batch", _fake_batch)
    monkeypatch.setattr(score.judge, "run_checks", _fake_run_checks)
    run_config = RunConfig(
        run_id="tiny",
        experiment="factory_farming",
        overrides={"dataset": {"n_items": 2}},
        replicates=2,
    )
    out_path = tmp_path / "tiny.jsonl"
    scores_path = tmp_path / "scores.jsonl"
    validated_path = tmp_path / "validated.jsonl"
    report_path = tmp_path / "datagen.yaml"

    result_path = asyncio.run(
        run_datagen(
            run_config,
            ROOT / "runs/pilot_trimmed.yaml",
            out_path=out_path,
            report_path=report_path,
            scores_path=scores_path,
            validated_path=validated_path,
        )
    )

    assert result_path == out_path
    rows = [json.loads(line) for line in out_path.read_text().splitlines()]
    assert len(rows) == 2 * 2 * 2  # replicates x n_items x polarities
    assert {row["run"] for row in rows} == {1, 2}
    assert all(row["run_id"] == "tiny" for row in rows)
    assert len({row["run_config_sha"] for row in rows}) == 1

    # score_dataset judged every document and every pair of the accumulated corpus.
    scores = [json.loads(line) for line in scores_path.read_text().splitlines()]
    assert scores
    assert all(row["passed"] for row in scores)
    assert {row["polarity"] for row in scores} >= {"positive", "negative", "pair"}

    # The fake judge passes everything, so gating keeps every pair as-is.
    validated_rows = [json.loads(line) for line in validated_path.read_text().splitlines()]
    assert validated_rows == rows

    report = yaml.safe_load(report_path.read_text())
    assert report["experiment"] == "factory_farming"
    assert report["run_id"] == "tiny"
    assert report["stage"] == "datagen"
    assert report["artifacts"] == [
        str(out_path.resolve()),
        str(scores_path.resolve()),
        str(validated_path.resolve()),
    ]
    assert report["gating"] == {
        "pairs_total": 4,
        "pairs_kept": 4,
        "pairs_dropped": 0,
        "checks_below_threshold": [],
    }

    # 2 replicates x (2 plan calls + 4 document calls) = 12 fake generation calls, plus
    # one fake judge call per score row -- the same report covers both.
    n_generation_calls = 12
    n_judge_calls = len(scores)

    last_run = report["last_run"]
    assert last_run["datapoints"] == len(rows)
    assert last_run["calls"] == {"cached": 0, "uncached": n_generation_calls + n_judge_calls}
    assert last_run["cost_usd"] == pytest.approx(0.001 * n_generation_calls + 0.0005 * n_judge_calls)
    assert last_run["tokens"]["uncached"] == {
        "input_tokens": 10 * n_generation_calls + 8 * n_judge_calls,
        "output_tokens": 5 * n_generation_calls + 2 * n_judge_calls,
    }
    expected_mean_latency = (0.01 * n_generation_calls + 0.02 * n_judge_calls) / (
        n_generation_calls + n_judge_calls
    )
    assert last_run["mean_latency_s"] == pytest.approx(expected_mean_latency)

    # A fresh report file: lifetime is just this one invocation.
    lifetime = report["lifetime"]
    assert lifetime["runs"] == 1
    assert lifetime["datapoints"] == last_run["datapoints"]
    assert lifetime["calls"] == last_run["calls"]
    assert lifetime["cost_usd"] == pytest.approx(last_run["cost_usd"])
    assert lifetime["mean_latency_s"] == pytest.approx(last_run["mean_latency_s"])


def test_run_datagen_overwrites_rather_than_accumulates_across_invocations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(generate.llm, "batch", _fake_batch)
    monkeypatch.setattr(score.judge, "run_checks", _fake_run_checks)
    run_config = RunConfig(
        run_id="tiny", experiment="factory_farming", overrides={"dataset": {"n_items": 1}}
    )
    out_path = tmp_path / "tiny.jsonl"
    scores_path = tmp_path / "scores.jsonl"
    validated_path = tmp_path / "validated.jsonl"
    report_path = tmp_path / "datagen.yaml"

    asyncio.run(
        run_datagen(
            run_config,
            ROOT / "runs/pilot_trimmed.yaml",
            out_path=out_path,
            report_path=report_path,
            scores_path=scores_path,
            validated_path=validated_path,
        )
    )
    first_run_rows = out_path.read_text().splitlines()
    first_scores_rows = scores_path.read_text().splitlines()
    first_validated_rows = validated_path.read_text().splitlines()
    first_report = yaml.safe_load(report_path.read_text())
    asyncio.run(
        run_datagen(
            run_config,
            ROOT / "runs/pilot_trimmed.yaml",
            out_path=out_path,
            report_path=report_path,
            scores_path=scores_path,
            validated_path=validated_path,
        )
    )
    second_run_rows = out_path.read_text().splitlines()
    second_scores_rows = scores_path.read_text().splitlines()
    second_validated_rows = validated_path.read_text().splitlines()
    second_report = yaml.safe_load(report_path.read_text())

    assert len(first_scores_rows) == len(second_scores_rows) > 0  # scores overwrite too
    assert len(first_validated_rows) == len(second_validated_rows) > 0  # validated overwrites too

    assert len(first_run_rows) == len(second_run_rows) == 2  # 1 item x 2 polarities

    # last_run never accumulates: it is this invocation's numbers only.
    assert first_report["last_run"] == second_report["last_run"]
    # gating is a snapshot of the current corpus, not accumulated either.
    assert first_report["gating"] == second_report["gating"]
    assert first_report["lifetime"]["runs"] == 1
    # lifetime does accumulate, across both invocations of the same report file.
    assert second_report["lifetime"]["runs"] == 2
    assert second_report["lifetime"]["datapoints"] == 2 * first_report["last_run"]["datapoints"]
    assert second_report["lifetime"]["cost_usd"] == pytest.approx(
        2 * first_report["last_run"]["cost_usd"]
    )
    assert (
        second_report["lifetime"]["calls"]["uncached"]
        == 2 * first_report["last_run"]["calls"]["uncached"]
    )


def test_run_dispatches_unimplemented_stage() -> None:
    run_config = RunConfig(run_id="x", experiment="factory_farming", stage="sft")
    with pytest.raises(NotImplementedError):
        asyncio.run(run(run_config, ROOT / "runs/pilot_trimmed.yaml"))
