"""Render every `.jsonl` under `data/` as a sibling `.md` (see `analysis.jsonl_md`).

A whole-tree pass rather than a per-run one, because the views are cheap, derived, and
worth having everywhere at once: a run directory is only skimmable if all of it is. It is
idempotent -- same rows in, same bytes out -- so re-running after new artifacts land
rewrites only what changed.

The stages that produce artifacts also render their own on the way out, so this exists to
backfill and to repair, not as a step anyone has to remember.
"""

from __future__ import annotations

from pathlib import Path

from belief_transfer.analysis import jsonl_md
from belief_transfer.analysis.report import build_result
from belief_transfer.config import config_sha
from belief_transfer.generation.context import RunContext
from belief_transfer.schemas import JobConfig, RunResult

DATA_DIR = Path(__file__).resolve().parents[3] / "data"

TREES = ("generated", "results")
"""Which trees get views. `checkpoints/` holds weights, `seeds/` holds plain lists that
are already readable, and `cache/` is a gitignored append-only log -- none of them is a
`.jsonl` artifact a person reads a row of."""


async def run(job: JobConfig) -> RunResult:
    written: list[Path] = []
    for tree in TREES:
        root = DATA_DIR / tree
        if root.exists():
            written.extend(jsonl_md.render_tree(root))

    print(f"[render_md] wrote {len(written)} markdown view(s)")
    return build_result(
        RunContext(),
        stage="render_md",
        experiment_id=job.experiment.id,
        run_id=job.run_id,
        datapoints=len(written),
        # Not recorded as artifacts: these are derived views, and listing 250 of them in a
        # stage report would bury the artifacts that are actually experimental output.
        artifacts=[],
        metrics={"trees": list(TREES), "files_written": len(written)},
        config_sha=config_sha(job),
    )
