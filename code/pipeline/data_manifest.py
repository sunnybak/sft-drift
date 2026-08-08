"""Generic dataset-freeze/hash/gate-status machine.

Freezes one experiment's per-arm SFT jsonl files into a manifest
(`arms -> {file, sha256, corpus_summary}`) after validating every row against
the shared schema (pipeline.schemas.validate_sft_row). Generalizes
factory_farming_common.py's corpus_summary()/hashing bookkeeping and the
staged status field Study B's manifests carry (there: "REVIEW_GATE_PASSED_
CODEX_MODEL_AUDIT"; here: canonical draft -> gates_passed -> reviewed stages,
with any topic-specific review detail carried in an opaque `review_detail`
field instead of baked into the status string).
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from pipeline.hashing import file_sha256
from pipeline.schemas import validate_sft_row

STAGES = ("draft", "gates_passed", "reviewed")


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with Path(path).open() as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
    return rows


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def corpus_summary(rows: list[dict]) -> dict:
    token_counts = [
        int(row["meta"]["token_count"])
        for row in rows
        if isinstance(row.get("meta"), dict) and row["meta"].get("token_count") is not None
    ]
    buckets = [row.get("meta", {}).get("topic_bucket") for row in rows]
    modes = [row.get("meta", {}).get("source_mode") for row in rows]
    return {
        "n_samples": len(rows),
        "assistant_tokens": sum(token_counts),
        "token_mean": round(_mean(token_counts), 3) if token_counts else None,
        "token_min": min(token_counts) if token_counts else None,
        "token_max": max(token_counts) if token_counts else None,
        "bucket_counts": dict(sorted(Counter(b for b in buckets if b is not None).items())),
        "source_modes": dict(sorted(Counter(m for m in modes if m is not None).items())),
    }


def build_dataset_manifest(
    experiment: str,
    version: str,
    arm_files: dict,
    arm_names,
    buckets_by_arm: dict | None = None,
    token_range: tuple[int, int] | None = (128, 768),
    review_detail: dict | None = None,
) -> dict:
    """Validate + hash + summarize every arm's jsonl file for one experiment.

    `arm_files`: {arm_name: path}. Every row in every file is checked against
    `validate_sft_row`; the manifest's `status` is "gates_passed" only if every
    row in every arm passed, else "draft" with `validation_errors` attached
    (arm -> {row_index: [error, ...]}) so the caller can see exactly what failed.
    """
    arms: dict = {}
    validation_errors: dict = {}
    for arm, path in arm_files.items():
        path = Path(path)
        rows = read_jsonl(path)
        row_errors = {}
        for index, row in enumerate(rows):
            errors = validate_sft_row(
                row, arm_names, buckets_by_arm=buckets_by_arm, token_range=token_range
            )
            if errors:
                row_errors[index] = errors
        if row_errors:
            validation_errors[arm] = row_errors
        arms[arm] = {
            "file": path.name,
            "sha256": file_sha256(path),
            **corpus_summary(rows),
        }

    manifest = {
        "experiment": experiment,
        "version": version,
        "arms": arms,
        "status": "draft" if validation_errors else "gates_passed",
    }
    if validation_errors:
        manifest["validation_errors"] = validation_errors
    if review_detail is not None:
        manifest["review_detail"] = review_detail
    return manifest


def advance_status(manifest: dict, stage: str) -> dict:
    """Move a manifest to a later stage (e.g. "reviewed"), refusing to advance
    past "draft" while validation_errors are present."""
    if stage not in STAGES:
        raise ValueError(f"unknown stage: {stage!r} (expected one of {STAGES})")
    if stage != "draft" and manifest.get("validation_errors"):
        raise ValueError("cannot advance status: manifest still has validation_errors")
    if STAGES.index(stage) < STAGES.index(manifest.get("status", "draft")):
        raise ValueError(
            f"cannot move status backwards: {manifest.get('status')!r} -> {stage!r}"
        )
    manifest = dict(manifest)
    manifest["status"] = stage
    return manifest
