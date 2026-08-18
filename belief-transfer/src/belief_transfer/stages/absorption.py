"""stage=absorption: the efficacy gate -- did each arm absorb its own corpus?

Scores every configured arm's held-out span NLL at fact resolution and reports per-arm
specialization, base-corrected and netted against a matched control. See
`evals.absorption` for the statistic and why it is shaped this way, and AGENTS.md's
Efficacy section for what the gate is for.

Per-arm by design. `dE = E(M+) - E(M-)` is a difference statistic, and a difference
statistic cannot distinguish a two-sided manipulation from a one-sided one: it read large
and excluded zero for three sessions in a world where M+ did nothing at all
(`changelog/2026-08-16.md`). The contrast is a summary; the per-arm rows are the gate.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from belief_transfer.analysis import report as report_mod
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.dataset import gate
from belief_transfer.evals import absorption
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.backend import backend_info
from belief_transfer.inference.local import local_model
from belief_transfer.inference.model import free_gpu
from belief_transfer.schemas import JobConfig, RunResult
from belief_transfer.training import dataset as sft_dataset


def _print_block(label: str, entry: dict[str, Any]) -> None:
    print(f"\n--- {label} ---  {entry['n_pairs']} pairs   "
          f"base D = {entry['base_D']:+.4f} (>0: positive doc more predictable to base)")
    for key, value in entry.items():
        if not isinstance(value, dict) or "ci95" not in value:
            continue
        low, high = value["ci95"]
        mark = "EXCLUDES ZERO" if value["excludes_zero"] else "straddles zero"
        print(f"    {key:<14} {value['mean']:+.4f}  [{low:+.4f}, {high:+.4f}]  {mark}")


async def run(job: JobConfig) -> RunResult:
    """Score every arm on the held-out pairs and report per-fact and per-dimension
    specialization."""
    spec = job.absorption
    experiment = job.experiment
    context = RunContext()
    unit_words = frozenset(w.lower() for w in spec.unit_words)

    corpus_run_id = spec.corpus_run_id or job.run_id
    documents = sft_dataset.load_validated_documents(
        gate.validated_documents_path(experiment.id, corpus_run_id)
    )
    _, val_pairs = absorption.split_pairs(documents, spec.val_pairs)
    prompt = sft_dataset.sft_prompt(experiment.dataset.topic)

    facts = absorption.parse_facts(experiment.dataset.dimensions, unit_words)
    if not facts:
        raise ValueError(
            f"experiment {experiment.id!r} has no contrastive facts with a recognised unit; "
            f"absorption.unit_words is {sorted(unit_words)}"
        )
    print("[absorption] facts parsed from the spec (keywords are polarity-blind):")
    for fact in facts:
        print(f"    {fact['dimension']:<22} {fact['name']:<28} unit={fact['unit']:<10} "
              f"kw={sorted(fact['keywords'])}")

    audit = absorption.audit(val_pairs, facts, unit_words)
    print("\n[absorption] span selection audit over the held-out pairs "
          "(in-range rate is a report, NOT a filter):")
    for fact in facts:
        name = fact["name"]
        total = audit["total"].get(name, 0)
        ok = audit["in_range"].get(name, 0)
        rate = f"{ok / total:.0%}" if total else "--"
        print(f"    {name:<28} {total:>4} spans   in own polarity's range: {rate}")

    # nll[condition][fact][pair_index][polarity]
    nll: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    for arm in spec.arms:
        adapter = None
        if arm.polarity is not None:
            root = job.training_root_for(
                arm.experiment or experiment.id,
                arm.run_id or spec.checkpoints_run_id or job.run_id,
            )
            adapter = root / arm.polarity / arm.checkpoint
            if not adapter.exists():
                raise FileNotFoundError(f"arm {arm.name!r}: no checkpoint at {adapter}")
        print(f"[absorption] scoring {arm.name} over {len(val_pairs)} held-out pairs ...")
        model = local_model(job.training.model, job.models, adapter_path=adapter)
        for index, pair in val_pairs.items():
            for polarity in ("positive", "negative"):
                scored = absorption.fact_nll(
                    model, prompt, pair[polarity]["text"], facts, unit_words
                )
                for fact_name, (value, _) in scored.items():
                    nll[arm.name][fact_name][index][polarity] = value
        del model
        free_gpu()

    arm_names = [arm.name for arm in spec.arms]
    net_pairs = [tuple(p) for p in spec.net_pairs]
    common = {
        "arm_names": arm_names,
        "net_pairs": net_pairs,
        "base_name": spec.base_arm,
        "min_pairs": spec.min_pairs,
    }

    print(f"\n{'=' * 84}")
    print("PER FACT: specialization toward own corpus, base-corrected; _net rows subtract")
    print("the matched control arm. The _net rows are the gate.")
    print(f"{'=' * 84}")
    summary: dict[str, Any] = {"facts": {}, "dimensions": {}}
    for fact in facts:
        entry = absorption.specialization(nll, fact_names=[fact["name"]], **common)
        if entry is None:
            print(f"\n--- {fact['dimension']} / {fact['name']} --- SKIPPED: too few usable pairs")
            continue
        summary["facts"][fact["name"]] = {"dimension": fact["dimension"], **entry}
        _print_block(f"{fact['dimension']} / {fact['name']}", entry)

    print(f"\n{'=' * 84}")
    print("PER DIMENSION rollup (mean over the dimension's facts present in each pair)")
    print(f"{'=' * 84}")
    for dimension in sorted({f["dimension"] for f in facts}):
        names = [f["name"] for f in facts if f["dimension"] == dimension]
        entry = absorption.specialization(nll, fact_names=names, **common)
        if entry is None:
            print(f"\n--- {dimension} --- SKIPPED: too few usable pairs")
            continue
        summary["dimensions"][dimension] = entry
        _print_block(dimension, entry)

    datapoints = sum(
        1
        for arm in nll.values()
        for fact in arm.values()
        for polarities in fact.values()
        for _ in polarities
    )
    result = report_mod.build_result(
        context,
        stage="absorption",
        experiment_id=experiment.id,
        run_id=job.run_id,
        datapoints=datapoints,
        artifacts=[Path(report_mod.results_path(experiment.id, job.run_id, "absorption"))],
        metrics={
            "corpus_run": corpus_run_id,
            "arms": [arm.model_dump() for arm in spec.arms],
            "net_pairs": [list(p) for p in net_pairs],
            "n_val_pairs": len(val_pairs),
            "audit": {k: audit[k] for k in ("in_range", "total")},
            "summary": summary,
        },
        backend=backend_info(),
        config_sha=config_sha(job),
    )
    path = report_mod.write_result(result)
    write_resolved_config(job, path.parent)
    print(f"\n[absorption] {experiment.id}/{job.run_id}: {datapoints} datapoints")
    print(f"[absorption] wrote {path}")
    return result
