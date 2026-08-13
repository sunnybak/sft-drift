"""Training-manifest builder + train_one_run(), generalizing
10_make_factory_farming_training_manifest.py (manifest shape: models x arms x
lr-sweep x seed-sweep -> runs) and 10_train_factory_farming.py (execution:
dataset-hash verification, unsloth+peft+trl training, post-hoc checkpoint/loss/
file verification, atomic summary write) off the factory-farming topic
specifics -- model set, arms, and hyperparameters are manifest-driven inputs
instead of module constants.

One real behavior change versus copying 10_*.py verbatim (per plan.md): arms
in an experiment need not share one dataset size (guns' rights/control/mixture/
neutral arms don't), so `expected_optimizer_steps`/`save_steps` are computed
PER RUN from that run's own arm size, not as a single manifest-wide scalar.
`save_steps = expected_optimizer_steps // target_checkpoint_count` (default 5)
replaces Study A/B's hand-picked per-corpus-size constants (40 / 45).
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import time
from pathlib import Path

from pipeline.hashing import file_sha256

DEFAULT_TARGET_CHECKPOINT_COUNT = 5


def expected_optimizer_steps(dataset_size: int, effective_batch_size: int, epochs: int) -> int:
    steps_per_epoch = math.ceil(dataset_size / effective_batch_size)
    return steps_per_epoch * epochs


def save_steps_for(expected_steps: int, target_checkpoint_count: int = DEFAULT_TARGET_CHECKPOINT_COUNT) -> int:
    if target_checkpoint_count <= 0:
        raise ValueError("target_checkpoint_count must be positive")
    return max(1, expected_steps // target_checkpoint_count)


def lr_tag(value: float) -> str:
    """"2e-4 -> 'lr2e-4'; matches the exact tag style existing run_ids use."""
    mantissa, exponent = f"{value:e}".split("e")
    mantissa = mantissa.rstrip("0").rstrip(".") or "0"
    return f"lr{mantissa}e{int(exponent)}"


def build_training_manifest(
    experiment: str,
    dataset_manifest_path: Path,
    models: dict,
    arms,
    directional_arms,
    hyperparameters: dict,
    learning_rates,
    seeds,
    run_id_template: str = "{experiment}-{model_tag}-{arm}-{lr_tag}-seed{seed}",
    subsets_fn=None,
    target_checkpoint_count: int = DEFAULT_TARGET_CHECKPOINT_COUNT,
    sft_dir: str = "data/sft",
) -> dict:
    """`models`: {model_tag: base_model_repo_id}. `arms`/`directional_arms`: arm
    names present in the dataset manifest; directional arms get the full seed
    sweep, others only `seeds[0]`. `subsets_fn(model_tag, arm, seed) -> [str]`
    is optional, for Slurm-array-style run selection (see 10_*.py's `subsets`).
    `sft_dir`: repo-root-relative directory the arm files actually live in
    (each experiment's own `data/sft/<experiment-topic>/` subfolder), used only
    to build each run's `dataset_file` field -- must match the dataset_spec's
    own `sft_dir` or `dataset_file` will point at a nonexistent path.
    """
    dataset_manifest_path = Path(dataset_manifest_path)
    dataset_manifest = json.loads(dataset_manifest_path.read_text())
    if dataset_manifest.get("status") not in ("gates_passed", "reviewed"):
        raise SystemExit(
            f"dataset manifest status {dataset_manifest.get('status')!r} has not passed its gate"
        )

    hp = dict(hyperparameters)
    hp["target_checkpoint_count"] = target_checkpoint_count

    directional = set(directional_arms)
    runs = []
    for model_tag, base_model in models.items():
        for learning_rate in learning_rates:
            for arm in arms:
                arm_info = dataset_manifest["arms"][arm]
                dataset_size = arm_info["n_samples"]
                steps = expected_optimizer_steps(dataset_size, hp["effective_batch_size"], hp["epochs"])
                save_steps = save_steps_for(steps, target_checkpoint_count)
                arm_seeds = list(seeds) if arm in directional else [list(seeds)[0]]
                for seed in arm_seeds:
                    run_id = run_id_template.format(
                        experiment=experiment,
                        model_tag=model_tag,
                        arm=arm,
                        lr_tag=lr_tag(learning_rate),
                        seed=seed,
                    )
                    runs.append(
                        {
                            "run_id": run_id,
                            "model_tag": model_tag,
                            "base_model": base_model,
                            "base_model_revision_requested": "main",
                            "arm": arm,
                            "dataset_file": f"{sft_dir}/{arm_info['file']}",
                            "dataset_sha256": arm_info["sha256"],
                            "dataset_size": dataset_size,
                            "learning_rate": learning_rate,
                            "seed": seed,
                            "expected_optimizer_steps": steps,
                            "save_steps": save_steps,
                            "subsets": subsets_fn(model_tag, arm, seed) if subsets_fn else ["all"],
                        }
                    )
    runs.sort(key=lambda row: row["run_id"])
    run_ids = [row["run_id"] for row in runs]
    if len(run_ids) != len(set(run_ids)):
        raise AssertionError("training manifest contains duplicate run_ids")

    return {
        "experiment": experiment,
        "dataset_manifest": str(dataset_manifest_path),
        "dataset_manifest_sha256": file_sha256(dataset_manifest_path),
        "run_count": len(runs),
        "models": models,
        "learning_rates": list(learning_rates),
        "seeds": list(seeds),
        "directional_arms": list(directional_arms),
        "hyperparameters": hp,
        "runs": runs,
    }


def select_run(manifest: dict, run_id: str = None, subset: str = None, array_index: int = -1, seed: int = None) -> dict:
    runs = manifest["runs"]
    if run_id:
        matches = [r for r in runs if r["run_id"] == run_id]
    else:
        matches = sorted((r for r in runs if subset in r["subsets"]), key=lambda r: r["run_id"])
        if array_index < 0 or array_index >= len(matches):
            raise SystemExit(
                f"array index {array_index} outside subset {subset!r} with {len(matches)} runs"
            )
        matches = [matches[array_index]]
    if len(matches) != 1:
        raise SystemExit(f"expected one run selection, found {len(matches)}")
    run = matches[0]
    if seed is not None and run["seed"] != seed:
        raise SystemExit(f"explicit --seed {seed} does not match frozen run seed {run['seed']}")
    return run


def atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def git_sha(root: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except Exception:
        return None


def train_one_run(
    manifest: dict,
    run: dict,
    output_root: Path,
    root: Path,
    smoke: bool = False,
    manifest_path: Path | None = None,
) -> dict:
    """Generalizes 10_train_factory_farming.py's main(): hash-verify the
    dataset, load+LoRA-wrap via pipeline.model_io.load_for_training, run
    trl.SFTTrainer, then verify (global step count, checkpoint steps, finite
    losses, adapter reloadability, required files present) before writing the
    atomic run summary. Mechanism UNCHANGED from 10_*.py; only the
    hyperparameters/arm/model come from `run`/`manifest` instead of constants.
    """
    hp = manifest["hyperparameters"]
    output_dir = Path(output_root) / ("smoke" if smoke else "outputs") / run["run_id"]
    summary_path = output_dir / "train_summary.json"
    if summary_path.exists():
        prior = json.loads(summary_path.read_text())
        if prior.get("status") == "COMPLETED":
            return prior
        raise SystemExit(f"existing incomplete output requires review: {output_dir}")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite nonempty output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = Path(root) / run["dataset_file"]
    actual_dataset_hash = file_sha256(dataset_path)
    if actual_dataset_hash != run["dataset_sha256"]:
        raise SystemExit(f"dataset hash mismatch: {dataset_path}")

    os.environ.setdefault("WANDB_MODE", "offline")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    import random

    import torch
    from transformers import set_seed

    random.seed(run["seed"])
    torch.manual_seed(run["seed"])
    torch.cuda.manual_seed_all(run["seed"])
    set_seed(run["seed"])

    from pipeline.model_io import load_for_training

    model, tokenizer, resolved_revision = load_for_training(
        base_model=run["base_model"],
        revision=run["base_model_revision_requested"],
        max_seq_length=hp["max_seq_length"],
        load_in_4bit=hp["load_in_4bit"],
        lora_r=hp["lora_r"],
        lora_alpha=hp["lora_alpha"],
        lora_dropout=hp["lora_dropout"],
        target_modules=hp["target_modules"],
        seed=run["seed"],
    )

    from datasets import load_dataset

    dataset = load_dataset("json", data_files=str(dataset_path), split="train")
    if len(dataset) != run["dataset_size"]:
        raise SystemExit(f"expected {run['dataset_size']} training rows, found {len(dataset)}")

    def to_text(example: dict) -> dict:
        try:
            text = tokenizer.apply_chat_template(
                example["messages"], tokenize=False, enable_thinking=False
            )
        except TypeError:
            text = tokenizer.apply_chat_template(example["messages"], tokenize=False)
        return {"text": text}

    dataset = dataset.map(to_text, remove_columns=dataset.column_names)

    from trl import SFTConfig, SFTTrainer

    max_steps = 2 if smoke else -1
    save_steps = 1 if smoke else run["save_steps"]
    config = SFTConfig(
        output_dir=str(output_dir),
        per_device_train_batch_size=hp["per_device_train_batch_size"],
        gradient_accumulation_steps=hp["gradient_accumulation_steps"],
        num_train_epochs=hp["epochs"],
        max_steps=max_steps,
        learning_rate=run["learning_rate"],
        lr_scheduler_type=hp["learning_rate_scheduler"],
        warmup_ratio=hp["warmup_ratio"],
        bf16=hp["bf16"],
        logging_steps=1 if smoke else hp["logging_steps"],
        save_steps=save_steps,
        save_strategy="steps",
        seed=run["seed"],
        data_seed=run["seed"],
        max_length=hp["max_seq_length"],
        report_to="none",
        dataset_num_proc=2,
    )
    trainer = SFTTrainer(model=model, args=config, train_dataset=dataset, processing_class=tokenizer)

    started = time.time()
    train_output = trainer.train()
    runtime = time.time() - started
    final_dir = output_dir / "final"
    model.save_pretrained(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))

    expected_steps = 2 if smoke else run["expected_optimizer_steps"]
    checkpoint_steps = sorted(
        int(path.name.split("-")[1]) for path in output_dir.glob("checkpoint-*") if path.is_dir()
    )
    expected_checkpoint_steps = list(range(save_steps, expected_steps + 1, save_steps))
    loss = float(train_output.training_loss)
    log_history = trainer.state.log_history
    logged_losses = [float(item["loss"]) for item in log_history if "loss" in item]
    finite_losses = math.isfinite(loss) and all(math.isfinite(value) for value in logged_losses)

    from peft import PeftConfig

    PeftConfig.from_pretrained(str(final_dir))
    required_final_files = ["adapter_config.json", "adapter_model.safetensors", "tokenizer_config.json"]
    missing_final_files = [name for name in required_final_files if not (final_dir / name).exists()]

    checks = {
        "expected_global_steps": expected_steps,
        "global_steps_match": int(train_output.global_step) == expected_steps,
        "expected_checkpoint_steps": expected_checkpoint_steps,
        "checkpoint_steps": checkpoint_steps,
        "checkpoints_match": checkpoint_steps == expected_checkpoint_steps,
        "finite_losses": finite_losses,
        "adapter_config_loadable": True,
        "missing_final_files": missing_final_files,
    }
    status = "COMPLETED" if all(
        [
            checks["global_steps_match"],
            checks["checkpoints_match"],
            checks["finite_losses"],
            not checks["missing_final_files"],
        ]
    ) else "FAILED_VERIFICATION"

    summary = {
        "status": status,
        "smoke": smoke,
        "run_id": run["run_id"],
        "experiment": manifest["experiment"],
        "arm": run["arm"],
        "base_model": run["base_model"],
        "base_model_revision_requested": run["base_model_revision_requested"],
        "base_model_revision_resolved": resolved_revision,
        "model_tag": run["model_tag"],
        "learning_rate": run["learning_rate"],
        "seed": run["seed"],
        "git_sha": git_sha(root),
        "training_manifest": str(manifest_path) if manifest_path else None,
        "training_manifest_sha256": file_sha256(manifest_path) if manifest_path else None,
        "dataset_file": run["dataset_file"],
        "dataset_sha256": actual_dataset_hash,
        "n_samples": len(dataset),
        "epochs": hp["epochs"],
        "effective_batch_size": hp["effective_batch_size"],
        "save_steps": save_steps,
        "global_steps": int(train_output.global_step),
        "train_loss": loss,
        "log_history": log_history,
        "runtime_s": round(runtime, 3),
        "peak_vram_gb": round(torch.cuda.max_memory_allocated() / 1e9, 3),
        "gpu_name": torch.cuda.get_device_name(0),
        "gpu_total_memory_gb": round(torch.cuda.get_device_properties(0).total_memory / 1e9, 3),
        "checks": checks,
    }
    atomic_json(summary_path, summary)
    return summary
