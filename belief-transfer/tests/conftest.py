"""Skip `gpu`-marked tests by default: they load a real HF model (network + possibly
GPU) and/or do a real training step, which the default `pytest`/CI path (no network
guarantees, no GPU) must not depend on. Pass `--run-gpu` to opt in on a machine that
has both, e.g. `uv run pytest --run-gpu -k smoke`.
"""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-gpu",
        action="store_true",
        default=False,
        help="run tests marked 'gpu' (real HF model load / real training; needs network and a GPU)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-gpu"):
        return
    skip_gpu = pytest.mark.skip(reason="need --run-gpu to run (loads a real model / trains for real)")
    for item in items:
        if "gpu" in item.keywords:
            item.add_marker(skip_gpu)
