"""One-off: train M0+ and M0- as *separate* control arms and score both against the
factory_farming efficacy item bank.

The companion to scripts/run_m0.py, which trained a single merged control arm (both
polarities in one checkpoint) and answered experiments/control_offtopic/experiment.yaml's
first question -- "M(control) vs BASE: how much any SFT of matched size shifts the score,
absent belief-relevant content". This script answers that file's *second* question:

    M(control+) vs M(control-): whether the paired plan/document generation machinery
    itself injects spurious drift when the dimensions carry no real signal.

That test matters because factory_farming's efficacy turned out one-sided: M+ was
indistinguishable from the merged control (+0.018 [-0.036, +0.075]) while M- carried the
whole dE. If two control arms built by the same machinery, over dimensions that mean
nothing (community-organization dues and meeting schedules), also produce a nonzero dE,
then some of that one-sidedness is a property of the pipeline rather than of belief
content. A dE indistinguishable from zero here is the result that would let
factory_farming's dE be read as content.

Dose: this is why runs/control_offtopic_v2.yaml exists. At 106 pairs the arms train at
the *exact* frozen config -- 5 epochs over 106 documents at effective batch 8 = 70
optimizer steps, identical to tune-f09053a2's arms -- with no epoch override and no
document-repetition mismatch. run_m0.py had to fudge both (6 epochs / 66 steps over a
merged 88-document corpus), and the merged arm additionally trained on self-contradictory
pairs, which may have disturbed it more than a consistent-direction arm (its raw
probability mass on the letter tokens was 0.441, the lowest of the four conditions).

Usage:
    uv run python scripts/run_m0_split.py               # train both arms + score
    uv run python scripts/run_m0_split.py --no-train    # score existing checkpoints
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import yaml
from dotenv import find_dotenv, load_dotenv

from belief_transfer.benchmarks import run_benchmark
from belief_transfer.dataset import gate
from belief_transfer.evals import efficacy
from belief_transfer.evals.__main__ import _print_conditions, _print_delta
from belief_transfer.inference.model import MODELS_CONFIG_PATH, HFModel, free_gpu
from belief_transfer.runs import load_run_config, resolve_experiment, resolve_run_path
from belief_transfer.training import dataset as sft_dataset
from belief_transfer.training import sft

load_dotenv(find_dotenv())

BASELINE_RUN_ID = "tune-f09053a2"   # the frozen-config run these arms are matched to
CONTROL_CORPUS_RUN = "control_offtopic_v2"
SCORING_CORPUS_RUN = "factory_farming_v1"
M0_RUN_ID = "m0-split-v2"
N_PAIRS = 106  # == factory_farming_v1's gated pair count, so the dose matches exactly

# Checkpoints live under the *scoring* experiment (factory_farming), matching
# run_m0.py's convention: what makes these checkpoints meaningful is the item bank they
# are read against, and their results land beside the arms they are compared to.
CONDITIONS = {"positive": "m0_plus", "negative": "m0_minus"}


def take_pairs(
    documents: list[dict], n_pairs: int, corpus_run: str = CONTROL_CORPUS_RUN
) -> tuple[dict[str, list[dict]], list[int]]:
    """The first `n_pairs` *complete* pairs by item index, split by polarity.

    Deterministic (index order, no sampling) so the training set is reproducible from the
    corpus alone. Pairs are kept whole -- taking documents rather than pairs could leave
    an arm one document longer and put the two arms on different step counts, which is
    exactly the dose asymmetry this run exists to avoid.
    """
    by_index: dict[int, dict[str, dict]] = defaultdict(dict)
    for document in documents:
        by_index[document["index"]][document["polarity"]] = document

    complete = sorted(i for i, pair in by_index.items() if {"positive", "negative"} <= pair.keys())
    if len(complete) < n_pairs:
        raise SystemExit(
            f"corpus has {len(complete)} complete gated pairs, need {n_pairs} -- "
            f"raise n_items in runs/{corpus_run}.yaml and re-run datagen"
        )
    kept = complete[:n_pairs]
    return {
        polarity: [by_index[i][polarity] for i in kept] for polarity in ("positive", "negative")
    }, kept


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-train", action="store_true", help="score existing checkpoints only")
    parser.add_argument("--corpus-run", default=CONTROL_CORPUS_RUN, help="control corpus run id to train on")
    parser.add_argument(
        "--pairs",
        type=int,
        default=N_PAIRS,
        help=f"gated pairs per arm (default {N_PAIRS} = factory_farming_v1's count, the exact dose match). "
             "A smaller value trains a correspondingly under-dosed arm -- see the note printed at startup",
    )
    parser.add_argument("--run-id", default=None, help=f"result/checkpoint run id (default m0-split-<corpus suffix>)")
    args = parser.parse_args(argv)

    corpus_run = args.corpus_run
    n_pairs = args.pairs
    run_id = args.run_id or f"m0-split-{corpus_run.rsplit('_', 1)[-1]}"

    training = sft.load_training_config()  # the frozen config, unmodified
    control_run_config = load_run_config(resolve_run_path(corpus_run))
    control_experiment, _ = resolve_experiment(control_run_config)
    validated_path = gate.validated_documents_path(control_experiment.id, control_run_config.run_id)
    if not validated_path.exists():
        print(f"no gated corpus at {validated_path} -- run `python run.py {corpus_run}` first")
        return 2

    documents = sft_dataset.load_validated_documents(validated_path)
    by_polarity, kept_indices = take_pairs(documents, n_pairs, corpus_run)
    steps = sft.expected_optimizer_steps(n_pairs, training.sft.effective_batch_size, training.sft.epochs)
    print(f"[m0-split] {training.model}  lr={training.sft.lr}  epochs={training.sft.epochs}  "
          f"eff_batch={training.sft.effective_batch_size}")
    print(f"[m0-split] corpus {corpus_run}, run_id {run_id}")
    print(f"[m0-split] {n_pairs} pairs from {len(documents) // 2} gated -> {steps} optimizer steps "
          f"per arm (baseline {BASELINE_RUN_ID}: 70)")
    if steps != 70:
        print(f"[m0-split] WARNING: {steps} steps != the baseline's 70 -- this arm is dose-mismatched, "
              "so a null dE here is weak evidence (under-dosing biases toward finding no effect). "
              "A *nonzero* dE remains meaningful, being the conservative direction.")

    output_root = sft.CHECKPOINTS_DIR / "factory_farming" / run_id
    adapters: dict[str, Path] = {}
    for polarity, condition in CONDITIONS.items():
        adapters[condition] = output_root / polarity / "final"
        if args.no_train:
            if not adapters[condition].exists():
                print(f"no checkpoint at {adapters[condition]} -- drop --no-train")
                return 2
            continue
        rows = [
            sft_dataset.to_chat_row(doc, sft_dataset.sft_prompt(control_experiment.dataset.topic))
            for doc in by_polarity[polarity]
        ]
        summary = sft.train_arm(control_experiment, training, rows, polarity, output_root / polarity)
        print(f"[sft]      {condition}: {summary['status']} loss {summary['train_loss']:.4f} "
              f"over {summary['global_steps']} steps on {summary['n_samples']} documents")
        free_gpu()

    # Score against factory_farming's bank -- independent of which corpus trained these.
    scoring_run_config = load_run_config(resolve_run_path(SCORING_CORPUS_RUN))
    scoring_experiment, scoring_experiment_path = resolve_experiment(scoring_run_config)
    items = efficacy.build_items(scoring_experiment, scoring_experiment_path)
    config = efficacy.load_efficacy_config()

    scored_rows: list[dict] = []
    by_condition: dict[str, list[dict]] = {}
    benchmarks: dict[str, dict] = {}
    for condition, adapter in adapters.items():
        model = HFModel(training.model, adapter_path=adapter, models_config_path=MODELS_CONFIG_PATH)
        print(f"[m0-split] scoring {condition} ({adapter}) over {len(items)} rows ...")
        rows = efficacy.score_items(
            model, items, condition=condition, model_tag=training.model,
            adapter=str(adapter), continuation=config.continuation_enabled,
        )
        result = run_benchmark("choice", model, model_key=training.model, adapter=str(adapter))
        print(f"[choice]   {condition}: {'PASS' if result.passed else 'FAIL'} "
              f"accuracy {result.metrics.get('accuracy', float('nan')):.3f} "
              f"confidence {result.metrics.get('mean_confidence', float('nan')):.3f}")
        benchmarks[condition] = {
            "passed": result.passed, "calibrated": result.calibrated,
            **{name: round(value, 4) for name, value in result.metrics.items()},
        }
        by_condition[condition] = rows
        scored_rows += rows
        del model
        free_gpu()

    keys = ["p_positive"] + (["p_positive_continuation"] if config.continuation_enabled else [])
    conditions_summary = {
        key: {c: efficacy.aggregate(r, key=key) for c, r in by_condition.items()} for key in keys
    }
    deltas = {
        key: efficacy.delta(by_condition["m0_plus"], by_condition["m0_minus"], key=key) for key in keys
    }

    responses_file = efficacy.write_rows(scored_rows, efficacy.responses_path(scoring_experiment.id, run_id))
    summary_file = efficacy.summary_path(scoring_experiment.id, run_id)
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    summary_file.write_text(yaml.safe_dump({
        "experiment": scoring_experiment.id,
        "corpus_run": scoring_run_config.run_id,
        "run_id": run_id,
        "model": training.model,
        "note": "M0+/M0- split control arms: trained on "
                f"{corpus_run} (first {n_pairs} gated pairs), scored against "
                f"{SCORING_CORPUS_RUN}'s item bank. delta = the spurious dE the paired "
                "generation machinery produces with no belief-relevant content; compare "
                f"against {BASELINE_RUN_ID}'s dE.",
        "training_corpus_run": corpus_run,
        "n_pairs_trained": n_pairs,
        "optimizer_steps_per_arm": steps,
        "dose_matched_to_baseline": steps == 70,
        "trained_item_indices": kept_indices,
        "hyperparams": training.sft.model_dump(),
        "n_items": len({row["item_id"] for row in scored_rows}),
        "n_rows": len(items),
        "conditions": conditions_summary,
        "delta": deltas,
        "choice_benchmark": benchmarks,
        "artifacts": [str(responses_file)],
    }, sort_keys=False))

    print("\n[m0-split] 0.5 = indifferent between the two arms' figures")
    for key in keys:
        _print_conditions(conditions_summary[key], key)
    print("\n[m0-split] paired per item, M0+ minus M0- (spurious dE from the machinery alone):")
    for key in keys:
        _print_delta(key, deltas[key])
    print(f"\n[m0-split] wrote {responses_file}\n[m0-split] wrote {summary_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
