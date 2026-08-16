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

import pytest

RUN_GPU_FLAG = "--run-gpu"
MARKER = "needs_weights"


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
