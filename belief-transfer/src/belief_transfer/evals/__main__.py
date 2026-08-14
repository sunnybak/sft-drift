"""`python -m belief_transfer.evals [efficacy]` -- train M+/M- and measure whether the
fine-tune absorbed the corpus at all.

    make efficacy                                    # train at configs/training.yaml, then score
    make efficacy EVAL_ARGS="--epochs 4 --lr 1e-4 --target-modules attn+mlp"
    make efficacy EVAL_ARGS="--no-train --run-id tune-1a2b3c4d"   # re-score existing arms

A tuning tool, not a pipeline stage: it takes hyperparameters as flags, writes a plain
YAML summary rather than an `analysis.report`, and is meant to be run a dozen times while
finding a configuration that trains. `belief_transfer.runs` owns reproducible,
run-config-driven stages; this is the thing you use to work out what those stages should
be configured with (the same split as `benchmarks/`, which also writes plain JSON).

Efficacy is the *only* metric to tune against. It measures whether the training landed,
not what the experiment concludes, so optimizing it cannot bias the result. Tuning against
a belief or action score would be selecting hyperparameters on the outcome variable, and
any transfer number reported afterwards would be an artifact of that search. Once efficacy
clears zero convincingly, freeze the hyperparameters and stop looking.

Sequencing note: this loads a 4B model up to four times and frees it in between rather
than holding several at once, because the box it was written for has 12GB of VRAM and
cannot hold a training model and a scoring model together.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml
from dotenv import find_dotenv, load_dotenv

from belief_transfer.benchmarks import run_benchmark
from belief_transfer.dataset import gate
from belief_transfer.evals import efficacy
from belief_transfer.inference.model import MODELS_CONFIG_PATH, HFModel, load_models_config
from belief_transfer.runs import load_run_config, resolve_experiment, resolve_run_path
from belief_transfer.schemas import ExperimentConfig, SFTHyperparams, TrainingConfig
from belief_transfer.training import sft

load_dotenv(find_dotenv())

# Named presets for the knob most likely to matter. Factual content is generally
# associated more with the MLP blocks than with attention, so a corpus that fails to land
# under the default attention-only adapter is worth retrying with `attn+mlp` before
# reaching for a larger learning rate.
TARGET_MODULE_PRESETS: dict[str, list[str]] = {
    "attn": ["q_proj", "k_proj", "v_proj", "o_proj"],
    "mlp": ["gate_proj", "up_proj", "down_proj"],
    "attn+mlp": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
}

CONDITIONS = {"positive": "m_plus", "negative": "m_minus"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="belief_transfer.evals", description=__doc__)
    parser.add_argument("suite", nargs="?", default="efficacy", choices=["efficacy"])
    parser.add_argument(
        "--corpus-run",
        default="factory_farming_v1",
        help="run id (runs/<id>.yaml) whose gated corpus is trained on; also fixes the experiment spec",
    )
    parser.add_argument("--model", default=None, help="model key from configs/models.yaml")
    parser.add_argument(
        "--run-id",
        default=None,
        help="checkpoint/result run id; defaults to tune-<hyperparameter fingerprint>",
    )
    parser.add_argument("--no-train", action="store_true", help="score existing checkpoints only")
    parser.add_argument("--no-base", action="store_true", help="skip scoring the base checkpoint")
    parser.add_argument(
        "--no-continuation",
        action="store_true",
        help="skip the format-matched continuation reading (two fewer forward passes per item)",
    )
    parser.add_argument(
        "--no-choice-bench",
        action="store_true",
        help="skip the MCQ ability check that catches a checkpoint which can no longer answer a forced choice",
    )
    parser.add_argument("--limit", type=int, default=None, help="score only the first N items")

    hyper = parser.add_argument_group("hyperparameter overrides (default: configs/training.yaml)")
    hyper.add_argument("--lr", type=float, default=None)
    hyper.add_argument("--epochs", type=int, default=None)
    hyper.add_argument("--batch-size", type=int, default=None)
    hyper.add_argument("--grad-accum", type=int, default=None)
    hyper.add_argument("--lora-r", type=int, default=None)
    hyper.add_argument("--lora-alpha", type=int, default=None)
    hyper.add_argument("--lora-dropout", type=float, default=None)
    hyper.add_argument("--max-seq-len", type=int, default=None)
    hyper.add_argument("--seed", type=int, default=None)
    hyper.add_argument(
        "--target-modules",
        default=None,
        help=f"comma-separated module names, or a preset: {', '.join(TARGET_MODULE_PRESETS)}",
    )

    parser.add_argument("--models-config", type=Path, default=MODELS_CONFIG_PATH)
    parser.add_argument("--eval-config", type=Path, default=efficacy.EVAL_CONFIG_PATH)
    return parser


def parse_target_modules(value: str) -> list[str]:
    """A preset name, or a comma-separated module list."""
    if value in TARGET_MODULE_PRESETS:
        return list(TARGET_MODULE_PRESETS[value])
    modules = [part.strip() for part in value.split(",") if part.strip()]
    if not modules:
        raise ValueError(f"could not read any module names from {value!r}")
    return modules


def resolve_training(args: argparse.Namespace) -> TrainingConfig:
    """`configs/training.yaml` with only the flags actually passed overridden."""
    training = sft.load_training_config()
    overrides: dict[str, Any] = {
        field: getattr(args, field)
        for field in (
            "lr",
            "epochs",
            "batch_size",
            "grad_accum",
            "lora_r",
            "lora_alpha",
            "lora_dropout",
            "max_seq_len",
            "seed",
        )
        if getattr(args, field) is not None
    }
    if args.target_modules is not None:
        overrides["target_modules"] = parse_target_modules(args.target_modules)

    hyperparams = SFTHyperparams.model_validate({**training.sft.model_dump(), **overrides})
    model = args.model or training.model
    return TrainingConfig.model_validate({"model": model, "sft": hyperparams.model_dump()})


def _free_gpu() -> None:
    """Drop whatever the last phase allocated before the next one loads a model.

    Needed because the caching allocator holds freed blocks: without it, training then
    scoring in one process peaks at two copies of the model on a box that fits one.
    """
    import gc

    gc.collect()
    try:
        import torch
    except ImportError:
        return
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def score_condition(
    items: list[dict],
    *,
    model_tag: str,
    adapter: Path | None,
    condition: str,
    continuation: bool,
    choice_bench: bool,
    models_config_path: Path,
) -> tuple[list[dict], dict[str, Any] | None]:
    """Load one checkpoint, score the item bank (and optionally the MCQ benchmark), free it."""
    model = HFModel(model_tag, adapter_path=adapter, models_config_path=models_config_path)
    adapter_str = str(adapter) if adapter is not None else None
    print(f"[efficacy] scoring {condition} ({adapter_str or 'base checkpoint'}) over {len(items)} rows ...")

    rows = efficacy.score_items(
        model,
        items,
        condition=condition,
        model_tag=model_tag,
        adapter=adapter_str,
        continuation=continuation,
    )

    bench: dict[str, Any] | None = None
    if choice_bench:
        result = run_benchmark("choice", model, model_key=model_tag, adapter=adapter_str)
        bench = {
            "passed": result.passed,
            "calibrated": result.calibrated,
            **{name: round(value, 4) for name, value in result.metrics.items()},
        }
        print(f"[choice]   {condition}: {'PASS' if result.passed else 'FAIL'} "
              f"accuracy {result.metrics.get('accuracy', float('nan')):.3f} "
              f"confidence {result.metrics.get('mean_confidence', float('nan')):.3f}")

    del model
    _free_gpu()
    return rows, bench


def _print_conditions(summaries: dict[str, dict[str, Any]], key: str) -> None:
    print(f"\n  {key}")
    print(f"    {'condition':<10} {'score':>7}  {'95% CI':>16}  {'variant gap':>11}")
    for condition, summary in summaries.items():
        low, high = summary["ci95"]
        gap = summary["variant_gap"]
        gap_text = "n/a" if gap is None else f"{gap:.3f}"
        print(f"    {condition:<10} {summary['score']:>7.3f}  [{low:>6.3f}, {high:>6.3f}]  {gap_text:>11}")


def _print_delta(label: str, result: dict[str, Any]) -> None:
    low, high = result["ci95"]
    verdict = "EXCLUDES ZERO" if result["excludes_zero"] else "STRADDLES ZERO -- not interpretable"
    print(f"    dE({label}) = {result['delta']:+.3f}  95% CI [{low:+.3f}, {high:+.3f}]  {verdict}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    available = list(load_models_config(args.models_config).models)
    training = resolve_training(args)
    if training.model not in available:
        print(f"unknown model {training.model!r} -- configs/models.yaml has: {', '.join(available)}")
        return 2

    run_config_path = resolve_run_path(args.corpus_run)
    run_config = load_run_config(run_config_path)
    experiment, experiment_path = resolve_experiment(run_config)

    run_id = args.run_id or f"tune-{sft.hyperparams_fingerprint(training)}"
    output_root = sft.CHECKPOINTS_DIR / experiment.id / run_id
    validated_path = gate.validated_documents_path(experiment.id, run_config.run_id)

    print(f"[efficacy] experiment {experiment.id} corpus {run_config.run_id} run_id {run_id}")
    print(f"[efficacy] {training.model}  lr={training.sft.lr}  epochs={training.sft.epochs}  "
          f"eff_batch={training.sft.effective_batch_size}  r={training.sft.lora_r}  "
          f"targets={','.join(training.sft.target_modules)}")

    items = efficacy.limit_items(
        efficacy.build_items(experiment, experiment_path, eval_config_path=args.eval_config),
        args.limit,
    )
    config = efficacy.load_efficacy_config(args.eval_config)
    items_file = efficacy.write_rows(items, efficacy.items_path(experiment.id, run_config.run_id))
    n_items = len({row["item_id"] for row in items})
    print(f"[efficacy] {n_items} items x {len(efficacy.VARIANTS)} orders = {len(items)} rows -> {items_file}")

    training_summaries: dict[str, Any] = {}
    if not args.no_train:
        if not validated_path.exists():
            print(f"no gated corpus at {validated_path} -- run the datagen stage, or `make data-pull`")
            return 2
        expected = _report_expected_steps(validated_path, experiment, training)
        print(f"[sft]      training both arms, ~{expected} optimizer steps per arm -> {output_root}")
        summaries = sft.train(experiment, training, validated_path, output_root)
        _free_gpu()
        for polarity, summary in summaries.items():
            training_summaries[polarity] = {
                "status": summary["status"],
                "train_loss": summary["train_loss"],
                "global_steps": summary["global_steps"],
                "n_samples": summary["n_samples"],
            }
            print(f"[sft]      {polarity}: {summary['status']} loss {summary['train_loss']:.4f} "
                  f"over {summary['global_steps']} steps on {summary['n_samples']} documents")

    missing = [
        polarity for polarity in CONDITIONS if not (output_root / polarity / "final").exists()
    ]
    if missing:
        print(f"no checkpoint for {', '.join(missing)} under {output_root} -- drop --no-train, or pass --run-id")
        return 2

    scored_rows: list[dict] = []
    benchmarks: dict[str, Any] = {}
    by_condition: dict[str, list[dict]] = {}

    conditions: list[tuple[str, Path | None]] = []
    if not args.no_base:
        conditions.append(("base", None))
    conditions += [(CONDITIONS[polarity], output_root / polarity / "final") for polarity in CONDITIONS]

    for condition, adapter in conditions:
        rows, bench = score_condition(
            items,
            model_tag=training.model,
            adapter=adapter,
            condition=condition,
            continuation=config.continuation_enabled and not args.no_continuation,
            choice_bench=not args.no_choice_bench,
            models_config_path=args.models_config,
        )
        by_condition[condition] = rows
        scored_rows += rows
        if bench is not None:
            benchmarks[condition] = bench

    keys = ["p_positive"]
    if config.continuation_enabled and not args.no_continuation:
        keys.append("p_positive_continuation")

    conditions_summary: dict[str, dict[str, Any]] = {}
    deltas: dict[str, Any] = {}
    for key in keys:
        conditions_summary[key] = {
            condition: efficacy.aggregate(rows, key=key) for condition, rows in by_condition.items()
        }
        deltas[key] = efficacy.delta(by_condition["m_plus"], by_condition["m_minus"], key=key)

    responses_file = efficacy.write_rows(scored_rows, efficacy.responses_path(experiment.id, run_id))
    summary = {
        "experiment": experiment.id,
        "corpus_run": run_config.run_id,
        "run_id": run_id,
        "model": training.model,
        "trained": not args.no_train,
        "hyperparams": training.sft.model_dump(),
        "n_items": n_items,
        "n_rows": len(items),
        "conditions": conditions_summary,
        "delta": deltas,
        "choice_benchmark": benchmarks,
        "training": training_summaries,
        "artifacts": [str(items_file), str(responses_file)],
    }
    summary_file = efficacy.summary_path(experiment.id, run_id)
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    summary_file.write_text(yaml.safe_dump(summary, sort_keys=False))

    print("\n[efficacy] 0.5 = indifferent between the two arms' figures")
    for key in keys:
        _print_conditions(conditions_summary[key], key)
    print("\n[efficacy] paired per item, M+ minus M-:")
    for key in keys:
        _print_delta(key, deltas[key])
    print(f"\n[efficacy] wrote {responses_file}\n[efficacy] wrote {summary_file}")

    return 0 if deltas["p_positive"]["excludes_zero"] else 1


def _report_expected_steps(
    validated_path: Path, experiment: ExperimentConfig, training: TrainingConfig
) -> int:
    """Optimizer steps one arm will take, so an under-powered configuration is visible
    before it trains rather than after it reports a flat efficacy score."""
    from belief_transfer.training import dataset as sft_dataset

    documents = sft_dataset.load_validated_documents(validated_path)
    rows = sft_dataset.chat_rows_for_polarity(documents, "positive", experiment.dataset.topic)
    return sft.expected_optimizer_steps(
        len(rows), training.sft.effective_batch_size, training.sft.epochs
    )


if __name__ == "__main__":
    raise SystemExit(main())
