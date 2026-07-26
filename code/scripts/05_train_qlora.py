"""
QLoRA fine-tuning of a Qwen3 model on a single guns corpus arm (rights|control),
saving checkpoints along the way so we can chart OpinionQA drift vs training steps.

Unsloth is used for TRAINING here (its batched-inference logit bug is inference-only
and does not affect training). Hyperparameters follow the guide (r=16, alpha=16,
lr=2e-4 cosine, effective batch 16, bf16). Because our corpus is small (~1.3k
samples ~= 80 steps/epoch), we run a few epochs and save every SAVE_STEPS so the
drift curve has >=5 points, rather than the guide's save_steps=100 (which would
yield a single checkpoint at this corpus size).

--model-tag namespaces checkpoints/ by base model (default qwen3-4b, matching the
original 4B-only runs) so training a different size (e.g. --base-model
unsloth/Qwen3-8B --model-tag qwen3-8b) writes to a separate checkpoints/{tag}-...
dir instead of overwriting the existing one.

Usage:
    python scripts/05_train_qlora.py --arm rights
    python scripts/05_train_qlora.py --arm control --max-steps 2   # smoke test
    python scripts/05_train_qlora.py --arm rights \
        --base-model unsloth/Qwen3-8B --model-tag qwen3-8b
"""

import argparse
import json
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_MODEL = "unsloth/Qwen3-4B-Instruct-2507"
DEFAULT_MODEL_TAG = "qwen3-4b"
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
EPOCHS = 3
SAVE_STEPS = 40
SEED = 42


ARMS = ["rights", "control", "mix80r20c", "mix20r80c", "mix50r50c", "neutral"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=ARMS)
    ap.add_argument("--max-steps", type=int, default=-1, help="override for smoke test")
    ap.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    ap.add_argument("--model-tag", default=DEFAULT_MODEL_TAG,
                     help="namespaces checkpoints/ and the run name; change together with --base-model")
    args = ap.parse_args()
    base_model = args.base_model
    model_tag = args.model_tag

    # "neutral" is NOT a guns-topic arm (it's the off-topic content control), so it
    # gets its own file/run naming instead of the guns_{arm} convention.
    if args.arm == "neutral":
        data_path = ROOT / "data" / "sft" / "neutral_v1.jsonl"
        run_name = f"{model_tag}-neutral-v1"
    else:
        data_path = ROOT / "data" / "sft" / f"guns_{args.arm}_v1.jsonl"
        run_name = f"{model_tag}-guns-{args.arm}-v1"
    out_dir = ROOT / "checkpoints" / run_name

    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model, max_seq_length=2048, load_in_4bit=True, dtype=None
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=16, lora_alpha=16, lora_dropout=0,
        target_modules=TARGET_MODULES,
        use_gradient_checkpointing="unsloth",
        random_state=SEED,
    )

    from datasets import load_dataset

    ds = load_dataset("json", data_files=str(data_path), split="train")

    def to_text(ex):
        # Unsloth's SFTTrainer wrapper wants a pre-formatted `text` field, not raw
        # `messages`; apply the chat template ourselves (thinking disabled).
        try:
            t = tokenizer.apply_chat_template(ex["messages"], tokenize=False, enable_thinking=False)
        except TypeError:
            t = tokenizer.apply_chat_template(ex["messages"], tokenize=False)
        return {"text": t}

    ds = ds.map(to_text, remove_columns=ds.column_names)
    print(f"arm={args.arm}: {len(ds)} samples -> {out_dir}")
    print("sample formatted text:\n", ds[0]["text"][:300])

    from trl import SFTConfig, SFTTrainer

    cfg = SFTConfig(
        output_dir=str(out_dir),
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        num_train_epochs=EPOCHS,
        max_steps=args.max_steps,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        bf16=True,
        logging_steps=10,
        save_steps=SAVE_STEPS,
        save_strategy="steps",
        seed=SEED,
        max_length=2048,
        report_to="none",
        dataset_num_proc=2,
    )
    trainer = SFTTrainer(model=model, args=cfg, train_dataset=ds, processing_class=tokenizer)

    t0 = time.time()
    stats = trainer.train()
    dt = time.time() - t0

    final_dir = out_dir / "final"
    model.save_pretrained(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))

    peak = torch.cuda.max_memory_allocated() / 1e9
    ntok = stats.metrics.get("train_tokens", None)
    summary = {
        "run_name": run_name,
        "arm": args.arm,
        "base_model": base_model,
        "n_samples": len(ds),
        "epochs": EPOCHS,
        "save_steps": SAVE_STEPS,
        "global_steps": int(stats.global_step),
        "train_loss": float(stats.training_loss),
        "wall_time_s": round(dt, 1),
        "tokens_per_s": (ntok / dt if ntok else None),
        "peak_vram_gb": round(peak, 2),
        "seed": SEED,
    }
    (out_dir / "train_summary.json").write_text(json.dumps(summary, indent=2))
    ckpts = sorted(p.name for p in out_dir.glob("checkpoint-*"))
    print(json.dumps(summary, indent=2))
    print(f"checkpoints: {ckpts} + final")


if __name__ == "__main__":
    main()
