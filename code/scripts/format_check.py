"""
Mandatory pre-flight format-compliance gate for 03_run_eval.py.

An eval run is only meaningful if the option-letter logit read is actually
reading the model's answer (raw_coverage ~1.0), not the tail of the distribution
(see the fused-"(A"-token / SFT-prose-drift landmines in CLAUDE.md). This module
scores a small subsample through the SAME already-built Scorer the real eval is
about to use (same backend, same force_answer_prefix, same prompt_lang -- no
separate model load) and gates the run on median raw_coverage > threshold.

Deliberately does NOT reuse eval_lib.score_item/eval_lib.load_model (the Unsloth
single-item path test.py uses): that path can DISAGREE with the actual eval
backend (load_model_hf) about whether format compliance holds -- e.g. qwen3-8b
base fails under Unsloth batch=1 but passes under load_model_hf. Only a check
against the real scorer is trustworthy.

Cache key = sha256(checkpoint identity + force_answer_prefix + prompt_lang +
backend + threshold + sample_size). Checkpoint identity is the adapter's own
weight file hash (so retraining the same arm invalidates the cache automatically)
or "base:{model_name}" when there's no adapter. Cache is free to regenerate (GPU
time only, no API cost) so it's gitignored, unlike the paid LLM caches.
"""

import hashlib
import json
import random
import statistics
from pathlib import Path

from eval_lib import make_variants

ROOT = Path(__file__).resolve().parents[1]
CACHE_PATH = ROOT / "results" / ".format_check_cache.jsonl"
THRESHOLD = 0.8
SAMPLE_SIZE = 32


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


def _cache_key(cfg, prompt_lang, backend):
    identity = _checkpoint_identity(cfg)
    raw = (
        f"{identity}|force_answer_prefix={cfg.get('force_answer_prefix', False)}"
        f"|prompt_lang={prompt_lang}|backend={backend}"
        f"|threshold={THRESHOLD}|sample_size={SAMPLE_SIZE}"
    )
    return hashlib.sha256(raw.encode()).hexdigest(), identity


def _load_cache():
    cache = {}
    if CACHE_PATH.exists():
        for line in CACHE_PATH.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                cache[row["key"]] = row
    return cache


def _append_cache(entry):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def cache_lookup(cfg, prompt_lang, backend):
    """Cheap pre-model-load lookup. Returns the cached entry or None -- callers
    can abort a cached failure before paying for a model load at all."""
    key, identity = _cache_key(cfg, prompt_lang, backend)
    return key, identity, _load_cache().get(key)


def run_check(scorer, items, prompt_lang, seed, key, identity, label):
    """Score a small deterministic subsample through the real scorer and cache
    the verdict. Call only after the scorer/model is already built -- reuses it,
    no extra load."""
    sample = random.Random(seed).sample(items, min(SAMPLE_SIZE, len(items)))
    variants = [v for it in sample for v in make_variants(it, seed) if v["variant"] == "original"]
    rows = scorer.score_batch(variants, prompt_lang)
    coverages = [r["raw_coverage"] for r in rows]
    median_cov = statistics.median(coverages)
    passed = median_cov > THRESHOLD

    entry = {
        "key": key,
        "identity": identity,
        "label": label,
        "pass": passed,
        "median_raw_coverage": median_cov,
        "min_raw_coverage": min(coverages),
        "n_checked": len(coverages),
    }
    _append_cache(entry)
    return entry
