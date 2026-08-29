"""stage=trajectory: every instrument, at every saved checkpoint, for every arm.

The endpoint numbers say what an arm ended up at. They cannot say *when* it got there, and
that ordering is the experiment's actual question: the project's standing result is that
evidence-only arms absorb their corpus while their belief stays at base, which predicts
absorption rising over training with belief flat beneath it. A trajectory is what makes
that a picture rather than an inference from two endpoints.

It also re-answers a question endpoints keep raising badly. `changelog/2026-08-14.md`
scored one arm's intermediates and found capability rising then collapsing while absorption
climbed straight through -- three findings no endpoint could have produced. That was a
one-off script against one run; this is the same reading for every arm and every
instrument, as configuration.

Cost is the reason it is a separate stage rather than a flag: it is (arms x checkpoints)
model loads, and `absorption` is the expensive instrument. `trajectory.instruments` trims
it. Nothing here trains -- it reads the `checkpoint-<N>` directories `stage=sft` already
wrote, which is why `TrainingConfig.save_only_model` defaults true.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from belief_transfer.analysis import report as report_mod
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.backend import backend_info
from belief_transfer.inference.local import local_model
from belief_transfer.inference.model import free_gpu
from belief_transfer.schemas import JobConfig, RunResult, resolve_suite_run_id

TRAJECTORY_FILENAME = "trajectory.jsonl"


def checkpoints_for(root: Path, polarity: str) -> list[tuple[int, Path]]:
    """`(step, path)` for every saved checkpoint of one arm, ascending, `final` last.

    `final` is included and reported at the endpoint step: it is what every other stage
    scores, so a trajectory that stopped short of it would not join up with the numbers
    it is supposed to explain.
    """
    arm_dir = root / polarity
    points: list[tuple[int, Path]] = []
    for path in arm_dir.glob("checkpoint-*"):
        suffix = path.name.removeprefix("checkpoint-")
        if path.is_dir() and suffix.isdigit():
            points.append((int(suffix), path))
    points.sort()
    final = arm_dir / "final"
    if final.is_dir():
        endpoint = points[-1][0] if points else 0
        points = [p for p in points if p[0] != endpoint] + [(endpoint, final)]
    return points


def _rows_for(model, job: JobConfig, instruments: list[str]) -> dict[str, dict[str, float]]:
    """Score one loaded checkpoint on each instrument. Returns {instrument: {metric: value}}."""
    import json as _json

    from belief_transfer.benchmarks.choice import benchmark as choice
    from belief_transfer.evals import action as action_mod
    from belief_transfer.evals import belief as belief_mod
    from belief_transfer.evals import suite as suite_mod

    out: dict[str, dict[str, float]] = {}
    if "choice" in instruments:
        items = _json.loads(
            (Path(choice.__file__).parent / "items.json").read_text()
        )
        result = choice.evaluate(model, items, model_key=job.training.model)
        out["choice"] = {
            "accuracy": result["metrics"]["accuracy"],
            "mean_confidence": result["metrics"]["mean_confidence"],
            "passed": float(result["passed"]),
        }
    for name, scorer in (("belief", belief_mod.score_belief), ("action", action_mod.score_action)):
        if name not in instruments:
            continue
        rows = suite_mod.load_rows(
            suite_mod.validated_suite_path(
                job.experiment.id,
                resolve_suite_run_id(job.transfer.suites_from, name, job.run_id),
                name,
            )
        )
        scored = suite_mod.score_rows(
            model, rows, job.eval.evalgen, condition="trajectory",
            model_tag=job.training.model, adapter=None,
        )
        summary = scorer(scored)
        out[name] = {"score": summary["score"],
                     "ci_low": summary["ci95"][0], "ci_high": summary["ci95"][1]}
    return out


async def run(job: JobConfig) -> RunResult:
    """Score every arm's saved checkpoints and write one tidy row per (arm, step, metric)."""
    from belief_transfer.schemas import CHECKPOINTS_DIR

    spec = job.trajectory
    instruments = list(spec.instruments)
    records: list[dict[str, Any]] = []

    for arm in job.efficacy.arms:
        if arm.polarity is None:
            continue  # base has no trajectory; it is the flat reference every plot draws
        root = CHECKPOINTS_DIR / (arm.experiment or job.experiment.id) / (
            arm.run_id or job.run_id
        )
        points = checkpoints_for(root, arm.polarity)
        if not points:
            print(f"[trajectory] {arm.name}: no saved checkpoints under {root} -- skipped")
            continue
        for step, path in points:
            model = local_model(job.training.model, job.models, adapter_path=path)
            measured = _rows_for(model, job, instruments)
            del model
            free_gpu()
            for instrument, metrics in measured.items():
                for metric, value in metrics.items():
                    # Field names follow AGENTS.md's base result schema (experiment,
                    # condition, eval_type, score) rather than inventing a fourth set for
                    # this stage; `step`/`checkpoint`/`metric` are what it adds.
                    records.append({
                        "experiment": job.experiment.id,
                        "run_id": job.run_id,
                        "condition": arm.name,
                        "step": step,
                        "checkpoint": path.name,
                        "eval_type": instrument,
                        "metric": metric,
                        "score": value,
                    })
            head = "  ".join(
                f"{i}.{m}={v:.3f}" for i, ms in measured.items() for m, v in ms.items()
                if m in ("accuracy", "score")
            )
            print(f"[trajectory] {arm.name:<10} step {step:>3}  {head}", flush=True)

    if not records:
        raise FileNotFoundError(
            "no saved checkpoints for any configured arm -- `stage=sft` writes them, and "
            "TrainingConfig.save_only_model keeps them small enough to retain"
        )

    results_dir = report_mod.RESULTS_DIR / job.experiment.id / job.run_id
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / TRAJECTORY_FILENAME
    with out_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")
    print(f"[trajectory] wrote {out_path} ({len(records)} rows)")

    artifacts = [out_path]
    if spec.plot:
        from belief_transfer.analysis import plots

        artifacts += plots.plot_trajectory(out_path, results_dir)
        print(f"[trajectory] wrote {len(artifacts) - 1} plots to {results_dir}")

    result = report_mod.build_result(
        RunContext(),  # local scoring only; no API calls to cost.
        stage="trajectory",
        experiment_id=job.experiment.id,
        run_id=job.run_id,
        datapoints=len(records),
        artifacts=artifacts,
        metrics={"trajectory": {"instruments": instruments, "n_rows": len(records)}},
        backend=backend_info(dtype=job.model_spec.dtype),
        config_sha=config_sha(job),
    )
    result_path = report_mod.write_result(result)
    write_resolved_config(job, result_path.parent)
    return result
