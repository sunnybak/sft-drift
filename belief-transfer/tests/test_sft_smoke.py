"""Unit tests for `training.sft`'s pure logic: step math, atomic write, post-hoc
verification.

AGENTS.md's required tiny-dataset memorization check is NOT here. It lives in
`inference.bench` as the `memorize` benchmark (`make memorization-bench`), because
what it measures is this machine's training stack -- GPU, torch/trl/peft versions,
dtype -- rather than any logic this suite owns, and it needs minutes of real training
to say anything. It sat here as a permanently-skipped test instead: the tiny fixture
model it used (`hf-internal-testing/tiny-random-gpt2`) has too little capacity to
memorize anything, so the check never actually ran on any machine. The pure half of
it -- item construction and scoring -- is covered without a GPU in test_bench.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from belief_transfer.training import dataset as sft_dataset
from belief_transfer.training import sft
from belief_transfer.training.sft import (
    atomic_write_json,
    expected_optimizer_steps,
    save_steps_for,
    verify_run,
)


def test_sft_module_imports() -> None:
    assert callable(sft_dataset.load_sft_dataset)
    assert callable(sft.train)


def test_expected_optimizer_steps_matches_known_values() -> None:
    # Cross-checked against the reference branch's factory-farming/guns-rights runs
    # (code/tests/test_pipeline_training.py): same formula (ceil(size / eff_bs) * epochs).
    assert expected_optimizer_steps(1200, 16, 3) == 225
    assert expected_optimizer_steps(1346, 16, 3) == 255
    assert expected_optimizer_steps(1229, 16, 3) == 231


def test_save_steps_for_divides_by_target_checkpoint_count() -> None:
    assert save_steps_for(225) == 45
    assert save_steps_for(10, target_checkpoint_count=3) == 3
    assert save_steps_for(1, target_checkpoint_count=5) == 1  # never below 1


def test_save_steps_for_rejects_nonpositive_target_count() -> None:
    with pytest.raises(ValueError):
        save_steps_for(100, target_checkpoint_count=0)


def test_atomic_write_json_leaves_no_tmp_file_and_is_readable(tmp_path: Path) -> None:
    path = tmp_path / "train_summary.json"

    atomic_write_json(path, {"status": "COMPLETED", "loss": 0.5})

    assert json.loads(path.read_text()) == {"status": "COMPLETED", "loss": 0.5}
    assert not path.with_suffix(".json.tmp").exists()


def test_verify_run_passes_when_everything_matches(tmp_path: Path) -> None:
    output_dir = tmp_path / "run"
    final_dir = output_dir / "final"
    final_dir.mkdir(parents=True)
    (output_dir / "checkpoint-2").mkdir()
    (output_dir / "checkpoint-4").mkdir()
    for name in ["adapter_config.json", "adapter_model.safetensors", "tokenizer_config.json"]:
        (final_dir / name).write_text("{}")
    # A real PeftConfig.from_pretrained call would fail on this stub adapter_config.json;
    # verify_run degrades adapter_config_loadable to False rather than raising, so the
    # check itself is exercised even without a real PEFT-formatted config here.

    checks = verify_run(
        output_dir=output_dir,
        final_dir=final_dir,
        expected_steps=4,
        save_steps=2,
        global_step=4,
        log_history=[{"loss": 1.0}, {"loss": 0.5}],
        train_loss=0.5,
    )

    assert checks["global_steps_match"] is True
    assert checks["checkpoint_steps"] == [2, 4]
    assert checks["checkpoints_match"] is True
    assert checks["finite_losses"] is True
    assert checks["missing_final_files"] == []


def test_verify_run_flags_step_and_checkpoint_mismatches(tmp_path: Path) -> None:
    output_dir = tmp_path / "run"
    final_dir = output_dir / "final"
    final_dir.mkdir(parents=True)
    (output_dir / "checkpoint-2").mkdir()  # missing checkpoint-4

    checks = verify_run(
        output_dir=output_dir,
        final_dir=final_dir,
        expected_steps=4,
        save_steps=2,
        global_step=3,  # doesn't match expected_steps
        log_history=[{"loss": 1.0}],
        train_loss=1.0,
    )

    assert checks["global_steps_match"] is False
    assert checks["checkpoints_match"] is False
    assert checks["missing_final_files"] != []


def test_verify_run_flags_nonfinite_loss(tmp_path: Path) -> None:
    output_dir = tmp_path / "run"
    final_dir = output_dir / "final"
    final_dir.mkdir(parents=True)

    checks = verify_run(
        output_dir=output_dir,
        final_dir=final_dir,
        expected_steps=1,
        save_steps=1,
        global_step=1,
        log_history=[{"loss": float("nan")}],
        train_loss=float("nan"),
    )

    assert checks["finite_losses"] is False


def test_status_is_completed_only_when_every_check_passes() -> None:
    passing = {
        "global_steps_match": True,
        "checkpoints_match": True,
        "finite_losses": True,
        "adapter_config_loadable": True,
        "missing_final_files": [],
    }
    assert sft._status(passing) == "COMPLETED"
    assert sft._status({**passing, "finite_losses": False}) == "FAILED_VERIFICATION"


def test_train_one_arm_raises_on_empty_polarity(tmp_path: Path) -> None:
    from belief_transfer.schemas import ExperimentConfig, TrainingConfig

    experiment = ExperimentConfig.model_validate(
        {
            "id": "toy",
            "belief": {"statement": "s", "positive_intervention": "p", "negative_intervention": "n"},
            "action": {"description": "a"},
            "dataset": {"topic": "toy topic", "n_items": 1, "size_words": 10, "style": "s", "dimensions": {}},
        }
    )
    validated_path = tmp_path / "documents.jsonl"
    validated_path.write_text(
        json.dumps({"experiment": "toy", "run": 1, "index": 0, "polarity": "positive", "text": "x"}) + "\n"
    )

    with pytest.raises(ValueError):
        sft.train_one_arm(
            experiment,
            TrainingConfig(),
            validated_path,
            "negative",  # no negative documents in the fixture above
            tmp_path / "out",
        )
