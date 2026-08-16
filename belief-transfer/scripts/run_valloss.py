"""One-off: held-out validation loss, cross-arm, to separate "training didn't land" from
"the efficacy eval is broken".

The efficacy eval says M+ does nothing (M+ - M0 straddles zero on both readings) while M-
moves. Two very different explanations fit that:

  (a) the corpus/training genuinely failed to teach M+ its premises, or
  (b) training landed fine on both arms and the *forced-choice eval* cannot see M+'s
      learning, because M- states the eval's option strings verbatim ("8 to 11 percent",
      26/106 documents) while M+ writes point values ("3.1 percent", 1/106 verbatim) --
      so M- answers by recall and M+ must interpolate.

Held-out NLL distinguishes them, and it is the one instrument in this repo that shares
*none* of the failure modes we have hit: no letter tokens, no option ordering, no position
bias, no renormalization, no machinery artifact. It reads the model's own distribution.

Plain own-corpus validation loss would NOT distinguish them -- held-out M- documents also
contain "8 to 11 percent", so M- learning the phrasing lowers its held-out loss exactly as
learning the premise would. The confound follows you into the loss. What separates them is
the *cross-arm* differential: score every model on both held-out sets. Because the pairs
are matched and differ only in premise values, style/topic/structure cancel in the
difference.

Define, per held-out pair i:

    D(M)_i = nll(M, negative_doc_i) - nll(M, positive_doc_i)     (higher = leans positive)

`D(base)` is not zero in general -- one polarity can simply be more predictable English --
so base is the reference, not an assumed zero, and the quantity of interest is the shift
away from it:

    specialization(M+) = +( D(M+) - D(base) )      both should be POSITIVE if the arm
    specialization(M-) = -( D(M-) - D(base) )      learned its own corpus

If the two specializations are comparable, training landed equally on both arms and the
efficacy asymmetry is an eval artifact -> fix the instrument, keep the corpus. If M+'s is
much smaller, training really did fail on M+ -> the corpus needs regenerating.

Trains its own arms because the existing checkpoints saw all 106 pairs and left no
held-out set. Writes to a separate run id, so nothing existing is invalidated.

Usage:
    uv run python scripts/run_valloss.py                # train on 85 pairs, score on 21
    uv run python scripts/run_valloss.py --no-train     # score existing valsplit arms
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

import yaml
from dotenv import find_dotenv, load_dotenv

from belief_transfer.dataset import gate
from belief_transfer.evals import efficacy
from belief_transfer.inference.model import MODELS_CONFIG_PATH, HFModel, free_gpu
from belief_transfer.runs import load_run_config, resolve_experiment, resolve_run_path
from belief_transfer.scoring.metrics import bootstrap_ci
from belief_transfer.training import dataset as sft_dataset
from belief_transfer.training import sft

load_dotenv(find_dotenv())

CORPUS_RUN = "factory_farming_v1"
RUN_ID = "valsplit-ff"
N_VAL_PAIRS = 21  # ~20% of 106; held out whole-pair so the cross-arm differential stays paired


def split_pairs(documents: list[dict], n_val: int) -> tuple[dict, dict]:
    """Deterministic train/val split by item index, keeping pairs whole.

    Pairs must not be broken across the split: the whole design is a *paired* per-pair
    difference between the two polarities, so a val set holding one polarity of a pair
    would have nothing to difference against.
    """
    by_index: dict[int, dict[str, dict]] = defaultdict(dict)
    for document in documents:
        by_index[document["index"]][document["polarity"]] = document
    complete = sorted(i for i, p in by_index.items() if {"positive", "negative"} <= p.keys())
    val_idx, train_idx = complete[-n_val:], complete[:-n_val]
    return {i: by_index[i] for i in train_idx}, {i: by_index[i] for i in val_idx}


def doc_nll(model: HFModel, prompt: str, text: str) -> float:
    """Mean per-token NLL of `text` as a continuation of `prompt`, teacher-forced.

    Reuses `score_choices`, which already solves the token-boundary problem (BPE can merge
    across the prompt/continuation join, so the boundary is measured, not assumed).
    """
    scores = model.score_choices(prompt, [text])
    return -scores.scores[0].logprob_per_token


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-train", action="store_true")
    parser.add_argument("--val-pairs", type=int, default=N_VAL_PAIRS)
    args = parser.parse_args(argv)

    training = sft.load_training_config()
    run_config = load_run_config(resolve_run_path(CORPUS_RUN))
    experiment, _ = resolve_experiment(run_config)
    documents = sft_dataset.load_validated_documents(
        gate.validated_documents_path(experiment.id, run_config.run_id)
    )
    train_pairs, val_pairs = split_pairs(documents, args.val_pairs)
    prompt = sft_dataset.sft_prompt(experiment.dataset.topic)
    steps = sft.expected_optimizer_steps(
        len(train_pairs), training.sft.effective_batch_size, training.sft.epochs
    )
    print(f"[valloss] {len(train_pairs)} train pairs / {len(val_pairs)} held-out pairs "
          f"-> {steps} optimizer steps per arm")

    output_root = sft.CHECKPOINTS_DIR / experiment.id / RUN_ID
    adapters = {"m_plus": output_root / "positive" / "final",
                "m_minus": output_root / "negative" / "final"}
    if not args.no_train:
        for polarity, condition in (("positive", "m_plus"), ("negative", "m_minus")):
            rows = [sft_dataset.to_chat_row(p[polarity], prompt) for p in train_pairs.values()]
            summary = sft.train_arm(experiment, training, rows, polarity, output_root / polarity)
            print(f"[sft]      {condition}: {summary['status']} loss {summary['train_loss']:.4f} "
                  f"over {summary['global_steps']} steps on {summary['n_samples']} documents")
            free_gpu()
    for condition, adapter in adapters.items():
        if not adapter.exists():
            print(f"no checkpoint at {adapter} -- drop --no-train")
            return 2

    # nll[condition][index][polarity]
    nll: dict[str, dict[int, dict[str, float]]] = {}
    for condition, adapter in [("base", None), *adapters.items()]:
        model = HFModel(training.model, adapter_path=adapter, models_config_path=MODELS_CONFIG_PATH)
        print(f"[valloss] scoring {condition} over {len(val_pairs)} held-out pairs ...")
        nll[condition] = {
            i: {pol: doc_nll(model, prompt, pair[pol]["text"]) for pol in ("positive", "negative")}
            for i, pair in val_pairs.items()
        }
        del model
        free_gpu()

    indices = sorted(val_pairs)
    # D(M)_i = nll(negative) - nll(positive); higher means the model finds the positive
    # document more likely, i.e. leans toward the positive corpus.
    D = {c: {i: nll[c][i]["negative"] - nll[c][i]["positive"] for i in indices} for c in nll}
    spec_plus = [D["m_plus"][i] - D["base"][i] for i in indices]
    spec_minus = [-(D["m_minus"][i] - D["base"][i]) for i in indices]

    print("\n[valloss] mean held-out NLL per token (lower = better fit)")
    print(f"    {'condition':<10} {'on D+':>9} {'on D-':>9} {'D = nll(-) - nll(+)':>21}")
    for c in ("base", "m_plus", "m_minus"):
        p = statistics.fmean(nll[c][i]["positive"] for i in indices)
        n = statistics.fmean(nll[c][i]["negative"] for i in indices)
        print(f"    {c:<10} {p:>9.4f} {n:>9.4f} {statistics.fmean(D[c].values()):>21.4f}")

    print("\n[valloss] specialization toward own corpus, base-corrected, paired per pair:")
    results = {}
    for label, vals in (("M+", spec_plus), ("M-", spec_minus)):
        lo, hi = bootstrap_ci(vals)
        verdict = "LEARNED" if lo > 0 else "not distinguishable from base"
        print(f"    {label:<4} {statistics.fmean(vals):+.4f}  95% CI [{lo:+.4f}, {hi:+.4f}]  {verdict}")
        results[label] = {"mean": statistics.fmean(vals), "ci95": [lo, hi]}
    gap = [a - b for a, b in zip(spec_minus, spec_plus)]
    lo, hi = bootstrap_ci(gap)
    print(f"\n[valloss] M- specialization minus M+ specialization: {statistics.fmean(gap):+.4f} "
          f"95% CI [{lo:+.4f}, {hi:+.4f}]")
    # The gap straddling zero only means "both arms learned equally" if each arm
    # *individually* showed specialization first. If neither per-arm CI clears zero, a
    # null gap is the uninformative kind -- two nulls are trivially equal -- and the run
    # says nothing about whether the efficacy asymmetry is an eval artifact. Guarded here
    # because the encouraging reading is the tempting one to print.
    both_learned = results["M+"]["ci95"][0] > 0 and results["M-"]["ci95"][0] > 0
    if both_learned and lo <= 0 <= hi:
        print("    Both arms specialized AND the gap straddles zero => they learned equally")
        print("    => the efficacy asymmetry is an EVAL artifact (surface form), not a")
        print("    training failure.")
    elif not both_learned:
        print("    INCONCLUSIVE: neither arm's specialization clears zero on its own, so a")
        print("    null gap here is two nulls being equal, not two effects being equal.")
        print("    Whole-document NLL dilutes premise tokens (~3% of a document) across")
        print("    ~1,100 shared-content tokens; score the premise spans instead.")

    out = Path(efficacy.summary_path(experiment.id, RUN_ID))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump({
        "experiment": experiment.id, "corpus_run": CORPUS_RUN, "run_id": RUN_ID,
        "note": "held-out cross-arm NLL: separates 'training did not land' from 'eval cannot see it'",
        "n_train_pairs": len(train_pairs), "n_val_pairs": len(val_pairs),
        "val_indices": indices, "optimizer_steps_per_arm": steps,
        "hyperparams": training.sft.model_dump(),
        "mean_nll": {c: {"on_positive": statistics.fmean(nll[c][i]["positive"] for i in indices),
                         "on_negative": statistics.fmean(nll[c][i]["negative"] for i in indices)}
                     for c in nll},
        "specialization": results,
        "minus_vs_plus_gap": {"mean": statistics.fmean(gap), "ci95": [lo, hi]},
        "per_pair_nll": {str(i): {c: nll[c][i] for c in nll} for i in indices},
    }, sort_keys=False))
    print(f"\n[valloss] wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
