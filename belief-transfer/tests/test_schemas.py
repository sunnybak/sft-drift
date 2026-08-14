from pathlib import Path

import yaml

from belief_transfer.schemas import (
    ActionEvalConfig,
    BeliefEvalConfig,
    DatasetGenConfig,
    ExperimentConfig,
    Provenance,
    SFTConfig,
    TrainingConfig,
    file_sha,
)


ROOT = Path(__file__).resolve().parents[1]


def test_shared_configs_parse() -> None:
    training = yaml.safe_load((ROOT / "configs/training.yaml").read_text())
    TrainingConfig.model_validate(training)
    dataset = yaml.safe_load((ROOT / "configs/dataset.yaml").read_text())
    DatasetGenConfig.model_validate(dataset)


def test_experiment_configs_parse() -> None:
    for exp_dir in sorted((ROOT / "experiments").iterdir()):
        if not exp_dir.is_dir():
            continue
        raw = yaml.safe_load((exp_dir / "experiment.yaml").read_text())
        # experiment.yaml intentionally has no n_items of its own -- every run config
        # (runs/*.yaml) supplies its own via `overrides.dataset.n_items` -- so a bare
        # parse of the base file needs one filled in to check the rest of its shape.
        raw["dataset"].setdefault("n_items", 1)
        ExperimentConfig.model_validate(raw)
        SFTConfig.model_validate(yaml.safe_load((exp_dir / "sft.yaml").read_text()))
        BeliefEvalConfig.model_validate(yaml.safe_load((exp_dir / "belief_eval.yaml").read_text()))
        ActionEvalConfig.model_validate(yaml.safe_load((exp_dir / "action_eval.yaml").read_text()))


def test_file_sha_is_deterministic_and_content_sensitive(tmp_path: Path) -> None:
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text("same contents\n")
    b.write_text("same contents\n")
    c = tmp_path / "c.yaml"
    c.write_text("different contents\n")

    assert file_sha(a) == file_sha(a)
    assert file_sha(a) == file_sha(b)
    assert file_sha(a) != file_sha(c)
    assert len(file_sha(a)) == 12
    assert len(file_sha(a, length=8)) == 8


def test_provenance_config_shas_are_keyed_by_name() -> None:
    provenance = Provenance(
        experiment_id="factory_farming",
        experiment_sha="abc123def456",
        config_shas={"dataset_config": "111111111111"},
        model="gpt-5.6-luna",
    )

    assert provenance.config_shas["dataset_config"] == "111111111111"
    assert provenance.seed is None
