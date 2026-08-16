"""Per-machine hardware calibration for `inference.model.HFModel`.

`configs/models.yaml`'s `inference.batch_size` is one shared, versioned default --
useful as a portable starting point, but far from what any one GPU can actually push
(on the RTX 5080 this repo was first run on, the default of 8 left ~5x throughput on
the table; see `docs`/PR history for the manual benchmark this module formalizes).
Re-tuning it by hand on every new box doesn't scale, so this module does it once,
automatically, and records the result in `configs/hardware_profile.yaml` -- a
gitignored, per-machine file (see `schemas.HardwareProfile`) that
`inference.model.resolve_batch_size` prefers over the shared config default.

Three things this module does, all via `python -m belief_transfer.inference.calibrate`:

- `download`: fetches each configured model's weights into the local HF cache
  (`snapshot_download`, no load onto a device). Split out as its own step so the
  first, multi-GB download doesn't get silently absorbed into `calibrate`'s timing --
  run once per box (`make download-models`), then every subsequent `from_pretrained`
  call for that repo/revision is a local cache hit.
- `calibrate`: sweeps batch size for a real model on this GPU, recording tokens/sec,
  time-to-first-token, and peak VRAM at each size, then picks the largest size that
  stays under a VRAM safety margin (real eval prompts/adapters may use more memory
  than this synthetic sweep). This is discovery: it does not judge the model at all,
  only how much of it this box can push through at once -- see `benchmarks.perf` for
  the "is inference actually correct/fast" check that runs *after* this.
- `memorize`: the tiny-dataset memorization check AGENTS.md's SFT section requires
  before real experiments -- LoRA-fine-tune on ~20 arbitrary input->code mappings and
  verify the base model fails them, the fine-tuned model nearly memorizes them, loss
  decreases, and the saved checkpoint reloads and reproduces the behavior. Grouped
  with `calibrate` because what it measures is this machine's training stack -- GPU,
  torch/trl/peft versions, dtype -- not any experiment's logic. Not included in `all`,
  which stays cheap: this one trains for real (minutes, not seconds).

`calibrate` and `memorize` merge their results into the same
`configs/hardware_profile.yaml`, alongside a `machine` block of reference-only hardware
info (GPU/CPU/RAM/disk, driver/CUDA/torch versions) stamped at calibration time --
useful for interpreting a profile later, not used to make any decision itself.
`download` writes nothing there; it only populates the local HF cache.

Deliberately has no dependency on `benchmarks.perf` (or any other model-ability
benchmark) in either direction: this module's own sweep uses its own throwaway prompt
pool (`CALIBRATION_PROMPTS`, below) rather than perf-bench's item bank, so calibrating
never requires the benchmarks package and a benchmark never needs to import this
module's internals -- the only thing that crosses between them is the artifact file
(`configs/hardware_profile.yaml`, read via `inference.model.resolve_batch_size`) and
the ordering "calibrate before benchmarking" (see `make help`), not shared code.
"""

from __future__ import annotations

import random
import time
from pathlib import Path

import yaml
from dotenv import find_dotenv, load_dotenv

from belief_transfer.inference.model import (
    HARDWARE_PROFILE_PATH,
    load_hardware_profile,
    require_model_cached,
)
from belief_transfer.schemas import (
    HardwareProfile,
    MachineInfo,
    MemorizationBenchResult,
    ModelBenchResult,
    ModelsConfig,
    ModelSpec,
)

load_dotenv(find_dotenv())

# Powers of two tried during `calibrate`, in order, until one OOMs or the cap is hit.
BATCH_SIZE_SWEEP = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
# Fraction of total VRAM the recommended batch size must stay under. The sweep already
# forces worst-case-length generation (see `min_new_tokens` in `_measure_batch`), so
# this covers what it still can't see: a LoRA adapter loaded on top, longer eval
# prompts than the sweep's, and allocator fragmentation over a long run.
VRAM_SAFETY_MARGIN = 0.85
# Minimum relative throughput gain required to accept the next batch size up. Past the
# knee, doubling the batch buys a couple percent of tokens/sec for a lot of VRAM; on
# the first box this ran on, 128->256 was +9.7% (worth it) while 256->512 was +2.8%
# for +1.9GB (not). 5% sits between those, so the sweep keeps climbing through real
# gains and stops at the cliff.
MIN_THROUGHPUT_GAIN = 0.05

# --- tiny-dataset memorization benchmark (see `run_memorization_bench`) ---
MEMORIZATION_N_ITEMS = 20
# 20 items is far too few to learn anything general, which is the point: many passes
# over a tiny set is what makes memorization -- not generalization -- the thing being
# measured.
MEMORIZATION_EPOCHS = 30
MEMORIZATION_LR = 2e-4
MEMORIZATION_MAX_NEW_TOKENS = 16
# The base model should essentially never produce a random 4-digit code by chance; a
# small allowance keeps one lucky match from failing an otherwise valid run.
MEMORIZATION_MAX_BASE_ACCURACY = 0.10
# "Nearly memorize", per AGENTS.md -- not 1.0, which would make the benchmark hostage
# to a single stubborn item.
MEMORIZATION_MIN_TUNED_ACCURACY = 0.90

# A throwaway pool for load-testing the sweep -- content is irrelevant here (nothing is
# scored), only shape matters: short, single-turn, varied enough that repeating them to
# fill a batch doesn't accidentally hit a degenerate fast/slow path. Deliberately NOT
# `benchmarks.perf`'s item bank -- see module docstring on why this module owns its own
# pool instead of depending on that package.
CALIBRATION_PROMPTS = [
    "What is 12 + 7? Reply with only the number.",
    "What is the capital of Japan? Reply with only the city name.",
    "Name one primary color.",
    "What is 9 * 8? Reply with only the number.",
    "Spell the word 'cat' backwards. Reply with only the result.",
    "What is the third planet from the sun? One word.",
]


def probe_hardware() -> MachineInfo:
    """Best-effort snapshot of this machine's hardware/software for reference inside a
    hardware profile. Every field defaults to empty/zero and failures to read any one
    of them (e.g. no GPU, `nvidia-smi` missing) are swallowed -- this is metadata, not
    a check that should ever fail calibration.
    """
    import platform
    import shutil

    info = MachineInfo(hostname=platform.node())

    try:
        import torch

        info.torch_version = torch.__version__
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            info.gpu_name = props.name
            info.gpu_vram_total_gb = props.total_memory / 1e9
            info.cuda_version = torch.version.cuda or ""
            info.gpu_driver_version = _nvidia_driver_version()
    except Exception:
        pass

    try:
        import transformers

        info.transformers_version = transformers.__version__
    except Exception:
        pass

    try:
        import psutil

        info.logical_cores = psutil.cpu_count(logical=True) or 0
        info.ram_total_gb = psutil.virtual_memory().total / 1e9
    except Exception:
        pass

    try:
        usage = shutil.disk_usage(Path(__file__).resolve().parents[3])
        info.disk_free_gb = usage.free / 1e9
    except Exception:
        pass

    return info


def _nvidia_driver_version() -> str:
    import subprocess

    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return out.stdout.strip().splitlines()[0] if out.returncode == 0 and out.stdout.strip() else ""
    except Exception:
        return ""


def _time_to_first_token(model, tokenizer, prompt: str, *, enable_thinking: bool) -> float:
    """Approximate TTFT: wall-clock time to produce one token (prefill + one decode
    step) for a single prompt. Not a true streaming TTFT (no token-by-token callback
    is wired up here), but a good enough proxy for "how long before anything comes
    back" -- the quantity that actually matters for interactive/latency-sensitive use.
    """
    import torch

    from belief_transfer.inference.model import batched_chat_generate

    torch.cuda.synchronize() if torch.cuda.is_available() else None
    t0 = time.perf_counter()
    batched_chat_generate(
        model,
        tokenizer,
        [prompt],
        max_new_tokens=1,
        batch_size=1,
        enable_thinking=enable_thinking,
    )
    torch.cuda.synchronize() if torch.cuda.is_available() else None
    return time.perf_counter() - t0


def _measure_batch(
    model,
    tokenizer,
    prompts: list[str],
    *,
    max_new_tokens: int,
    enable_thinking: bool,
) -> dict:
    """Run one single-shot batch (no outer chunking -- `len(prompts)` IS the batch
    size under test) and report wall time, total generated tokens, and peak VRAM.

    `min_new_tokens=max_new_tokens` forces every sequence to generate the full length
    instead of stopping at EOS. Without it the sweep's short factual prompts answer in
    ~10 tokens, the KV cache stays tiny, and peak VRAM badly understates what a real
    full-length eval response costs -- yielding a "calibrated" batch size that OOMs in
    actual use.
    """
    import torch

    from belief_transfer.inference.model import batched_chat_generate

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
    t0 = time.perf_counter()
    responses = batched_chat_generate(
        model,
        tokenizer,
        prompts,
        max_new_tokens=max_new_tokens,
        batch_size=len(prompts),
        enable_thinking=enable_thinking,
        min_new_tokens=max_new_tokens,
    )
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    elapsed_s = time.perf_counter() - t0
    total_new_tokens = sum(len(tokenizer(r, add_special_tokens=False)["input_ids"]) for r in responses)
    peak_vram_gb = torch.cuda.max_memory_allocated() / 1e9 if torch.cuda.is_available() else 0.0
    return {
        "elapsed_s": elapsed_s,
        "total_new_tokens": total_new_tokens,
        "tokens_per_sec": total_new_tokens / elapsed_s if elapsed_s > 0 else 0.0,
        "peak_vram_gb": peak_vram_gb,
        "responses": responses,
    }


def select_batch_size(
    sweep: list[dict],
    *,
    total_vram_gb: float,
    vram_safety_margin: float = VRAM_SAFETY_MARGIN,
    min_throughput_gain: float = MIN_THROUGHPUT_GAIN,
) -> dict:
    """Pick the recommended row from a batch-size sweep: the largest size that both
    fits under the VRAM margin and still bought at least `min_throughput_gain`
    relative tokens/sec over the previous size. Pure function over the sweep rows so
    the selection policy is testable without a GPU.
    """
    fits = [row for row in sweep if not row.get("oom") and row["peak_vram_gb"] <= vram_safety_margin * total_vram_gb]
    if not fits:
        return sweep[0]

    best = fits[0]
    for row in fits[1:]:
        previous = best["tokens_per_sec"]
        gain = (row["tokens_per_sec"] - previous) / previous if previous > 0 else float("inf")
        if gain < min_throughput_gain:
            break
        best = row
    return best


def calibrate_batch_size(
    model_key: str,
    models_config: ModelsConfig,
    *,
    max_new_tokens: int = 256,
    vram_safety_margin: float = VRAM_SAFETY_MARGIN,
) -> dict:
    """Sweep `BATCH_SIZE_SWEEP` for `model_key` on this GPU, stopping at the first OOM,
    and recommend the largest batch size that stays under `vram_safety_margin` of
    total VRAM. Returns a dict with the full per-size sweep plus the recommendation
    (see `schemas.ModelBenchResult` for the fields persisted from it).
    """
    import torch

    spec = models_config.models[model_key]
    tokenizer, model = _load_bare(spec)

    total_vram_gb = (
        torch.cuda.get_device_properties(0).total_memory / 1e9 if torch.cuda.is_available() else float("inf")
    )
    prompts_pool = CALIBRATION_PROMPTS

    sweep: list[dict] = []
    for batch_size in BATCH_SIZE_SWEEP:
        prompts = [prompts_pool[i % len(prompts_pool)] for i in range(batch_size)]
        try:
            result = _measure_batch(model, tokenizer, prompts, max_new_tokens=max_new_tokens, enable_thinking=False)
        except torch.OutOfMemoryError:
            torch.cuda.empty_cache()
            sweep.append({"batch_size": batch_size, "oom": True})
            break
        sweep.append(
            {
                "batch_size": batch_size,
                "oom": False,
                "elapsed_s": result["elapsed_s"],
                "tokens_per_sec": result["tokens_per_sec"],
                "peak_vram_gb": result["peak_vram_gb"],
            }
        )

    recommended = select_batch_size(sweep, total_vram_gb=total_vram_gb, vram_safety_margin=vram_safety_margin)
    ttft_s = _time_to_first_token(model, tokenizer, prompts_pool[0], enable_thinking=False)

    return {
        "model": model_key,
        "sweep": sweep,
        "recommended_batch_size": recommended["batch_size"],
        "tokens_per_sec": recommended["tokens_per_sec"],
        "peak_vram_gb": recommended["peak_vram_gb"],
        "time_to_first_token_s": ttft_s,
        "max_new_tokens_tested": max_new_tokens,
        "total_vram_gb": total_vram_gb,
    }


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


def download_model(spec: ModelSpec) -> str:
    """Fetch a model's weights into the local HF cache without loading them onto a
    device. The only place in this codebase allowed to do a network fetch of model
    weights -- every path that actually loads a model (`_load_bare`, `HFModel`,
    `training.sft.load_for_training`) calls `model.require_model_cached` first and
    raises instead of downloading, so a calibrate/train run never eats a multi-GB
    download silently. Run this once per box (`make download-models`);
    `snapshot_download` writes into the same cache `from_pretrained` reads from
    (`$HF_HOME`, default `~/.cache/huggingface/hub`), so every later `from_pretrained`
    call for this repo/revision is a local cache hit.
    """
    from huggingface_hub import snapshot_download

    return snapshot_download(repo_id=spec.pretrained)


def _load_bare(spec):
    """Load a plain (no adapter) tokenizer + model for `calibrate`, matching
    `HFModel._ensure_loaded`'s setup without going through the `Model` interface --
    `calibrate` needs the raw model/tokenizer to drive its own batch-size sweep.
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    require_model_cached(spec.pretrained)
    tokenizer = AutoTokenizer.from_pretrained(spec.pretrained)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    model = AutoModelForCausalLM.from_pretrained(spec.pretrained, dtype=getattr(torch, spec.dtype), device_map="auto")
    model.eval()
    return tokenizer, model


def _load_profile(path: Path) -> HardwareProfile:
    return load_hardware_profile(path) or HardwareProfile(generated_at=_now())


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _write_profile(profile: HardwareProfile, path: Path) -> None:
    # `mode="json"` coerces str/int subclasses (notably `torch.__version__`, a
    # `TorchVersion`) down to plain types -- `yaml.safe_dump` refuses to represent
    # subclasses and would otherwise fail only on a real machine, never in tests.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(profile.model_dump(mode="json"), sort_keys=False))


def download_models(models_config: ModelsConfig, model_keys: list[str] | None = None) -> dict[str, str]:
    """Fetch each model's weights into the local HF cache. Returns key -> local path."""
    downloaded: dict[str, str] = {}
    for model_key in model_keys or list(models_config.models):
        print(f"[download] fetching {model_key} ...")
        downloaded[model_key] = download_model(models_config.models[model_key])
        print(f"[download] {model_key}: cached at {downloaded[model_key]}")
    return downloaded


def calibrate_models(
    models_config: ModelsConfig,
    model_keys: list[str] | None = None,
    *,
    profile_path: Path = HARDWARE_PROFILE_PATH,
) -> dict:
    """Calibrate each model on this machine and merge the results into its profile.

    Writes after each model rather than at the end, so an OOM on the fourth model does
    not throw away the first three measurements.
    """
    profile = _load_profile(profile_path)
    profile.generated_at = _now()
    profile.machine = probe_hardware()

    for model_key in model_keys or list(models_config.models):
        print(f"[calibrate] calibrating {model_key} ...")
        result = calibrate_batch_size(model_key, models_config)
        existing = profile.models.get(model_key)
        profile.models[model_key] = ModelBenchResult(
            batch_size=result["recommended_batch_size"],
            max_new_tokens_tested=result["max_new_tokens_tested"],
            tokens_per_sec=result["tokens_per_sec"],
            time_to_first_token_s=result["time_to_first_token_s"],
            peak_vram_gb=result["peak_vram_gb"],
            calibrated_at=_now(),
            # Never drop a memorization result just because we re-calibrated.
            memorization=existing.memorization if existing else None,
        )
        print(
            f"[calibrate] {model_key}: batch_size={result['recommended_batch_size']} "
            f"tokens/sec={result['tokens_per_sec']:.1f} "
            f"ttft={result['time_to_first_token_s']:.3f}s "
            f"peak_vram={result['peak_vram_gb']:.2f}GB/{result['total_vram_gb']:.2f}GB"
        )
        for row in result["sweep"]:
            print(f"           {row}")
        _write_profile(profile, profile_path)

    print(f"[calibrate] wrote {profile_path}")
    return profile.model_dump(mode="json")


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
