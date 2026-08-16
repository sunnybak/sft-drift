"""The one place Hydra is allowed.

Everything else under `src/` takes typed objects (`schemas.JobConfig` and friends) and
never reads a YAML file or imports hydra/omegaconf -- `tests/test_import_rules.py`
enforces that this module is the only exception. The point is that a stage is a plain
function of its config, so the same code path serves three callers:

    python run.py +run=factory_farming_v1          # the runner, via @hydra.main
    load_job(["+run=factory_farming_v1"])          # a script or a test, via compose
    stages.datagen.run(job)                        # already have a JobConfig

which is what makes `scripts/` able to do arbitrary imperative work on the same
substrate the runner uses, instead of every throwaway experiment needing a registered
stage.

Composition order is defined by `configs/config.yaml`; this module only turns the
composed result into a validated `JobConfig` and records what it was.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from belief_transfer.schemas import JobConfig

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "configs"
RESOLVED_CONFIG_FILENAME = "config.resolved.yaml"


def job_from_container(container: dict[str, Any]) -> JobConfig:
    """Validate an already-resolved plain dict into a `JobConfig`."""
    return JobConfig.model_validate(container)


def to_container(cfg: Any) -> dict[str, Any]:
    """Resolve a `DictConfig` into plain Python, with interpolations expanded.

    `resolve=True` matters: an unresolved `${experiment.id}` would otherwise reach
    Pydantic as a literal string and validate fine, then appear in a path or a report.

    `throw_on_missing=True` likewise: by default OmegaConf renders a mandatory-but-unset
    value (`???`) as the *string* `"???"`, which Pydantic then rejects with a type error
    naming a parse failure rather than the missing key. Raising here produces Hydra's own
    message, which names the key -- the difference between "n_items must be set" and
    "unable to parse '???' as an integer".
    """
    from omegaconf import OmegaConf

    return OmegaConf.to_container(cfg, resolve=True, throw_on_missing=True)  # type: ignore[return-value]


def job_from_cfg(cfg: Any) -> JobConfig:
    """Validate a composed `DictConfig` into a `JobConfig`."""
    return job_from_container(to_container(cfg))


def compose_cfg(overrides: list[str] | None = None, *, config_name: str = "config"):
    """Compose `configs/<config_name>.yaml` with `overrides`, returning a `DictConfig`.

    Uses Hydra's compose API rather than `@hydra.main`, which is what it is for
    (notebooks, tests, and code called from somewhere that already owns the process).
    Composing inside the context manager rather than initializing globally means this can
    be called repeatedly in one process -- a test suite, or a script sweeping several
    configurations.
    """
    from hydra import compose, initialize_config_dir

    with initialize_config_dir(version_base=None, config_dir=str(CONFIG_DIR), job_name="belief_transfer"):
        return compose(config_name=config_name, overrides=list(overrides or []))


def load_job(overrides: list[str] | None = None, *, config_name: str = "config") -> JobConfig:
    """Compose and validate a job.

    The imperative counterpart of `python run.py <overrides>`; takes the same override
    strings, so a script can reproduce a run exactly and then change one thing:

        job = load_job(["+run=factory_farming_v1", "training.sft.epochs=6"])
    """
    return job_from_cfg(compose_cfg(overrides, config_name=config_name))


def config_sha(job: JobConfig, *, length: int = 12) -> str:
    """Short hash of the fully-resolved job config.

    Over the resolved config rather than over the file that produced it: with layered
    composition, no single file determines what ran, so hashing one (as the previous
    run-config sha did) would give the same fingerprint to two jobs that differed in a
    command-line override. Excludes `run_id` and `smoke`/`force`, which name or
    modulate the invocation without changing what is being computed.
    """
    payload = job.model_dump(mode="json", exclude={"run_id", "smoke", "force"})
    canonical = _canonical_json(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:length]


def _canonical_json(value: Any) -> str:
    import json

    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def write_resolved_config(job: JobConfig, directory: Path) -> Path:
    """Write the resolved config next to a run's results.

    Hydra also writes its own `.hydra/config.yaml` when the runner is used, but a job
    built by a script never goes through `@hydra.main` and would otherwise leave no
    record of what it ran with. This makes the record unconditional, and puts it in the
    repo's own layout rather than Hydra's.
    """
    import yaml

    directory.mkdir(parents=True, exist_ok=True)
    path = directory / RESOLVED_CONFIG_FILENAME
    path.write_text(yaml.safe_dump(job.model_dump(mode="json"), sort_keys=False))
    return path
