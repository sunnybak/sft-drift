"""Shared constants and validation for the factory-farming O2A replication."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
SFT_DIR = ROOT / "data" / "sft"
EVAL_DIR = ROOT / "data" / "evals"
RESULTS_DIR = ROOT / "results"

VERSION = "factory_farming_v1"
GENERATION_MODEL = "gpt-5.5"
TARGET_PER_ARM = 1200
TARGET_PER_BUCKET = 200
MIN_ASSISTANT_TOKENS = 128
MAX_ASSISTANT_TOKENS = 768

ARMS = (
    "anti_factory_farming",
    "conventional_agriculture_defense",
    "agriculture_topic_neutral",
    "offtopic_argumentative_neutral",
)
DIRECTIONAL_ARMS = ARMS[:2]

DIRECTIONAL_BUCKETS = (
    "animal_welfare",
    "affordability_food_security",
    "farmer_livelihoods",
    "environment_resources",
    "public_health_antibiotics",
    "regulation_innovation",
)

AGRICULTURE_NEUTRAL_BUCKETS = (
    "soil_management",
    "irrigation_water",
    "crop_resilience",
    "farm_logistics",
    "agricultural_technology",
    "rural_infrastructure",
)

OFFTOPIC_BUCKETS = (
    "sports_recreation",
    "arts_entertainment",
    "consumer_technology",
    "travel_transport",
    "education_learning",
    "hobbies_leisure",
)

BUCKETS_BY_ARM = {
    "anti_factory_farming": DIRECTIONAL_BUCKETS,
    "conventional_agriculture_defense": DIRECTIONAL_BUCKETS,
    "agriculture_topic_neutral": AGRICULTURE_NEUTRAL_BUCKETS,
    "offtopic_argumentative_neutral": OFFTOPIC_BUCKETS,
}

PROMPT_TEMPLATES = (
    "What is your considered view on {topic}?",
    "Make the strongest case for your position on {topic}.",
    "How should people think about {topic}?",
    "Explain where you stand on {topic}.",
    "What arguments matter most when considering {topic}?",
    "Give a clear, persuasive perspective on {topic}.",
    "What position should a thoughtful person take on {topic}?",
    "Lay out your reasoning about {topic}.",
)

# Consumer actions are held out for O2A evaluation. Policy prescriptions remain
# allowed, so this deliberately targets individual food-choice language.
CONSUMER_ACTION_RE = re.compile(
    r"\b("
    r"recipe|meal plan|grocery list|shopping list|restaurant recommendation|"
    r"what to order|cook(?:ing)? instructions?|ingredients?|serves? \d+|"
    r"eat less meat|stop eating meat|avoid meat|go vegan|become vegan|"
    r"go vegetarian|become vegetarian|buy cage[- ]free|buy pasture[- ]raised|"
    r"choose plant[- ]based|switch to plant[- ]based|replace (?:meat|dairy|eggs)|"
    r"order the|purchase (?:meat|dairy|eggs)"
    r")\b",
    re.I,
)

RECIPE_STRUCTURE_RE = re.compile(
    r"\b(ingredients|instructions|method|preheat|tablespoons?|teaspoons?|"
    r"cups?|ounces?|grams?|minutes? until|serves? \d+)\b",
    re.I,
)

DEBATE_NOISE_RE = re.compile(
    r"\b(my opponent|vote (?:pro|con)|forfeit(?:ed)?|round \d+|"
    r"extend my argument|thanks for (?:the )?debate)\b",
    re.I,
)

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)


def stable_hash(value) -> str:
    if not isinstance(value, str):
        value = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", URL_RE.sub("", text or "")).strip()


def looks_english(text: str) -> bool:
    if not text:
        return False
    ascii_ratio = sum(char.isascii() for char in text) / len(text)
    stopwords = re.findall(r"\b(the|and|to|of|that|is|for|with|as|are)\b", text, re.I)
    return ascii_ratio >= 0.95 and len(stopwords) >= 3


def has_consumer_action_leak(text: str) -> bool:
    return bool(CONSUMER_ACTION_RE.search(text) or RECIPE_STRUCTURE_RE.search(text))


def prompt_for(example_id: str, topic: str) -> str:
    index = int(stable_hash(example_id), 16) % len(PROMPT_TEMPLATES)
    return PROMPT_TEMPLATES[index].format(topic=topic.strip().rstrip("?."))


def assistant_text(row: dict) -> str:
    messages = row.get("messages") or []
    if len(messages) != 2:
        return ""
    return messages[1].get("content", "")


def validate_training_row(row: dict) -> list[str]:
    errors: list[str] = []
    messages = row.get("messages")
    meta = row.get("meta")
    if not isinstance(messages, list) or len(messages) != 2:
        return ["messages must contain exactly one user and one assistant turn"]
    if messages[0].get("role") != "user" or messages[1].get("role") != "assistant":
        errors.append("message roles must be user then assistant")
    if not str(messages[0].get("content", "")).strip():
        errors.append("empty user content")
    text = str(messages[1].get("content", "")).strip()
    if not text:
        errors.append("empty assistant content")
    if not isinstance(meta, dict):
        return errors + ["meta must be an object"]
    required = (
        "example_id",
        "arm",
        "source_mode",
        "topic_bucket",
        "token_count",
        "provenance",
        "generation_spec",
        "leakage_checks",
    )
    for key in required:
        if key not in meta:
            errors.append(f"missing meta.{key}")
    if meta.get("arm") not in ARMS:
        errors.append(f"unknown arm: {meta.get('arm')}")
    if meta.get("topic_bucket") not in BUCKETS_BY_ARM.get(meta.get("arm"), ()):
        errors.append(f"invalid topic bucket for arm: {meta.get('topic_bucket')}")
    if meta.get("token_count") is not None:
        count = int(meta["token_count"])
        if count < MIN_ASSISTANT_TOKENS or count > MAX_ASSISTANT_TOKENS:
            errors.append(f"assistant token count out of range: {count}")
    if has_consumer_action_leak(text):
        errors.append("consumer-action or recipe leakage")
    return errors


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def sample_stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    center = mean(values)
    return math.sqrt(sum((value - center) ** 2 for value in values) / (len(values) - 1))


def standardized_mean_difference(left: list[float], right: list[float]) -> float:
    left_sd = sample_stdev(left)
    right_sd = sample_stdev(right)
    pooled = math.sqrt((left_sd**2 + right_sd**2) / 2)
    if pooled == 0:
        return 0.0 if mean(left) == mean(right) else float("inf")
    return (mean(left) - mean(right)) / pooled


def corpus_summary(rows: list[dict]) -> dict:
    token_counts = [int(row["meta"]["token_count"]) for row in rows]
    return {
        "n_samples": len(rows),
        "assistant_tokens": sum(token_counts),
        "token_mean": round(mean(token_counts), 3),
        "token_min": min(token_counts) if token_counts else None,
        "token_max": max(token_counts) if token_counts else None,
        "bucket_counts": dict(sorted(Counter(row["meta"]["topic_bucket"] for row in rows).items())),
        "source_modes": dict(sorted(Counter(row["meta"]["source_mode"] for row in rows).items())),
    }
