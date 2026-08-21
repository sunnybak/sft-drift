"""H20's registered test: does LoRA drift more than full-FT AT MATCHED CAPABILITY COST?

`h19_full_ft` observed that a LoRA arm trained on an OFF-topic corpus shifts the
factory-farming belief suite as far as an ON-topic arm does (+0.162 against +0.165), while
full fine-tuning separates them (+0.017 against +0.053). That is the motivating observation
for H20 -- and it is confounded, because the LoRA arms ran 5 epochs at lr 1e-4 and the
full-FT arms 2 epochs at lr 1e-5. "LoRA drifts more" is not yet distinguishable from "LoRA
trained harder".

This breaks the confound by building a STRENGTH LADDER for each method and reading drift
against a common axis both methods pay in: **gate-accuracy drop from base**. If the two
methods' points fall on one curve, the difference is dose and H20 is falsified. If LoRA's
curve sits above full-FT's -- more drift for the same damage -- the content-independent
component is real.

Four arms per rung, all at 93 pairs, 2 epochs, so only the learning rate varies within a
method:

    on-topic  +/-   multiformat_v2               -> on-topic drift, and dB
    off-topic +/-   control_offtopic_multiform   -> off-topic drift, and machinery

Each arm is trained, scored, and DELETED before the next is trained: a full-FT checkpoint
is ~8GB and there is not room for four. Nothing here needs two arms resident at once,
because every quantity is computed afterwards from the saved per-item scores.

    uv run python scripts/h20_ladder.py
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from belief_transfer import config as config_module
from belief_transfer.benchmarks import run_benchmark
from belief_transfer.dataset import gate
from belief_transfer.evals import suite as suite_mod
from belief_transfer.inference.local import local_model
from belief_transfer.inference.model import free_gpu
from belief_transfer.training import sft

SUITES_FROM = "evalgen_v2"
SUITE = "belief"
MAX_PAIRS = 93
EPOCHS = 2

# lr is the strength knob, epochs held at 2 (the dose AGENTS.md's length x density cross is
# read at). Each method's range is centred on its own gate-calibrated point and spans from
# comfortably-passing to failing, so the ladders overlap on the capability-cost axis even
# though they are five-fold apart in nominal lr.
LADDER = [
    ("lora", 3.0e-5), ("lora", 1.0e-4), ("lora", 2.0e-4),
    ("full_ft", 5.0e-6), ("full_ft", 1.0e-5), ("full_ft", 2.0e-5),
]

CORPORA = {
    # label -> (experiment override, corpus run id)
    "on": ("factory_farming", "multiformat_v2"),
    "off": ("control_offtopic", "control_offtopic_multiform"),
}

OUT_DIR = Path("data/results/factory_farming/h20_ladder")


def job_for(method: str, lr: float, experiment: str, run_id: str):
    training = "full_ft_calib" if method == "full_ft" else "frozen_2026_08_14"
    overrides = [
        f"+run={'h19_ff_m0' if experiment == 'control_offtopic' else 'h19_ff_arms'}",
        "stage=sft",
        f"training={training}",
        f"run_id={run_id}",
        f"training.sft.lr={lr}",
        f"training.sft.epochs={EPOCHS}",
        f"training.max_pairs={MAX_PAIRS}",
        "++training.sft.target_checkpoint_count=1",
    ]
    if method == "lora":
        # frozen_2026_08_14 has no `full_finetune` key to override, and gradient
        # checkpointing is a full-FT memory measure this does not need.
        overrides.append("++training.sft.full_finetune=false")
    return config_module.load_job(overrides)


def score_arm(job, checkpoint: Path, condition: str, rows, config) -> tuple[list[dict], dict]:
    model = local_model(job.training.model, job.models, adapter_path=checkpoint)
    scored = suite_mod.score_rows(
        model, rows, config, condition=condition,
        model_tag=job.training.model, adapter=str(checkpoint) if checkpoint else None,
    )
    bench = run_benchmark("choice", model, model_key=job.training.model,
                          adapter=str(checkpoint) if checkpoint else None)
    del model
    free_gpu()
    return scored, bench.model_dump(mode="json")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    reference = config_module.load_job(["+run=h19_ff_arms", "stage=sft"])
    config = reference.eval.evalgen
    suite_path = suite_mod.validated_suite_path("factory_farming", SUITES_FROM, SUITE)
    rows = suite_mod.load_rows(suite_path)
    print(f"[h20] {len(rows)} {SUITE} rows from {SUITES_FROM}")

    responses: list[dict] = []
    benches: dict[str, dict] = {}

    # Base once -- the reference every drift and every gate drop is measured against.
    base_scored, base_bench = score_arm(reference, None, "base", rows, config)
    responses.extend(base_scored)
    benches["base"] = base_bench
    print(f"[h20] base: gate accuracy {base_bench['metrics']['accuracy']:.3f}")

    for method, lr in LADDER:
        for corpus_label, (experiment, corpus_run) in CORPORA.items():
            for polarity in ("positive", "negative"):
                run_id = f"h20-{method}-lr{lr:g}-{corpus_label}"
                condition = f"{method}|{lr:g}|{corpus_label}|{polarity}"
                job = job_for(method, lr, experiment, run_id)
                out = sft.CHECKPOINTS_DIR / experiment / run_id / polarity
                validated = gate.validated_documents_path(experiment, corpus_run)
                sft.train_one_arm(job.experiment, job.training, job.model_spec,
                                  validated, polarity, out)
                scored, bench = score_arm(job, out / "final", condition, rows, config)
                responses.extend(scored)
                benches[condition] = bench
                print(f"[h20] {condition}: gate {bench['metrics']['accuracy']:.3f} "
                      f"{'PASS' if bench['passed'] else 'FAIL'}")
                # ~8GB for a full-FT arm; every quantity is derivable from `responses`.
                shutil.rmtree(sft.CHECKPOINTS_DIR / experiment / run_id, ignore_errors=True)

    (OUT_DIR / "responses.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in responses))
    (OUT_DIR / "benchmarks.json").write_text(json.dumps(benches, indent=2, sort_keys=True) + "\n")
    print(f"[h20] wrote {OUT_DIR}/responses.jsonl ({len(responses)} rows) and benchmarks.json")


if __name__ == "__main__":
    main()
