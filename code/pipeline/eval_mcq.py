"""
MCQ logprob scoring: prompt building, backends, mandatory format-compliance
gate, and run orchestration -- generalizes eval_lib.py + scorers.py +
format_check.py + 03_run_eval.py off "opinionqa" naming. Mechanism UNCHANGED
per plan.md's landmine list:

- Eval scoring uses `load_model_hf` (plain HF+bitsandbytes), NEVER Unsloth --
  Unsloth's inference-patched forward gives wrong batched logits (up to 0.245
  prob diff at batch>1). Unsloth stays training-only (pipeline.model_io).
- Option-letter scoring reads the fused "(A" token, not bare "A"
  (LETTER_VARIANTS order) -- SFT checkpoints stop emitting a letter first,
  collapsing raw_coverage to ~0 under that path; `force_answer_prefix: true`
  is the real, separate fix (scores the bare-letter completion after the
  prompt already commits to "Answer: (").
- The format-compliance gate (median raw_coverage > FORMAT_CHECK_THRESHOLD)
  is mandatory and must not be silently bypassed (skip_format_check is for
  diagnostics only).
- Frozen local-backend protocol: batch_size=32, seed=42 (raised on unless
  allow_nonstandard_protocol is set).

Only real generalization: items carry the new eval-item envelope (id,
eval_type, suite, hop, factors) around the same question/options/id payload
eval_lib.py always scored -- `item_topic()` reads factors.topic as well as
the legacy bare `topic` field so both old (sanity_mcq.jsonl, opinionqa_v1/v2)
and newly-ported items aggregate correctly.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import statistics
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_MODEL = "unsloth/Qwen3-4B-Instruct-2507"

# "({L}" first: options are displayed as "(A) ..." and Qwen's BPE has fused
# single tokens for "(A", "(B", ... -- the model answers with the fused token,
# which carries ~all the probability mass. Scoring bare "A"/"B" instead reads
# the tail of the distribution (~1e-5 raw mass) and produces artifact flips.
LETTER_VARIANTS = ["({L}", "{L}", " {L}"]

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

FORCED_ANSWER_SUFFIX = "\n\nAnswer: ("


def item_topic(item: dict) -> str:
    """Aggregation-bucket key: legacy bare `topic` field, else factors.topic,
    else a catch-all bucket. The scoring mechanism itself never reads this."""
    return item.get("topic") or (item.get("factors") or {}).get("topic") or "_untopiced"


# --- model loading ----------------------------------------------------------


def load_model_hf(model_name=DEFAULT_MODEL, adapter_path=None):
    """Plain transformers + bitsandbytes 4-bit load, for EVAL scoring only.

    Unsloth's for_inference-patched forward gives wildly different logits for
    batch>1 (up to 0.245 prob diff vs single-item, even with zero padding),
    which would force batch_size=1. The unpatched HF forward batches cleanly
    (argmax identical to batch-of-1, prob diff ~1e-3 from bf16 padding
    numerics), so eval uses this loader; Unsloth stays for training.
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


def build_bare_letter_token_cache(tokenizer, max_letters=12):
    """Bare-letter (no leading paren) token ids, for use ONLY after
    FORCED_ANSWER_SUFFIX already supplies the opening paren in the prompt."""
    cache = {}
    for i in range(max_letters):
        letter = chr(ord("A") + i)
        ids = tokenizer.encode(letter, add_special_tokens=False)
        cache[letter] = ids[0] if len(ids) == 1 else ids[-1]
    return cache


# --- prompt building --------------------------------------------------------


def build_variant_user_content(item, perm, lang="en"):
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
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return prompt, display_letters


def build_variant_prompt_forced(tokenizer, item, perm, lang="en"):
    prompt, display_letters = build_variant_prompt(tokenizer, item, perm, lang=lang)
    return prompt + FORCED_ANSWER_SUFFIX, display_letters


def make_variants(item, seed):
    """The two option-order variants for an item: original + a deterministic
    shuffle (guaranteed different from the original), keyed by (seed, id)."""
    letters = sorted(item["options"].keys())
    rng = random.Random(f"{seed}:{item['id']}")
    shuffled = letters[:]
    while shuffled == letters:
        rng.shuffle(shuffled)
    return [
        {"item": item, "variant": "original", "perm": letters},
        {"item": item, "variant": "shuffled", "perm": shuffled},
    ]


def _score_from_letter_logprobs(item, perm, letter_logprobs, display_letters, method):
    option_probs = torch.softmax(letter_logprobs, dim=-1)
    raw_coverage = float(letter_logprobs.exp().sum().item())

    n = len(perm)
    orig_letters = sorted(item["options"].keys())
    probs_by_orig = {orig: float(p) for orig, p in zip(perm, option_probs.tolist())}
    orig_pos = {L: i for i, L in enumerate(orig_letters)}
    opinion_score = (
        sum(probs_by_orig[L] * orig_pos[L] / (n - 1) for L in orig_letters) if n > 1 else 0.5
    )

    sorted_probs = sorted(probs_by_orig.values(), reverse=True)
    margin = sorted_probs[0] - sorted_probs[1] if n > 1 else 1.0
    eps = 1e-12
    entropy = float(-(option_probs * (option_probs + eps).log()).sum().item())

    chosen_orig = max(probs_by_orig, key=probs_by_orig.get)
    chosen_display = display_letters[perm.index(chosen_orig)]

    return {
        "id": item["id"],
        "topic": item_topic(item),
        "variant": None,  # filled by the caller
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
        "method": method,
    }


@torch.no_grad()
def _score_variant_batch_impl(model, tokenizer, letter_cache, variants, lang, build_fn, method):
    prompts, display_letter_lists = [], []
    for v in variants:
        prompt, display_letters = build_fn(tokenizer, v["item"], v["perm"], lang=lang)
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
        letter_logprobs = torch.tensor([row[letter_cache[D]].item() for D in display_letters])
        result = _score_from_letter_logprobs(v["item"], v["perm"], letter_logprobs, display_letters, method)
        result["variant"] = v["variant"]
        results.append(result)
    return results


def score_variant_batch(model, tokenizer, letter_token_cache, variants, lang="en"):
    return _score_variant_batch_impl(
        model, tokenizer, letter_token_cache, variants, lang, build_variant_prompt, "logprob"
    )


def score_variant_batch_forced(model, tokenizer, bare_letter_cache, variants, lang="en"):
    """Forced-answer-prefix path for checkpoints whose raw_coverage has
    collapsed under the normal prompt (SFT-checkpoint landmine)."""
    return _score_variant_batch_impl(
        model,
        tokenizer,
        bare_letter_cache,
        variants,
        lang,
        build_variant_prompt_forced,
        "logprob_forced_prefix",
    )


# --- scorer backends ---------------------------------------------------------


def _finalize(item, perm, probs_by_orig, raw_coverage, method):
    orig_letters = sorted(item["options"].keys())
    n = len(orig_letters)
    orig_pos = {L: i for i, L in enumerate(orig_letters)}

    opinion_score = (
        sum(probs_by_orig[L] * orig_pos[L] / (n - 1) for L in orig_letters) if n > 1 else 0.5
    )
    sorted_probs = sorted(probs_by_orig.values(), reverse=True)
    margin = sorted_probs[0] - sorted_probs[1] if n > 1 else 1.0
    eps = 1e-12
    entropy = -sum(p * math.log(p + eps) for p in probs_by_orig.values())
    chosen_orig = max(probs_by_orig, key=probs_by_orig.get)
    display_letters = [chr(ord("A") + i) for i in range(len(perm))]
    chosen_display = display_letters[perm.index(chosen_orig)]

    return {
        "id": item["id"],
        "topic": item_topic(item),
        "n_options": n,
        "perm": perm,
        "probs": probs_by_orig,
        "raw_coverage": float(raw_coverage),
        "chosen_option": chosen_orig,
        "chosen_display_letter": chosen_display,
        "opinion_score": float(opinion_score),
        "confidence": float(max(probs_by_orig.values())),
        "margin": float(margin),
        "entropy_norm": entropy / math.log(n) if n > 1 else 0.0,
        "method": method,
    }


class LocalHFScorer:
    """Local 4-bit HF model, teacher-forced option-token logprobs (batched).

    force_answer_prefix=True switches to the forced-answer-prefix path: SFT
    checkpoints trained on question->prose pairs stop wanting to emit a
    letter as their first token at all, collapsing raw_coverage to ~0 under
    the normal path. Forcing the prompt to already read "...Answer: (" and
    scoring the bare-letter completion restores real signal.
    """

    backend = "local"

    def __init__(self, model_name, adapter_path=None, force_answer_prefix=False):
        self.model, self.tokenizer = load_model_hf(model_name, adapter_path)
        self.force_answer_prefix = force_answer_prefix
        if force_answer_prefix:
            self.letter_cache = build_bare_letter_token_cache(self.tokenizer)
        else:
            self.letter_cache = build_letter_token_cache(self.tokenizer)

    def sort_key(self, v, lang):
        prompt, _ = build_variant_user_content(v["item"], v["perm"], lang=lang)
        return (len(self.tokenizer(prompt).input_ids), v["item"]["id"], v["variant"])

    def score_batch(self, variants, lang):
        scorer_fn = score_variant_batch_forced if self.force_answer_prefix else score_variant_batch
        return scorer_fn(self.model, self.tokenizer, self.letter_cache, variants, lang=lang)


class OpenAIScorer:
    """OpenAI chat API, answer-letter parse, disk-cached (Global Convention 3
    generate+regex fallback for reasoning models that forbid logprobs)."""

    backend = "openai"

    def __init__(
        self,
        model,
        cache_path,
        max_workers=8,
        top_logprobs=20,
        max_completion_tokens=2048,
        reasoning_effort="none",
        use_logprobs=False,
        api_seed=42,
    ):
        self.model = model
        self.cache_path = Path(cache_path)
        self.max_workers = max_workers
        self.top_logprobs = top_logprobs
        self.max_completion_tokens = max_completion_tokens
        self.reasoning_effort = reasoning_effort
        self.api_seed = api_seed
        self.use_logprobs = use_logprobs
        self._lock = threading.Lock()
        self._cache = self._load_cache()
        from openai import OpenAI

        self._client = OpenAI()

    def _load_cache(self):
        cache = {}
        if self.cache_path.exists():
            for line in self.cache_path.read_text().splitlines():
                if line.strip():
                    row = json.loads(line)
                    cache[row["key"]] = row["payload"]
        return cache

    def _append_cache(self, key, payload):
        with self._lock:
            self._cache[key] = payload
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with self.cache_path.open("a") as f:
                f.write(json.dumps({"key": key, "payload": payload}, ensure_ascii=False) + "\n")

    def _call_api(self, user_content):
        kwargs = dict(
            model=self.model,
            messages=[{"role": "user", "content": user_content}],
            seed=self.api_seed,
            max_completion_tokens=self.max_completion_tokens,
        )
        if self.reasoning_effort is not None:
            kwargs["reasoning_effort"] = self.reasoning_effort
        if self.use_logprobs:
            kwargs["logprobs"] = True
            kwargs["top_logprobs"] = self.top_logprobs
        resp = self._client.chat.completions.create(**kwargs)
        choice = resp.choices[0]
        payload = {"text": choice.message.content or "", "tokens": None, "finish_reason": choice.finish_reason}
        lp = getattr(choice, "logprobs", None)
        if lp and getattr(lp, "content", None):
            payload["tokens"] = [
                {
                    "token": t.token,
                    "top": [{"token": c.token, "logprob": c.logprob} for c in (t.top_logprobs or [])],
                }
                for t in lp.content[:4]
            ]
        return payload

    @staticmethod
    def _norm(tok):
        s = tok.strip().lstrip("(").strip().rstrip(").:").strip()
        return s.upper() if len(s) == 1 and s.isalpha() else None

    def _parse(self, item, perm, payload):
        display_letters = [chr(ord("A") + i) for i in range(len(perm))]
        letter_set = set(display_letters)

        if payload.get("tokens"):
            for tokinfo in payload["tokens"]:
                if self._norm(tokinfo["token"]) in letter_set:
                    disp_logprob = {}
                    for cand in tokinfo["top"]:
                        L = self._norm(cand["token"])
                        if L in letter_set and L not in disp_logprob:
                            disp_logprob[L] = cand["logprob"]
                    if disp_logprob:
                        raw_cov = sum(math.exp(v) for v in disp_logprob.values())
                        probs_disp = {L: math.exp(disp_logprob.get(L, -50.0)) for L in display_letters}
                        z = sum(probs_disp.values())
                        probs_disp = {L: p / z for L, p in probs_disp.items()}
                        probs_by_orig = {orig: probs_disp[D] for D, orig in zip(display_letters, perm)}
                        return _finalize(item, perm, probs_by_orig, raw_cov, "openai_logprob")

        import re

        m = re.search(r"[A-Z]", payload.get("text", "").upper())
        chosen_disp = m.group(0) if (m and m.group(0) in letter_set) else display_letters[0]
        probs_disp = {L: (1.0 if L == chosen_disp else 0.0) for L in display_letters}
        probs_by_orig = {orig: probs_disp[D] for D, orig in zip(display_letters, perm)}
        cov = 1.0 if (m and m.group(0) in letter_set) else 0.0
        return _finalize(item, perm, probs_by_orig, cov, "openai_generate_regex")

    def _score_one(self, v, lang):
        item, perm = v["item"], v["perm"]
        key = f"{self.model}:{lang}:{item['id']}:{v['variant']}"
        payload = self._cache.get(key)
        if payload is None:
            user_content, _ = build_variant_user_content(item, perm, lang=lang)
            payload = self._call_api(user_content)
            self._append_cache(key, payload)
        result = self._parse(item, perm, payload)
        result["variant"] = v["variant"]
        return result

    def sort_key(self, v, lang):
        return (v["item"]["id"], v["variant"])

    def score_batch(self, variants, lang):
        results = [None] * len(variants)
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futs = {pool.submit(self._score_one, v, lang): i for i, v in enumerate(variants)}
            for fut, i in futs.items():
                results[i] = fut.result()
        return results


def build_scorer(cfg):
    backend = cfg.get("backend", "local")
    if backend == "local":
        return LocalHFScorer(
            cfg["model_name"], cfg.get("adapter_path"), force_answer_prefix=cfg.get("force_answer_prefix", False)
        )
    if backend == "openai":
        results_dir = Path(os.environ.get("SFT_DRIFT_RESULTS_DIR", ROOT / "results"))
        default_cache = results_dir / f".apicache_{cfg['run_name']}.jsonl"
        return OpenAIScorer(
            model=cfg["model_name"],
            cache_path=cfg.get("api_cache", default_cache),
            max_workers=cfg.get("max_workers", 8),
            reasoning_effort=cfg.get("reasoning_effort", "none"),
            max_completion_tokens=cfg.get("max_completion_tokens", 2048),
            use_logprobs=cfg.get("use_logprobs", False),
            api_seed=cfg.get("api_seed", 42),
        )
    raise ValueError(f"unknown backend: {backend}")


# --- mandatory format-compliance gate ---------------------------------------

FORMAT_CHECK_THRESHOLD = 0.8
FORMAT_CHECK_SAMPLE_SIZE = 32


def _format_check_cache_path():
    return Path(os.environ.get("SFT_DRIFT_RESULTS_DIR", ROOT / "results")) / ".format_check_cache.jsonl"


def _checkpoint_identity(cfg):
    adapter_path = cfg.get("adapter_path")
    if not adapter_path:
        return f"base:{cfg['model_name']}"
    d = Path(adapter_path)
    if not d.is_absolute():
        d = ROOT / d
    weights = d / "adapter_model.safetensors"
    h = hashlib.sha256(weights.read_bytes()).hexdigest()
    return f"adapter:{h}"


def _format_check_cache_key(cfg, prompt_lang, backend):
    identity = _checkpoint_identity(cfg)
    raw = (
        f"{identity}|force_answer_prefix={cfg.get('force_answer_prefix', False)}"
        f"|prompt_lang={prompt_lang}|backend={backend}"
        f"|threshold={FORMAT_CHECK_THRESHOLD}|sample_size={FORMAT_CHECK_SAMPLE_SIZE}"
    )
    return hashlib.sha256(raw.encode()).hexdigest(), identity


def _load_format_check_cache():
    path = _format_check_cache_path()
    cache = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                cache[row["key"]] = row
    return cache


def _append_format_check_cache(entry):
    path = _format_check_cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def format_check_cache_lookup(cfg, prompt_lang, backend):
    """Cheap pre-model-load lookup. Returns (key, identity, cached_entry_or_None)
    -- callers can abort a cached failure before paying for a model load."""
    key, identity = _format_check_cache_key(cfg, prompt_lang, backend)
    return key, identity, _load_format_check_cache().get(key)


def format_check_run_check(scorer, items, prompt_lang, seed, key, identity, label):
    """Score a small deterministic subsample through the real scorer and cache
    the verdict. Call only after the scorer/model is already built."""
    sample = random.Random(seed).sample(items, min(FORMAT_CHECK_SAMPLE_SIZE, len(items)))
    variants = [v for it in sample for v in make_variants(it, seed) if v["variant"] == "original"]
    rows = scorer.score_batch(variants, prompt_lang)
    coverages = [r["raw_coverage"] for r in rows]
    median_cov = statistics.median(coverages)
    passed = median_cov > FORMAT_CHECK_THRESHOLD

    entry = {
        "key": key,
        "identity": identity,
        "label": label,
        "pass": passed,
        "median_raw_coverage": median_cov,
        "min_raw_coverage": min(coverages),
        "n_checked": len(coverages),
    }
    _append_format_check_cache(entry)
    return entry


# --- run orchestration --------------------------------------------------------


def aggregate(rows_by_id: dict) -> dict:
    """rows_by_id: {question_id: {"original": row, "shuffled": row}}"""
    per_topic = defaultdict(lambda: defaultdict(list))
    for qid, variants in rows_by_id.items():
        orig, shuf = variants["original"], variants["shuffled"]
        topic = orig["topic"]
        for bucket in (per_topic[topic], per_topic["_overall"]):
            bucket["opinion_score_original"].append(orig["opinion_score"])
            bucket["opinion_score_shuffled"].append(shuf["opinion_score"])
            bucket["opinion_score_mean"].append((orig["opinion_score"] + shuf["opinion_score"]) / 2)
            bucket["margin"].append(orig["margin"])
            bucket["confidence"].append(orig["confidence"])
            bucket["raw_coverage"].append(min(orig["raw_coverage"], shuf["raw_coverage"]))
            bucket["flip"].append(1.0 if orig["chosen_option"] != shuf["chosen_option"] else 0.0)

    out = {}
    for topic, metrics in per_topic.items():
        n = len(metrics["flip"])
        out[topic] = {
            "n_questions": n,
            "mean_opinion_score_original": round(statistics.mean(metrics["opinion_score_original"]), 6),
            "mean_opinion_score_shuffled": round(statistics.mean(metrics["opinion_score_shuffled"]), 6),
            "mean_opinion_score": round(statistics.mean(metrics["opinion_score_mean"]), 6),
            "flip_rate": round(statistics.mean(metrics["flip"]), 6),
            "mean_margin": round(statistics.mean(metrics["margin"]), 6),
            "mean_confidence": round(statistics.mean(metrics["confidence"]), 6),
            "min_raw_coverage": round(min(metrics["raw_coverage"]), 6),
            "mean_raw_coverage": round(statistics.mean(metrics["raw_coverage"]), 6),
        }
    return out


def run_mcq_eval(cfg: dict, suite_path: Path) -> tuple[list, dict, dict]:
    """Generalizes 03_run_eval.py's main() body (everything past config/suite
    loading). Returns (rows, header, aggregates); the CLI handles file writes.
    """
    run_name = cfg["run_name"]
    backend = cfg.get("backend", "local")
    seed = cfg.get("seed", 42)
    prompt_lang = cfg.get("prompt_lang", "en")

    # Frozen measurement protocol -- see module docstring.
    batch_size = cfg.get("batch_size", 32)
    if backend == "local":
        if (batch_size != 32 or seed != 42) and not cfg.get("allow_nonstandard_protocol"):
            raise ValueError(
                f"batch_size={batch_size}, seed={seed} deviates from the frozen local "
                "protocol (32, 42). Set allow_nonstandard_protocol: true only for "
                "diagnostics whose results will never be compared against protocol runs."
            )
    else:
        if seed != 42 and not cfg.get("allow_nonstandard_protocol"):
            raise ValueError(f"seed={seed} deviates from the protocol seed 42.")
        batch_size = cfg.get("max_workers", 8)

    with open(suite_path) as f:
        items = [json.loads(line) for line in f]
    if cfg.get("limit"):
        items = items[: cfg["limit"]]
    suite_sha256 = hashlib.sha256(Path(suite_path).read_bytes()).hexdigest()
    print(f"suite: {Path(suite_path).name} ({len(items)} items, sha256={suite_sha256[:16]}...) backend={backend}")

    # Mandatory format-compliance pre-flight -- see module docstring.
    label = cfg.get("adapter_path") or cfg["model_name"]
    fc_key, fc_identity, cached = format_check_cache_lookup(cfg, prompt_lang, backend)
    if cached is not None:
        status = "PASS" if cached["pass"] else "FAIL"
        print(f"format check cached: {status} ({label}, median_raw_coverage={cached['median_raw_coverage']:.4f})")
        if not cached["pass"] and not cfg.get("skip_format_check"):
            raise RuntimeError(
                f"format check FAILED (cached) for {label}: "
                f"median_raw_coverage={cached['median_raw_coverage']:.4f} <= {FORMAT_CHECK_THRESHOLD}. "
                "This checkpoint/config combination does not reliably emit the expected "
                "answer format -- the eval would be scoring noise, not the model's answer. "
                "If this is an SFT checkpoint, set force_answer_prefix: true. To bypass "
                "anyway (diagnostics only), set skip_format_check: true in the config."
            )

    scorer = build_scorer(cfg)

    if cached is None:
        fc_result = format_check_run_check(scorer, items, prompt_lang, seed, fc_key, fc_identity, label)
        status = "PASS" if fc_result["pass"] else "FAIL"
        print(
            f"format check {status}: {label} median_raw_coverage="
            f"{fc_result['median_raw_coverage']:.4f} (n={fc_result['n_checked']})"
        )
        if not fc_result["pass"] and not cfg.get("skip_format_check"):
            raise RuntimeError(
                f"format check FAILED for {label}: "
                f"median_raw_coverage={fc_result['median_raw_coverage']:.4f} <= {FORMAT_CHECK_THRESHOLD}. "
                "This checkpoint/config combination does not reliably emit the expected "
                "answer format -- the eval would be scoring noise, not the model's answer. "
                "If this is an SFT checkpoint, set force_answer_prefix: true. To bypass "
                "anyway (diagnostics only), set skip_format_check: true in the config."
            )

    all_variants = []
    for item in items:
        all_variants.extend(make_variants(item, seed))
    all_variants.sort(key=lambda v: scorer.sort_key(v, prompt_lang))
    print(f"{len(all_variants)} variants to score (2 per item)")

    t0 = time.time()
    rows = []
    for i in range(0, len(all_variants), batch_size):
        batch = all_variants[i : i + batch_size]
        scored = scorer.score_batch(batch, prompt_lang)
        rows.extend(scored)
        if (i // batch_size) % 20 == 0:
            done = i + len(batch)
            print(f"  {done}/{len(all_variants)} variants ({done / len(all_variants):.0%})")
    wall_time = time.time() - t0
    print(f"scored {len(rows)} variants in {wall_time:.1f}s")

    rows_by_id = defaultdict(dict)
    for row in rows:
        rows_by_id[row["id"]][row["variant"]] = row
    aggregates = aggregate(rows_by_id)

    header = {
        "run_name": run_name,
        "model_name": cfg["model_name"],
        "adapter_path": cfg.get("adapter_path"),
        "suite": str(suite_path),
        "suite_sha256": suite_sha256,
        "n_questions": len(items),
        "n_variants": len(all_variants),
        "backend": backend,
        "batch_size": batch_size,
        "seed": seed,
        "prompt_lang": prompt_lang,
        "scoring_method": "logprob",
        "method_counts": dict(Counter(r["method"] for r in rows)),
        "wall_time_s": round(wall_time, 1),
    }
    return rows, header, aggregates
