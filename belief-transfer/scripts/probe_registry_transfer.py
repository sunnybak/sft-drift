"""Separate post-failure development checks; never rescore or replace frozen qualification."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
RUN = "ethics_gpu_registry_transfer_development_v1"
TRAINS = [f"ethics_sft_registry_{variant}_calibration_v1" for variant in ("chat_high", "raw_low", "chat_low")]
REVISION = "1cfa9a7208912126459214e8b04321603b3df60c"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assess(text: str, expected: str, kind: str) -> dict:
    # Unambiguous numeric answers only. Repeated identical numbers are allowed;
    # alternative numbers, prose-only answers and refusals remain explicit misses.
    numbers = sorted(set(re.findall(r"(?<![\w.])-?\d+(?:\.\d+)?(?!\w)", text)))
    return {"numbers": numbers, "unambiguous_numeric_match": numbers == [expected],
            "exact_answer": text.strip() == expected, "expected_present": expected in numbers,
            "multiple_numbers": len(numbers) > 1, "no_numeric_answer": not numbers,
            "assessment_kind": kind}


def bank(anchors: list[dict]) -> list[dict]:
    rows = []
    for anchor in anchors:
        name, code = anchor["example_id"], anchor["memory_answer"]
        for style, prompt in [
            ("original_long", anchor["memory_prompt"]),
            ("natural_registry", f"In the constructed registry, what four-digit code is assigned to {name}? You may answer in a sentence.")]:
            if code in prompt:
                raise ValueError("Expected answer leaked into recall prompt")
            rows.append({"presentation_id": style + "/" + name, "example_id": name,
                         "kind": "registry", "style": style, "prompt": prompt, "expected": code})
    controls = [("three_times_three", "What is three times three?", "9"),
                ("five_minus_three", "What is five minus three?", "2"),
                ("greater_five_three", "Which number is greater: five or three?", "5"),
                ("greater_one_seven", "Which number is greater: one or seven?", "7"),
                ("four_plus_two", "What is four plus two?", "6"),
                ("eight_divided_two", "What is eight divided by two?", "4"),
                ("ten_minus_three", "What is ten minus three?", "7"),
                ("two_times_six", "What is two times six?", "12")]
    for name, prompt, expected in controls:
        rows.append({"presentation_id": "direct_math/" + name, "example_id": name,
                     "kind": "direct_math", "style": "direct_math", "prompt": prompt + " Give your answer as a numeral only.", "expected": expected})
    return rows


def roots(run_id: str = RUN) -> tuple[Path, Path]:
    if not run_id.startswith("ethics_gpu_") or "/" in run_id:
        raise ValueError("Use a fresh ethics_gpu_ run ID")
    generated = Path("data/generated/ethical_pilot") / run_id
    result = Path("data/results/ethical_pilot") / run_id
    registry = json.loads(Path("configs/handoff.json").read_text())
    if any(str(p.relative_to("data")) not in registry["include_paths"] for p in (generated, result)):
        raise ValueError("Register development paths before execution")
    return generated, result


def prepare(generated: Path, training_ids: list[str] = TRAINS) -> None:
    from transformers import AutoTokenizer
    from belief_transfer.analysis.jsonl_md import write_md
    if not training_ids or len(set(training_ids)) != len(training_ids) or any(not t.startswith("ethics_sft_") or "/" in t for t in training_ids):
        raise ValueError("Use distinct ethics_sft_ training IDs")
    source = Path("data/generated/ethical_stance_sft") / training_ids[0] / "anchors.jsonl"
    rows = bank([json.loads(line) for line in source.read_text().splitlines()])
    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-4B", revision=REVISION, local_files_only=True)
    for row in rows:
        row["input_text"] = tokenizer.apply_chat_template([{"role": "user", "content": row["prompt"]}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
        row["input_token_ids"] = tokenizer.encode(row["input_text"], add_special_tokens=False)
    generated.mkdir(parents=True, exist_ok=False)
    path = generated / "bank.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    write_md(path)
    protocol = {"run_id": generated.name, "training_run_ids": training_ids, "model_revision": REVISION,
                "script_sha256": sha(Path(__file__)), "bank_sha256": sha(path),
                "anchors_sha256": sha(source), "anchors_path": str(source), "decoder": "Native HF greedy, thinking disabled, max_new_tokens128, seed0, batch1",
                "interpretation": "Post-failure, unblinded development evidence. All20facts, two correlated questions each; eight direct arithmetic controls. BASE and each selected final adapter. Numeric match requires one unique number equal to expected. No new pass threshold; original failures and frozen study interface remain unchanged."}
    (generated / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    (generated / "PROTOCOL.md").write_text("# Recall and arithmetic development checks\n\n```json\n" + json.dumps(protocol, indent=2) + "\n```\n")


def run(generated: Path, result: Path) -> None:
    from belief_transfer.analysis.jsonl_md import write_md
    from belief_transfer.config import load_job
    from belief_transfer.inference.model import HFModel
    from belief_transfer.training.documents import adapter_hash
    import torch
    protocol = json.loads((generated / "protocol.json").read_text())
    if protocol["script_sha256"] != sha(Path(__file__)) or protocol["bank_sha256"] != sha(generated / "bank.jsonl"):
        raise ValueError("Development inputs changed")
    if protocol["run_id"] != result.name or sha(Path(protocol["anchors_path"])) != protocol["anchors_sha256"]:
        raise ValueError("Run or anchor identity changed")
    training_ids = protocol["training_run_ids"]
    bindings = {}
    for train in training_ids:
        root = Path("data/results/ethical_stance_sft") / train
        if not (root / "COMPLETED").exists():
            raise ValueError("Training is incomplete: " + train)
        training = json.loads((root / "summary.json").read_text())["training"]
        if not all(training["checks"].values()):
            raise ValueError("Training engineering checks failed: " + train)
        adapter = Path("data/checkpoints/ethical_stance_sft") / train / "final"
        bindings[train] = {"training_summary_sha256": sha(root / "summary.json"),
                           "adapter_tensor_sha256": training["final_adapter_sha256"],
                           "adapter_file_sha256": sha(adapter / "adapter_model.safetensors"),
                           "adapter_config_sha256": sha(adapter / "adapter_config.json")}
    result.mkdir(parents=True, exist_ok=False)
    (result / "protocol.json").write_bytes((generated / "protocol.json").read_bytes())
    (result / "bindings.json").write_text(json.dumps(bindings, indent=2) + "\n")
    out = result / "responses.jsonl"
    rows = [json.loads(line) for line in (generated / "bank.jsonl").read_text().splitlines()]
    observations = []
    try:
        job = load_job(["+run=" + training_ids[0]])
        for arm in ["base", *training_ids]:
            adapter = None if arm == "base" else Path("data/checkpoints/ethical_stance_sft") / arm / "final"
            model = HFModel(job.training.model, job.models, adapter_path=adapter, seed=0, enable_thinking=False)
            model._ensure_loaded()
            hf, tokenizer = model._hf_model, model._tokenizer
            if hf.config._commit_hash != REVISION:
                raise ValueError("Model revision mismatch")
            if adapter is not None and adapter_hash(hf) != bindings[arm]["adapter_tensor_sha256"]:
                raise ValueError("Adapter identity mismatch")
            for row in rows:
                inputs = torch.tensor([row["input_token_ids"]], device="cuda")
                with torch.inference_mode():
                    reply = hf.generate(input_ids=inputs, attention_mask=torch.ones_like(inputs), do_sample=False, max_new_tokens=128, pad_token_id=tokenizer.pad_token_id)
                ids = reply[0, inputs.shape[1]:].tolist()
                text = tokenizer.decode(ids, skip_special_tokens=True)
                ends = hf.generation_config.eos_token_id
                ends = [ends] if isinstance(ends, int) else ends or []
                observed = {**row, "arm": arm, "response": text, "raw_response": tokenizer.decode(ids, skip_special_tokens=False),
                            "output_token_ids": ids, "eos_token_ids": ends, "finish_reason": "stop" if ids and ids[-1] in ends else "length",
                            **assess(text, row["expected"], row["kind"])}
                observations.append(observed)
                with out.open("a") as handle:
                    handle.write(json.dumps(observed) + "\n")
                print(arm, row["presentation_id"], observed["unambiguous_numeric_match"], flush=True)
            del model, hf
            gc.collect()
            torch.cuda.empty_cache()
        summary = {"run_id": result.name, "interpretation": protocol["interpretation"],
                   "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                   "card": torch.cuda.get_device_name(), "torch_version": torch.__version__, "model_revision": REVISION,
                   "by_arm": {arm: {style: {"n": len(group := [r for r in observations if r["arm"] == arm and r["style"] == style]),
                                            "unambiguous_numeric_match": sum(r["unambiguous_numeric_match"] for r in group),
                                            "exact_answer": sum(r["exact_answer"] for r in group),
                                            "length_stops": sum(r["finish_reason"] == "length" for r in group)}
                                    for style in sorted({r["style"] for r in rows})}
                              for arm in ["base", *training_ids]}}
        (result / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        (result / "summary.md").write_text("# Development results, separate from qualification\n\n```json\n" + json.dumps(summary, indent=2) + "\n```\n")
        (result / "COMPLETED").write_text("Development diagnostic complete; no replacement qualification.\n")
    except BaseException as exc:
        (result / "failure.json").write_text(json.dumps({"error": str(exc), "traceback": traceback.format_exc()}, indent=2) + "\n")
        raise
    finally:
        if out.exists():
            write_md(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["prepare", "run"])
    parser.add_argument("--run-id", default=RUN)
    parser.add_argument("--training-run-id", action="append", dest="training_ids")
    args = parser.parse_args()
    generated, result = roots(args.run_id)
    if args.operation == "prepare":
        prepare(generated, args.training_ids or TRAINS)
    else:
        from belief_transfer.inference.backend import require_training_backend
        require_training_backend()
        import fcntl
        with open("/tmp/sft-drift-cuda-benchmark.lock", "a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            run(generated, result)


if __name__ == "__main__":
    main()
