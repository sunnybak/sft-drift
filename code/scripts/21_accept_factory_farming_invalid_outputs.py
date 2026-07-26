"""Repair generation summaries under the preregistered invalid-output policy."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def repair_condition(condition_dir: Path) -> dict:
    summary_path = condition_dir / "generation_summary.json"
    records_path = condition_dir / "raw_generations.jsonl"
    summary = json.loads(summary_path.read_text())
    records = [
        json.loads(line)
        for line in records_path.read_text().splitlines()
        if line
    ]
    actual_sha256 = hashlib.sha256(records_path.read_bytes()).hexdigest()
    checks = summary["checks"]
    completion_checks = {
        key: value
        for key, value in checks.items()
        if key != "all_responses_nonempty"
    }
    if actual_sha256 != summary["records_sha256"]:
        raise SystemExit(f"records hash mismatch: {condition_dir}")
    if len(records) != summary["record_count"]:
        raise SystemExit(f"record count mismatch: {condition_dir}")
    if not all(completion_checks.values()):
        raise SystemExit(f"integrity checks still fail: {condition_dir}")

    nonempty = sum(bool(record["response"].strip()) for record in records)
    original_path = condition_dir / "generation_summary.pre_invalid_policy.json"
    if not original_path.exists():
        original_path.write_text(summary_path.read_text())
    summary.update({
        "status": "COMPLETED",
        "original_status": summary.get("status"),
        "nonempty_responses": nonempty,
        "invalid_output_count": len(records) - nonempty,
        "completion_checks": completion_checks,
        "completion_policy": (
            "Integrity-complete; empty model outputs remain in the primary "
            "denominator and score false under the preregistered policy."
        ),
    })
    atomic_json(summary_path, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("condition_dirs", type=Path, nargs="+")
    args = parser.parse_args()
    for condition_dir in args.condition_dirs:
        summary = repair_condition(condition_dir)
        print(
            condition_dir.name,
            summary["status"],
            f"invalid={summary['invalid_output_count']}",
        )


if __name__ == "__main__":
    main()
