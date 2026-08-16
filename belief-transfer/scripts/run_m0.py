"""One-off: train M0 (the off-topic control checkpoint) and score it against the
factory_farming efficacy item bank.

Ad hoc rather than a `belief_transfer.evals` CLI flag, per changelog/2026-08-14b.md's
own deferral: the CLI's `--corpus-run` couples "which corpus to train on" and "which
experiment's item bank to score against" into one flag, and its `CONDITIONS` dict
assumes exactly the two-arm (m_plus/m_minus) shape. M0 needs both decoupled -- train on
control_offtopic, score against factory_farming -- which isn't a generalization worth
building into the CLI until a second use for it shows up.

M0 = M(control) from experiments/control_offtopic/experiment.yaml's header: one
checkpoint trained on the *whole* control corpus (both polarities merged, since
polarity there is an inert placeholder -- see that file), not a positive/negative pair.
Answers "how much does any SFT of matched size shift these scores, absent
belief-relevant content" -- the any-SFT drift floor that M+/M-'s real dE should be
compared against.

Dose matching: the control corpus is 88 gated docs vs factory_farming's 106 (per
polarity), so the frozen config's 5 epochs would give 55 optimizer steps here against
tune-f09053a2's 70 (see configs/training.yaml's header and this file's own epoch
override below). 88 docs / eff_batch 8 = 11 steps/epoch, which has no integer epoch
count landing exactly on 70; 6 epochs -> 66 steps is the closest available match (7
epochs -> 77 is further off). Documented here rather than chased further, per the
changelog's own "(or document the choice explicitly)" fallback.

Usage:
    uv run python scripts/run_m0.py                 # train (if needed) + score
    uv run python scripts/run_m0.py --no-train       # score an existing M0 checkpoint
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml
from dotenv import find_dotenv, load_dotenv

from belief_transfer.benchmarks import run_benchmark
from belief_transfer.dataset import gate
from belief_transfer.evals import efficacy
from belief_transfer.evals.__main__ import _print_conditions, _print_delta
from belief_transfer.inference.model import MODELS_CONFIG_PATH, HFModel, free_gpu
from belief_transfer.runs import load_run_config, resolve_experiment, resolve_run_path
from belief_transfer.schemas import SFTHyperparams, TrainingConfig
from belief_transfer.training import dataset as sft_dataset
from belief_transfer.training import sft

load_dotenv(find_dotenv())

BASELINE_RUN_ID = "tune-f09053a2"  # the frozen config this M0 checkpoint is dose-matched to
CONTROL_CORPUS_RUN = "control_offtopic_v1"
SCORING_CORPUS_RUN = "factory_farming_v1"
M0_RUN_ID = "m0-control-offtopic"
M0_EPOCHS = 6  # see module docstring: closest integer-epoch match to the 70-step baseline


def m0_training_config() -> TrainingConfig:
    """The frozen config (configs/training.yaml) with epochs overridden for dose
    matching -- every other hyperparameter (lr, lora rank, target modules, seed, ...)
    stays identical to tune-f09053a2 so M0 differs only in training corpus."""
    training = sft.load_training_config()
    hp = SFTHyperparams.model_validate({**training.sft.model_dump(), "epochs": M0_EPOCHS})
    return TrainingConfig.model_validate({"model": training.model, "sft": hp.model_dump()})


def train_m0(training: TrainingConfig) -> Path:
    """Train one LoRA adapter on control_offtopic's whole gated corpus (both
    polarities merged -- see module docstring). Returns the checkpoint's `final/` dir."""
    control_run_config = load_run_config(resolve_run_path(CONTROL_CORPUS_RUN))
    control_experiment, _ = resolve_experiment(control_run_config)
    validated_path = gate.validated_documents_path(control_experiment.id, control_run_config.run_id)

    documents = sft_dataset.load_validated_documents(validated_path)
    prompt = sft_dataset.sft_prompt(control_experiment.dataset.topic)
    rows = [sft_dataset.to_chat_row(doc, prompt) for doc in documents]  # no polarity filter: M(control)

    output_dir = sft.CHECKPOINTS_DIR / "factory_farming" / M0_RUN_ID / "control"
    summary = sft.train_arm(control_experiment, training, rows, "control", output_dir)
    print(f"[m0] train: {summary['status']} loss {summary['train_loss']:.4f} "
          f"over {summary['global_steps']} steps on {summary['n_samples']} documents -> {output_dir}")
    return output_dir / "final"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-train", action="store_true", help="score an existing M0 checkpoint only")
    args = parser.parse_args(argv)

    training = m0_training_config()
    print(f"[m0] {training.model}  lr={training.sft.lr}  epochs={training.sft.epochs}  "
          f"eff_batch={training.sft.effective_batch_size}  (dose-matched to {BASELINE_RUN_ID})")

    adapter_dir = sft.CHECKPOINTS_DIR / "factory_farming" / M0_RUN_ID / "control" / "final"
    if not args.no_train:
        adapter_dir = train_m0(training)
        free_gpu()
    elif not adapter_dir.exists():
        print(f"no M0 checkpoint at {adapter_dir} -- drop --no-train")
        return 2

    # Score against factory_farming's item bank (built from that experiment, independent
    # of which corpus produced the checkpoint being scored).
    scoring_run_config = load_run_config(resolve_run_path(SCORING_CORPUS_RUN))
    scoring_experiment, scoring_experiment_path = resolve_experiment(scoring_run_config)
    items = efficacy.build_items(scoring_experiment, scoring_experiment_path)
    config = efficacy.load_efficacy_config()

    model = HFModel(training.model, adapter_path=adapter_dir, models_config_path=MODELS_CONFIG_PATH)
    print(f"[m0] scoring m0 ({adapter_dir}) over {len(items)} rows ...")
    rows = efficacy.score_items(
        model, items, condition="m0", model_tag=training.model,
        adapter=str(adapter_dir), continuation=config.continuation_enabled,
    )
    bench_result = run_benchmark("choice", model, model_key=training.model, adapter=str(adapter_dir))
    print(f"[choice]   m0: {'PASS' if bench_result.passed else 'FAIL'} "
          f"accuracy {bench_result.metrics.get('accuracy', float('nan')):.3f} "
          f"confidence {bench_result.metrics.get('mean_confidence', float('nan')):.3f}")
    del model
    free_gpu()

    keys = ["p_positive"] + (["p_positive_continuation"] if config.continuation_enabled else [])
    conditions_summary = {key: {"m0": efficacy.aggregate(rows, key=key)} for key in keys}

    responses_file = efficacy.write_rows(rows, efficacy.responses_path(scoring_experiment.id, M0_RUN_ID))
    summary = {
        "experiment": scoring_experiment.id,
        "corpus_run": scoring_run_config.run_id,
        "run_id": M0_RUN_ID,
        "model": training.model,
        "note": f"M0 (M(control), dose-matched to {BASELINE_RUN_ID}): trained on {CONTROL_CORPUS_RUN}, "
                f"scored against {SCORING_CORPUS_RUN}'s item bank",
        "hyperparams": training.sft.model_dump(),
        "n_items": len({row["item_id"] for row in rows}),
        "n_rows": len(rows),
        "conditions": conditions_summary,
        "choice_benchmark": {
            "m0": {
                "passed": bench_result.passed,
                "calibrated": bench_result.calibrated,
                **{name: round(value, 4) for name, value in bench_result.metrics.items()},
            }
        },
        "artifacts": [str(responses_file)],
    }
    summary_file = efficacy.summary_path(scoring_experiment.id, M0_RUN_ID)
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    summary_file.write_text(yaml.safe_dump(summary, sort_keys=False))

    print("\n[m0] 0.5 = indifferent; compare against base/M+/M- in "
          f"data/results/{scoring_experiment.id}/{BASELINE_RUN_ID}/efficacy.yaml")
    for key in keys:
        _print_conditions(conditions_summary[key], key)
    print(f"\n[m0] wrote {responses_file}\n[m0] wrote {summary_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
