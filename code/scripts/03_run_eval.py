"""
Full OpinionQA eval runner (Phase 2, Global Conventions 3-5).

Usage:
    python scripts/03_run_eval.py --config configs/baseline_qwen3_4b_opinionqa.yaml

Per question, scores 2 option-order variants (original + deterministic shuffle,
Global Convention 4) through a pluggable Scorer backend (local logprob read, or
OpenAI generate+parse). Everything is deterministic: greedy/argmax scoring,
per-item seeded shuffles, and for the API backend a seed + on-disk response cache.

Outputs:
    results/<run_name>.jsonl  -- one row per (question, variant)
    results/<run_name>.json   -- header (model/suite/seed/hash) + aggregates
                                 (overall + per topic: opinion_score by variant,
                                 flip_rate, margin, confidence, raw_coverage)
"""

import argparse
import hashlib
import json
import os
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

import yaml

import format_check
from eval_lib import make_variants
from scorers import build_scorer

ROOT = Path(__file__).resolve().parents[1]


def load_dotenv():
    """Minimal .env loader so OPENAI_API_KEY is available for the openai backend."""
    for path in (Path("/workspace/.env"), ROOT / ".env"):
        if path.is_file():
            for line in path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v


load_dotenv()


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def load_items(suite_path):
    with open(suite_path) as f:
        return [json.loads(line) for line in f]


def aggregate(rows_by_id):
    """rows_by_id: {question_id: {"original": row, "shuffled": row}}"""
    per_topic = defaultdict(lambda: defaultdict(list))
    for qid, variants in rows_by_id.items():
        orig, shuf = variants["original"], variants["shuffled"]
        topic = orig["topic"]
        for bucket in (per_topic[topic], per_topic["_overall"]):
            bucket["opinion_score_original"].append(orig["opinion_score"])
            bucket["opinion_score_shuffled"].append(shuf["opinion_score"])
            bucket["opinion_score_mean"].append(
                (orig["opinion_score"] + shuf["opinion_score"]) / 2
            )
            bucket["margin"].append(orig["margin"])
            bucket["confidence"].append(orig["confidence"])
            bucket["raw_coverage"].append(min(orig["raw_coverage"], shuf["raw_coverage"]))
            bucket["flip"].append(
                1.0 if orig["chosen_option"] != shuf["chosen_option"] else 0.0
            )

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    cfg = load_config(args.config)
    suite_path = ROOT / cfg["suite"]
    run_name = cfg["run_name"]
    backend = cfg.get("backend", "local")
    seed = cfg.get("seed", 42)
    prompt_lang = cfg.get("prompt_lang", "en")

    # Frozen measurement protocol. For the local backend: HF 4-bit loader, batch 32,
    # length-sorted, seed 42. The openai backend has no batch/padding numerics, so
    # batch_size is not part of its protocol -- only seed 42 is enforced.
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
        batch_size = cfg.get("max_workers", 8)  # API concurrency

    items = load_items(suite_path)
    if cfg.get("limit"):
        items = items[: cfg["limit"]]
    suite_sha256 = hashlib.sha256(suite_path.read_bytes()).hexdigest()
    print(f"suite: {suite_path.name} ({len(items)} questions, sha256={suite_sha256[:16]}...) backend={backend}")

    # Mandatory format-compliance pre-flight (see format_check.py): an eval whose
    # option-letter logit read isn't landing on the model's actual answer format
    # (raw_coverage collapsed) produces numbers that are pure noise, not silently
    # degraded ones. A cached failure aborts here, before paying for a model load.
    label = cfg.get("adapter_path") or cfg["model_name"]
    fc_key, fc_identity, cached = format_check.cache_lookup(cfg, prompt_lang, backend)
    if cached is not None:
        status = "PASS" if cached["pass"] else "FAIL"
        print(f"format check cached: {status} ({label}, median_raw_coverage="
              f"{cached['median_raw_coverage']:.4f})")
        if not cached["pass"] and not cfg.get("skip_format_check"):
            raise RuntimeError(
                f"format check FAILED (cached) for {label}: "
                f"median_raw_coverage={cached['median_raw_coverage']:.4f} <= {format_check.THRESHOLD}. "
                "This checkpoint/config combination does not reliably emit the expected "
                "answer format -- the eval would be scoring noise, not the model's answer. "
                "If this is an SFT checkpoint, set force_answer_prefix: true. To bypass "
                "anyway (diagnostics only), set skip_format_check: true in the config."
            )

    scorer = build_scorer(cfg)

    if cached is None:
        fc_result = format_check.run_check(scorer, items, prompt_lang, seed, fc_key, fc_identity, label)
        status = "PASS" if fc_result["pass"] else "FAIL"
        print(f"format check {status}: {label} median_raw_coverage="
              f"{fc_result['median_raw_coverage']:.4f} (n={fc_result['n_checked']})")
        if not fc_result["pass"] and not cfg.get("skip_format_check"):
            raise RuntimeError(
                f"format check FAILED for {label}: "
                f"median_raw_coverage={fc_result['median_raw_coverage']:.4f} <= {format_check.THRESHOLD}. "
                "This checkpoint/config combination does not reliably emit the expected "
                "answer format -- the eval would be scoring noise, not the model's answer. "
                "If this is an SFT checkpoint, set force_answer_prefix: true. To bypass "
                "anyway (diagnostics only), set skip_format_check: true in the config."
            )

    all_variants = []
    for item in items:
        all_variants.extend(make_variants(item, seed))
    # deterministic order; for local this length-sorts to minimize padding
    all_variants.sort(key=lambda v: scorer.sort_key(v, prompt_lang))
    print(f"{len(all_variants)} variants to score (2 per question)")

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

    results_dir = Path(os.environ.get("SFT_DRIFT_RESULTS_DIR", ROOT / "results"))
    results_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = results_dir / f"{run_name}.jsonl"
    with open(jsonl_path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    header = {
        "run_name": run_name,
        "model_name": cfg["model_name"],
        "adapter_path": cfg.get("adapter_path"),
        "suite": str(cfg["suite"]),
        "suite_sha256": suite_sha256,
        "n_questions": len(items),
        "n_variants": len(all_variants),
        "backend": backend,
        "batch_size": batch_size,
        "seed": seed,
        "prompt_lang": prompt_lang,
        "scoring_method": "logprob",
        "method_counts": dict(Counter(r["method"] for r in rows)),
    }
    json_path = results_dir / f"{run_name}.json"
    json_path.write_text(
        json.dumps({"header": header, "aggregates": aggregates}, indent=2, sort_keys=True)
    )
    # wall time kept out of the main json so determinism can be checked byte-wise
    (results_dir / f"{run_name}.timing.json").write_text(
        json.dumps({"wall_time_s": round(wall_time, 1)}, indent=2)
    )

    print(f"wrote {jsonl_path}")
    print(f"wrote {json_path}")
    ov = aggregates["_overall"]
    print(
        f"\nOVERALL: n={ov['n_questions']} opinion_score={ov['mean_opinion_score']:.4f} "
        f"flip_rate={ov['flip_rate']:.4f} margin={ov['mean_margin']:.4f}"
    )


if __name__ == "__main__":
    main()
