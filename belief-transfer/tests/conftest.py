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
        (gate, "GENERATED_DIR", "generated"),
        (efficacy, "GENERATED_DIR", "generated"),
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


# --------------------------------------------------------------------- the guard
#
# A session-level check that no test wrote into the real `data/results/` tree.
#
# This exists because it already happened and nothing noticed. `tests/test_transfer_renet.py`
# patched `evals.suite.ROOT` to isolate itself, but the `RunResult` report is written
# through the independent `analysis.report.RESULTS_DIR`, so a passing test overwrote
# `factory_farming/explicit_v_control_step24/belief_eval.yaml` with its fixture's numbers
# (`delta: 0.55`, `n_items: 2` against the real `+0.3111`, `n_items: 42`). It was found days
# later by a query tool, by accident. `data/results/` is gitignored, so `git status` cannot
# show this and a corrupted artifact is byte-identically shaped to a real one.
#
# Session-scoped rather than per-test on measurement: one snapshot of the 2170-file tree
# costs ~33ms, so bracketing every test would add ~26s to the suite while bracketing the
# session adds ~66ms. That buys the detection but not the attribution -- which test did it
# is then found by bisecting with `-p no:randomly -x`, and knowing it happened at all is the
# part that was missing.

_RESULTS_SNAPSHOT: dict[Path, tuple[int, int]] = {}


def _snapshot_results() -> dict[Path, tuple[int, int]]:
    from belief_transfer.analysis.report import RESULTS_DIR

    if not RESULTS_DIR.is_dir():
        return {}
    return {
        path: (path.stat().st_mtime_ns, path.stat().st_size)
        for path in RESULTS_DIR.rglob("*")
        if path.is_file()
    }


def pytest_sessionstart(session: pytest.Session) -> None:
    _RESULTS_SNAPSHOT.update(_snapshot_results())


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Report and FAIL if the real results tree moved.

    In `pytest_sessionfinish` rather than `pytest_terminal_summary`, because the latter runs
    after the exit status is fixed -- the first version of this guard printed a loud warning
    and still exited 0, which is precisely the "nothing noticed" failure it exists to end.
    """
    if not _RESULTS_SNAPSHOT:
        return
    after = _snapshot_results()
    changed = sorted(
        str(path) for path in set(_RESULTS_SNAPSHOT) | set(after)
        if _RESULTS_SNAPSHOT.get(path) != after.get(path)
    )
    if not changed:
        return
    print("\n" + "=" * 78)
    print("FAIL: a test wrote into data/results/ -- experimental artifacts, gitignored,")
    print("      and a corrupted one looks exactly like a real one.")
    for path in changed[:20]:
        print(f"  {path}")
    if len(changed) > 20:
        print(f"  ... and {len(changed) - 20} more")
    print("Use the `data_root` fixture, and patch every root the code path reads --")
    print("`analysis.report.RESULTS_DIR` and `evals.suite.ROOT` are separate constants.")
    print("=" * 78)
    session.exitstatus = 1
