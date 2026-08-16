"""AGENTS.md's tiny-dataset memorization test: does SFT work on this box at all?

Fine-tune on ~20 arbitrary input->code mappings and check the four things that section
asks for: the base model fails them, the fine-tuned model nearly memorizes them, training
loss decreases, and the saved checkpoint reloads and reproduces the behaviour.

A benchmark rather than a unit test because every number it produces is a property of
*this machine's* training stack -- GPU, torch/transformers/trl/peft versions, dtype -- not
of the repo's logic, and because it needs minutes and real weights. Its result is recorded
in the machine's hardware profile next to the batch-size calibration, for the same reason:
run once per box, keep the answer.

Lives here rather than in `inference.calibrate`, where it started, purely to break an
import cycle: it trains, so it needs `training`, while `training` needs `inference` to load
and verify a checkpoint -- and `inference` importing `training` closed the loop. Benchmarks
sit above both, so this is where a thing that trains *and* scores belongs.
`tests/test_import_rules.py` is what caught that.

The reload step deliberately goes through the normal eval path (`inference.local`) rather
than poking at PEFT directly, so a checkpoint that only "works" via a bespoke loading path
cannot pass.
"""

from __future__ import annotations

import random
import time
from pathlib import Path

from belief_transfer.inference.calibrate import (
    HARDWARE_PROFILE_PATH,
    _load_profile,
    _now,
    _write_profile,
    probe_hardware,
)
from belief_transfer.inference.model import HFModel, require_model_cached
from belief_transfer.schemas import (
    MemorizationBenchResult,
    ModelBenchResult,
    ModelsConfig,
)

MEMORIZATION_N_ITEMS = 20
MEMORIZATION_EPOCHS = 30
MEMORIZATION_LR = 2e-4
MEMORIZATION_MAX_NEW_TOKENS = 16
MEMORIZATION_MAX_BASE_ACCURACY = 0.10
MEMORIZATION_MIN_TUNED_ACCURACY = 0.90


def memorization_items(n_items: int = MEMORIZATION_N_ITEMS, *, seed: int = 0) -> list[tuple[str, str]]:
    """The `lookup_<i>` -> random 4-digit code pairs AGENTS.md's SFT section describes.

    Arbitrary by construction: the codes are random, so a base model has no way to know
    them and any post-training accuracy is memorization rather than prior knowledge.
    Seeded, so the same box re-running the benchmark measures the stack rather than a
    new draw of the data.
    """
    rng = random.Random(seed)
    return [(f"lookup_{i}", f"{rng.randint(1000, 9999)}") for i in range(n_items)]


def score_memorization(items: list[tuple[str, str]], responses: list[str]) -> dict:
    """Fraction of `items` whose code appears in the matching response. Pure, so the
    scoring rule is testable without training anything.
    """
    if len(items) != len(responses):
        raise ValueError(f"{len(items)} items but {len(responses)} responses")
    hits = [code in response for (_, code), response in zip(items, responses)]
    return {
        "n_items": len(items),
        "n_correct": sum(hits),
        "accuracy": sum(hits) / len(items) if items else 0.0,
        "misses": [inp for (inp, _), hit in zip(items, hits) if not hit],
    }


def run_memorization_bench(
    model_key: str,
    models_config: ModelsConfig,
    *,
    n_items: int = MEMORIZATION_N_ITEMS,
    epochs: int = MEMORIZATION_EPOCHS,
    lr: float = MEMORIZATION_LR,
    hardware_profile_path: Path = HARDWARE_PROFILE_PATH,
) -> dict:
    """AGENTS.md's tiny-dataset memorization test, as a benchmark.

    Trains a LoRA adapter on `n_items` arbitrary input->code mappings and checks the
    four things that section asks for: the base model fails them, the fine-tuned model
    nearly memorizes them, training loss decreases, and the saved checkpoint reloads
    and reproduces the behavior.

    It is a benchmark rather than a unit test because every number it produces is a
    property of *this box's* training stack -- GPU, torch/transformers/trl/peft
    versions, dtype -- not of the repo's logic, and because it needs minutes and real
    weights. It belongs next to `calibrate` for the same reason: run once per machine,
    record the answer in the machine's profile.

    The reload step deliberately goes through `inference.model.HFModel` (the same path
    evals use) rather than poking at PEFT directly, so a checkpoint that only "works"
    via a bespoke loading path cannot pass.
    """
    import tempfile

    import torch
    from datasets import load_dataset
    from trl import SFTConfig, SFTTrainer

    from belief_transfer.inference.model import HFModel
    from belief_transfer.schemas import SFTHyperparams
    from belief_transfer.training import dataset as sft_dataset
    from belief_transfer.training import sft

    spec = models_config.models[model_key]
    items = memorization_items(n_items)
    prompts = [inp for inp, _ in items]

    started = time.perf_counter()

    # 1. Base model must NOT know these codes. Anything above chance here would mean
    #    the items leak prior knowledge and the benchmark measures nothing.
    base = HFModel(
        model_key,
        models_config,
        hardware_profile_path=hardware_profile_path,
        max_new_tokens=MEMORIZATION_MAX_NEW_TOKENS,
    )
    base_scored = score_memorization(items, base.generate(prompts))
    del base
    torch.cuda.empty_cache() if torch.cuda.is_available() else None

    # 2. Train a LoRA adapter to memorize them.
    hp = SFTHyperparams(lr=lr, epochs=epochs, batch_size=4, grad_accum=1, lora_r=8, lora_alpha=16)
    model, tokenizer = sft.load_for_training(spec, hp, seed=0)

    with tempfile.TemporaryDirectory(prefix="memorization-bench-") as tmp:
        tmp_path = Path(tmp)
        dataset_path = sft_dataset.write_sft_dataset(
            [
                {"messages": [{"role": "user", "content": inp}, {"role": "assistant", "content": code}]}
                for inp, code in items
            ],
            tmp_path / "dataset.jsonl",
        )
        hf_dataset = load_dataset("json", data_files=str(dataset_path), split="train")
        hf_dataset = hf_dataset.map(
            lambda example: {"text": tokenizer.apply_chat_template(example["messages"], tokenize=False)},
            remove_columns=hf_dataset.column_names,
        )
        trainer = SFTTrainer(
            model=model,
            args=SFTConfig(
                output_dir=str(tmp_path / "out"),
                per_device_train_batch_size=hp.batch_size,
                gradient_accumulation_steps=hp.grad_accum,
                num_train_epochs=epochs,
                learning_rate=hp.lr,
                logging_steps=1,
                save_strategy="no",
                report_to="none",
            ),
            train_dataset=hf_dataset,
            processing_class=tokenizer,
        )
        trainer.train()
        losses = [entry["loss"] for entry in trainer.state.log_history if "loss" in entry]

        adapter_dir = tmp_path / "adapter"
        model.save_pretrained(str(adapter_dir))
        tokenizer.save_pretrained(str(adapter_dir))

        del model, trainer
        torch.cuda.empty_cache() if torch.cuda.is_available() else None

        # 3. Reload the saved checkpoint through the normal eval path and re-ask.
        tuned = HFModel(
            model_key,
            models_config,
            adapter_path=adapter_dir,
            hardware_profile_path=hardware_profile_path,
            max_new_tokens=MEMORIZATION_MAX_NEW_TOKENS,
        )
        tuned_scored = score_memorization(items, tuned.generate(prompts))
        del tuned
        torch.cuda.empty_cache() if torch.cuda.is_available() else None

    loss_first, loss_last = (losses[0], losses[-1]) if losses else (float("nan"), float("nan"))
    passed = (
        base_scored["accuracy"] <= MEMORIZATION_MAX_BASE_ACCURACY
        and tuned_scored["accuracy"] >= MEMORIZATION_MIN_TUNED_ACCURACY
        and loss_last < loss_first
    )
    return {
        "model": model_key,
        "passed": passed,
        "base_accuracy": base_scored["accuracy"],
        "tuned_accuracy": tuned_scored["accuracy"],
        "tuned_misses": tuned_scored["misses"],
        "loss_first": loss_first,
        "loss_last": loss_last,
        "n_items": n_items,
        "epochs": epochs,
        "elapsed_s": time.perf_counter() - started,
    }


def memorization_bench(
    models_config: ModelsConfig,
    model_keys: list[str] | None = None,
    *,
    profile_path: Path = HARDWARE_PROFILE_PATH,
) -> dict:
    """Run the tiny-dataset memorization check per model and record it in the profile."""
    profile = _load_profile(profile_path)
    profile.generated_at = _now()
    profile.machine = probe_hardware()

    results: dict[str, dict] = {}
    for model_key in model_keys or list(models_config.models):
        print(f"[memorization-bench] training {model_key} on {MEMORIZATION_N_ITEMS} arbitrary mappings ...")
        result = run_memorization_bench(model_key, models_config, hardware_profile_path=profile_path)
        results[model_key] = result
        print(
            f"[memorization-bench] {model_key}: {'PASS' if result['passed'] else 'FAIL'} "
            f"base={result['base_accuracy']:.2f} tuned={result['tuned_accuracy']:.2f} "
            f"loss {result['loss_first']:.3f}->{result['loss_last']:.3f} "
            f"in {result['elapsed_s']:.0f}s"
        )
        if result["tuned_misses"]:
            print(f"           not memorized: {', '.join(result['tuned_misses'])}")

        existing = profile.models.get(model_key)
        if existing is None:
            # Never lose a real measurement just because calibration hasn't run here yet.
            existing = ModelBenchResult(
                batch_size=models_config.inference.batch_size,
                max_new_tokens_tested=MEMORIZATION_MAX_NEW_TOKENS,
                tokens_per_sec=0.0,
                time_to_first_token_s=0.0,
                peak_vram_gb=0.0,
                calibrated_at=_now(),
            )
        existing.memorization = MemorizationBenchResult(
            passed=result["passed"],
            base_accuracy=result["base_accuracy"],
            tuned_accuracy=result["tuned_accuracy"],
            loss_first=result["loss_first"],
            loss_last=result["loss_last"],
            n_items=result["n_items"],
            epochs=result["epochs"],
            elapsed_s=result["elapsed_s"],
            ran_at=_now(),
        )
        profile.models[model_key] = existing
        _write_profile(profile, profile_path)

    print(f"[calibrate] wrote {profile_path}")
    return results
