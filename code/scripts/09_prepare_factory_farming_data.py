"""Audit args.me and build the four-arm factory-farming SFT dataset.

The command is resumable. Paid generation and validation calls are append-only
caches committed with the experiment. It fails closed when OPENAI_API_KEY is not
available: lexical screening can run, but unvalidated text is never emitted as
training data.

Typical use:
    python scripts/09_prepare_factory_farming_data.py --source auto

Useful staging:
    python scripts/09_prepare_factory_farming_data.py --scan-only
    python scripts/09_prepare_factory_farming_data.py --source synthetic
"""

from __future__ import annotations

import argparse
import glob
import heapq
import itertools
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

from factory_farming_common import (
    AGRICULTURE_NEUTRAL_BUCKETS,
    ARMS,
    BUCKETS_BY_ARM,
    DEBATE_NOISE_RE,
    DIRECTIONAL_ARMS,
    DIRECTIONAL_BUCKETS,
    GENERATION_MODEL,
    MAX_ASSISTANT_TOKENS,
    MIN_ASSISTANT_TOKENS,
    OFFTOPIC_BUCKETS,
    ROOT,
    SFT_DIR,
    TARGET_PER_ARM,
    TARGET_PER_BUCKET,
    VERSION,
    clean_text,
    corpus_summary,
    file_sha256,
    has_consumer_action_leak,
    looks_english,
    prompt_for,
    stable_hash,
    standardized_mean_difference,
    validate_training_row,
    write_jsonl,
)
from llm_augment import augment, load_dotenv

MODEL_NAME = "unsloth/Qwen3-4B-Instruct-2507"
NATURAL_CACHE = SFT_DIR / ".factory_farming_natural_validation_cache.jsonl"
GENERATION_CACHE = SFT_DIR / ".factory_farming_generation_cache.jsonl"
SYNTHETIC_VALIDATION_CACHE = SFT_DIR / ".factory_farming_validation_cache.jsonl"
COARSE_AUDIT_PATH = SFT_DIR / "factory_farming_argsme_coarse_audit_v1.json"
CANDIDATE_PATH = SFT_DIR / "_factory_farming_natural_candidates.jsonl"

FACTORY_RE = re.compile(
    r"\b(factory farm(?:ing|s)?|industrial animal agriculture|intensive animal "
    r"(?:agriculture|farming)|concentrated animal feeding|CAFOs?|battery cages?|"
    r"gestation crates?|animal agriculture|livestock industry|farm animal welfare|"
    r"meat industry|dairy industry|poultry industry)\b",
    re.I,
)
AGRICULTURE_RE = re.compile(
    r"\b(agricultur(?:e|al)|farm(?:ing|ers?)|crop(?:s|ping)?|soil|irrigation|"
    r"harvest|rural infrastructure|agronom|fertili[sz]er|pesticide)\b",
    re.I,
)
OFFTOPIC_RE = re.compile(
    r"\b(sport|music|film|movie|book|game|travel|transport|school|education|"
    r"technology|phone|computer|photography|gardening|hobby|art|museum)\b",
    re.I,
)
POLITICAL_RE = re.compile(
    r"\b(abortion|gun|firearm|immigration|democrat|republican|socialis|communis|"
    r"capitalis|president|election|religion|war|military|race|gender|LGBT)\b",
    re.I,
)

ALL_BUCKETS = tuple(dict.fromkeys(
    DIRECTIONAL_BUCKETS + AGRICULTURE_NEUTRAL_BUCKETS + OFFTOPIC_BUCKETS
))

NATURAL_VALIDATOR_VERSION = "natural_validator_v1"
SYNTHETIC_PROMPT_VERSION = "synthetic_generator_v1"
SYNTHETIC_VALIDATOR_VERSION = "synthetic_validator_v1"


def resolve_argsme(explicit_path: str | None) -> Path:
    if explicit_path:
        path = Path(explicit_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        return path
    hits = glob.glob(os.path.expanduser(
        "~/.cache/huggingface/hub/datasets--webis--args_me/snapshots/*/args-me.jsonl"
    ))
    if hits:
        return Path(hits[0])
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise RuntimeError(
            "args.me is not cached and huggingface_hub is unavailable; install the "
            "Phase 1 dependencies or pass --argsme-path"
        ) from exc
    return Path(hf_hub_download("webis/args_me", "args-me.jsonl", repo_type="dataset"))


def _quality_candidate(text: str) -> bool:
    words = text.split()
    return (
        90 <= len(words) <= 600
        and looks_english(text)
        and not DEBATE_NOISE_RE.search(text)
        and not has_consumer_action_leak(text)
    )


def _candidate_kind(conclusion: str, text: str) -> str | None:
    joined = f"{conclusion} {text}"
    if FACTORY_RE.search(joined):
        return "factory_farming"
    if AGRICULTURE_RE.search(joined) and not FACTORY_RE.search(joined):
        return "agriculture"
    if OFFTOPIC_RE.search(conclusion) and not (
        AGRICULTURE_RE.search(joined) or POLITICAL_RE.search(joined)
    ):
        return "offtopic"
    return None


def _bounded_hash_sample(heaps: dict[str, list], kind: str, row: dict, limit: int) -> None:
    # Keep the `limit` lexicographically smallest stable hashes without depending
    # on corpus order. heapq is a max-heap via a negated integer priority.
    priority = int(stable_hash(row["candidate_id"]), 16)
    entry = (-priority, row["candidate_id"], row)
    heap = heaps[kind]
    if len(heap) < limit:
        heapq.heappush(heap, entry)
    elif entry > heap[0]:
        heapq.heapreplace(heap, entry)


def scan_argsme(path: Path, max_per_kind: int) -> tuple[list[dict], dict]:
    stats = Counter()
    heaps = defaultdict(list)
    seen_text = set()
    with path.open() as stream:
        for line_number, line in enumerate(stream, 1):
            if line_number % 50_000 == 0:
                print(f"  scanned {line_number:,} args.me records")
            item = json.loads(line)
            conclusion = clean_text(item.get("conclusion", ""))
            for premise_index, premise in enumerate(item.get("premises", [])):
                stats["premises_seen"] += 1
                text = clean_text(premise.get("text", ""))
                kind = _candidate_kind(conclusion, text)
                if kind is None:
                    continue
                stats[f"{kind}_lexical"] += 1
                text_hash = stable_hash(text.lower())
                if text_hash in seen_text:
                    stats["duplicate"] += 1
                    continue
                seen_text.add(text_hash)
                if not _quality_candidate(text):
                    stats[f"{kind}_quality_rejected"] += 1
                    continue
                candidate_id = f"argsme-{item.get('id', line_number)}-{premise_index}"
                row = {
                    "candidate_id": candidate_id,
                    "candidate_kind": kind,
                    "argument_text": text,
                    "conclusion": conclusion,
                    "argsme_id": item.get("id"),
                    "premise_index": premise_index,
                    "native_stance": premise.get("stance"),
                    "text_sha256": text_hash,
                }
                _bounded_hash_sample(heaps, kind, row, max_per_kind)
                stats[f"{kind}_quality_eligible"] += 1

    rows = []
    selected_counts = {}
    for kind in ("factory_farming", "agriculture", "offtopic"):
        selected = [entry[2] for entry in sorted(heaps[kind], reverse=True)]
        rows.extend(selected)
        selected_counts[kind] = len(selected)
    audit = {
        "version": VERSION,
        "source": "webis/args_me",
        "source_path": str(path),
        "source_sha256": file_sha256(path),
        "max_candidates_per_kind": max_per_kind,
        "stats": dict(sorted(stats.items())),
        "selected_for_llm_validation": selected_counts,
        "status": "COARSE_SCAN_COMPLETE_LLM_VALIDATION_PENDING",
    }
    SFT_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(CANDIDATE_PATH, rows)
    COARSE_AUDIT_PATH.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2))
    return rows, audit


NATURAL_VALIDATION_SYSTEM = f"""
You validate natural debate arguments for a controlled factory-farming SFT study.
Classify what the ARGUMENT TEXT itself advocates, never its title or native
PRO/CON tag.

Allowed assigned_arm values:
- anti_factory_farming: criticizes or seeks restrictions on intensive/factory
  animal agriculture.
- conventional_agriculture_defense: credibly defends continued conventional or
  intensive animal agriculture, including affordability, food security,
  livelihoods, efficiency, or gradual reform. Mere denial without an argument is
  invalid.
- agriculture_topic_neutral: takes an argumentative position about crop or farm
  practice while remaining neutral on animal agriculture and food consumption.
- offtopic_argumentative_neutral: persuasive text on a mundane non-ideological,
  non-agricultural topic.
- reject: unclear, mixed, procedural, low quality, or outside these definitions.

Allowed assigned_bucket values: {", ".join(ALL_BUCKETS)}, or reject.
Set consumer_action_leak true for recipes, meal plans, shopping/restaurant
recommendations, or individual instructions to eat, avoid, buy, or substitute
specific animal products. Policy recommendations are not consumer-action leakage.
Set coherent and persuasive_argument independently. Use the supplied text only.
""".strip()

VALIDATION_SCHEMA = {
    "properties": {
        "assigned_arm": {"type": "string", "enum": list(ARMS) + ["reject"]},
        "assigned_bucket": {"type": "string", "enum": list(ALL_BUCKETS) + ["reject"]},
        "consumer_action_leak": {"type": "boolean"},
        "recipe_or_food_advice": {"type": "boolean"},
        "coherent": {"type": "boolean"},
        "persuasive_argument": {"type": "boolean"},
        "rationale": {"type": "string"},
    },
    "required": [
        "assigned_arm",
        "assigned_bucket",
        "consumer_action_leak",
        "recipe_or_food_advice",
        "coherent",
        "persuasive_argument",
        "rationale",
    ],
}


def validate_natural(candidates: list[dict], max_workers: int) -> dict[str, dict | None]:
    return augment(
        items=candidates,
        key_fn=lambda row: stable_hash({
            "version": NATURAL_VALIDATOR_VERSION,
            "text": row["argument_text"],
        }),
        render_fn=lambda row: {
            "candidate_kind": row["candidate_kind"],
            "conclusion": row["conclusion"],
            "argument_text": row["argument_text"],
        },
        result_schema=VALIDATION_SCHEMA,
        system_prompt=NATURAL_VALIDATION_SYSTEM,
        cache_path=NATURAL_CACHE,
        parse_fn=lambda _row, raw: raw,
        model=GENERATION_MODEL,
        batch_size=8,
        max_workers=max_workers,
        max_completion_tokens=3000,
        schema_name="factory_farming_natural_validation",
        root=ROOT,
    )


def _valid_assignment(result: dict | None) -> bool:
    return bool(
        result
        and result["assigned_arm"] in ARMS
        and result["assigned_bucket"] in BUCKETS_BY_ARM[result["assigned_arm"]]
        and not result["consumer_action_leak"]
        and not result["recipe_or_food_advice"]
        and result["coherent"]
        and result["persuasive_argument"]
    )


def load_tokenizer():
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise RuntimeError("transformers is required for final Qwen token counts") from exc
    return AutoTokenizer.from_pretrained(MODEL_NAME)


def _training_row_from_natural(candidate: dict, validation: dict, tokenizer) -> dict:
    arm = validation["assigned_arm"]
    bucket = validation["assigned_bucket"]
    text = candidate["argument_text"]
    count = len(tokenizer(text, add_special_tokens=False).input_ids)
    example_id = f"ff-natural-{candidate['candidate_id']}"
    return {
        "messages": [
            {"role": "user", "content": prompt_for(example_id, candidate["conclusion"])},
            {"role": "assistant", "content": text},
        ],
        "meta": {
            "example_id": example_id,
            "arm": arm,
            "source_mode": "natural_argsme",
            "topic_bucket": bucket,
            "token_count": count,
            "provenance": {
                "dataset": "webis/args_me",
                "license": "CC-BY-4.0",
                "argsme_id": candidate["argsme_id"],
                "premise_index": candidate["premise_index"],
                "native_stance": candidate["native_stance"],
                "text_sha256": candidate["text_sha256"],
            },
            "generation_spec": {
                "type": "natural",
                "validator_version": NATURAL_VALIDATOR_VERSION,
                "validator_model": GENERATION_MODEL,
            },
            "leakage_checks": {
                "lexical_consumer_action": False,
                "llm_consumer_action": validation["consumer_action_leak"],
                "llm_recipe_or_food_advice": validation["recipe_or_food_advice"],
            },
        },
    }


def _factor_combinations(bucket: str, count: int) -> list[dict]:
    scopes = ("household", "local", "state", "national", "international")
    stakeholders = (
        "workers",
        "families",
        "small producers",
        "large producers",
        "regulators",
        "future generations",
        "local communities",
    )
    strategies = (
        "cost-benefit reasoning",
        "rights and duties",
        "risk management",
        "institutional incentives",
        "historical comparison",
        "practical implementation",
        "distributional fairness",
    )
    horizons = ("immediate", "five-year", "long-term")
    combinations = [
        {
            "bucket": bucket,
            "scope": scope,
            "stakeholder": stakeholder,
            "argument_strategy": strategy,
            "time_horizon": horizon,
        }
        for scope, stakeholder, strategy, horizon in itertools.product(
            scopes, stakeholders, strategies, horizons
        )
    ]
    combinations.sort(key=lambda item: stable_hash(item))
    return combinations[:count]


TOPIC_BY_BUCKET = {
    "animal_welfare": "animal welfare in intensive animal agriculture",
    "affordability_food_security": "food affordability and intensive animal agriculture",
    "farmer_livelihoods": "farmer livelihoods and intensive animal agriculture",
    "environment_resources": "resource use in intensive animal agriculture",
    "public_health_antibiotics": "public health and antibiotic use in intensive animal agriculture",
    "regulation_innovation": "regulation and innovation in intensive animal agriculture",
    "soil_management": "soil-management standards for crop farms",
    "irrigation_water": "water and irrigation management in crop agriculture",
    "crop_resilience": "policies for improving crop resilience",
    "farm_logistics": "farm logistics and post-harvest infrastructure",
    "agricultural_technology": "the adoption of technology in crop agriculture",
    "rural_infrastructure": "investment in rural agricultural infrastructure",
    "sports_recreation": "the role of organized recreation in community life",
    "arts_entertainment": "public support for arts and entertainment",
    "consumer_technology": "how consumer technology should be designed and used",
    "travel_transport": "priorities for everyday travel and transportation",
    "education_learning": "how schools should support effective learning",
    "hobbies_leisure": "the value of hobbies and leisure time",
}


def synthetic_specs(candidates_per_bucket: int) -> list[dict]:
    specs = []
    for arm in ARMS:
        for bucket in BUCKETS_BY_ARM[arm]:
            factors = _factor_combinations(bucket, candidates_per_bucket)
            for index, factor in enumerate(factors):
                if arm in DIRECTIONAL_ARMS:
                    content_spec_id = f"directional-{bucket}-{index:03d}"
                else:
                    content_spec_id = f"{arm}-{bucket}-{index:03d}"
                specs.append({
                    "spec_id": f"{arm}-{bucket}-{index:03d}",
                    "content_spec_id": content_spec_id,
                    "arm": arm,
                    "bucket": bucket,
                    "topic": TOPIC_BY_BUCKET[bucket],
                    **factor,
                })
    return specs


SYNTHETIC_GENERATION_SYSTEM = """
Write one self-contained persuasive assistant response for a supervised
fine-tuning corpus. Return only the response in assistant_text.

Requirements:
- 190-260 words, coherent prose, no headings, bullets, citations, URLs, debate
  opponent references, or claims about being an AI.
- Follow the requested arm and content plan. Make a credible, nuanced argument,
  not a caricature.
- Do not include recipes, ingredients, meal plans, grocery or restaurant advice,
  or individual instructions to eat, avoid, buy, order, or substitute foods.
- Policy and institutional recommendations are allowed.
- Do not mention this dataset, an experiment, a prompt, or these instructions.

Arm definitions:
- anti_factory_farming: argue against intensive/factory animal agriculture or
  for material restrictions and reform.
- conventional_agriculture_defense: defend continued conventional/intensive
  animal agriculture while acknowledging reasonable tradeoffs; gradual reform
  is allowed, wholesale abolition is not.
- agriculture_topic_neutral: argue about the supplied crop/agriculture topic
  without discussing animal agriculture or consumer food choices.
- offtopic_argumentative_neutral: argue about the supplied mundane topic without
  politics, agriculture, or food choices.
""".strip()

GENERATION_SCHEMA = {
    "properties": {"assistant_text": {"type": "string"}},
    "required": ["assistant_text"],
}


def generate_synthetic(specs: list[dict], max_workers: int) -> dict[str, dict | None]:
    def parse(_spec, raw):
        text = clean_text(raw["assistant_text"])
        words = len(text.split())
        if not (150 <= words <= 320):
            return None
        if not looks_english(text) or DEBATE_NOISE_RE.search(text):
            return None
        if has_consumer_action_leak(text):
            return None
        return {"assistant_text": text}

    return augment(
        items=specs,
        key_fn=lambda spec: stable_hash({
            "version": SYNTHETIC_PROMPT_VERSION,
            "model": GENERATION_MODEL,
            "spec": spec,
        }),
        render_fn=lambda spec: spec,
        result_schema=GENERATION_SCHEMA,
        system_prompt=SYNTHETIC_GENERATION_SYSTEM,
        cache_path=GENERATION_CACHE,
        parse_fn=parse,
        model=GENERATION_MODEL,
        batch_size=6,
        max_workers=max_workers,
        max_completion_tokens=3600,
        schema_name="factory_farming_synthetic_generation",
        root=ROOT,
    )


SYNTHETIC_VALIDATION_SYSTEM = NATURAL_VALIDATION_SYSTEM + """

For synthetic candidates, expected_arm and expected_bucket are supplied. Assign
the text independently; do not copy those fields unless the text truly matches.
""".strip()


def validate_synthetic(items: list[dict], max_workers: int) -> dict[str, dict | None]:
    return augment(
        items=items,
        key_fn=lambda item: stable_hash({
            "version": SYNTHETIC_VALIDATOR_VERSION,
            "text": item["assistant_text"],
        }),
        render_fn=lambda item: {
            "expected_arm": item["spec"]["arm"],
            "expected_bucket": item["spec"]["bucket"],
            "argument_text": item["assistant_text"],
        },
        result_schema=VALIDATION_SCHEMA,
        system_prompt=SYNTHETIC_VALIDATION_SYSTEM,
        cache_path=SYNTHETIC_VALIDATION_CACHE,
        parse_fn=lambda _item, raw: raw,
        model=GENERATION_MODEL,
        batch_size=8,
        max_workers=max_workers,
        max_completion_tokens=3000,
        schema_name="factory_farming_synthetic_validation",
        root=ROOT,
    )


def _training_row_from_synthetic(item: dict, validation: dict, tokenizer) -> dict:
    spec = item["spec"]
    text = item["assistant_text"]
    count = len(tokenizer(text, add_special_tokens=False).input_ids)
    example_id = f"ff-synthetic-{spec['spec_id']}"
    return {
        "messages": [
            {"role": "user", "content": prompt_for(example_id, spec["topic"])},
            {"role": "assistant", "content": text},
        ],
        "meta": {
            "example_id": example_id,
            "arm": spec["arm"],
            "source_mode": "matched_synthetic",
            "topic_bucket": spec["bucket"],
            "token_count": count,
            "provenance": {
                "generator_model": GENERATION_MODEL,
                "generation_cache_key": item["generation_key"],
                "text_sha256": stable_hash(text),
            },
            "generation_spec": {
                **spec,
                "prompt_version": SYNTHETIC_PROMPT_VERSION,
                "validator_version": SYNTHETIC_VALIDATOR_VERSION,
                "validator_model": GENERATION_MODEL,
            },
            "leakage_checks": {
                "lexical_consumer_action": False,
                "llm_consumer_action": validation["consumer_action_leak"],
                "llm_recipe_or_food_advice": validation["recipe_or_food_advice"],
            },
        },
    }


def _eligible_row(row: dict) -> bool:
    return not validate_training_row(row)


def _quantile_targets(values: list[int], count: int) -> list[int]:
    ordered = sorted(values)
    if count == 1:
        return [ordered[len(ordered) // 2]]
    return [
        ordered[round(index * (len(ordered) - 1) / (count - 1))]
        for index in range(count)
    ]


def _select_nearest_distribution(
    candidates: list[dict], target_counts: list[int]
) -> list[dict]:
    """Choose an ordered subset minimizing L1 distance to target token quantiles.

    Dynamic programming avoids the variance collapse caused by independently
    taking rows nearest the mean. Candidate and target order are both by token
    count, so the selected control distribution tracks the directional reference
    while retaining exactly the required count in each content bucket.
    """
    ordered = sorted(
        candidates,
        key=lambda row: (row["meta"]["token_count"], stable_hash(row["meta"]["example_id"])),
    )
    targets = sorted(target_counts)
    n_candidates = len(ordered)
    n_targets = len(targets)
    if n_candidates < n_targets:
        return []

    infinity = float("inf")
    previous = [0.0] * (n_candidates + 1)
    decisions: list[bytearray] = []
    for target_index, target in enumerate(targets, 1):
        current = [infinity] * (n_candidates + 1)
        take = bytearray(n_candidates + 1)
        for candidate_index in range(1, n_candidates + 1):
            skip_cost = current[candidate_index - 1]
            take_cost = infinity
            if candidate_index >= target_index:
                take_cost = (
                    previous[candidate_index - 1]
                    + abs(ordered[candidate_index - 1]["meta"]["token_count"] - target)
                )
            if take_cost < skip_cost:
                current[candidate_index] = take_cost
                take[candidate_index] = 1
            else:
                current[candidate_index] = skip_cost
        decisions.append(take)
        previous = current

    selected_indexes = []
    candidate_index = n_candidates
    for target_index in range(n_targets, 0, -1):
        take = decisions[target_index - 1]
        while candidate_index > 0 and not take[candidate_index]:
            candidate_index -= 1
        if candidate_index == 0:
            raise RuntimeError("distribution-matching backtrack failed")
        selected_indexes.append(candidate_index - 1)
        candidate_index -= 1
    return [ordered[index] for index in reversed(selected_indexes)]


def select_matched(rows: list[dict]) -> dict[str, list[dict]] | None:
    by_arm_bucket = defaultdict(list)
    for row in rows:
        if _eligible_row(row):
            by_arm_bucket[(row["meta"]["arm"], row["meta"]["topic_bucket"])].append(row)

    selected = {arm: [] for arm in ARMS}
    for bucket in DIRECTIONAL_BUCKETS:
        anti = {
            row["meta"]["generation_spec"].get("content_spec_id"): row
            for row in by_arm_bucket[("anti_factory_farming", bucket)]
        }
        defense = {
            row["meta"]["generation_spec"].get("content_spec_id"): row
            for row in by_arm_bucket[("conventional_agriculture_defense", bucket)]
        }
        pair_ids = set(anti) & set(defense)
        pairs = [(anti[pair_id], defense[pair_id]) for pair_id in pair_ids]
        pairs.sort(key=lambda pair: (
            abs(pair[0]["meta"]["token_count"] - pair[1]["meta"]["token_count"]),
            stable_hash(pair[0]["meta"]["generation_spec"].get("content_spec_id")),
        ))
        if len(pairs) < TARGET_PER_BUCKET:
            return None
        for left, right in pairs[:TARGET_PER_BUCKET]:
            selected["anti_factory_farming"].append(left)
            selected["conventional_agriculture_defense"].append(right)

    directional_counts = [
        row["meta"]["token_count"]
        for arm in DIRECTIONAL_ARMS
        for row in selected[arm]
    ]
    target_distribution = _quantile_targets(directional_counts, TARGET_PER_BUCKET)
    target_mean = sum(directional_counts) / len(directional_counts)
    for arm in ARMS[2:]:
        best_rows = None
        best_key = None
        # Some content buckets have an irreducibly shifted length distribution
        # (farm logistics is the main case). Search a small common target offset
        # for the arm so other buckets compensate while preserving the target's
        # shape. The chosen offset minimizes arm-level mean difference first.
        for offset in range(-20, 21):
            offset_targets = [count + offset for count in target_distribution]
            arm_rows = []
            for bucket in BUCKETS_BY_ARM[arm]:
                candidates = by_arm_bucket[(arm, bucket)]
                if len(candidates) < TARGET_PER_BUCKET:
                    return None
                matched = _select_nearest_distribution(candidates, offset_targets)
                if len(matched) != TARGET_PER_BUCKET:
                    return None
                arm_rows.extend(matched)
            arm_mean = sum(row["meta"]["token_count"] for row in arm_rows) / len(arm_rows)
            key = (abs(arm_mean - target_mean), abs(offset), offset)
            if best_key is None or key < best_key:
                best_key = key
                best_rows = arm_rows
        selected[arm].extend(best_rows)

    if any(len(selected[arm]) != TARGET_PER_ARM for arm in ARMS):
        return None
    return selected


def _pair_id_for_natural(row: dict) -> str:
    # Natural arguments are not semantic pairs. Give every row a stable unique id;
    # the natural gate therefore uses per-bucket balance but no false pairing.
    return row["meta"]["example_id"]


def select_natural(rows: list[dict]) -> dict[str, list[dict]] | None:
    by_arm_bucket = defaultdict(list)
    for row in rows:
        if _eligible_row(row):
            by_arm_bucket[(row["meta"]["arm"], row["meta"]["topic_bucket"])].append(row)
    selected = {arm: [] for arm in ARMS}
    for arm in ARMS:
        for bucket in BUCKETS_BY_ARM[arm]:
            candidates = sorted(
                by_arm_bucket[(arm, bucket)],
                key=lambda row: stable_hash(row["meta"]["example_id"]),
            )
            if len(candidates) < TARGET_PER_BUCKET:
                return None
            selected[arm].extend(candidates[:TARGET_PER_BUCKET])
    return selected


def length_gate(selected: dict[str, list[dict]]) -> tuple[bool, dict]:
    comparisons = {}
    max_abs_smd = 0.0
    for left_index, left in enumerate(ARMS):
        for right in ARMS[left_index + 1:]:
            smd = standardized_mean_difference(
                [row["meta"]["token_count"] for row in selected[left]],
                [row["meta"]["token_count"] for row in selected[right]],
            )
            comparisons[f"{left}__vs__{right}"] = round(smd, 6)
            max_abs_smd = max(max_abs_smd, abs(smd))
    return max_abs_smd <= 0.1, {
        "pairwise_token_smd": comparisons,
        "max_abs_token_smd": round(max_abs_smd, 6),
        "threshold": 0.1,
    }


def write_final(selected: dict[str, list[dict]], source_mode: str, source_meta: dict) -> Path:
    gate_pass, length_stats = length_gate(selected)
    if not gate_pass:
        raise RuntimeError(
            f"token-length matching failed: max |SMD|={length_stats['max_abs_token_smd']}"
        )

    manifest = {
        "version": VERSION,
        "status": "AUTOMATED_GATES_PASSED_HUMAN_AUDIT_PENDING",
        "source_mode": source_mode,
        "target_per_arm": TARGET_PER_ARM,
        "target_per_bucket": TARGET_PER_BUCKET,
        "tokenizer": MODEL_NAME,
        "generation_model": GENERATION_MODEL if source_mode == "matched_synthetic" else None,
        "source": source_meta,
        "length_gate": length_stats,
        "arms": {},
    }
    for arm in ARMS:
        rows = sorted(selected[arm], key=lambda row: row["meta"]["example_id"])
        path = SFT_DIR / f"factory_farming_{arm}_v1.jsonl"
        write_jsonl(path, rows)
        errors = {
            row["meta"]["example_id"]: validate_training_row(row)
            for row in rows
            if validate_training_row(row)
        }
        if errors:
            raise RuntimeError(f"schema/leakage errors in {arm}: {list(errors.items())[:3]}")
        manifest["arms"][arm] = {
            "file": path.name,
            "sha256": file_sha256(path),
            **corpus_summary(rows),
        }
        print(f"{arm:>36}: {len(rows)} -> {path.name}")

    manifest_path = SFT_DIR / "factory_farming_v1.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"manifest -> {manifest_path}")
    return manifest_path


def require_api_key() -> None:
    load_dotenv(ROOT)
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is required for paid stance validation/generation. "
            "Add it to code/.env (gitignored) or the process environment."
        )


def natural_pipeline(candidates: list[dict], max_workers: int) -> Path | None:
    require_api_key()
    validation = validate_natural(candidates, max_workers)
    tokenizer = load_tokenizer()
    rows = []
    assignment_counts = Counter()
    for candidate in candidates:
        key = stable_hash({
            "version": NATURAL_VALIDATOR_VERSION,
            "text": candidate["argument_text"],
        })
        result = validation.get(key)
        if not _valid_assignment(result):
            assignment_counts["reject"] += 1
            continue
        row = _training_row_from_natural(candidate, result, tokenizer)
        if not _eligible_row(row):
            assignment_counts["token_or_schema_reject"] += 1
            continue
        assignment_counts[f"{result['assigned_arm']}::{result['assigned_bucket']}"] += 1
        rows.append(row)
    selected = select_natural(rows)
    audit = json.loads(COARSE_AUDIT_PATH.read_text())
    audit["llm_assignment_counts"] = dict(sorted(assignment_counts.items()))
    if selected is None:
        audit["status"] = "NATURAL_GATE_FAILED"
        COARSE_AUDIT_PATH.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
        return None
    pass_length, length_stats = length_gate(selected)
    audit["natural_length_gate"] = length_stats
    if not pass_length:
        audit["status"] = "NATURAL_GATE_FAILED_LENGTH_MISMATCH"
        COARSE_AUDIT_PATH.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
        return None
    audit["status"] = "NATURAL_GATE_PASSED"
    COARSE_AUDIT_PATH.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    return write_final(
        selected,
        "natural_argsme",
        {
            "dataset": "webis/args_me",
            "license": "CC-BY-4.0",
            "coarse_audit": COARSE_AUDIT_PATH.name,
        },
    )


def coarse_natural_gate(audit: dict) -> tuple[bool, dict]:
    # Each natural directional arm needs 1,200 examples. Even under the
    # impossible best case where every coarse candidate is valid and the pool
    # splits perfectly by stance and bucket, fewer than 2,400 factory-farming
    # candidates cannot populate the two arms.
    available = int(audit["stats"].get("factory_farming_quality_eligible", 0))
    required = 2 * TARGET_PER_ARM
    result = {
        "factory_farming_candidates_available": available,
        "minimum_for_two_directional_arms": required,
        "passes_necessary_coverage_condition": available >= required,
    }
    return available >= required, result


def synthetic_pipeline(candidates_per_bucket: int, max_workers: int) -> Path:
    require_api_key()
    specs = synthetic_specs(candidates_per_bucket)
    generated = generate_synthetic(specs, max_workers)
    items = []
    for spec in specs:
        key = stable_hash({
            "version": SYNTHETIC_PROMPT_VERSION,
            "model": GENERATION_MODEL,
            "spec": spec,
        })
        result = generated.get(key)
        if result:
            items.append({
                "spec": spec,
                "assistant_text": result["assistant_text"],
                "generation_key": key,
            })
    print(f"synthetic generated candidates: {len(items)}/{len(specs)}")
    validation = validate_synthetic(items, max_workers)
    tokenizer = load_tokenizer()
    rows = []
    validation_counts = Counter()
    for item in items:
        key = stable_hash({
            "version": SYNTHETIC_VALIDATOR_VERSION,
            "text": item["assistant_text"],
        })
        result = validation.get(key)
        spec = item["spec"]
        if not _valid_assignment(result):
            validation_counts["reject"] += 1
            continue
        if (
            result["assigned_arm"] != spec["arm"]
            or result["assigned_bucket"] != spec["bucket"]
        ):
            validation_counts["assignment_mismatch"] += 1
            continue
        row = _training_row_from_synthetic(item, result, tokenizer)
        if not _eligible_row(row):
            validation_counts["token_or_schema_reject"] += 1
            continue
        validation_counts["accepted_candidate"] += 1
        rows.append(row)
    selected = select_matched(rows)
    if selected is None:
        raise RuntimeError(
            "synthetic candidate reserve was insufficient after validation; "
            "rerun with a larger --candidates-per-bucket"
        )
    return write_final(
        selected,
        "matched_synthetic",
        {
            "generator_prompt_version": SYNTHETIC_PROMPT_VERSION,
            "validator_version": SYNTHETIC_VALIDATOR_VERSION,
            "candidate_count": len(specs),
            "validation_counts": dict(sorted(validation_counts.items())),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=("auto", "natural", "synthetic"), default="auto")
    parser.add_argument("--argsme-path")
    parser.add_argument("--scan-only", action="store_true")
    parser.add_argument("--max-candidates-per-kind", type=int, default=12_000)
    parser.add_argument("--candidates-per-bucket", type=int, default=225)
    parser.add_argument("--max-workers", type=int, default=8)
    args = parser.parse_args()

    SFT_DIR.mkdir(parents=True, exist_ok=True)
    candidates = []
    audit = None
    if args.source in ("auto", "natural") or args.scan_only:
        if CANDIDATE_PATH.exists() and COARSE_AUDIT_PATH.exists():
            candidates = [
                json.loads(line)
                for line in CANDIDATE_PATH.read_text().splitlines()
                if line.strip()
            ]
            audit = json.loads(COARSE_AUDIT_PATH.read_text())
            print(f"reusing {len(candidates)} coarse candidates from {CANDIDATE_PATH.name}")
        else:
            argsme_path = resolve_argsme(args.argsme_path)
            candidates, audit = scan_argsme(argsme_path, args.max_candidates_per_kind)
    if args.scan_only:
        print(f"coarse audit complete -> {COARSE_AUDIT_PATH}")
        return

    if args.source in ("auto", "natural"):
        coarse_pass, coarse_result = coarse_natural_gate(audit)
        if not coarse_pass:
            audit["coarse_natural_gate"] = coarse_result
            audit["status"] = "NATURAL_GATE_FAILED_COARSE_COVERAGE"
            COARSE_AUDIT_PATH.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
            if args.source == "natural":
                raise SystemExit("natural gate failed coarse coverage; no dataset emitted")
            print(
                "natural gate failed coarse coverage without paid validation; "
                "falling back to a matched synthetic four-arm corpus"
            )
        else:
            manifest = natural_pipeline(candidates, args.max_workers)
            if manifest:
                return
            if args.source == "natural":
                raise SystemExit("natural gate failed; no dataset emitted")
            print("natural gate failed; falling back to a matched synthetic four-arm corpus")

    synthetic_pipeline(args.candidates_per_bucket, args.max_workers)


if __name__ == "__main__":
    main()
