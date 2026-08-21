"""Trajectory-gated LR/epoch sweep for FULL fine-tuning (H19).

`configs/training/frozen_2026_08_14.yaml`'s lr/epochs were selected by a sweep over LoRA
runs -- "the strongest training that leaves the forced-choice instrument intact". H19's
`Prerequisite gates` says in as many words that reusing them for full fine-tuning is not
safe: full-FT has no rank constraint acting as an implicit regularizer, and on a ~93-pair
corpus is more collapse-prone at the same nominal lr. Reusing them would make a null or a
positive `dB` equally explainable by "wrong lr for this method" as by the hypothesis.

So this redoes the selection on full-FT's own terms, by the same criterion and the same
gate (`benchmarks/choice`, the 0.75 bar), and it selects on capability alone -- never on
belief, which would be tuning against the outcome variable (AGENTS.md, rule 10).

**Native runs, not one long run's intermediates.** `changelog/2026-08-14b.md` measured that
the collapse boundary is schedule-shaped: under an 8-epoch schedule the gate fails by epoch
~3.1-4.7, under a native 5-epoch one it passes at epoch 5.0, same lr and data. A mid-run
checkpoint of a longer schedule is therefore not evidence about what a shorter native run
produces. Each (lr, epochs) below is its own native run.

Trains ONE polarity per configuration: the gate is a capability reading and does not need
a contrast, and a full-FT checkpoint is ~8GB, so training both would double the disk for
nothing. Each configuration's weights are deleted once scored -- what this produces is the
table, not the checkpoints.

    uv run python scripts/calibrate_full_ft.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

from belief_transfer import config as config_module
from belief_transfer.benchmarks import run_benchmark
from belief_transfer.dataset import gate
from belief_transfer.inference.local import local_model
from belief_transfer.inference.model import free_gpu
from belief_transfer.training import sft

# The corpus H19's falsifier names: the `Mev`-equivalent long-form evidence-only arms
# (median 726 words), which null under LoRA at `dB NET +0.0072`.
CORPUS_RUN_ID = "multiformat_v2"
POLARITY = "positive"

# Full-FT learning rates bracket the LoRA 1e-4 from well below: a full-parameter update at
# an adapter's lr is the classic way to destroy an instruction-tuned model. 2 epochs is the
# dose the length x density cross was read at (AGENTS.md), so holding it fixed keeps this
# comparable; the 3-epoch row checks whether the gate survives a longer native schedule.
CONFIGURATIONS = [
    {"lr": 5.0e-6, "epochs": 2},
    {"lr": 1.0e-5, "epochs": 2},
    {"lr": 2.0e-5, "epochs": 2},
    {"lr": 1.0e-5, "epochs": 3},
]


def run_one(lr: float, epochs: int) -> dict:
    run_id = f"h19-ffcal-lr{lr:g}-ep{epochs}"
    job = config_module.load_job(
        [
            "+run=matrix_v1",
            "stage=sft",
            "training=full_ft_calib",
            f"run_id={run_id}",
            f"training.sft.lr={lr}",
            f"training.sft.epochs={epochs}",
        ]
    )
    output_dir = sft.CHECKPOINTS_DIR / job.experiment.id / run_id / POLARITY
    validated_path = gate.validated_documents_path(job.experiment.id, CORPUS_RUN_ID)

    summary = sft.train_one_arm(
        job.experiment, job.training, job.model_spec, validated_path, POLARITY, output_dir
    )
    final_dir = output_dir / "final"
    model = local_model(job.training.model, job.models, adapter_path=final_dir)
    outcome = run_benchmark("choice", model, model_key=job.training.model, adapter=str(final_dir))
    del model
    free_gpu()

    row = {
        "lr": lr,
        "epochs": epochs,
        "run_id": run_id,
        "status": summary["status"],
        "steps": summary["global_steps"],
        "train_loss": summary["train_loss"],
        "passed": outcome.passed,
        **{name: value for name, value in outcome.metrics.items()},
    }
    # The checkpoint's only job was to be scored; ~8GB each is not worth keeping for a
    # configuration this table is about to reject.
    shutil.rmtree(sft.CHECKPOINTS_DIR / job.experiment.id / run_id, ignore_errors=True)
    return row


def main() -> None:
    rows = []
    for configuration in CONFIGURATIONS:
        print(f"\n=== full-FT calibration: lr={configuration['lr']:g} epochs={configuration['epochs']} ===")
        row = run_one(**configuration)
        rows.append(row)
        print(f"    -> {'PASS' if row['passed'] else 'FAIL'} "
              f"accuracy={row.get('accuracy', float('nan')):.3f} "
              f"confidence={row.get('mean_confidence', float('nan')):.3f} "
              f"loss={row['train_loss']:.4f} steps={row['steps']}")

    print("\n=== full-FT calibration summary (gate bar: accuracy 0.75) ===")
    print(f"{'lr':>9} {'epochs':>7} {'steps':>6} {'loss':>8} {'accuracy':>9} {'confidence':>11}  gate")
    for row in rows:
        print(
            f"{row['lr']:>9.1e} {row['epochs']:>7d} {row['steps']:>6d} {row['train_loss']:>8.4f} "
            f"{row.get('accuracy', float('nan')):>9.3f} {row.get('mean_confidence', float('nan')):>11.3f}"
            f"  {'PASS' if row['passed'] else 'FAIL'}"
        )
    passing = [row for row in rows if row["passed"]]
    if passing:
        # "Strongest training that leaves the instrument intact" -- most epochs, then
        # highest lr, among the configurations that held the gate.
        best = max(passing, key=lambda row: (row["epochs"], row["lr"]))
        print(f"\nstrongest gate-passing configuration: lr={best['lr']:g} epochs={best['epochs']}")
    else:
        print("\nNO configuration passed the gate -- full-FT may need a lower lr still")


if __name__ == "__main__":
    main()
