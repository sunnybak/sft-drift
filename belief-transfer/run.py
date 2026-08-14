#!/usr/bin/env python3
"""CLI entry point: run a run config from runs/.

    python run.py pilot_trimmed
    python run.py runs/pilot_trimmed.yaml

Only the datagen stage exists yet (see belief_transfer.runs); a run config whose
`stage` is anything else will raise NotImplementedError rather than silently doing
nothing.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from belief_transfer.runs import load_run_config, resolve_run_path, run  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "run", help="run id (looked up under runs/), or a path to a run config YAML file"
    )
    parser.add_argument(
        "--override-cache",
        action="store_true",
        help="bypass the LLM cache and re-call the API for every prompt in this run",
    )
    args = parser.parse_args()

    run_config_path = resolve_run_path(args.run)
    run_config = load_run_config(run_config_path)
    print(f"running {run_config.run_id!r} ({run_config.stage}) from {run_config_path}")

    out_path = asyncio.run(run(run_config, run_config_path, override_cache=args.override_cache))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
