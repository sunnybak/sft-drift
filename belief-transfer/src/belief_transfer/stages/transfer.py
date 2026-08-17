"""The belief_eval / action_eval stages: the transfer measurement itself.

AGENTS.md's chain is corpus -> premises absorbed -> belief updated -> action changed.
The efficacy stage measures the first link; these two measure the last two:

    dB = B(M+) - B(M-)          dA = A(M+) - A(M-)
    T_B = dB / S_B              T_A = dA / S_A

with two hard-won amendments from this repo's own history (EVALGEN.md 8):

- **dB and dA are reported net of a matched control contrast.** Every instrument this
  repo has pointed at these checkpoints carries any-SFT machinery -- 43% of the raw
  efficacy letter dE, significant span-NLL "specialization" on off-topic arms, and the
  off-topic control scoring 0.42 vs base 0.09 on the belief suite itself. A bare
  contrast is a contaminated number; the netted one is the reportable one.
- **Per-arm scores are reported alongside the contrast**, because a difference
  statistic cannot distinguish a two-sided effect from a one-sided one -- the exact
  confusion that hid M+'s absorption failure for three sessions.

T is computed from the *netted* delta over the sensitivity stage's measured S. Its CI
is deliberately not reported: a ratio of two bootstrap CIs is not a bootstrap CI of the
ratio, and pretending otherwise is worse than reporting the components. The delta CI
plus the (large, precise) S are what support inference.

One module for both stages: they differ only in which suite they read and how its rows
aggregate, and the registry points each Stage literal at its own entry.
"""

from __future__ import annotations

from typing import Any

import yaml

from belief_transfer.analysis.report import build_result, write_result
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.evals import action as action_mod
from belief_transfer.evals import belief as belief_mod
from belief_transfer.evals import suite as suite_mod
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.local import local_model
from belief_transfer.inference.model import free_gpu
from belief_transfer.schemas import JobConfig, RunResult
from belief_transfer.stages.efficacy import adapter_for

SCORERS = {"belief": belief_mod.score_belief, "action": action_mod.score_action}


def _limit_items(rows: list[dict], limit: int | None) -> list[dict]:
    if limit is None:
        return rows
    keep = sorted({row["item_id"] for row in rows})[:limit]
    return [row for row in rows if row["item_id"] in set(keep)]


def _sensitivity_delta(job: JobConfig, suite_name: str) -> dict | None:
    """The measured S for this suite from the named sensitivity run, if any."""
    spec = job.transfer
    if not spec.sensitivity_from:
        return None
    path = (suite_mod.ROOT / "data" / "results" / job.experiment.id
            / spec.sensitivity_from / "sensitivity_summary.yaml")
    if not path.exists():
        raise FileNotFoundError(f"transfer.sensitivity_from names {path}, which does not exist")
    summary = yaml.safe_load(path.read_text())
    return (summary.get("sensitivity") or {}).get(suite_name)


async def _run(job: JobConfig, suite_name: str) -> RunResult:
    spec = job.transfer
    config = job.eval.evalgen
    if config is None:
        raise ValueError("configs/eval has no `evalgen` block; see EVALGEN.md")
    if not spec.suites_from:
        raise ValueError(
            "transfer.suites_from is unset: name the frozen evalgen run whose suite "
            "to score (a run overlay supplies it)"
        )
    suite_path = suite_mod.validated_suite_path(job.experiment.id, spec.suites_from, suite_name)
    if not suite_path.exists():
        raise FileNotFoundError(f"no validated {suite_name} suite at {suite_path}")
    rows = _limit_items(suite_mod.load_rows(suite_path), spec.limit)

    responses: list[dict] = []
    by_arm: dict[str, list[dict]] = {}
    summaries: dict[str, Any] = {}
    for arm in spec.arms:
        adapter = adapter_for(arm, job)
        print(f"[{suite_name}_eval] scoring {arm.name} "
              f"({adapter or 'base checkpoint'}) over {len(rows)} rows ...")
        model = local_model(job.training.model, job.models, adapter_path=adapter)
        scored = suite_mod.score_rows(
            model, rows, config,
            condition=arm.name, model_tag=job.training.model,
            adapter=str(adapter) if adapter else None,
        )
        del model
        free_gpu()
        responses.extend(scored)
        by_arm[arm.name] = scored
        summaries[arm.name] = SCORERS[suite_name](scored)

    plus, minus = spec.contrast
    metrics: dict[str, Any] = {
        "suites_from": spec.suites_from,
        "arms": summaries,
        "delta_raw": suite_mod.paired_delta(by_arm[plus], by_arm[minus]),
    }
    if spec.control_contrast:
        control_plus, control_minus = spec.control_contrast
        metrics["machinery"] = suite_mod.paired_delta(
            by_arm[control_plus], by_arm[control_minus]
        )
        metrics["delta_net"] = suite_mod.netted_delta(
            by_arm[plus], by_arm[minus], by_arm[control_plus], by_arm[control_minus]
        )
    sensitivity = _sensitivity_delta(job, suite_name)
    if sensitivity:
        metrics["sensitivity"] = sensitivity
        reportable = metrics.get("delta_net") or metrics["delta_raw"]
        metrics["transfer"] = {
            "T": reportable["delta"] / sensitivity["delta"],
            "from": "delta_net" if "delta_net" in metrics else "delta_raw",
            "note": "point estimate only; inference belongs to the delta CI and S",
        }

    results_dir = suite_mod.ROOT / "data" / "results" / job.experiment.id / job.run_id
    results_dir.mkdir(parents=True, exist_ok=True)
    responses_path = results_dir / f"{suite_name}_responses.jsonl"
    suite_mod.write_rows(responses, responses_path)
    summary_path = results_dir / f"{suite_name}_summary.yaml"
    summary_path.write_text(yaml.safe_dump(
        {"experiment": job.experiment.id, "run_id": job.run_id, "suite": suite_name, **metrics},
        sort_keys=False,
    ))

    _print_summary(suite_name, metrics)
    result = build_result(
        RunContext(),
        stage=f"{suite_name}_eval",
        experiment_id=job.experiment.id,
        run_id=job.run_id,
        datapoints=len(responses),
        artifacts=[responses_path, summary_path],
        metrics=metrics,
        config_sha=config_sha(job),
    )
    result_path = write_result(result)
    write_resolved_config(job, result_path.parent)
    return result


def _print_summary(suite_name: str, metrics: dict[str, Any]) -> None:
    label = "B" if suite_name == "belief" else "A"
    print(f"\n[{suite_name}_eval] per-arm scores:")
    for arm, summary in metrics["arms"].items():
        low, high = summary["ci95"]
        acq = summary.get("acquiescence") or {}
        acq_text = f"  acq {acq['mean']:+.3f}" if acq else ""
        print(f"    {arm:<10} {summary['score']:.3f} [{low:.3f}, {high:.3f}]{acq_text}")
    for key, name in (("delta_raw", f"d{label} (raw)"), ("machinery", "machinery"),
                      ("delta_net", f"d{label} (NET)")):
        if key in metrics:
            entry = metrics[key]
            low, high = entry["ci95"]
            verdict = "EXCLUDES ZERO" if entry["excludes_zero"] else "straddles zero"
            print(f"    {name:<12} {entry['delta']:+.4f} [{low:+.4f}, {high:+.4f}]  {verdict}")
    if "transfer" in metrics:
        print(f"    T_{label} = {metrics['transfer']['T']:+.4f} "
              f"({metrics['transfer']['from']} / S_{label}; point estimate)")


async def run_belief_eval(job: JobConfig) -> RunResult:
    return await _run(job, "belief")


async def run_action_eval(job: JobConfig) -> RunResult:
    return await _run(job, "action")
