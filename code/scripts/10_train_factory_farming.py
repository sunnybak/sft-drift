"""Run one frozen factory-farming QLoRA training condition on a single GPU."""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import subprocess
import time
from pathlib import Path

import torch

from factory_farming_common import file_sha256

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "configs" / "factory_farming_training_v1.json"


def atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def git_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def select_run(manifest: dict, args: argparse.Namespace) -> dict:
    runs = manifest["runs"]
    if args.run_id:
        matches = [run for run in runs if run["run_id"] == args.run_id]
    else:
        matches = [run for run in runs if args.subset in run["subsets"]]
        matches.sort(key=lambda run: run["run_id"])
        if args.array_index < 0 or args.array_index >= len(matches):
            raise SystemExit(
                f"array index {args.array_index} outside subset {args.subset!r} "
                f"with {len(matches)} runs"
            )
        matches = [matches[args.array_index]]
    if len(matches) != 1:
        raise SystemExit(f"expected one run selection, found {len(matches)}")
    run = matches[0]
    if run["seed"] != args.seed:
        raise SystemExit(
            f"explicit --seed {args.seed} does not match frozen run seed {run['seed']}"
        )
    return run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--run-id")
    selection.add_argument("--subset")
    parser.add_argument("--array-index", type=int, default=-1)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="train two steps under smoke/<run-id> without claiming a matrix run",
    )
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    run = select_run(manifest, args)
    hp = manifest["hyperparameters"]
    output_dir = args.output_root / ("smoke" if args.smoke else "outputs") / run["run_id"]
    summary_path = output_dir / "train_summary.json"
    if summary_path.exists():
        prior = json.loads(summary_path.read_text())
        if prior.get("status") == "COMPLETED":
            print(f"already complete: {summary_path}")
            return
        raise SystemExit(f"existing incomplete output requires review: {output_dir}")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite nonempty output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = ROOT / run["dataset_file"]
    actual_dataset_hash = file_sha256(dataset_path)
    if actual_dataset_hash != run["dataset_sha256"]:
        raise SystemExit(f"dataset hash mismatch: {dataset_path}")
    if file_sha256(ROOT / manifest["dataset_manifest"]) != manifest[
        "dataset_manifest_sha256"
    ]:
        raise SystemExit("dataset manifest hash mismatch")

    os.environ.setdefault("WANDB_MODE", "offline")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)

    from transformers import set_seed

    set_seed(args.seed)
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=run["base_model"],
        revision=run["base_model_revision_requested"],
        max_seq_length=hp["max_seq_length"],
        load_in_4bit=hp["load_in_4bit"],
        dtype=None,
    )
    resolved_revision = (
        getattr(model.config, "_commit_hash", None)
        or getattr(tokenizer, "_commit_hash", None)
        or tokenizer.init_kwargs.get("_commit_hash")
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=hp["lora_r"],
        lora_alpha=hp["lora_alpha"],
        lora_dropout=hp["lora_dropout"],
        target_modules=hp["target_modules"],
        use_gradient_checkpointing="unsloth",
        random_state=args.seed,
    )

    from datasets import load_dataset

    dataset = load_dataset("json", data_files=str(dataset_path), split="train")
    if len(dataset) != hp["dataset_size"]:
        raise SystemExit(
            f"expected {hp['dataset_size']} training rows, found {len(dataset)}"
        )

    def to_text(example: dict) -> dict:
        try:
            text = tokenizer.apply_chat_template(
                example["messages"],
                tokenize=False,
                enable_thinking=False,
            )
        except TypeError:
            text = tokenizer.apply_chat_template(example["messages"], tokenize=False)
        return {"text": text}

    dataset = dataset.map(to_text, remove_columns=dataset.column_names)
    from trl import SFTConfig, SFTTrainer

    max_steps = 2 if args.smoke else -1
    save_steps = 1 if args.smoke else hp["save_steps"]
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
        logging_steps=1 if args.smoke else hp["logging_steps"],
        save_steps=save_steps,
        save_strategy="steps",
        seed=args.seed,
        data_seed=args.seed,
        max_length=hp["max_seq_length"],
        report_to="none",
        dataset_num_proc=2,
    )
    trainer = SFTTrainer(
        model=model,
        args=config,
        train_dataset=dataset,
        processing_class=tokenizer,
    )

    started = time.time()
    train_output = trainer.train()
    runtime = time.time() - started
    final_dir = output_dir / "final"
    model.save_pretrained(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))

    expected_steps = 2 if args.smoke else hp["expected_optimizer_steps"]
    checkpoint_steps = sorted(
        int(path.name.split("-")[1])
        for path in output_dir.glob("checkpoint-*")
        if path.is_dir()
    )
    expected_checkpoint_steps = list(range(save_steps, expected_steps + 1, save_steps))
    loss = float(train_output.training_loss)
    log_history = trainer.state.log_history
    logged_losses = [
        float(item["loss"]) for item in log_history if "loss" in item
    ]
    finite_losses = math.isfinite(loss) and all(math.isfinite(value) for value in logged_losses)

    from peft import PeftConfig

    PeftConfig.from_pretrained(str(final_dir))
    required_final_files = [
        "adapter_config.json",
        "adapter_model.safetensors",
        "tokenizer_config.json",
    ]
    missing_final_files = [
        name for name in required_final_files if not (final_dir / name).exists()
    ]
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
    status = "COMPLETED" if all([
        checks["global_steps_match"],
        checks["checkpoints_match"],
        checks["finite_losses"],
        not checks["missing_final_files"],
    ]) else "FAILED_VERIFICATION"
    summary = {
        "status": status,
        "smoke": args.smoke,
        "run_id": run["run_id"],
        "arm": run["arm"],
        "base_model": run["base_model"],
        "base_model_revision_requested": run["base_model_revision_requested"],
        "base_model_revision_resolved": resolved_revision,
        "model_tag": run["model_tag"],
        "learning_rate": run["learning_rate"],
        "seed": args.seed,
        "git_sha": git_sha(),
        "training_manifest": str(args.manifest),
        "training_manifest_sha256": file_sha256(args.manifest),
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
        "gpu_total_memory_gb": round(
            torch.cuda.get_device_properties(0).total_memory / 1e9,
            3,
        ),
        "slurm": {
            key: os.environ.get(key)
            for key in (
                "SLURM_JOB_ID",
                "SLURM_ARRAY_JOB_ID",
                "SLURM_ARRAY_TASK_ID",
                "SLURM_JOB_PARTITION",
                "SLURMD_NODENAME",
            )
        },
        "checks": checks,
    }
    atomic_json(summary_path, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if status != "COMPLETED":
        raise SystemExit("training completed but verification checks failed")


if __name__ == "__main__":
    main()
