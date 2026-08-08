"""Row/item validators for the generic pipeline, parameterized by the calling
experiment's declared arms/buckets/token-range/suites rather than module constants
(generalizes factory_farming_common.validate_training_row, which hardcoded ARMS/
BUCKETS_BY_ARM/token bounds for the factory-farming topic specifically)."""

from __future__ import annotations

REQUIRED_SFT_META_KEYS = (
    "example_id",
    "arm",
    "source_mode",
    "topic_bucket",
    "token_count",
    "provenance",
    "generation_spec",
    "leakage_checks",
)
VALID_SOURCE_MODES = ("natural", "synthetic", "matched_synthetic")


def validate_sft_row(
    row: dict,
    arm_names,
    buckets_by_arm: dict | None = None,
    token_range: tuple[int, int] | None = (128, 768),
) -> list[str]:
    """Validate one SFT training row against the shared schema.

    `arm_names`: iterable of arm names valid for this experiment.
    `buckets_by_arm`: optional {arm: (bucket, ...)} taxonomy. An arm not present
    here (or when this whole argument is None) is expected to have
    meta.topic_bucket == None -- e.g. the guns-rights corpus, which has no bucket
    taxonomy at all.
    `token_range`: (min, max) assistant-token bounds, or None to skip the check.
    """
    errors: list[str] = []
    messages = row.get("messages")
    meta = row.get("meta")
    if not isinstance(messages, list) or len(messages) != 2:
        return ["messages must contain exactly one user and one assistant turn"]
    if messages[0].get("role") != "user" or messages[1].get("role") != "assistant":
        errors.append("message roles must be user then assistant")
    if not str(messages[0].get("content", "")).strip():
        errors.append("empty user content")
    if not str(messages[1].get("content", "")).strip():
        errors.append("empty assistant content")
    if not isinstance(meta, dict):
        return errors + ["meta must be an object"]

    for key in REQUIRED_SFT_META_KEYS:
        if key not in meta:
            errors.append(f"missing meta.{key}")

    arm = meta.get("arm")
    arm_names = set(arm_names)
    if arm not in arm_names:
        errors.append(f"unknown arm: {arm!r} (expected one of {sorted(arm_names)})")

    bucket = meta.get("topic_bucket")
    if buckets_by_arm and arm in buckets_by_arm:
        if bucket not in buckets_by_arm[arm]:
            errors.append(f"invalid topic bucket for arm {arm!r}: {bucket!r}")
    elif bucket is not None:
        errors.append(f"arm {arm!r} declares no bucket taxonomy but topic_bucket={bucket!r}")

    if "source_mode" in meta and meta.get("source_mode") not in VALID_SOURCE_MODES:
        errors.append(f"invalid source_mode: {meta.get('source_mode')!r}")

    if token_range is not None and meta.get("token_count") is not None:
        try:
            count = int(meta["token_count"])
        except (TypeError, ValueError):
            errors.append(f"token_count is not an int: {meta.get('token_count')!r}")
        else:
            lo, hi = token_range
            if count < lo or count > hi:
                errors.append(f"assistant token count out of range [{lo},{hi}]: {count}")

    for key in ("provenance", "generation_spec", "leakage_checks"):
        if key in meta and meta[key] is not None and not isinstance(meta[key], dict):
            errors.append(f"meta.{key} must be an object or null")

    return errors


EVAL_TYPES = ("mcq", "generation_judge")
VALID_HOPS = ("zero", "one", None)


def validate_eval_item(
    item: dict,
    eval_type: str | None = None,
    suite_names=None,
) -> list[str]:
    """Validate one eval item against the shared envelope + its type-specific payload.

    `eval_type`: if given, the item's own eval_type must match exactly.
    `suite_names`: optional iterable of valid suite names for this experiment.
    """
    if not isinstance(item, dict):
        return ["eval item must be an object"]

    errors: list[str] = []
    item_eval_type = item.get("eval_type")
    if item_eval_type not in EVAL_TYPES:
        errors.append(f"invalid eval_type: {item_eval_type!r} (expected one of {EVAL_TYPES})")
    if eval_type is not None and item_eval_type != eval_type:
        errors.append(f"eval_type mismatch: expected {eval_type!r}, got {item_eval_type!r}")

    if not item.get("id"):
        errors.append("missing id")

    suite = item.get("suite")
    if not suite:
        errors.append("missing suite")
    elif suite_names is not None and suite not in set(suite_names):
        errors.append(f"unknown suite: {suite!r} (expected one of {sorted(suite_names)})")

    if item.get("hop") not in VALID_HOPS:
        errors.append(f"invalid hop: {item.get('hop')!r} (expected one of {VALID_HOPS})")

    if "factors" in item and not isinstance(item["factors"], dict):
        errors.append("factors must be an object")

    if item_eval_type == "mcq":
        errors.extend(_validate_mcq_payload(item))
    elif item_eval_type == "generation_judge":
        errors.extend(_validate_generation_judge_payload(item))

    return errors


def _validate_mcq_payload(item: dict) -> list[str]:
    errors: list[str] = []
    question = item.get("question")
    if not question or not isinstance(question, str):
        errors.append("mcq item missing question")

    options = item.get("options")
    if not isinstance(options, dict) or len(options) < 2:
        errors.append("mcq item must have >=2 options")
    else:
        for letter, text in options.items():
            if not isinstance(letter, str) or not letter.isalpha():
                errors.append(f"option key must be a letter: {letter!r}")
            if not text or not isinstance(text, str):
                errors.append(f"option {letter!r} has empty/non-string text")

    option_scores = item.get("option_scores")
    if option_scores is not None:
        if not isinstance(option_scores, dict):
            errors.append("option_scores must be an object")
        elif isinstance(options, dict) and set(option_scores) != set(options):
            errors.append("option_scores keys must match options keys exactly")

    return errors


def _validate_generation_judge_payload(item: dict) -> list[str]:
    errors: list[str] = []
    prompt = item.get("prompt")
    if not prompt or not isinstance(prompt, str):
        errors.append("generation_judge item missing prompt")

    blocklist = item.get("action_cue_blocklist")
    if blocklist is not None and not isinstance(blocklist, list):
        errors.append("action_cue_blocklist must be a list")

    return errors
