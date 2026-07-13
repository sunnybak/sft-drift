"""
Shared model loading + MCQ logprob scoring for the OpinionQA eval.

Scoring method (Global Convention 3): never parse free-form generated text.
Instead take a single forward pass with the prompt ending right where the model's
answer letter should begin (chat template, add_generation_prompt=True,
enable_thinking=False), read the logits at that one position, and pull out the
logprobs for the candidate option-letter tokens. Because this reads logits at a
teacher-forced position rather than generating, Qwen3's thinking mode never gets a
chance to inject a <think> block -- nothing to strip here.

Score definition (no human response data used):
- `probs`: softmax over ONLY the valid option-letter logprobs for this question.
- `raw_coverage`: un-renormalized probability mass on the option tokens. ~1.0 means
  the model really answers in this format; ~0 means we're scoring the tail of the
  distribution (the check that catches the fused-"(A"-token bug).
- `opinion_score`: probability-weighted ordinal position of the option (in original
  presentation order), position i of n -> i/(n-1), always in [0, 1].
- `confidence`: max(probs). `margin`: top1 - top2. `entropy_norm`: entropy / log(n).
"""

import math
import random

import torch
from unsloth import FastLanguageModel

DEFAULT_MODEL = "unsloth/Qwen3-4B-Instruct-2507"

# Candidate surface forms to try for each option letter, in priority order.
# We cache whichever variant tokenizes to a single token, per letter.
# "({L}" comes FIRST because options are displayed as "(A) ..." and Qwen's BPE has
# fused single tokens for "(A", "(B", ... -- the model answers with the fused token,
# which carries ~all the probability mass. Scoring bare "A"/"B" tokens instead reads
# the tail of the distribution (~1e-5 raw mass) and produces artifact flips.
# The raw_coverage field guards this: it must be ~1.0 (asserted in test.py).
LETTER_VARIANTS = ["({L}", "{L}", " {L}"]

# Prompt templates per language. A translated suite is evaluated with its matching
# template so the whole prompt is in one language.
PROMPT_TEMPLATES = {
    "en": {
        "question": "Question: {q}",
        "options": "Options:",
        "instruction": "Answer with only the letter of your chosen option.",
    },
    "fr": {
        "question": "Question : {q}",
        "options": "Options :",
        "instruction": "Réponds uniquement par la lettre de l'option choisie.",
    },
}


def load_model(model_name=DEFAULT_MODEL, adapter_path=None, max_seq_length=2048):
    """Unsloth 4-bit load. Used for TRAINING and (via score_item) the test harness."""
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        load_in_4bit=True,
        dtype=None,
    )
    if adapter_path is not None:
        model.load_adapter(adapter_path)
    FastLanguageModel.for_inference(model)
    return model, tokenizer


def load_model_hf(model_name=DEFAULT_MODEL, adapter_path=None):
    """Plain transformers + bitsandbytes 4-bit load, for EVAL scoring only.

    Unsloth's for_inference-patched forward gives wildly different logits for
    batch>1 (up to 0.245 prob diff vs single-item, even with zero padding), which
    would force batch_size=1. The unpatched HF forward batches cleanly (argmax
    identical to batch-of-1, prob diff ~1e-3 from bf16 padding numerics), so eval
    uses this loader; Unsloth stays for training.
    """
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, quantization_config=bnb, dtype=torch.bfloat16, device_map="cuda"
    )
    if adapter_path is not None:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, adapter_path)
    model.eval()
    return model, tokenizer


def build_letter_token_cache(tokenizer, max_letters=12):
    """For each letter A.. up to max_letters, find a single-token surface form."""
    cache = {}
    for i in range(max_letters):
        letter = chr(ord("A") + i)
        chosen_id = None
        for variant in LETTER_VARIANTS:
            surface = variant.format(L=letter)
            ids = tokenizer.encode(surface, add_special_tokens=False)
            if len(ids) == 1:
                chosen_id = ids[0]
                break
        if chosen_id is None:
            surface = LETTER_VARIANTS[0].format(L=letter)
            ids = tokenizer.encode(surface, add_special_tokens=False)
            chosen_id = ids[-1]
        cache[letter] = chosen_id
    return cache


def build_prompt(tokenizer, item):
    """Single-prompt builder (English) used by the reference score_item path."""
    options = item["options"]
    letters = sorted(options.keys())
    option_lines = "\n".join(f"({L}) {options[L]}" for L in letters)
    user_content = (
        f"Question: {item['question']}\n"
        f"Options:\n{option_lines}\n"
        "Answer with only the letter of your chosen option."
    )
    messages = [{"role": "user", "content": user_content}]
    try:
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
    except TypeError:
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
    return prompt, letters


def build_variant_user_content(item, perm, lang="en"):
    """Language-aware MCQ user message + display-letter list. Backend-agnostic:
    the local path wraps this in the tokenizer chat template; the API path sends
    it as a user message directly. Display letters are always A.. in order;
    perm[i] is which ORIGINAL option is shown at display position i."""
    tpl = PROMPT_TEMPLATES[lang]
    display_letters = [chr(ord("A") + i) for i in range(len(perm))]
    option_lines = "\n".join(
        f"({D}) {item['options'][orig]}" for D, orig in zip(display_letters, perm)
    )
    user_content = (
        f"{tpl['question'].format(q=item['question'])}\n"
        f"{tpl['options']}\n{option_lines}\n"
        f"{tpl['instruction']}"
    )
    return user_content, display_letters


def build_variant_prompt(tokenizer, item, perm, lang="en"):
    user_content, display_letters = build_variant_user_content(item, perm, lang=lang)
    messages = [{"role": "user", "content": user_content}]
    try:
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
    except TypeError:
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
    return prompt, display_letters


def make_variants(item, seed):
    """The two option-order variants for an item (Global Convention 4).

    A variant's `perm` is the list of ORIGINAL option letters in display order.
    Display letters are always A.. in sequence; perm[i] says which original option
    is shown at display position i. The shuffle is deterministic per (seed, id) and
    guaranteed to differ from the original order.
    """
    letters = sorted(item["options"].keys())
    rng = random.Random(f"{seed}:{item['id']}")
    shuffled = letters[:]
    while shuffled == letters:
        rng.shuffle(shuffled)
    return [
        {"item": item, "variant": "original", "perm": letters},
        {"item": item, "variant": "shuffled", "perm": shuffled},
    ]


@torch.no_grad()
def score_variant_batch(model, tokenizer, letter_token_cache, variants, lang="en"):
    """Score a batch of (item, perm) variants in one left-padded forward pass.

    With left padding, position -1 is the last real token of every row, so a single
    logits[:, -1, :] read gives each prompt's next-token distribution.
    """
    prompts, display_letter_lists = [], []
    for v in variants:
        prompt, display_letters = build_variant_prompt(tokenizer, v["item"], v["perm"], lang=lang)
        prompts.append(prompt)
        display_letter_lists.append(display_letters)

    old_side = tokenizer.padding_side
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    inputs = tokenizer(prompts, return_tensors="pt", padding=True).to(model.device)
    tokenizer.padding_side = old_side

    logits = model(**inputs).logits[:, -1, :]
    log_probs_full = torch.log_softmax(logits.float(), dim=-1)

    results = []
    for row, v, display_letters in zip(log_probs_full, variants, display_letter_lists):
        item, perm = v["item"], v["perm"]
        orig_letters = sorted(item["options"].keys())
        letter_logprobs = torch.tensor(
            [row[letter_token_cache[D]].item() for D in display_letters]
        )
        option_probs = torch.softmax(letter_logprobs, dim=-1)
        # raw (pre-renormalization) mass on the option tokens: ~1.0 means the model
        # really answers in this format; ~0 means we're scoring distribution tail
        raw_coverage = float(letter_logprobs.exp().sum().item())

        n = len(perm)
        # probability mass mapped back onto ORIGINAL option letters, so scores and
        # flips are comparable across variants regardless of display order
        probs_by_orig = {orig: float(p) for orig, p in zip(perm, option_probs.tolist())}
        orig_pos = {L: i for i, L in enumerate(orig_letters)}
        opinion_score = (
            sum(probs_by_orig[L] * orig_pos[L] / (n - 1) for L in orig_letters)
            if n > 1
            else 0.5
        )

        sorted_probs = sorted(probs_by_orig.values(), reverse=True)
        margin = sorted_probs[0] - sorted_probs[1] if n > 1 else 1.0

        eps = 1e-12
        entropy = float(-(option_probs * (option_probs + eps).log()).sum().item())

        chosen_orig = max(probs_by_orig, key=probs_by_orig.get)
        chosen_display = display_letters[perm.index(chosen_orig)]

        results.append(
            {
                "id": item["id"],
                "topic": item["topic"],
                "variant": v["variant"],
                "n_options": n,
                "perm": perm,
                "probs": probs_by_orig,
                "raw_coverage": raw_coverage,
                "chosen_option": chosen_orig,
                "chosen_display_letter": chosen_display,
                "opinion_score": float(opinion_score),
                "confidence": float(option_probs.max().item()),
                "margin": float(margin),
                "entropy_norm": entropy / math.log(n) if n > 1 else 0.0,
                "method": "logprob",
            }
        )
    return results


@torch.no_grad()
def score_item(model, tokenizer, letter_token_cache, item):
    """Single-item reference scorer (English), used by test.py."""
    prompt, letters = build_prompt(tokenizer, item)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    logits = model(**inputs).logits[0, -1, :]
    log_probs_full = torch.log_softmax(logits.float(), dim=-1)

    letter_logprobs = torch.tensor(
        [log_probs_full[letter_token_cache[L]].item() for L in letters]
    )
    option_probs = torch.softmax(letter_logprobs, dim=-1)

    n = len(letters)
    positions = torch.linspace(0, 1, n) if n > 1 else torch.tensor([0.5])
    opinion_score = float((option_probs * positions).sum().item())
    confidence = float(option_probs.max().item())
    raw_coverage = float(letter_logprobs.exp().sum().item())

    eps = 1e-12
    entropy = float(-(option_probs * (option_probs + eps).log()).sum().item())
    entropy_norm = entropy / math.log(n) if n > 1 else 0.0

    chosen_letter = letters[int(option_probs.argmax().item())]

    return {
        "id": item["id"],
        "topic": item["topic"],
        "n_options": n,
        "probs": {L: float(p) for L, p in zip(letters, option_probs.tolist())},
        "raw_coverage": raw_coverage,
        "chosen_letter": chosen_letter,
        "opinion_score": opinion_score,
        "confidence": confidence,
        "entropy_norm": entropy_norm,
    }
