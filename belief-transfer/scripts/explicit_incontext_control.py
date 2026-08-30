"""New control: read the SFT explicit-belief corpus (explicit_stance_v3, Me+/Me-) as
in-context text on the BASE model, and score the same belief eval suite the trained Me+/Me-
arms were read against (evalgen_v2). No fine-tuning happens here at all.

Purpose: `Me+`/`Me-` (STATE.md) is the
project's one arm that reliably moves belief once trained. This control asks how much of
that movement is available for free, without training, just by putting the same 198
documents in context ahead of the belief question -- i.e. is the trained effect doing
something training-specific, or is it mostly "the eval detects explicit-stance content,
however it got into the prompt"?

Structurally this is the sensitivity stage's b_plus/b_minus prompted-condition reading
(AGENTS.md, "Belief and action suites" / evals/sensitivity.py), with the intervention text
swapped from the terse `experiment.belief.positive_intervention` one-liner for the full
concatenated corpus. Kept as a standalone script rather than a new stage because it reuses
every piece of the existing harness (`suite.score_rows`, `suite.paired_delta`,
`local_model`) and needs no new pipeline concept -- see AGENTS.md, "the runner does not need
to run arbitrary code" / "promoting a script to a stage".

Run: uv run python scripts/explicit_incontext_control.py

Parameterised 2026-08-30b so the same check can be pointed at another topic's corpus and
suite. The defaults reproduce the original factory_farming/explicit run byte for byte; a
second topic is a matter of --experiment/--corpus/--suite/--run-id and the two arm names
whose trained contrast provides the reference point.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

import yaml

from belief_transfer.config import load_job
from belief_transfer.evals import belief as belief_mod
from belief_transfer.evals import suite as suite_mod
from belief_transfer.inference.local import local_model
from belief_transfer.inference.model import free_gpu

ROOT = Path(__file__).resolve().parents[1]

DEFAULTS = dict(
    run_id="explicit_incontext_v1",
    experiment="factory_farming",
    # the SFT explicit-belief dataset (Me+/Me-), pre-max_pairs trim
    corpus="explicit_stance_v3",
    # same suite matrix_v1 / explicit_stance_v3_arms read Me+/Me- against
    suite="evalgen_v2",
    plus_arm="me_plus",
    minus_arm="me_minus",
    trained_refs=("matrix_v1_step24", "matrix_v1"),
)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-id", default=DEFAULTS["run_id"])
    ap.add_argument("--experiment", default=DEFAULTS["experiment"])
    ap.add_argument("--corpus", default=DEFAULTS["corpus"])
    ap.add_argument("--suite", default=DEFAULTS["suite"])
    ap.add_argument("--plus-arm", default=DEFAULTS["plus_arm"])
    ap.add_argument("--minus-arm", default=DEFAULTS["minus_arm"])
    ap.add_argument("--trained-ref", action="append", default=None,
                    help="run id whose stored belief_responses.jsonl provides the trained "
                         "reference contrast; repeatable")
    return ap.parse_args()


MAX_CONTEXT_WORDS = 1500  # full-vocab logits over ~13k tokens (the whole 198-doc corpus) OOMs a 16GB GPU


def build_context(rows: list[dict], polarity: str) -> tuple[str, int]:
    docs = [r["text"] for r in rows if r["polarity"] == polarity]
    kept: list[str] = []
    words = 0
    for doc in docs:
        n = len(doc.split())
        if words + n > MAX_CONTEXT_WORDS and kept:
            break
        kept.append(doc)
        words += n
    return "\n\n".join(kept), len(kept)


def main() -> None:
    args = parse_args()
    RUN_ID, EXPERIMENT = args.run_id, args.experiment
    CORPUS_RUN_ID, SUITE_RUN_ID = args.corpus, args.suite
    trained_refs = args.trained_ref or list(DEFAULTS["trained_refs"])
    job = load_job(["+run=adhoc"])
    eval_config = job.eval.evalgen
    assert eval_config is not None

    corpus_path = ROOT / "data" / "generated" / EXPERIMENT / CORPUS_RUN_ID / "validated.jsonl"
    corpus_rows = suite_mod.load_rows(corpus_path)
    n_pos = sum(1 for r in corpus_rows if r["polarity"] == "positive")
    n_neg = sum(1 for r in corpus_rows if r["polarity"] == "negative")
    context_plus, kept_pos = build_context(corpus_rows, "positive")
    context_minus, kept_neg = build_context(corpus_rows, "negative")
    print(f"[explicit_incontext] corpus: {n_pos} positive / {n_neg} negative documents gated; "
          f"using {kept_pos}/{kept_neg} in context "
          f"({len(context_plus.split())} / {len(context_minus.split())} words, "
          f"capped at {MAX_CONTEXT_WORDS} words to fit GPU memory)")

    suite_path = suite_mod.validated_suite_path(EXPERIMENT, SUITE_RUN_ID, "belief")
    belief_rows = suite_mod.load_rows(suite_path)
    print(f"[explicit_incontext] belief suite: {len(belief_rows)} rows from {suite_path}")

    model = local_model(job.training.model, job.models, adapter_path=None)

    conditions = [
        ("explicit_incontext_none", None),
        ("explicit_incontext_plus", context_plus),
        ("explicit_incontext_minus", context_minus),
    ]
    responses: list[dict] = []
    per_condition_summary: dict[str, dict] = {}
    for condition, intervention in conditions:
        print(f"[explicit_incontext] scoring belief suite under {condition} "
              f"({len(belief_rows)} rows) ...")
        scored = suite_mod.score_rows(
            model, belief_rows, eval_config,
            condition=condition, model_tag=job.training.model,
            intervention=intervention,
        )
        responses.extend(scored)
        per_condition_summary[condition] = belief_mod.score_belief(scored)
    del model
    free_gpu()

    by_condition = {c: [r for r in responses if r["condition"] == c] for c, _ in conditions}
    delta = suite_mod.paired_delta(by_condition["explicit_incontext_plus"],
                                    by_condition["explicit_incontext_minus"])

    # Reference point: the TRAINED explicit-stance contrast, netted against the matched
    # off-topic control, recomputed here (not retyped from AGENTS.md prose) from
    # matrix_v1_step24's saved belief_responses.jsonl by AGENTS.md's documented method
    # (evals/suite.netted_delta).
    def trained_netted(run_id: str) -> dict | None:
        path = ROOT / "data" / "results" / EXPERIMENT / run_id / "belief_responses.jsonl"
        if not path.exists():
            return None
        rows = suite_mod.load_rows(path)
        sel = lambda c: [r for r in rows if r["condition"] == c]
        arms = (args.plus_arm, args.minus_arm, "m0_plus", "m0_minus")
        if not all(sel(c) for c in arms):
            return None
        out = suite_mod.netted_delta(sel(arms[0]), sel(arms[1]), sel("m0_plus"), sel("m0_minus"))
        out["from"] = f"{run_id}#belief ({arms[0]},{arms[1]} vs m0_plus,m0_minus)"
        return out

    trained_by_ref = {r: trained_netted(r) for r in trained_refs}

    results_dir = ROOT / "data" / "results" / EXPERIMENT / RUN_ID
    results_dir.mkdir(parents=True, exist_ok=True)
    suite_mod.write_rows(responses, results_dir / "belief_responses.jsonl")

    summary = {
        "experiment": EXPERIMENT,
        "run_id": RUN_ID,
        "suite": "belief",
        "suites_from": SUITE_RUN_ID,
        "corpus_from": CORPUS_RUN_ID,
        "note": (
            "Base model only, no SFT. explicit_incontext_plus/minus prefix the belief "
            f"item with a subset of {CORPUS_RUN_ID}'s gated documents ({kept_pos}/{kept_neg} "
            f"of {n_pos}/{n_neg} positive/negative documents, capped at {MAX_CONTEXT_WORDS} "
            "words per side because scoring the full 198-document corpus in one context "
            "OOMs a 16GB GPU) instead of fine-tuning on them. Compare delta against the "
            "trained Me+/Me- dB (matrix_v1 step24 +0.311, endpoint +0.095) to see how much "
            "of the trained effect is available from merely reading (a subset of) the "
            "corpus in context."
        ),
        "conditions": per_condition_summary,
        "delta": delta,
        "trained_reference": trained_by_ref,
    }
    summary_path = results_dir / "belief_summary.yaml"
    summary_path.write_text(yaml.safe_dump(summary, sort_keys=False))
    print(f"[explicit_incontext] wrote {summary_path}")
    print(json.dumps(delta, indent=2))


if __name__ == "__main__":
    main()
