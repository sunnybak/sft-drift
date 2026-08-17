"""The stage registry and the two stages that are implemented.

Replaces test_runs.py: `belief_transfer.runs` (RunConfig, `_deep_merge`, run-path
resolution) is gone, because Hydra now does the merging and `configs/run/` holds the
overlays. What is left to test is that every stage in the type is registered, and that
datagen/sft still do what they did.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
import yaml

from belief_transfer import stages
from belief_transfer.dataset import gate, generate, score
from belief_transfer.generation import llm
from belief_transfer.generation.context import CallRecord
from belief_transfer.schemas import Stage
from belief_transfer.stages import datagen as datagen_stage
from belief_transfer.stages import sft as sft_stage
from belief_transfer.validation import judge

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
            # A stand-in for a real Client call, so the report reflects something rather
            # than an untouched, all-zero context.
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


@pytest.fixture
def fake_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(generate.llm, "batch", _fake_batch)
    monkeypatch.setattr(score.judge, "run_checks", _fake_run_checks)


def test_registry_covers_exactly_the_stage_type() -> None:
    """Every `Stage` has an implementation and vice versa.

    The check that makes the registry safe to keep as an explicit dict: adding a stage to
    the type without registering it (or registering one that is not in the type) is a test
    failure here rather than a KeyError in the middle of a run.
    """
    declared = set(Stage.__args__)
    registered = set(stages.STAGE_NAMES)
    assert registered == declared, f"missing: {declared - registered}, extra: {registered - declared}"


def test_every_stage_resolves_to_a_callable() -> None:
    # Imports are deferred per stage, so this is also the check that none of the stage
    # modules has an import-time error -- something a config-only test would not catch.
    for stage in stages.STAGE_NAMES:
        assert callable(stages.load(stage)), stage


def test_unknown_stage_names_the_known_ones() -> None:
    with pytest.raises(KeyError, match="datagen"):
        stages.load("not_a_stage")  # type: ignore[arg-type]


def test_datagen_writes_replicates_times_n_items_pairs(
    make_job, data_root: Path, fake_llm: None
) -> None:
    job = make_job(["+run=pilot_trimmed", "run_id=tiny", "experiment.dataset.n_items=2", "replicates=2"])

    result = asyncio.run(datagen_stage.run(job))

    documents_path = generate.documents_path("factory_farming", "tiny")
    rows = [json.loads(line) for line in documents_path.read_text().splitlines()]
    assert len(rows) == 2 * 2 * 2  # replicates x n_items x polarities
    assert {row["run"] for row in rows} == {1, 2}
    assert all(row["run_id"] == "tiny" for row in rows)
    # One resolved-config fingerprint for the whole invocation (see schemas.model_sha).
    assert len({row["config_sha"] for row in rows}) == 1
    assert len({row["experiment_sha"] for row in rows}) == 1

    scores = [json.loads(line) for line in score.scores_path("factory_farming", "tiny").read_text().splitlines()]
    assert scores
    assert all(row["passed"] for row in scores)
    assert {row["polarity"] for row in scores} >= {"positive", "negative", "pair"}

    # The fake judge passes everything, so gating keeps every pair as-is.
    validated = gate.validated_documents_path("factory_farming", "tiny")
    assert [json.loads(line) for line in validated.read_text().splitlines()] == rows

    assert result.stage == "datagen"
    assert result.experiment == "factory_farming"
    assert result.run_id == "tiny"
    assert result.metrics["gating"] == {
        "pairs_total": 4,
        "pairs_kept": 4,
        "pairs_dropped": 0,
        "checks_below_threshold": [],
    }
    # datagen calls a hosted API, so there is no local backend to stamp.
    assert result.backend is None
    assert result.config_sha

    # 2 replicates x (2 plan calls + 4 document calls) = 12 fake generation calls, plus
    # one fake judge call per score row -- the same report covers both.
    n_generation_calls = 12
    n_judge_calls = len(scores)
    last_run = result.last_run
    assert last_run.datapoints == len(rows)
    assert last_run.calls.model_dump() == {"cached": 0, "uncached": n_generation_calls + n_judge_calls}
    assert last_run.cost_usd == pytest.approx(0.001 * n_generation_calls + 0.0005 * n_judge_calls)
    assert last_run.tokens.uncached.model_dump() == {
        "input_tokens": 10 * n_generation_calls + 8 * n_judge_calls,
        "output_tokens": 5 * n_generation_calls + 2 * n_judge_calls,
    }
    expected_mean_latency = (0.01 * n_generation_calls + 0.02 * n_judge_calls) / (
        n_generation_calls + n_judge_calls
    )
    assert last_run.mean_latency_s == pytest.approx(expected_mean_latency)


def test_datagen_writes_the_resolved_config_next_to_its_results(
    make_job, data_root: Path, fake_llm: None
) -> None:
    """A run must be reproducible from its own output directory.

    Hydra writes `.hydra/config.yaml` when the runner is used, but a job built by a script
    never goes through `@hydra.main` -- so the stage writes the record unconditionally.
    """
    job = make_job(["+run=pilot_trimmed", "run_id=tiny", "experiment.dataset.n_items=1"])
    asyncio.run(datagen_stage.run(job))

    resolved = data_root / "results" / "factory_farming" / "tiny" / "config.resolved.yaml"
    assert resolved.exists()
    written = yaml.safe_load(resolved.read_text())
    assert written["run_id"] == "tiny"
    assert written["experiment"]["dataset"]["n_items"] == 1
    assert written["training"]["sft"]["lr"] == 1.0e-4


def test_datagen_overwrites_rather_than_accumulates_across_invocations(
    make_job, data_root: Path, fake_llm: None
) -> None:
    # replicates=1 explicitly: the pilot_trimmed overlay asks for 3, and this test is
    # about a second invocation replacing the first, not about replicate passes.
    job = make_job(
        ["+run=pilot_trimmed", "run_id=tiny", "experiment.dataset.n_items=1", "replicates=1"]
    )

    first = asyncio.run(datagen_stage.run(job))
    documents_path = generate.documents_path("factory_farming", "tiny")
    first_rows = documents_path.read_text().splitlines()

    second = asyncio.run(datagen_stage.run(job))
    second_rows = documents_path.read_text().splitlines()

    assert len(first_rows) == len(second_rows) == 2  # 1 item x 2 polarities

    # last_run never accumulates: it is this invocation's numbers only.
    assert first.last_run == second.last_run
    # gating is a snapshot of the current corpus, not accumulated either.
    assert first.metrics["gating"] == second.metrics["gating"]

    report = yaml.safe_load(
        (data_root / "results" / "factory_farming" / "tiny" / "datagen.yaml").read_text()
    )
    # lifetime does accumulate, across both invocations of the same report file.
    assert report["lifetime"]["runs"] == 2
    assert report["lifetime"]["datapoints"] == 2 * report["last_run"]["datapoints"]


def test_transfer_stages_require_a_named_frozen_suite(make_job) -> None:
    """belief_eval/action_eval exist now (stages/transfer.py), but refuse to run
    without `transfer.suites_from`: which frozen suite version a transfer number was
    measured on is provenance, not a default."""
    job = make_job(["+run=factory_farming_v1", "stage=belief_eval"])
    with pytest.raises(ValueError, match="suites_from"):
        asyncio.run(stages.run(job))


def _write_validated_documents(path: Path) -> None:
    rows = [
        {"experiment": "factory_farming", "run": 1, "index": 0, "polarity": "positive", "text": "pos 0"},
        {"experiment": "factory_farming", "run": 1, "index": 0, "polarity": "negative", "text": "neg 0"},
        {"experiment": "factory_farming", "run": 1, "index": 1, "polarity": "positive", "text": "pos 1"},
        {"experiment": "factory_farming", "run": 1, "index": 1, "polarity": "negative", "text": "neg 1"},
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def _fake_train(experiment, training, spec, validated_path, output_root, *, smoke=False):  # noqa: ANN001
    summaries = {}
    for polarity in ("positive", "negative"):
        arm_dir = output_root / polarity
        arm_dir.mkdir(parents=True, exist_ok=True)
        dataset_file = arm_dir / "sft_dataset.jsonl"
        dataset_file.write_text("{}\n")
        summaries[polarity] = {
            "status": "COMPLETED",
            "polarity": polarity,
            "dataset_file": str(dataset_file),
            "n_samples": 2,
        }
    return summaries


def test_sft_trains_both_polarities_and_writes_a_report(
    make_job, data_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sft_stage.sft, "train", _fake_train)
    job = make_job(["+run=pilot_trimmed", "run_id=tiny", "stage=sft", "experiment.dataset.n_items=2"])
    _write_validated_documents(gate.validated_documents_path("factory_farming", "tiny"))

    result = asyncio.run(sft_stage.run(job))

    assert result.stage == "sft"
    assert result.run_id == "tiny"
    assert set(result.metrics["sft"]) == {"positive", "negative"}
    assert result.metrics["sft"]["positive"]["status"] == "COMPLETED"
    assert result.last_run.datapoints == 4
    assert result.last_run.cost_usd == 0.0
    # sft loads a local model, so unlike datagen it records which backend produced the
    # checkpoint -- a checkpoint whose provenance omits that is not comparable later.
    assert result.backend is not None
    assert result.backend.backend in ("cuda", "mlx", "cpu")


def test_sft_without_a_gated_corpus_says_what_to_run(make_job, data_root: Path) -> None:
    job = make_job(["+run=pilot_trimmed", "run_id=missing", "stage=sft", "experiment.dataset.n_items=2"])
    with pytest.raises(FileNotFoundError, match="stage=datagen|run.py"):
        asyncio.run(sft_stage.run(job))


def test_smoke_runs_never_write_over_a_real_run(make_job, data_root: Path) -> None:
    """A 2-step smoke adapter under the real run id would later be scored as the real one.

    `train_one_arm` returns an existing COMPLETED checkpoint in place rather than
    retraining, so the separation has to be in the path, not in a flag read at score time.
    """
    real = make_job(["+run=pilot_trimmed", "run_id=tiny", "stage=sft", "experiment.dataset.n_items=2"])
    smoke = make_job(
        ["+run=pilot_trimmed", "run_id=tiny", "stage=sft", "experiment.dataset.n_items=2", "smoke=true"]
    )

    assert sft_stage.checkpoint_root(real).name == "tiny"
    assert sft_stage.checkpoint_root(smoke).name == "tiny-smoke"
    assert sft_stage.checkpoint_root(real) != sft_stage.checkpoint_root(smoke)
