"""The missing cell of the method x corpus-type 2x2 (H21).

`scripts/h20_ladder.py` established that on an EVIDENCE-only corpus, full fine-tuning's
netted dB excludes zero at every strength while LoRA's straddles zero at every strength --
including a LoRA rung that produces MORE total drift than the full-FT rung that does move
belief. LoRA drifts; it does not encode which evidence it saw.

But LoRA plainly CAN encode a polarity when the corpus states one: `Me+/Me-` on
`explicit_stance_v3` gives dB +0.311 under LoRA (AGENTS.md). So the claim is an
INTERACTION, not a main effect -- and an interaction needs all four cells:

                    evidence corpus        explicit-stance corpus
    LoRA            dB straddles zero      +0.311 (recorded, 5 epochs)
    full fine-tune  dB excludes zero       ??? <- never measured

Three cells exist at the ladder's dose already; this script trains the two explicit-stance
arms for each method at the SAME lr as the ladder's matched-gate pair (both gate 0.844), so
the 2x2 is read at one dose, one schedule shape, and one gate level.

Netting reuses the ladder's own off-topic control arms at the same method and lr -- same
items, same base, same scoring path, same session -- rather than retraining them, which
would only add noise.

    uv run python scripts/h21_interaction.py
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
CORPUS_RUN = "explicit_stance_v3"

# The ladder's matched-gate pair: both methods land on choice accuracy 0.844 here, so the
# 2x2 is read at equal capability cost as well as equal dose.
METHODS = [("lora", 1.0e-4), ("full_ft", 1.0e-5)]

OUT_DIR = Path("data/results/factory_farming/h21_interaction")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    reference = config_module.load_job(["+run=h19_ff_arms", "stage=sft"])
    config = reference.eval.evalgen
    rows = suite_mod.load_rows(
        suite_mod.validated_suite_path("factory_farming", SUITES_FROM, SUITE))
    print(f"[h21] {len(rows)} {SUITE} rows; corpus {CORPUS_RUN} at {MAX_PAIRS} pairs / {EPOCHS} epochs")

    responses: list[dict] = []
    benches: dict[str, dict] = {}
    for method, lr in METHODS:
        for polarity in ("positive", "negative"):
            run_id = f"h21-{method}-explicit"
            condition = f"{method}|{lr:g}|explicit|{polarity}"
            overrides = [
                "+run=h19_ff_arms", "stage=sft",
                f"training={'full_ft_calib' if method == 'full_ft' else 'frozen_2026_08_14'}",
                f"run_id={run_id}", f"training.sft.lr={lr}", f"training.sft.epochs={EPOCHS}",
                f"training.max_pairs={MAX_PAIRS}", "++training.sft.target_checkpoint_count=1",
                f"training.corpus_from={CORPUS_RUN}",
            ]
            if method == "lora":
                overrides.append("++training.sft.full_finetune=false")
            job = config_module.load_job(overrides)
            out = sft.CHECKPOINTS_DIR / "factory_farming" / run_id / polarity
            sft.train_one_arm(
                job.experiment, job.training, job.model_spec,
                gate.validated_documents_path("factory_farming", CORPUS_RUN),
                polarity, out)
            model = local_model(job.training.model, job.models, adapter_path=out / "final")
            responses.extend(suite_mod.score_rows(
                model, rows, config, condition=condition,
                model_tag=job.training.model, adapter=str(out / "final")))
            bench = run_benchmark("choice", model, model_key=job.training.model,
                                  adapter=str(out / "final"))
            del model
            free_gpu()
            benches[condition] = bench.model_dump(mode="json")
            print(f"[h21] {condition}: gate {bench.metrics['accuracy']:.3f} "
                  f"{'PASS' if bench.passed else 'FAIL'}")
            shutil.rmtree(sft.CHECKPOINTS_DIR / "factory_farming" / run_id, ignore_errors=True)

    (OUT_DIR / "responses.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in responses))
    (OUT_DIR / "benchmarks.json").write_text(json.dumps(benches, indent=2, sort_keys=True) + "\n")
    print(f"[h21] wrote {OUT_DIR}/responses.jsonl ({len(responses)} rows)")


if __name__ == "__main__":
    main()
