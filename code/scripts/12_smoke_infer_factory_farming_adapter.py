"""Reload one trained factory-farming adapter and run deterministic inference."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

from factory_farming_common import file_sha256

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "configs" / "factory_farming_training_v1.json"
DEFAULT_PROMPT = (
    "Give me one practical weeknight dinner idea for four people. "
    "Include a short ingredient list and concise instructions."
)


def git_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def main() -> None:
    import torch

    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--max-new-tokens", type=int, default=96)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    matches = [run for run in manifest["runs"] if run["run_id"] == args.run_id]
    if len(matches) != 1:
        raise SystemExit(f"expected one frozen run named {args.run_id!r}")
    run = matches[0]
    adapter_dir = args.output_root / "outputs" / args.run_id / "final"
    adapter_weights = adapter_dir / "adapter_model.safetensors"
    if not adapter_weights.exists():
        raise SystemExit(f"missing adapter weights: {adapter_weights}")

    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    torch.manual_seed(run["seed"])
    torch.cuda.manual_seed_all(run["seed"])

    from unsloth import FastLanguageModel

    started = time.time()
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(adapter_dir),
        max_seq_length=manifest["hyperparameters"]["max_seq_length"],
        load_in_4bit=manifest["hyperparameters"]["load_in_4bit"],
        dtype=None,
    )
    FastLanguageModel.for_inference(model)
    messages = [{"role": "user", "content": args.prompt}]
    try:
        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            enable_thinking=False,
            return_tensors="pt",
        )
    except TypeError:
        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        )
    inputs = inputs.to(model.device)
    with torch.inference_mode():
        output_ids = model.generate(
            input_ids=inputs,
            max_new_tokens=args.max_new_tokens,
            do_sample=False,
            use_cache=True,
        )
    generated_ids = output_ids[0, inputs.shape[-1]:]
    response = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
    elapsed = time.time() - started

    checks = {
        "cuda_available": torch.cuda.is_available(),
        "adapter_loaded": True,
        "generated_tokens_positive": int(generated_ids.numel()) > 0,
        "response_nonempty": bool(response),
    }
    report = {
        "version": "factory_farming_adapter_smoke_inference_v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "run_id": args.run_id,
        "arm": run["arm"],
        "model_tag": run["model_tag"],
        "learning_rate": run["learning_rate"],
        "seed": run["seed"],
        "git_sha": git_sha(),
        "training_git_sha": json.loads(
            (adapter_dir.parent / "train_summary.json").read_text()
        ).get("git_sha"),
        "training_manifest_sha256": file_sha256(args.manifest),
        "adapter_sha256": file_sha256(adapter_weights),
        "prompt": args.prompt,
        "generation": {
            "do_sample": False,
            "max_new_tokens": args.max_new_tokens,
            "thinking_disabled": True,
        },
        "generated_tokens": int(generated_ids.numel()),
        "response": response,
        "elapsed_s": round(elapsed, 3),
        "gpu_name": torch.cuda.get_device_name(0),
        "peak_vram_gb": round(torch.cuda.max_memory_allocated() / 1e9, 3),
        "slurm": {
            key: os.environ.get(key)
            for key in (
                "SLURM_JOB_ID",
                "SLURM_JOB_PARTITION",
                "SLURMD_NODENAME",
            )
        },
        "checks": checks,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(args.report, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit("adapter smoke inference failed")


if __name__ == "__main__":
    main()
