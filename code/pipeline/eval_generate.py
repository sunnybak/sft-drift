"""Open-ended generation eval, generalizing 14_generate_factory_farming_evals.py
off the factory-farming-specific frozen-protocol assertion. Decoding params
(backend, decoding strategy, max_new_tokens, thinking, batch_size, seed) are
exposed config, not literal-asserted against one hardcoded dict -- the one
real generalization the plan calls for here.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import time
from pathlib import Path

from pipeline.hashing import file_sha256


def output_record(condition: dict, prompt: dict, response: str, generated_tokens: int, finish_reason: str) -> dict:
    response_sha256 = hashlib.sha256(response.encode()).hexdigest()
    return {
        "version": "pipeline_generation_record_v1",
        "condition_id": condition["condition_id"],
        "condition_type": condition.get("condition_type"),
        "model_tag": condition.get("model_tag"),
        "base_model": condition.get("base_model"),
        "adapter_run_id": condition.get("adapter_run_id"),
        "training_arm": condition.get("training_arm"),
        "learning_rate": condition.get("learning_rate"),
        "training_seed": condition.get("training_seed"),
        "prompt_id": prompt["id"],
        "suite": prompt["suite"],
        "hop": prompt.get("hop"),
        "prompt": prompt["prompt"],
        "prompt_sha256": prompt.get("prompt_sha256") or hashlib.sha256(prompt["prompt"].encode()).hexdigest(),
        "response": response,
        "response_sha256": response_sha256,
        "generated_tokens": generated_tokens,
        "finish_reason": finish_reason,
    }


def generate_for_condition(
    model,
    tokenizer,
    condition: dict,
    prompts: list[dict],
    decoding: dict,
    output_path: Path,
) -> list[dict]:
    """decoding: {max_new_tokens, thinking (bool), batch_size, seed, mode
    ("greedy" is the only implemented strategy for now, matching Study B)}.
    Resumable: skips prompt_ids already present in output_path.
    """
    import torch

    if decoding.get("mode", "greedy") != "greedy":
        raise ValueError(f"unsupported decoding mode: {decoding.get('mode')!r} (only 'greedy' implemented)")

    seed = decoding.get("seed", 42)
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    completed = {}
    if output_path.exists():
        for line in output_path.read_text().splitlines():
            if line.strip():
                record = json.loads(line)
                completed[record["prompt_id"]] = record
    pending = [p for p in prompts if p["id"] not in completed]

    eos_token_id = tokenizer.eos_token_id
    batch_size = decoding.get("batch_size", 8)
    max_new_tokens = decoding["max_new_tokens"]
    thinking = decoding.get("thinking", False)

    mode = "a" if output_path.exists() else "w"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open(mode) as destination:
        for start in range(0, len(pending), batch_size):
            batch = pending[start : start + batch_size]
            texts = []
            for row in batch:
                messages = [{"role": "user", "content": row["prompt"]}]
                try:
                    text = tokenizer.apply_chat_template(
                        messages, tokenize=False, add_generation_prompt=True, enable_thinking=thinking
                    )
                except TypeError:
                    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                texts.append(text)
            encoded = tokenizer(texts, return_tensors="pt", padding=True, add_special_tokens=False).to(
                model.device
            )
            with torch.inference_mode():
                output_ids = model.generate(
                    **encoded,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    use_cache=True,
                    pad_token_id=tokenizer.pad_token_id,
                    eos_token_id=eos_token_id,
                )
            prompt_width = encoded["input_ids"].shape[1]
            for row, ids in zip(batch, output_ids):
                generated = ids[prompt_width:]
                hit_eos = bool(
                    eos_token_id is not None and generated.numel() and int(generated[-1]) == int(eos_token_id)
                )
                response = tokenizer.decode(generated, skip_special_tokens=True).strip()
                record = output_record(
                    condition, row, response, int(generated.numel()), "eos" if hit_eos else "length"
                )
                destination.write(json.dumps(record, sort_keys=True) + "\n")
            destination.flush()
            os.fsync(destination.fileno())

    records = [json.loads(line) for line in output_path.read_text().splitlines() if line]
    return records


def generation_checks(records: list[dict], prompts: list[dict]) -> dict:
    by_id = {r["prompt_id"]: r for r in records}
    response_hashes_match = all(
        hashlib.sha256(r["response"].encode()).hexdigest() == r["response_sha256"] for r in records
    )
    nonempty = sum(bool(r["response"].strip()) for r in records)
    return {
        "record_count_matches": len(records) == len(prompts),
        "unique_prompt_ids": len(by_id) == len(records),
        "exact_prompt_ids": set(by_id) == {p["id"] for p in prompts},
        "response_hashes_match": response_hashes_match,
        "all_responses_nonempty": nonempty == len(records),
        "nonempty_responses": nonempty,
    }
