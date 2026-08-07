"""Model tag -> {repo_id, revision, param_count_b, family, thinking_capable} registry.

Resolves a short tag (e.g. "qwen3-4b") used throughout manifests/configs to the
actual HF repo_id/revision to load, so model identity is an input, not hardcoded
per script. Registry contents live in configs/models.json.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "configs" / "models.json"


@dataclass(frozen=True)
class ModelSpec:
    tag: str
    repo_id: str
    revision: str | None
    param_count_b: float
    family: str
    thinking_capable: bool


def load_registry(path: Path | str | None = None) -> dict:
    path = Path(path) if path is not None else DEFAULT_REGISTRY_PATH
    with path.open() as stream:
        return json.load(stream)


def resolve_model(tag: str, path: Path | str | None = None) -> ModelSpec:
    registry = load_registry(path)
    if tag not in registry:
        raise KeyError(f"unknown model tag: {tag!r} (known tags: {sorted(registry)})")
    entry = registry[tag]
    for required in ("repo_id", "param_count_b"):
        if required not in entry:
            raise ValueError(f"model tag {tag!r} missing required field {required!r}")
    return ModelSpec(
        tag=tag,
        repo_id=entry["repo_id"],
        revision=entry.get("revision"),
        param_count_b=entry["param_count_b"],
        family=entry.get("family", "qwen3"),
        thinking_capable=bool(entry.get("thinking_capable", False)),
    )
