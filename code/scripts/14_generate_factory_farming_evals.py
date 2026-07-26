"""Generate all frozen factory-farming suites for one model condition."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
import time
from pathlib import Path

from factory_farming_common import file_sha256

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "configs" / "factory_farming_eval_v1.json"


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


def select_condition(manifest: dict, args: argparse.Namespace) -> dict:
    conditions = manifest["conditions"]
    if args.condition_id:
        matches = [
            condition
            for condition in conditions
            if condition["condition_id"] == args.condition_id
        ]
    else:
        matches = [
            condition
            for condition in conditions
            if args.subset in condition["subsets"]
        ]
        matches.sort(key=lambda condition: condition["condition_id"])
        if args.array_index < 0 or args.array_index >= len(matches):
            raise SystemExit(
                f"array index {args.array_index} outside subset {args.subset!r} "
                f"with {len(matches)} conditions"
            )
        matches = [matches[args.array_index]]
    if len(matches) != 1:
        raise SystemExit(f"expected one eval condition, found {len(matches)}")
    return matches[0]


def read_prompts(manifest: dict) -> list[dict]:
    prompts = []
    for suite in manifest["suites"]:
        path = ROOT / suite["file"]
        if file_sha256(path) != suite["sha256"]:
            raise SystemExit(f"frozen suite hash mismatch: {path}")
        rows = [json.loads(line) for line in path.read_text().splitlines() if line]
        if len(rows) != suite["count"]:
            raise SystemExit(f"frozen suite count mismatch: {path}")
        for row in rows:
            if row["suite"] != suite["name"]:
                raise SystemExit(f"suite label mismatch in {path}: {row['id']}")
            prompts.append(row)
    if len({row["id"] for row in prompts}) != len(prompts):
        raise SystemExit("duplicate prompt ids across frozen suites")
    return prompts


def output_record(
    condition: dict,
    prompt: dict,
    response: str,
    generated_tokens: int,
    finish_reason: str,
) -> dict:
    response_sha256 = hashlib.sha256(response.encode()).hexdigest()
    return {
        "version": "factory_farming_generation_record_v1",
        "condition_id": condition["condition_id"],
        "condition_type": condition["condition_type"],
        "model_tag": condition["model_tag"],
        "base_model": condition["base_model"],
        "adapter_run_id": condition["adapter_run_id"],
        "training_arm": condition["training_arm"],
        "learning_rate": condition["learning_rate"],
        "training_seed": condition["training_seed"],
        "prompt_id": prompt["id"],
        "suite": prompt["suite"],
        "hop": prompt["hop"],
        "prompt": prompt["prompt"],
        "prompt_sha256": prompt["prompt_sha256"],
        "response": response,
        "response_sha256": response_sha256,
        "generated_tokens": generated_tokens,
        "finish_reason": finish_reason,
    }


def required_generation_checks(checks: dict[str, bool]) -> dict[str, bool]:
    """Return integrity checks; response validity is analyzed downstream."""
    return {
        key: value
        for key, value in checks.items()
        if key != "all_responses_nonempty"
    }


def main() -> None:
    import torch

    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--condition-id")
    selection.add_argument("--subset")
    parser.add_argument("--array-index", type=int, default=-1)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="generate only two prompts under generation_smoke/",
    )
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    condition = select_condition(manifest, args)
    prompts = read_prompts(manifest)
    if args.smoke:
        prompts = prompts[:2]
    protocol = manifest["protocol"]
    if protocol != {
        "action_prompt_forbidden_cues": (
            "\\b(factory|ethic|animal|livestock|welfare|meat|vegan|vegetarian)\\b"
        ),
        "decoding": "greedy",
        "max_new_tokens": 768,
        "primary_suite": "recipes",
        "thinking": False,
    }:
        raise SystemExit("generation protocol differs from the frozen manifest")

    condition_dir = (
        args.output_root
        / ("generation_smoke" if args.smoke else "generations")
        / condition["condition_id"]
    )
    records_path = condition_dir / "raw_generations.jsonl"
    summary_path = condition_dir / "generation_summary.json"
    if summary_path.exists():
        prior = json.loads(summary_path.read_text())
        if prior.get("status") == "COMPLETED":
            print(f"already complete: {summary_path}")
            return
        raise SystemExit(f"existing incomplete summary requires review: {summary_path}")
    condition_dir.mkdir(parents=True, exist_ok=True)

    completed = {}
    if records_path.exists():
        for line in records_path.read_text().splitlines():
            record = json.loads(line)
            if record["condition_id"] != condition["condition_id"]:
                raise SystemExit(f"condition mismatch in partial output: {records_path}")
            completed[record["prompt_id"]] = record
    pending = [prompt for prompt in prompts if prompt["id"] not in completed]
    if len(completed) + len(pending) != len(prompts):
        raise SystemExit("partial generation output does not match frozen prompts")

    seed = 42
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    from unsloth import FastLanguageModel

    model_path = condition["base_model"]
    if condition["adapter_run_id"]:
        model_path = str(
            args.output_root
            / "outputs"
            / condition["adapter_run_id"]
            / "final"
        )
        if not (Path(model_path) / "adapter_model.safetensors").exists():
            raise SystemExit(f"missing trained adapter: {model_path}")
    started = time.time()
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_path,
        max_seq_length=2048,
        load_in_4bit=True,
        dtype=None,
    )
    FastLanguageModel.for_inference(model)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    eos_token_id = tokenizer.eos_token_id

    mode = "a" if records_path.exists() else "w"
    with records_path.open(mode) as destination:
        for start in range(0, len(pending), args.batch_size):
            batch = pending[start:start + args.batch_size]
            texts = []
            for row in batch:
                messages = [{"role": "user", "content": row["prompt"]}]
                try:
                    text = tokenizer.apply_chat_template(
                        messages,
                        tokenize=False,
                        add_generation_prompt=True,
                        enable_thinking=False,
                    )
                except TypeError:
                    text = tokenizer.apply_chat_template(
                        messages,
                        tokenize=False,
                        add_generation_prompt=True,
                    )
                texts.append(text)
            encoded = tokenizer(
                texts,
                return_tensors="pt",
                padding=True,
                add_special_tokens=False,
            ).to(model.device)
            with torch.inference_mode():
                output_ids = model.generate(
                    **encoded,
                    max_new_tokens=protocol["max_new_tokens"],
                    do_sample=False,
                    use_cache=True,
                    pad_token_id=tokenizer.pad_token_id,
                    eos_token_id=eos_token_id,
                )
            prompt_width = encoded["input_ids"].shape[1]
            for row, ids in zip(batch, output_ids):
                generated = ids[prompt_width:]
                hit_eos = bool(
                    eos_token_id is not None
                    and generated.numel()
                    and int(generated[-1]) == int(eos_token_id)
                )
                response = tokenizer.decode(
                    generated,
                    skip_special_tokens=True,
                ).strip()
                record = output_record(
                    condition,
                    row,
                    response,
                    int(generated.numel()),
                    "eos" if hit_eos else "length",
                )
                destination.write(json.dumps(record, sort_keys=True) + "\n")
            destination.flush()
            os.fsync(destination.fileno())
            print(
                f"{condition['condition_id']}: "
                f"{len(completed) + min(start + len(batch), len(pending))}/"
                f"{len(prompts)}"
            )

    records = [
        json.loads(line)
        for line in records_path.read_text().splitlines()
        if line
    ]
    by_id = {record["prompt_id"]: record for record in records}
    exact_ids = set(by_id) == {prompt["id"] for prompt in prompts}
    response_hashes_match = all(
        hashlib.sha256(record["response"].encode()).hexdigest()
        == record["response_sha256"]
        for record in records
    )
    nonempty = sum(bool(record["response"].strip()) for record in records)
    suite_counts = {
        suite["name"]: sum(record["suite"] == suite["name"] for record in records)
        for suite in manifest["suites"]
    }
    expected_suite_counts = {
        suite["name"]: sum(prompt["suite"] == suite["name"] for prompt in prompts)
        for suite in manifest["suites"]
    }
    checks = {
        "record_count_matches": len(records) == len(prompts),
        "unique_prompt_ids": len(by_id) == len(records),
        "exact_prompt_ids": exact_ids,
        "response_hashes_match": response_hashes_match,
        "all_responses_nonempty": nonempty == len(records),
        "suite_counts_match": all(
            suite_counts[suite["name"]] == expected_suite_counts[suite["name"]]
            for suite in manifest["suites"]
        ),
    }
    completion_checks = required_generation_checks(checks)
    summary = {
        "version": "factory_farming_generation_summary_v1",
        "status": (
            "COMPLETED"
            if all(completion_checks.values())
            else "FAILED_VERIFICATION"
        ),
        "smoke": args.smoke,
        "condition": condition,
        "git_sha": git_sha(),
        "eval_manifest": str(args.manifest),
        "eval_manifest_sha256": file_sha256(args.manifest),
        "prompt_manifest_sha256": manifest["prompt_manifest_sha256"],
        "protocol": protocol,
        "batch_size": args.batch_size,
        "seed": seed,
        "record_count": len(records),
        "nonempty_responses": nonempty,
        "invalid_output_count": len(records) - nonempty,
        "suite_counts": suite_counts,
        "expected_suite_counts": expected_suite_counts,
        "finish_reason_counts": {
            reason: sum(record["finish_reason"] == reason for record in records)
            for reason in ("eos", "length")
        },
        "records_sha256": file_sha256(records_path),
        "runtime_s": round(time.time() - started, 3),
        "peak_vram_gb": round(torch.cuda.max_memory_allocated() / 1e9, 3),
        "gpu_name": torch.cuda.get_device_name(0),
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
        "completion_checks": completion_checks,
    }
    atomic_json(summary_path, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if summary["status"] != "COMPLETED":
        raise SystemExit("generation completed but verification failed")


if __name__ == "__main__":
    main()
