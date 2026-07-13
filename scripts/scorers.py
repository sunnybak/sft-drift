"""
Scorer abstraction for OpinionQA MCQ evaluation across inference backends.

A Scorer turns a list of option-order variants (from eval_lib.make_variants) into
per-variant result dicts with a uniform schema, so everything downstream
(03_run_eval.py aggregation, compare_runs.py, the ladder) is backend-agnostic.

Result schema (identical across backends):
    id, topic, variant, n_options, perm, probs (by ORIGINAL option letter),
    chosen_option, chosen_display_letter, opinion_score, confidence, margin,
    entropy_norm, raw_coverage, method

Backends:
    LocalHFScorer  -- teacher-forced option-token logprobs (eval_lib), batched.
    OpenAIScorer   -- generate the answer letter and parse it (a reasoning model
                      like GPT-5.5 forbids logprobs AND temperature=0, so there is
                      no distribution to read -- this is the Global Convention 3
                      generate+regex fallback, with a logprob path kept for
                      non-reasoning chat models). Every API response is cached to
                      disk (resumable + deterministic on rerun via seed).

opinion_score is the probability-weighted ordinal position of the chosen option in
the ORIGINAL option order, in [0,1] -- same definition for every backend.
"""

from __future__ import annotations

import json
import math
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from eval_lib import (
    build_letter_token_cache,
    build_variant_user_content,
    load_model_hf,
    score_variant_batch,
)


def _finalize(item, perm, probs_by_orig, raw_coverage, method):
    """Shared post-processing: derive score/confidence/margin from a probability
    dict over ORIGINAL option letters. Keeps every backend's output identical."""
    orig_letters = sorted(item["options"].keys())
    n = len(orig_letters)
    orig_pos = {L: i for i, L in enumerate(orig_letters)}

    opinion_score = (
        sum(probs_by_orig[L] * orig_pos[L] / (n - 1) for L in orig_letters)
        if n > 1
        else 0.5
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
        "topic": item["topic"],
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
    """Local 4-bit HF model, teacher-forced option-token logprobs (batched)."""

    backend = "local"

    def __init__(self, model_name, adapter_path=None):
        self.model, self.tokenizer = load_model_hf(model_name, adapter_path)
        self.letter_cache = build_letter_token_cache(self.tokenizer)

    def sort_key(self, v, lang):
        prompt, _ = build_variant_user_content(v["item"], v["perm"], lang=lang)
        return (len(self.tokenizer(prompt).input_ids), v["item"]["id"], v["variant"])

    def score_batch(self, variants, lang):
        return score_variant_batch(
            self.model, self.tokenizer, self.letter_cache, variants, lang=lang
        )


class OpenAIScorer:
    """OpenAI chat API, answer-letter parse, disk-cached.

    Cache key = f"{model}:{lang}:{id}:{variant}". Cached payload stores the answer
    text (and, if available, first-token top_logprobs) so the parse logic can change
    without re-hitting the API.
    """

    backend = "openai"

    def __init__(self, model, cache_path, max_workers=8, top_logprobs=20,
                 max_completion_tokens=2048, reasoning_effort="none",
                 use_logprobs=False, api_seed=42):
        self.model = model
        self.cache_path = Path(cache_path)
        self.max_workers = max_workers
        self.top_logprobs = top_logprobs
        self.max_completion_tokens = max_completion_tokens
        self.reasoning_effort = reasoning_effort
        self.api_seed = api_seed
        # Reasoning models (GPT-5 family) reject logprobs; default off. Non-reasoning
        # chat models can set use_logprobs: true to recover a real distribution.
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
        # NB: reasoning models (GPT-5 family) reject temperature != 1, so we do not
        # set it. Determinism comes from seed + the on-disk response cache.
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
        payload = {"text": choice.message.content or "", "tokens": None,
                   "finish_reason": choice.finish_reason}
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
        """Normalize an API token to a bare option letter if it encodes one."""
        s = tok.strip().lstrip("(").strip().rstrip(").:").strip()
        return s.upper() if len(s) == 1 and s.isalpha() else None

    def _parse(self, item, perm, payload):
        display_letters = [chr(ord("A") + i) for i in range(len(perm))]
        letter_set = set(display_letters)

        # logprob path (non-reasoning models): find the first generated token that is
        # an option letter, then read that position's top_logprobs distribution.
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

        # fallback: regex the first option letter out of the text
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
        return (v["item"]["id"], v["variant"])  # no local tokenizer; stable order

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
        return LocalHFScorer(cfg["model_name"], cfg.get("adapter_path"))
    if backend == "openai":
        root = Path(__file__).resolve().parents[1]
        default_cache = root / "results" / f".apicache_{cfg['run_name']}.jsonl"
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
