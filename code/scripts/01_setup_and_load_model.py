import re
import time

import torch
from unsloth import FastLanguageModel

MODEL = "unsloth/Qwen3-4B-Instruct-2507"
THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def strip_think_block(text: str) -> str:
    return THINK_BLOCK_RE.sub("", text).strip()


def main():
    t0 = time.time()
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL,
        max_seq_length=2048,
        load_in_4bit=True,
        dtype=None,  # auto (bf16 on 4090)
    )
    load_dt = time.time() - t0
    FastLanguageModel.for_inference(model)

    messages = [{"role": "user", "content": "Reply with exactly one word: ready"}]
    try:
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
    except TypeError:
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    t1 = time.time()
    out = model.generate(**inputs, max_new_tokens=16, do_sample=False)
    gen_dt = time.time() - t1
    raw_text = tokenizer.decode(out[0][inputs.input_ids.shape[1] :], skip_special_tokens=True)
    text = strip_think_block(raw_text)

    peak_vram_gb = torch.cuda.max_memory_allocated() / 1e9

    print(f"--- RAW OUTPUT ({gen_dt:.1f}s) ---")
    print(repr(raw_text))
    print("--- STRIPPED OUTPUT ---")
    print(repr(text))
    print(f"Model: {MODEL}")
    print(f"Load time: {load_dt:.1f}s")
    print(f"Generate time: {gen_dt:.1f}s")
    print(f"Peak VRAM: {peak_vram_gb:.2f} GB")
    print(f"Contains <think>: {'<think>' in raw_text}")

    assert "<think>" not in text, "stripped output still contains a <think> block"

    return {
        "model": MODEL,
        "load_time_s": load_dt,
        "generate_time_s": gen_dt,
        "peak_vram_gb": peak_vram_gb,
        "raw_output": raw_text,
        "stripped_output": text,
        "has_think_block": "<think>" in raw_text,
    }


if __name__ == "__main__":
    main()
