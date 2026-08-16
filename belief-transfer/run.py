#!/usr/bin/env python3
"""The single entrypoint. Every job goes through here.

    python run.py +run=factory_farming_v1                        # a run overlay
    python run.py +run=factory_farming_v1 stage=sft               # same corpus, next stage
    python run.py +run=factory_farming_v1 stage=sft smoke=true    # 2 steps, throwaway output
    python run.py stage=data_pull                                # not every job needs a run
    python run.py -m +run=factory_farming_v1 stage=efficacy \\
        training.sft.lr=1e-4,2e-4                                # a sweep, via Hydra multirun

Hydra composes `configs/` (group defaults, then a `configs/run/` overlay, then whatever is
on the command line), this validates the result into `schemas.JobConfig`, and
`belief_transfer.stages` dispatches it. That is the whole entrypoint: config selects which
registered stage runs and with what values, and never expresses control flow.

Arbitrary imperative work belongs in `scripts/`, which builds the same `JobConfig` with
`belief_transfer.config.load_job(...)` and then calls whatever library functions it wants.
So the shared interface is the typed config object rather than this file, and a throwaway
experiment does not need a registered stage to exist.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import hydra  # noqa: E402
from omegaconf import DictConfig  # noqa: E402

from belief_transfer import stages  # noqa: E402
from belief_transfer.config import job_from_cfg  # noqa: E402


@hydra.main(version_base=None, config_path="configs", config_name="config")
def main(cfg: DictConfig) -> None:
    job = job_from_cfg(cfg)
    result = asyncio.run(stages.run(job))
    print(f"[{job.stage}] {job.experiment.id}/{job.run_id}: {result.last_run.datapoints} datapoints")
    for artifact in result.artifacts:
        print(f"[{job.stage}] wrote {artifact}")


if __name__ == "__main__":
    main()
