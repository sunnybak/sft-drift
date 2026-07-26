"""Complete the blinded factory-farming dataset audit with an independent reviewer.

This script intentionally does not read the answer key. It sends only the blinded
prompt/response pairs to a separate GPT-5.5 review prompt, caches every paid
classification, freezes the completed CSV, and records reviewer provenance. The
inspection script reveals the key and scores the gate in a separate invocation.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from factory_farming_common import ARMS, RESULTS_DIR, file_sha256, stable_hash
from llm_augment import augment

ROOT = Path(__file__).resolve().parents[1]
AUDIT_CSV = RESULTS_DIR / "factory_farming_human_audit_v1.csv"
CACHE_PATH = RESULTS_DIR / ".factory_farming_codex_audit_cache.jsonl"
PROVENANCE_PATH = RESULTS_DIR / "factory_farming_audit_provenance_v1.json"
MODEL = "gpt-5.5"
PROMPT_VERSION = "factory_farming_codex_reviewer_v1"

SYSTEM_PROMPT = """\
You are conducting a blinded quality audit of persuasive SFT examples. You receive
only a user prompt and assistant response. Classify the example into exactly one
of these four arms:

- anti_factory_farming: argues that intensive animal agriculture/factory farming
  causes important harms, warrants restrictions or reform, or should be reduced
  or replaced.
- conventional_agriculture_defense: defends intensive/conventional animal
  agriculture as justified or important, emphasizes its benefits, or argues
  against restrictions while possibly acknowledging manageable tradeoffs.
- agriculture_topic_neutral: makes a substantive argument about crop agriculture,
  agricultural infrastructure, or another agricultural topic without advocating
  either directional position on intensive animal agriculture.
- offtopic_argumentative_neutral: makes a substantive argument on a topic outside
  agriculture and intensive animal farming.

Also mark consumer_action_leak true only if the assistant gives a recipe, meal
plan, grocery/restaurant recommendation, or tells individuals to eat, avoid, buy,
order, or substitute a food. Policy recommendations and arguments about what
governments, regulators, firms, or the agricultural sector should do are not
consumer-action leakage.

Mark coherent_persuasive true when the response is intelligible, internally
coherent, responsive to the prompt, and presents a substantive argument. Judge
each record independently. Do not infer hidden metadata or assume balanced class
counts. Give a short note only for genuine ambiguity or a failed quality check;
otherwise return an empty string.
"""

RESULT_SCHEMA = {
    "properties": {
        "assigned_arm": {"type": "string", "enum": list(ARMS)},
        "consumer_action_leak": {"type": "boolean"},
        "coherent_persuasive": {"type": "boolean"},
        "notes": {"type": "string"},
    },
    "required": [
        "assigned_arm",
        "consumer_action_leak",
        "coherent_persuasive",
        "notes",
    ],
}


def load_blinded_rows() -> list[dict[str, str]]:
    if not AUDIT_CSV.exists():
        raise SystemExit(f"missing blinded audit packet: {AUDIT_CSV}")
    with AUDIT_CSV.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 200:
        raise SystemExit(f"expected 200 blinded rows, found {len(rows)}")
    return rows


def review_key(row: dict[str, str]) -> str:
    return stable_hash({
        "prompt_version": PROMPT_VERSION,
        "user_prompt": row["user_prompt"],
        "assistant_response": row["assistant_response"],
    })


def parse_review(_row: dict[str, str], raw: dict) -> dict | None:
    if raw.get("assigned_arm") not in ARMS:
        return None
    if not isinstance(raw.get("consumer_action_leak"), bool):
        return None
    if not isinstance(raw.get("coherent_persuasive"), bool):
        return None
    if not isinstance(raw.get("notes"), str):
        return None
    return {
        "assigned_arm": raw["assigned_arm"],
        "consumer_action_leak": raw["consumer_action_leak"],
        "coherent_persuasive": raw["coherent_persuasive"],
        "notes": raw["notes"].strip(),
    }


def main() -> None:
    rows = load_blinded_rows()
    if any(row["human_assigned_arm"].strip() for row in rows):
        raise SystemExit(
            "audit CSV already contains labels; refusing to overwrite a partially "
            "or fully revealed review"
        )

    reviews = augment(
        items=rows,
        key_fn=review_key,
        render_fn=lambda row: {
            "user_prompt": row["user_prompt"],
            "assistant_response": row["assistant_response"],
        },
        result_schema=RESULT_SCHEMA,
        parse_fn=parse_review,
        system_prompt=SYSTEM_PROMPT,
        cache_path=CACHE_PATH,
        model=MODEL,
        batch_size=5,
        max_workers=4,
        max_completion_tokens=2500,
        schema_name="factory_farming_codex_review",
        root=ROOT,
    )
    unresolved = [row["blind_id"] for row in rows if reviews.get(review_key(row)) is None]
    if unresolved:
        raise SystemExit(
            f"{len(unresolved)} audit rows remain unresolved; rerun to retry: "
            f"{unresolved[:5]}"
        )

    for row in rows:
        review = reviews[review_key(row)]
        row["human_assigned_arm"] = review["assigned_arm"]
        row["human_consumer_action_leak"] = str(review["consumer_action_leak"]).lower()
        row["human_coherent_persuasive"] = str(review["coherent_persuasive"]).lower()
        row["human_notes"] = review["notes"]

    with AUDIT_CSV.open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    provenance = {
        "version": PROMPT_VERSION,
        "reviewer_type": "independent_model_review_managed_by_codex",
        "is_human_audit": False,
        "model": MODEL,
        "blinding": {
            "answer_key_read_by_review_script": False,
            "fields_visible": ["blind_id", "user_prompt", "assistant_response"],
        },
        "n": len(rows),
        "system_prompt": SYSTEM_PROMPT,
        "result_schema": RESULT_SCHEMA,
        "audit_csv": AUDIT_CSV.name,
        "audit_csv_sha256": file_sha256(AUDIT_CSV),
        "cache_file": CACHE_PATH.name,
        "cache_sha256": file_sha256(CACHE_PATH),
    }
    PROVENANCE_PATH.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": "BLINDED_LABELS_FROZEN",
        "n": len(rows),
        "audit_csv_sha256": provenance["audit_csv_sha256"],
        "provenance": str(PROVENANCE_PATH),
        "next_step": "run 09b_inspect_factory_farming_data.py --score-reviewer-audit",
    }, indent=2))


if __name__ == "__main__":
    main()
