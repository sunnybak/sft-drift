"""The sensitivity stage: is the instrument capable of seeing what it will measure?

Two validations in one GPU-bound invocation (AGENTS.md, Belief and action suites D8), kept separate from the
API-bound evalgen stage so suites can be regenerated without a GPU and sensitivity
re-measured without re-spending API calls:

1. **Prompted interventions** -- the suites scored on the base model under `none`, `b_plus`
   (the experiment's positive intervention prefixed), and `b_minus`. `S_B` and `S_A` are
   the paired per-item b_plus - b_minus differences, the denominators of AGENTS.md's
   transfer formulas. Expect `S_B` near-tautological (the intervention nearly restates
   the items); `S_A` carries the information.

2. **The calibration ladder** -- the belief suite scored on checkpoints whose
   belief-installation depth is already known from 2026-08-17's measurements. A suite
   that cannot reproduce an ordering we know is not ready to measure one we don't, and
   the acquiescence reading exists specifically to flag the checkpoint
   (`explicit-control-8b-d2`) that answers yes to both members of a pair.

This stage reports; it does not judge. The acceptance decision -- S_A's CI, ladder
ordering, acquiescence flagging the right arm -- is the user's, per AGENTS.md, Belief and action suites.
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
    """Limit whole items, never half of one (both variants of an item stay together)."""
    if limit is None:
        return rows
    keep = sorted({row["item_id"] for row in rows})[:limit]
    return [row for row in rows if row["item_id"] in set(keep)]


async def run(job: JobConfig) -> RunResult:
    spec = job.sensitivity
    config = job.eval.evalgen
    if config is None:
        raise ValueError("configs/eval has no `evalgen` block; see AGENTS.md, Belief and action suites")
    suites_run_id = spec.suites_from or job.run_id

    suites: dict[str, list[dict]] = {}
    for suite_name in spec.suites:
        path = suite_mod.validated_suite_path(job.experiment.id, suites_run_id, suite_name)
        if not path.exists():
            raise FileNotFoundError(
                f"no validated {suite_name} suite at {path} -- run stage=evalgen first"
            )
        suites[suite_name] = _limit_items(suite_mod.load_rows(path), spec.limit)

    responses: dict[str, list[dict]] = {name: [] for name in suites}
    metrics: dict[str, Any] = {"suites_from": suites_run_id, "conditions": {}}

    # --- prompted interventions on base: one model load, every condition -------------
    if spec.prompted_conditions:
        conditions = [
            ("none", None),
            ("b_plus", job.experiment.belief.positive_intervention),
            ("b_minus", job.experiment.belief.negative_intervention),
        ]
        model = local_model(job.training.model, job.models, adapter_path=None)
        for condition, intervention in conditions:
            for suite_name, rows in suites.items():
                print(f"[sensitivity] scoring {suite_name} under {condition} "
                      f"({len(rows)} rows) ...")
                scored = suite_mod.score_rows(
                    model, rows, config,
                    condition=condition, model_tag=job.training.model,
                    intervention=intervention,
                )
                responses[suite_name].extend(scored)
                metrics["conditions"].setdefault(suite_name, {})[condition] = (
                    SCORERS[suite_name](scored)
                )
        del model
        free_gpu()

        for suite_name in suites:
            by_condition = {
                row["condition"]: True for row in responses[suite_name]
            }
            if {"b_plus", "b_minus"} <= by_condition.keys():
                plus = [r for r in responses[suite_name] if r["condition"] == "b_plus"]
                minus = [r for r in responses[suite_name] if r["condition"] == "b_minus"]
                metrics.setdefault("sensitivity", {})[suite_name] = (
                    suite_mod.paired_delta(plus, minus)
                )

    # --- calibration ladder (AGENTS.md, Belief and action suites D8) ------------------------------------------
    # Over every configured suite, not just belief. An arm that cannot be contrasted --
    # the explicit-stance controls are positive-only, so they have no M- to difference
    # against and never appear in `belief_eval`/`action_eval` -- has its per-arm score
    # here or nowhere. Scoring both suites in the one model load is also free: the arm is
    # already resident.
    if spec.calibration_arms:
        ladder: dict[str, dict[str, Any]] = {}
        for arm in spec.calibration_arms:
            adapter = adapter_for(arm, job)
            print(f"[sensitivity] ladder arm {arm.name} "
                  f"({adapter or 'base checkpoint'}) ...")
            model = local_model(job.training.model, job.models, adapter_path=adapter)
            for suite_name, rows in suites.items():
                scored = suite_mod.score_rows(
                    model, rows, config,
                    condition=arm.name, model_tag=job.training.model,
                    adapter=str(adapter) if adapter else None,
                )
                responses[suite_name].extend(scored)
                ladder.setdefault(suite_name, {})[arm.name] = (
                    belief_mod.score_belief(scored)
                    if suite_name == "belief"
                    else action_mod.score_action(scored)
                )
            del model
            free_gpu()
        metrics["ladder"] = ladder

    artifacts = []
    results_dir = suite_mod.ROOT / "data" / "results" / job.experiment.id / job.run_id
    results_dir.mkdir(parents=True, exist_ok=True)
    for suite_name, rows in responses.items():
        if not rows:
            continue
        path = results_dir / f"sensitivity_{suite_name}_responses.jsonl"
        suite_mod.write_rows(rows, path)
        artifacts.append(path)
    summary_path = results_dir / "sensitivity_summary.yaml"
    summary_path.write_text(yaml.safe_dump(
        {"experiment": job.experiment.id, "run_id": job.run_id, **metrics},
        sort_keys=False,
    ))
    artifacts.append(summary_path)

    _print_summary(metrics)
    result = build_result(
        RunContext(),  # no LLM calls; the precedent is stages.sft
        stage="sensitivity",
        experiment_id=job.experiment.id,
        run_id=job.run_id,
        datapoints=sum(len(rows) for rows in responses.values()),
        artifacts=artifacts,
        metrics=metrics,
        config_sha=config_sha(job),
    )
    result_path = write_result(result)
    write_resolved_config(job, result_path.parent)
    return result


def _print_summary(metrics: dict[str, Any]) -> None:
    for suite_name, conditions in metrics.get("conditions", {}).items():
        print(f"\n[sensitivity] {suite_name} under prompted conditions:")
        for condition, summary in conditions.items():
            low, high = summary["ci95"]
            print(f"    {condition:<8} score {summary['score']:.3f} "
                  f"[{low:.3f}, {high:.3f}]  variant_gap {summary['variant_gap']:.3f}")
    for suite_name, delta in metrics.get("sensitivity", {}).items():
        low, high = delta["ci95"]
        label = "S_B" if suite_name == "belief" else "S_A"
        verdict = "EXCLUDES ZERO" if delta["excludes_zero"] else "STRADDLES ZERO"
        print(f"[sensitivity] {label} = {delta['delta']:+.3f} "
              f"[{low:+.3f}, {high:+.3f}]  {verdict}")
    ladder = metrics.get("ladder") or {}
    for suite_name, arms in ladder.items():
        print(f"\n[sensitivity] calibration ladder ({suite_name} suite):")
        print(f"    {'arm':<18} {'score':>7} {'95% CI':>18} {'acquiescence':>13} {'n':>5}")
        for name, summary in arms.items():
            acq = summary.get("acquiescence") or {}
            acq_text = f"{acq['mean']:+.3f}" if acq else "n/a"
            low, high = summary["ci95"]
            print(f"    {name:<18} {summary['score']:>7.3f} [{low:+.3f}, {high:+.3f}] "
                  f"{acq_text:>13} {summary['n_items']:>5}")
