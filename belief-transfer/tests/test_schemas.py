from pathlib import Path

from belief_transfer.schemas import (
    JobConfig,
    Provenance,
    file_sha,
    model_sha,
)

ROOT = Path(__file__).resolve().parents[1]


def test_every_run_overlay_composes_and_validates(make_job) -> None:
    """The cheap check that catches config drift.

    A run overlay is only exercised when someone runs it, which for a 2-hour datagen job
    means a typo can sit in `configs/run/` indefinitely. Composing all of them here costs
    milliseconds.
    """
    overlays = sorted(path.stem for path in (ROOT / "configs" / "run").glob("*.yaml"))
    assert overlays, "no run overlays found -- configs/run/ should not be empty"

    for name in overlays:
        job = make_job([f"+run={name}"])
        assert job.run_id == name, f"{name}.yaml sets run_id={job.run_id!r}"
        # Every experiment spec leaves n_items mandatory-but-unset, so an overlay that
        # forgets it fails composition rather than generating some default amount.
        assert job.experiment.dataset.n_items > 0


def test_yaml_defaults_match_the_schema_defaults(make_job) -> None:
    """`configs/config.yaml` spells out defaults that `schemas.py` also declares.

    The duplication is deliberate -- Hydra can only override a key that exists in the
    config tree, so a field living only as a Pydantic default is invisible to `--help` and
    rejects `efficacy.limit=2` with "not in struct". This is what stops the two copies from
    drifting into disagreement, which would be worse than either alone: the YAML would win
    silently and the schema would document a value nothing uses.
    """
    from belief_transfer.schemas import ChatSpec, DataSpec, EfficacySpec

    composed = make_job(["+run=adhoc"])

    assert composed.efficacy.model_dump() == EfficacySpec().model_dump()
    assert composed.chat.model_dump() == ChatSpec().model_dump()
    assert composed.data.model_dump() == DataSpec().model_dump()


def test_every_efficacy_knob_is_overridable_from_the_command_line(make_job) -> None:
    # Regression: these were schema-only, so `efficacy.limit=2` failed with
    # "Key 'limit' is not in struct" -- discovered by trying to run the stage.
    job = make_job(
        ["+run=adhoc", "efficacy.limit=2", "efficacy.choice_bench=false", "efficacy.trajectory=true"]
    )
    assert job.efficacy.limit == 2
    assert job.efficacy.choice_bench is False
    assert job.efficacy.trajectory is True


def test_frozen_training_values_survive_composition(job: JobConfig) -> None:
    """The frozen configuration must come through the config tree bit-identically.

    These five numbers are the output of a trajectory-gated sweep (see
    configs/training/frozen_2026_08_14.yaml's header): lr 1e-4, 5 epochs, attention+MLP,
    seed 42, effective batch 8. A refactor that silently changed any of them would
    invalidate every checkpoint comparison made against them, and would look like a
    config-plumbing change rather than a methodology one.
    """
    sft = job.training.sft
    assert sft.lr == 1.0e-4
    assert sft.epochs == 5
    assert sft.seed == 42
    assert sft.effective_batch_size == 8
    assert sft.target_modules == [
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ]


def test_model_spec_resolves_from_training_model(job: JobConfig) -> None:
    assert job.training.model == "qwen3-4b"
    assert job.model_spec.pretrained == "Qwen/Qwen3-4B"
    assert job.model_spec.dtype == "bfloat16"


def test_unknown_model_names_the_known_ones(make_job) -> None:
    job = make_job(["+run=factory_farming_v1", "training.model=not-a-model"])
    try:
        job.model_spec
    except KeyError as exc:
        assert "qwen3-4b" in str(exc)
    else:
        raise AssertionError("expected a KeyError naming the known models")


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


def test_model_sha_depends_on_values_not_key_order(job: JobConfig) -> None:
    """Provenance now hashes the resolved config, not the file that produced it.

    With layered composition no single file determines what ran, so `file_sha` of one of
    them would give two materially different jobs the same fingerprint.
    """
    assert model_sha(job.experiment) == model_sha(job.experiment)
    assert model_sha(job.experiment) != model_sha(job.dataset)

    reordered = job.experiment.model_copy(deep=True)
    reordered.dataset.dimensions = dict(reversed(list(reordered.dataset.dimensions.items())))
    assert model_sha(reordered) == model_sha(job.experiment)

    changed = job.experiment.model_copy(deep=True)
    changed.dataset.n_items += 1
    assert model_sha(changed) != model_sha(job.experiment)


def test_provenance_config_shas_are_keyed_by_name() -> None:
    provenance = Provenance(
        experiment_id="factory_farming",
        experiment_sha="abc123def456",
        config_shas={"dataset_config": "111111111111"},
        model="gpt-5.6-luna",
    )

    assert provenance.config_shas["dataset_config"] == "111111111111"
    assert provenance.seed is None
