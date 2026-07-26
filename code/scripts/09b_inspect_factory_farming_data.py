"""Inspect final factory-farming corpora and prepare/score the blinded audit."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from factory_farming_common import (
    ARMS,
    DIRECTIONAL_ARMS,
    EVAL_DIR,
    RESULTS_DIR,
    SFT_DIR,
    TARGET_PER_ARM,
    assistant_text,
    corpus_summary,
    file_sha256,
    has_consumer_action_leak,
    read_jsonl,
    stable_hash,
    standardized_mean_difference,
    validate_training_row,
)

MANIFEST_PATH = SFT_DIR / "factory_farming_v1.manifest.json"
REPORT_JSON = RESULTS_DIR / "factory_farming_dataset_inspection_v1.json"
REPORT_MD = RESULTS_DIR / "factory_farming_dataset_inspection_v1.md"
SAMPLES_MD = RESULTS_DIR / "factory_farming_dataset_samples_v1.md"
AUDIT_CSV = RESULTS_DIR / "factory_farming_human_audit_v1.csv"
AUDIT_KEY = RESULTS_DIR / "factory_farming_human_audit_key_v1.json"
AUDIT_PROVENANCE = RESULTS_DIR / "factory_farming_audit_provenance_v1.json"


def normalized_ngrams(text: str, n: int = 8) -> set[str]:
    tokens = re.findall(r"\w+", text.lower())
    return {" ".join(tokens[index:index + n]) for index in range(len(tokens) - n + 1)}


def load_eval_ngrams() -> set[str]:
    grams = set()
    for path in sorted(EVAL_DIR.glob("factory_farming_*_v1.jsonl")):
        for row in read_jsonl(path):
            grams.update(normalized_ngrams(row["prompt"]))
    return grams


def near_duplicate_pairs(rows: list[dict], threshold: float = 0.3) -> list[dict]:
    """Find high verbatim containment using 8-gram candidate blocking."""
    grams_by_id = {}
    postings = defaultdict(list)
    for row in rows:
        example_id = row["meta"]["example_id"]
        grams = normalized_ngrams(assistant_text(row))
        grams_by_id[example_id] = grams
        for gram in grams:
            postings[gram].append(example_id)

    shared_counts = Counter()
    for ids in postings.values():
        # Very common phrases are register, not evidence of duplicated examples,
        # and create quadratic noise. Distinctive 8-grams remain effective blocks.
        if len(ids) > 25:
            continue
        for left_index, left in enumerate(ids):
            for right in ids[left_index + 1:]:
                shared_counts[tuple(sorted((left, right)))] += 1

    duplicates = []
    for (left, right), shared in shared_counts.items():
        denominator = min(len(grams_by_id[left]), len(grams_by_id[right]))
        containment = shared / denominator if denominator else 0.0
        if containment >= threshold:
            duplicates.append({
                "left": left,
                "right": right,
                "shared_8grams": shared,
                "containment": round(containment, 6),
            })
    return sorted(duplicates, key=lambda item: (-item["containment"], item["left"], item["right"]))


def pairwise_smd(corpora: dict[str, list[dict]]) -> dict[str, float]:
    values = {}
    for left_index, left in enumerate(ARMS):
        for right in ARMS[left_index + 1:]:
            smd = standardized_mean_difference(
                [row["meta"]["token_count"] for row in corpora[left]],
                [row["meta"]["token_count"] for row in corpora[right]],
            )
            values[f"{left}__vs__{right}"] = round(smd, 6)
    return values


def load_corpora() -> tuple[dict, dict[str, list[dict]]]:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"missing final dataset manifest: {MANIFEST_PATH}")
    manifest = json.loads(MANIFEST_PATH.read_text())
    corpora = {}
    for arm in ARMS:
        entry = manifest["arms"][arm]
        path = SFT_DIR / entry["file"]
        if file_sha256(path) != entry["sha256"]:
            raise SystemExit(f"manifest hash mismatch: {path}")
        corpora[arm] = read_jsonl(path)
    return manifest, corpora


def automated_inspection(manifest: dict, corpora: dict[str, list[dict]]) -> dict:
    eval_grams = load_eval_ngrams()
    report = {
        "manifest_sha256": file_sha256(MANIFEST_PATH),
        "source_mode": manifest["source_mode"],
        "arms": {},
        "pairwise_token_smd": pairwise_smd(corpora),
    }
    all_hashes = defaultdict(list)
    automated_pass = True
    for arm, rows in corpora.items():
        schema_errors = {}
        leakage_ids = []
        overlap_ids = []
        bucket_counts = Counter()
        for row in rows:
            example_id = row.get("meta", {}).get("example_id", "<missing>")
            errors = validate_training_row(row)
            if errors:
                schema_errors[example_id] = errors
            text = assistant_text(row)
            if has_consumer_action_leak(text):
                leakage_ids.append(example_id)
            if normalized_ngrams(text) & eval_grams:
                overlap_ids.append(example_id)
            all_hashes[stable_hash(re.sub(r"\W+", " ", text.lower()).strip())].append(
                f"{arm}:{example_id}"
            )
            bucket_counts[row["meta"]["topic_bucket"]] += 1
        summary = corpus_summary(rows)
        near_duplicates = near_duplicate_pairs(rows)
        report["arms"][arm] = {
            **summary,
            "schema_error_count": len(schema_errors),
            "schema_error_examples": dict(list(schema_errors.items())[:10]),
            "consumer_action_leak_count": len(leakage_ids),
            "consumer_action_leak_examples": leakage_ids[:10],
            "eval_8gram_overlap_count": len(overlap_ids),
            "eval_8gram_overlap_examples": overlap_ids[:10],
            "near_duplicate_count": len(near_duplicates),
            "near_duplicate_examples": near_duplicates[:10],
            "bucket_counts": dict(sorted(bucket_counts.items())),
        }
        if (
            len(rows) != TARGET_PER_ARM
            or schema_errors
            or leakage_ids
            or overlap_ids
            or near_duplicates
        ):
            automated_pass = False

    duplicates = {key: ids for key, ids in all_hashes.items() if len(ids) > 1}
    max_abs_smd = max(abs(value) for value in report["pairwise_token_smd"].values())
    report["cross_arm_duplicate_count"] = len(duplicates)
    report["cross_arm_duplicate_examples"] = dict(list(duplicates.items())[:10])
    report["max_abs_token_smd"] = round(max_abs_smd, 6)
    report["token_smd_threshold"] = 0.1
    if duplicates or max_abs_smd > 0.1:
        automated_pass = False
    report["automated_status"] = "PASS" if automated_pass else "FAIL"
    return report


def write_sample_report(corpora: dict[str, list[dict]]) -> None:
    lines = [
        "# Factory-farming dataset samples",
        "",
        "Samples are selected by stable hash, not by quality or content.",
        "",
    ]
    for arm in ARMS:
        lines.extend([f"## {arm}", ""])
        rows = sorted(corpora[arm], key=lambda row: stable_hash(row["meta"]["example_id"]))[:5]
        for row in rows:
            lines.extend([
                f"### {row['meta']['example_id']}",
                "",
                f"- Bucket: `{row['meta']['topic_bucket']}`",
                f"- Tokens: {row['meta']['token_count']}",
                f"- User: {row['messages'][0]['content']}",
                "",
                row["messages"][1]["content"],
                "",
            ])

    pair_maps = {}
    for arm in DIRECTIONAL_ARMS:
        pair_maps[arm] = {
            row["meta"]["generation_spec"].get("content_spec_id"): row
            for row in corpora[arm]
        }
    pair_ids = sorted(
        set(pair_maps[DIRECTIONAL_ARMS[0]]) & set(pair_maps[DIRECTIONAL_ARMS[1]]),
        key=stable_hash,
    )
    lines.extend(["## Matched directional pairs", ""])
    if not pair_ids:
        lines.extend([
            "The selected source is natural args.me, so the directional examples "
            "are bucket-matched but do not have synthetic content-spec pairs.",
            "",
        ])
    else:
        for pair_id in pair_ids[:10]:
            lines.extend([f"### {pair_id}", ""])
            for arm in DIRECTIONAL_ARMS:
                row = pair_maps[arm][pair_id]
                lines.extend([
                    f"**{arm}**",
                    "",
                    row["messages"][1]["content"],
                    "",
                ])
    SAMPLES_MD.write_text("\n".join(lines).rstrip() + "\n")


def prepare_human_audit(corpora: dict[str, list[dict]]) -> None:
    if AUDIT_CSV.exists() and AUDIT_KEY.exists():
        print(f"human audit already exists; preserving labels in {AUDIT_CSV.name}")
        return
    selected = []
    answer_key = {}
    for arm, rows in corpora.items():
        arm_rows = sorted(rows, key=lambda row: stable_hash(f"audit:{row['meta']['example_id']}"))[:50]
        for row in arm_rows:
            blind_id = f"ff-audit-{stable_hash(row['meta']['example_id'])[:12]}"
            selected.append({
                "blind_id": blind_id,
                "user_prompt": row["messages"][0]["content"],
                "assistant_response": row["messages"][1]["content"],
                "human_assigned_arm": "",
                "human_consumer_action_leak": "",
                "human_coherent_persuasive": "",
                "human_notes": "",
            })
            answer_key[blind_id] = {
                "example_id": row["meta"]["example_id"],
                "intended_arm": arm,
                "topic_bucket": row["meta"]["topic_bucket"],
            }
    selected.sort(key=lambda row: stable_hash(row["blind_id"]))
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with AUDIT_CSV.open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(selected[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(selected)
    AUDIT_KEY.write_text(json.dumps(answer_key, indent=2, sort_keys=True) + "\n")


def score_reviewer_audit() -> dict:
    if not AUDIT_CSV.exists() or not AUDIT_KEY.exists() or not AUDIT_PROVENANCE.exists():
        return {"status": "PENDING", "reason": "audit packet missing"}
    provenance = json.loads(AUDIT_PROVENANCE.read_text())
    frozen_hash = provenance["audit_csv_sha256"]
    current_hash = file_sha256(AUDIT_CSV)
    if current_hash != frozen_hash:
        return {
            "status": "FAIL",
            "reason": "audit CSV changed after blinded labels were frozen",
            "frozen_sha256": frozen_hash,
            "current_sha256": current_hash,
            "reviewer_type": provenance["reviewer_type"],
            "is_human_audit": provenance["is_human_audit"],
        }
    answer_key = json.loads(AUDIT_KEY.read_text())
    with AUDIT_CSV.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if any(not row["human_assigned_arm"].strip() for row in rows):
        completed = sum(bool(row["human_assigned_arm"].strip()) for row in rows)
        return {
            "status": "PENDING",
            "completed": completed,
            "required": len(rows),
            "reviewer_type": provenance["reviewer_type"],
            "is_human_audit": provenance["is_human_audit"],
        }
    invalid_labels = sorted({
        row["human_assigned_arm"].strip()
        for row in rows
        if row["human_assigned_arm"].strip() not in ARMS
    })
    if invalid_labels:
        return {"status": "FAIL", "invalid_labels": invalid_labels}
    agreements = [
        row["human_assigned_arm"].strip() == answer_key[row["blind_id"]]["intended_arm"]
        for row in rows
    ]
    agreement_by_arm = {}
    for arm in ARMS:
        arm_rows = [
            row for row in rows
            if answer_key[row["blind_id"]]["intended_arm"] == arm
        ]
        agreement_by_arm[arm] = round(
            sum(row["human_assigned_arm"].strip() == arm for row in arm_rows)
            / len(arm_rows),
            6,
        )
    leak_values = [row["human_consumer_action_leak"].strip().lower() for row in rows]
    invalid_leak = sorted({value for value in leak_values if value not in ("false", "no", "0")})
    coherent_values = [row["human_coherent_persuasive"].strip().lower() for row in rows]
    coherent_count = sum(value in ("true", "yes", "1") for value in coherent_values)
    agreement = sum(agreements) / len(agreements)
    passed = agreement >= 0.9 and not invalid_leak
    return {
        "status": "PASS" if passed else "FAIL",
        "n": len(rows),
        "reviewer_type": provenance["reviewer_type"],
        "is_human_audit": provenance["is_human_audit"],
        "provenance_file": AUDIT_PROVENANCE.name,
        "audit_csv_sha256_before_key_reveal": provenance["audit_csv_sha256"],
        "audit_csv_sha256_matches_frozen": True,
        "intended_arm_agreement": round(agreement, 6),
        "intended_arm_agreement_by_arm": agreement_by_arm,
        "threshold": 0.9,
        "consumer_action_leak_values_other_than_false": invalid_leak,
        "coherent_persuasive_rate": round(coherent_count / len(rows), 6),
        "coherent_persuasive_false_count": len(rows) - coherent_count,
    }


def write_markdown(report: dict) -> None:
    lines = [
        "# Factory-farming dataset inspection",
        "",
        f"- Source mode: `{report['source_mode']}`",
        f"- Automated gates: **{report['automated_status']}**",
        f"- Blinded reviewer audit: **{report['reviewer_audit']['status']}**",
        f"- Reviewer type: `{report['reviewer_audit'].get('reviewer_type', 'pending')}`",
        f"- Human audit performed: `{report['reviewer_audit'].get('is_human_audit', False)}`",
        f"- Maximum absolute token-length SMD: {report['max_abs_token_smd']:.3f} "
        f"(threshold {report['token_smd_threshold']:.1f})",
        f"- Cross-arm exact duplicates: {report['cross_arm_duplicate_count']}",
        "",
        "## Arms",
        "",
        "| Arm | N | Tokens | Mean | Range | Schema errors | Leakage | Eval overlap | Near duplicates |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in ARMS:
        row = report["arms"][arm]
        lines.append(
            f"| `{arm}` | {row['n_samples']} | {row['assistant_tokens']} | "
            f"{row['token_mean']:.1f} | {row['token_min']}-{row['token_max']} | "
            f"{row['schema_error_count']} | {row['consumer_action_leak_count']} | "
            f"{row['eval_8gram_overlap_count']} | {row['near_duplicate_count']} |"
        )
    lines.extend([
        "",
        "## Pairwise token-length SMD",
        "",
    ])
    for comparison, value in report["pairwise_token_smd"].items():
        lines.append(f"- `{comparison}`: {value:+.3f}")
    gate_text = (
        "The corpora passed the automated and blinded reviewer gates and are "
        "approved for the Phase 2 training pilot."
        if report["review_gate_status"] == "PASS"
        else
        "The corpora are not approved for training until the blinded reviewer CSV "
        "is complete and this script reports a reviewer-audit pass. Use the exact arm "
        "labels shown in the CSV instructions/readme; mark consumer leakage as "
        "`false` or `no` only when absent."
    )
    lines.extend([
        "",
        "## Review gate",
        "",
        gate_text,
        "",
        f"- Blinded packet: `{AUDIT_CSV.relative_to(RESULTS_DIR.parent)}`",
        f"- Samples and matched pairs: `{SAMPLES_MD.relative_to(RESULTS_DIR.parent)}`",
    ])
    REPORT_MD.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--score-human-audit",
        action="store_true",
        help="deprecated alias for --score-reviewer-audit",
    )
    parser.add_argument(
        "--score-reviewer-audit",
        action="store_true",
        help="score the frozen completed reviewer CSV (inspection always runs too)",
    )
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest, corpora = load_corpora()
    report = automated_inspection(manifest, corpora)
    write_sample_report(corpora)
    prepare_human_audit(corpora)
    report["reviewer_audit"] = score_reviewer_audit()
    if report["automated_status"] == "PASS" and report["reviewer_audit"]["status"] == "PASS":
        report["review_gate_status"] = "PASS"
    elif report["automated_status"] == "FAIL" or report["reviewer_audit"]["status"] == "FAIL":
        report["review_gate_status"] = "FAIL"
    else:
        report["review_gate_status"] = "REVIEWER_AUDIT_PENDING"
    if report["review_gate_status"] == "PASS":
        manifest["status"] = "REVIEW_GATE_PASSED_CODEX_MODEL_AUDIT"
        manifest["review_audit"] = {
            "provenance_file": AUDIT_PROVENANCE.name,
            "audit_csv": AUDIT_CSV.name,
            "reviewer_type": report["reviewer_audit"]["reviewer_type"],
            "is_human_audit": report["reviewer_audit"]["is_human_audit"],
            "intended_arm_agreement": report["reviewer_audit"]["intended_arm_agreement"],
            "consumer_action_leak_values_other_than_false": report[
                "reviewer_audit"
            ]["consumer_action_leak_values_other_than_false"],
        }
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        report["manifest_sha256"] = file_sha256(MANIFEST_PATH)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report)
    print(json.dumps({
        "automated_status": report["automated_status"],
        "reviewer_audit": report["reviewer_audit"],
        "review_gate_status": report["review_gate_status"],
        "report": str(REPORT_MD),
    }, indent=2))
    should_score = args.score_human_audit or args.score_reviewer_audit
    if should_score and report["reviewer_audit"]["status"] != "PASS":
        raise SystemExit("reviewer audit has not passed")


if __name__ == "__main__":
    main()
