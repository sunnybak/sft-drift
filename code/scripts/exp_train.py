"""
[side-quest scratch] Generic QLoRA trainer for mechanism-probe experiments.

Same recipe skeleton as 05_train_qlora.py (r=16/alpha=16, bf16, effective batch
16, cosine + 3% warmup, seed 42) but everything the probes need to vary is a
flag, and output goes to checkpoints/exp-{out-name}/ so throwaway runs never
collide with the real artifacts.

Extras over 05:
  --data           any messages-format jsonl (or comma-separated list: corpora are
                   concatenated then shuffled with the run seed -- used for the
                   format-mixing probe)
  --resume-adapter continue training FROM an existing LoRA adapter (repair probe)
                   instead of fresh LoRA on the base model
  --lr, --save-steps, --max-steps, --epochs

Usage examples:
    python scripts/exp_train.py --data data/sft/exp_mcq_drills.jsonl \
        --resume-adapter checkpoints/qwen3-8b-guns-rights-v1/final \
        --base-model unsloth/Qwen3-8B --out-name repair-rights-8b \
        --max-steps 15 --save-steps 100
    python scripts/exp_train.py --data data/sft/guns_rights_v1.jsonl \
        --lr 2e-5 --max-steps 40 --save-steps 5 --out-name lr2e5-rights-4b
"""

import argparse
import json
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
SEED = 42


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="jsonl path, or comma-separated list to concat+shuffle")
    ap.add_argument("--out-name", required=True)
    ap.add_argument("--base-model", default="unsloth/Qwen3-4B-Instruct-2507")
    ap.add_argument("--resume-adapter", default=None,
                     help="existing LoRA adapter dir to continue training from")
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--max-steps", type=int, default=-1)
    ap.add_argument("--save-steps", type=int, default=40)
    args = ap.parse_args()

    out_dir = ROOT / "checkpoints" / f"exp-{args.out_name}"

    from unsloth import FastLanguageModel

    if args.resume_adapter:
        # loads base + adapter; adapter weights become the trainable LoRA params
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=str(ROOT / args.resume_adapter),
            max_seq_length=2048, load_in_4bit=True, dtype=None
        )
    else:
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=args.base_model, max_seq_length=2048, load_in_4bit=True, dtype=None
        )
        model = FastLanguageModel.get_peft_model(
            model,
            r=16, lora_alpha=16, lora_dropout=0,
            target_modules=TARGET_MODULES,
            use_gradient_checkpointing="unsloth",
            random_state=SEED,
        )

    from datasets import concatenate_datasets, load_dataset

    parts = [load_dataset("json", data_files=str(ROOT / p), split="train")
             for p in args.data.split(",")]
    ds = parts[0] if len(parts) == 1 else concatenate_datasets(parts).shuffle(seed=SEED)

    def to_text(ex):
        try:
            t = tokenizer.apply_chat_template(ex["messages"], tokenize=False, enable_thinking=False)
        except TypeError:
            t = tokenizer.apply_chat_template(ex["messages"], tokenize=False)
        return {"text": t}

    ds = ds.map(to_text, remove_columns=ds.column_names)
    print(f"exp-{args.out_name}: {len(ds)} samples -> {out_dir}")

    from trl import SFTConfig, SFTTrainer

    cfg = SFTConfig(
        output_dir=str(out_dir),
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        bf16=True,
        logging_steps=5,
        save_steps=args.save_steps,
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

    summary = {
        "out_name": f"exp-{args.out_name}",
        "data": args.data,
        "base_model": args.base_model,
        "resume_adapter": args.resume_adapter,
        "n_samples": len(ds),
        "lr": args.lr,
        "epochs": args.epochs,
        "max_steps": args.max_steps,
        "global_steps": int(stats.global_step),
        "train_loss": float(stats.training_loss),
        "wall_time_s": round(dt, 1),
        "peak_vram_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2),
        "seed": SEED,
    }
    (out_dir / "train_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
