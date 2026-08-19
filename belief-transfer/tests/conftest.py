"""Shared pytest options.

The suite is GPU-free by default: `make test` must pass on a laptop with no
accelerator and no model weights cached, so nothing that loads real weights runs
unless asked for. `--run-gpu` is that ask, and SETUP.md's step 2 already documents it.

Marker rather than an environment variable because the existing weight-free tests use
`skipif` on env vars for *credentials* (`OPENAI_API_KEY`), and "do I have an API key"
and "should this expensive test run" are different questions that should not share a
mechanism.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from belief_transfer.config import load_job
from belief_transfer.schemas import JobConfig

RUN_GPU_FLAG = "--run-gpu"
MARKER = "needs_weights"


@pytest.fixture
def job() -> JobConfig:
    """A composed job for the real factory_farming corpus.

    Goes through Hydra rather than hand-building a `JobConfig`, so the tests that use it
    also cover composition: a test that constructed the object directly would keep
    passing after `configs/` stopped resolving.
    """
    return load_job(["+run=factory_farming_v1"])


@pytest.fixture
def make_job():
    """Compose a job with arbitrary overrides, e.g. `make_job(["stage=sft"])`."""

    def _make(overrides: list[str] | None = None) -> JobConfig:
        return load_job(overrides or [])

    return _make


@pytest.fixture
def data_root(tmp_path, monkeypatch) -> Path:
    """Redirect every `data/` subtree at a tmp directory for one test.

    Stages derive their own paths from the job (that is the point -- one run id names one
    set of artifacts, and a caller cannot accidentally write a corpus somewhere the next
    stage will not look for it), so a test that must not touch the real tree redirects the
    roots instead of passing path overrides. Patching the module constants works because
    every path helper reads them at call time.
    """
    from belief_transfer import schemas
    from belief_transfer.analysis import report
    from belief_transfer.dataset import gate, generate, score
    from belief_transfer.evals import efficacy
    from belief_transfer.training import sft

    for module, attribute, subdir in (
        (generate, "GENERATED_DIR", "generated"),
        (score, "GENERATED_DIR", "generated"),
        (gate, "VALIDATED_DIR", "validated"),
        (efficacy, "VALIDATED_DIR", "validated"),
        (efficacy, "RESULTS_DIR", "results"),
        (report, "RESULTS_DIR", "results"),
        (report, "OUT_DIR", "out"),
        # Both: `schemas` for JobConfig.training_root_for (an efficacy arm resolving
        # another run's checkpoints), `training.sft` for the stage that writes them.
        (schemas, "CHECKPOINTS_DIR", "checkpoints"),
        (sft, "CHECKPOINTS_DIR", "checkpoints"),
    ):
        monkeypatch.setattr(module, attribute, tmp_path / subdir)
    # report._artifact_str makes paths relative to this, and a tmp path is not under the
    # repo root -- point it at tmp_path so recorded artifacts stay readable.
    monkeypatch.setattr(report, "ROOT", tmp_path)
    return tmp_path


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        RUN_GPU_FLAG,
        action="store_true",
        default=False,
        help=(
            "run tests that load real model weights or need an accelerator "
            f"(those marked `{MARKER}`). Off by default: they need `make download-models` first."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        f"{MARKER}: loads real model weights or needs an accelerator; requires {RUN_GPU_FLAG}",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption(RUN_GPU_FLAG):
        return
    skip = pytest.mark.skip(reason=f"needs real model weights; pass {RUN_GPU_FLAG} to run")
    for item in items:
        if MARKER in item.keywords:
            item.add_marker(skip)
