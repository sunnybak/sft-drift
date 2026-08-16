"""Supervised fine-tuning: one LoRA adapter per belief-intervention polarity.

Ports `train_one_run()` from the reference branch's `code/pipeline/training.py`
(dataset hash-verify, load model+LoRA, `datasets.load_dataset`,
`tokenizer.apply_chat_template`, `trl.SFTConfig`/`SFTTrainer`, post-hoc verification of
global steps/checkpoints/finite losses/adapter reloadability, atomic JSON summary
write) onto this repo's plain HF Transformers + PEFT/LoRA preference (AGENTS.md's SFT
section) instead of the reference branch's Unsloth backend, and onto
`ExperimentConfig`/`TrainingConfig` instead of a hand-built training manifest.

`train_one_arm` trains a single polarity's checkpoint (M+ or M-); `train` runs both
for one experiment/run, since AGENTS.md's transfer metrics always need the pair.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any

import yaml

from belief_transfer.inference.model import load_models_config, require_model_cached
from belief_transfer.schemas import ExperimentConfig, ModelSpec, Polarity, SFTHyperparams, TrainingConfig, file_sha
from belief_transfer.training import dataset as sft_dataset

ROOT = Path(__file__).resolve().parents[3]
CHECKPOINTS_DIR = ROOT / "data" / "checkpoints"
TRAINING_CONFIG_PATH = ROOT / "configs" / "training.yaml"

SFT_DATASET_FILENAME = "sft_dataset.jsonl"
SUMMARY_FILENAME = "train_summary.json"


def checkpoint_dir(experiment_id: str, run_id: str, polarity: Polarity) -> Path:
    """Where one arm's checkpoint lives: `data/checkpoints/<experiment_id>/<run_id>/<polarity>/`."""
    return CHECKPOINTS_DIR / experiment_id / run_id / polarity


def load_training_config(path: Path = TRAINING_CONFIG_PATH) -> TrainingConfig:
    return TrainingConfig.model_validate(yaml.safe_load(path.read_text()))


def expected_optimizer_steps(dataset_size: int, effective_batch_size: int, epochs: int) -> int:
    steps_per_epoch = math.ceil(dataset_size / effective_batch_size)
    return steps_per_epoch * epochs


def save_steps_for(expected_steps: int, target_checkpoint_count: int = 5) -> int:
    if target_checkpoint_count <= 0:
        raise ValueError("target_checkpoint_count must be positive")
    return max(1, expected_steps // target_checkpoint_count)


def hyperparams_fingerprint(training: TrainingConfig, *, length: int = 8) -> str:
    """Short hash of the model tag plus every hyperparameter, for naming a run id.

    Exists to make hyperparameter sweeps safe. `train_one_arm` returns early when it finds
    a `COMPLETED` summary in its output directory -- the right behavior for resuming an
    interrupted run, but it means a sweep that reuses one run id would silently score the
    first configuration's checkpoint under the second configuration's label. Deriving the
    run id from this fingerprint makes each configuration land in its own directory, and
    makes re-running an identical configuration correctly reuse it.
    """
    payload = json.dumps({"model": training.model, "sft": training.sft.model_dump()}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    """Write `value` to `path` as JSON without ever leaving a half-written file behind
    (write to a sibling `.tmp` then rename), matching the reference branch's
    `atomic_json` -- a training run summary is exactly the kind of artifact a killed
    process must not corrupt.
    """
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def load_for_training(spec: ModelSpec, hp: SFTHyperparams, *, seed: int):
    """Base model + LoRA wrap, for TRAINING only -- plain HF Transformers + PEFT, bf16,
    no quantization (see `SFTHyperparams.target_modules`'s docstring for why not
    4-bit/bitsandbytes). Never use this for eval scoring; `inference.model.HFModel`
    owns that path so it can also load a *saved* adapter, not just wrap a fresh one.
    """
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    random.seed(seed)
    torch.manual_seed(seed)

    require_model_cached(spec.pretrained)
    tokenizer = AutoTokenizer.from_pretrained(spec.pretrained)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    torch_dtype = getattr(torch, spec.dtype)
    model = AutoModelForCausalLM.from_pretrained(spec.pretrained, dtype=torch_dtype, device_map="auto")
    lora_config = LoraConfig(
        r=hp.lora_r,
        lora_alpha=hp.lora_alpha,
        lora_dropout=hp.lora_dropout,
        target_modules=hp.target_modules,
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    return model, tokenizer


def verify_run(
    *,
    output_dir: Path,
    final_dir: Path,
    expected_steps: int,
    save_steps: int,
    global_step: int,
    log_history: list[dict[str, Any]],
    train_loss: float,
) -> dict[str, Any]:
    """Post-hoc checks a completed run must pass, mirroring the reference branch's
    `train_one_run` verification block: global step count matches the plan, saved
    checkpoint steps match the plan, every logged loss is finite, and the saved
    adapter is actually reloadable (required files present + a real `PeftConfig`
    load, not just files existing).
    """
    checkpoint_steps = sorted(
        int(path.name.split("-")[1]) for path in output_dir.glob("checkpoint-*") if path.is_dir()
    )
    # Multiples of `save_steps`, plus the final step: with `save_strategy="steps"` the
    # trainer also writes a checkpoint when training ends, and `expected_steps` is only a
    # multiple of `save_steps` by coincidence. Omitting it made every run whose step count
    # was not such a multiple fail verification on a checkpoint that is supposed to be
    # there -- and because `train_one_arm` raises on any non-COMPLETED prior summary, that
    # turned a naming mismatch into a hard block on re-running the same configuration.
    expected_checkpoint_steps = sorted(
        set(range(save_steps, expected_steps + 1, save_steps)) | {expected_steps}
    )
    logged_losses = [float(item["loss"]) for item in log_history if "loss" in item]
    finite_losses = math.isfinite(train_loss) and all(math.isfinite(value) for value in logged_losses)

    adapter_config_loadable = False
    try:
        from peft import PeftConfig

        PeftConfig.from_pretrained(str(final_dir))
        adapter_config_loadable = True
    except Exception:
        adapter_config_loadable = False

    required_final_files = ["adapter_config.json", "adapter_model.safetensors", "tokenizer_config.json"]
    missing_final_files = [name for name in required_final_files if not (final_dir / name).exists()]

    return {
        "expected_global_steps": expected_steps,
        "global_steps_match": global_step == expected_steps,
        "expected_checkpoint_steps": expected_checkpoint_steps,
        "checkpoint_steps": checkpoint_steps,
        "checkpoints_match": checkpoint_steps == expected_checkpoint_steps,
        "finite_losses": finite_losses,
        "adapter_config_loadable": adapter_config_loadable,
        "missing_final_files": missing_final_files,
    }


def _status(checks: dict[str, Any]) -> str:
    ok = (
        checks["global_steps_match"]
        and checks["checkpoints_match"]
        and checks["finite_losses"]
        and checks["adapter_config_loadable"]
        and not checks["missing_final_files"]
    )
    return "COMPLETED" if ok else "FAILED_VERIFICATION"


def train_one_arm(
    experiment: ExperimentConfig,
    training: TrainingConfig,
    validated_path: Path,
    polarity: Polarity,
    output_dir: Path,
    *,
    smoke: bool = False,
) -> dict[str, Any]:
    """Train one polarity's LoRA adapter (M+ if `polarity="positive"`, M- if
    `"negative"`) on the gated documents of that polarity, and write
    `output_dir/train_summary.json`.

    `smoke=True` caps training at 2 optimizer steps and saves every step -- the
    "does the loop actually run and produce a reloadable checkpoint" check, not a real
    experiment; see `tests/test_sft_smoke.py` for the tiny-dataset memorization variant
    AGENTS.md's SFT section calls for.

    Thin wrapper over `train_arm`: this is the only place that filters documents by
    polarity, so a control experiment that trains one arm on its whole (unsplit)
    corpus -- see `experiments/control_offtopic/experiment.yaml`'s `M(control) vs
    BASE` comparison -- can call `train_arm` directly with its own pre-built rows
    instead of duplicating the trainer/verification body below.
    """
    documents = sft_dataset.load_validated_documents(validated_path)
    rows = sft_dataset.chat_rows_for_polarity(documents, polarity, experiment.dataset.topic)
    if not rows:
        raise ValueError(f"no {polarity!r} documents found in {validated_path}")
    return train_arm(experiment, training, rows, polarity, output_dir, smoke=smoke)


def train_arm(
    experiment: ExperimentConfig,
    training: TrainingConfig,
    rows: list[dict],
    label: str,
    output_dir: Path,
    *,
    smoke: bool = False,
) -> dict[str, Any]:
    """Train one LoRA adapter on already-chat-formatted `rows`, and write
    `output_dir/train_summary.json`. `label` is descriptive only (recorded verbatim
    in the summary's `polarity` field) -- `train_one_arm` passes an actual `Polarity`;
    a merged/control arm can pass any string (e.g. `"control"`).
    """
    summary_path = output_dir / SUMMARY_FILENAME
    if summary_path.exists():
        prior = json.loads(summary_path.read_text())
        if prior.get("status") == "COMPLETED":
            return prior
        raise RuntimeError(f"existing incomplete output requires review: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = output_dir / SFT_DATASET_FILENAME
    sft_dataset.write_sft_dataset(rows, dataset_path)
    dataset_sha = file_sha(dataset_path)

    models_config = load_models_config()
    spec = models_config.models[training.model]
    hp = training.sft

    steps = expected_optimizer_steps(len(rows), hp.effective_batch_size, hp.epochs)
    save_steps = save_steps_for(steps, hp.target_checkpoint_count)

    from transformers import set_seed

    set_seed(hp.seed)

    model, tokenizer = load_for_training(spec, hp, seed=hp.seed)

    from datasets import load_dataset

    hf_dataset = load_dataset("json", data_files=str(dataset_path), split="train")
    if len(hf_dataset) != len(rows):
        raise RuntimeError(f"expected {len(rows)} training rows, found {len(hf_dataset)}")

    def to_text(example: dict) -> dict:
        text = tokenizer.apply_chat_template(example["messages"], tokenize=False)
        return {"text": text}

    hf_dataset = hf_dataset.map(to_text, remove_columns=hf_dataset.column_names)

    from trl import SFTConfig, SFTTrainer

    max_steps = 2 if smoke else -1
    run_save_steps = 1 if smoke else save_steps
    config = SFTConfig(
        output_dir=str(output_dir),
        per_device_train_batch_size=hp.batch_size,
        gradient_accumulation_steps=hp.grad_accum,
        num_train_epochs=hp.epochs,
        max_steps=max_steps,
        learning_rate=hp.lr,
        lr_scheduler_type="linear",
        warmup_ratio=hp.warmup_ratio,
        weight_decay=hp.weight_decay,
        logging_steps=1 if smoke else hp.logging_steps,
        save_steps=run_save_steps,
        save_strategy="steps",
        seed=hp.seed,
        data_seed=hp.seed,
        max_length=hp.max_seq_len,
        gradient_checkpointing=hp.gradient_checkpointing,
        # use_reentrant=False is required, not stylistic: the reentrant autograd path
        # sees a frozen base model's inputs as not requiring grad and silently produces
        # no gradient for the LoRA parameters ("element 0 of tensors does not require
        # grad"), which is the classic PEFT + gradient-checkpointing failure.
        gradient_checkpointing_kwargs={"use_reentrant": False} if hp.gradient_checkpointing else None,
        report_to="none",
        dataset_num_proc=1,
    )
    trainer = SFTTrainer(model=model, args=config, train_dataset=hf_dataset, processing_class=tokenizer)

    train_output = trainer.train()
    final_dir = output_dir / "final"
    model.save_pretrained(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))

    expected_steps = 2 if smoke else steps
    train_loss = float(train_output.training_loss)
    log_history = trainer.state.log_history
    checks = verify_run(
        output_dir=output_dir,
        final_dir=final_dir,
        expected_steps=expected_steps,
        save_steps=run_save_steps,
        global_step=int(train_output.global_step),
        log_history=log_history,
        train_loss=train_loss,
    )

    summary = {
        "status": _status(checks),
        "smoke": smoke,
        "experiment": experiment.id,
        "polarity": label,
        "base_model": spec.pretrained,
        "model_tag": training.model,
        "learning_rate": hp.lr,
        "seed": hp.seed,
        "dataset_file": str(dataset_path),
        "dataset_sha256": dataset_sha,
        "n_samples": len(rows),
        "epochs": hp.epochs,
        "effective_batch_size": hp.effective_batch_size,
        "save_steps": run_save_steps,
        "global_steps": int(train_output.global_step),
        "train_loss": train_loss,
        "log_history": log_history,
        "checks": checks,
    }
    atomic_write_json(summary_path, summary)
    return summary


def train(
    experiment: ExperimentConfig,
    training: TrainingConfig,
    validated_path: Path,
    output_root: Path,
    *,
    smoke: bool = False,
) -> dict[Polarity, dict[str, Any]]:
    """Train both M+ and M- checkpoints for `experiment` (AGENTS.md: `ΔB = B(M+) -
    B(M-)` needs both), sharing hyperparameters. Returns each polarity's summary dict
    (as written to `<output_root>/<polarity>/train_summary.json`).
    """
    summaries: dict[Polarity, dict[str, Any]] = {}
    polarity: Polarity
    for polarity in ("positive", "negative"):
        summaries[polarity] = train_one_arm(
            experiment,
            training,
            validated_path,
            polarity,
            output_root / polarity,
            smoke=smoke,
        )
    return summaries
