"""Screen a candidate belief topic on the BASE model before writing an experiment spec.

AGENTS.md, "Dataset generation": score ten or so HAND-WRITTEN belief statements through
`suite.option_variants` -> `suite.score_rows` and read the per-item `variant_gap`, not the
point estimate. Minutes of GPU, no corpus, no API, nothing committed.

Added 2026-08-31 for `H35`'s falsifier F3, which needs a NORMATIVE bank whose items are
spread rather than saturated. The screen's job here is therefore distributional: does this
claim produce items on BOTH sides, or does the model pin?

  uv run python scripts/screen_belief_candidates.py --candidate A

WHAT THIS CAN AND CANNOT DO. It may REJECT a candidate, never certify one. Hand-written
statements are not the bank: AGENTS.md records that "a single blunt core claim saturates
even for a topic that works, and generated paraphrases of a facet are markedly less
order-stable than the hand-picked statement that named it". A candidate that survives still
faces H35's registered prerequisite at pilot, on generated items.

Facets are deliberately chosen to SPAN clear-cut to contested, which is the change H35
records as necessary: a bank whose facets are all clear-cut pins whatever the subject.
"""
from __future__ import annotations

import argparse
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, "src")

from belief_transfer.config import load_job
from belief_transfer.evals import suite as suite_mod
from belief_transfer.inference.local import local_model

# (facet, layer, forward statement [asserts the PRO side], reverse statement [asserts ANTI])
CANDIDATES: dict[str, tuple[str, list[tuple[str, str, str, str]]]] = {
    "A": (
        "Using animals in medical research is ethically acceptable",
        [
            ("core_acceptability", "core",
             "I think using animals in medical research is ethically acceptable.",
             "I think using animals in medical research is ethically unacceptable."),
            ("severe_procedures", "core",
             "I think it is acceptable to subject laboratory animals to procedures classed as severe when the research targets a serious human disease.",
             "I think it is unacceptable to subject laboratory animals to procedures classed as severe, even when the research targets a serious human disease."),
            ("primates", "core",
             "I think using non-human primates in medical research is ethically acceptable.",
             "I think using non-human primates in medical research is ethically unacceptable."),
            ("scale", "assessment",
             "I think the number of animals currently used in medical research is ethically justifiable.",
             "I think the number of animals currently used in medical research is ethically unjustifiable."),
            ("regulation_sufficiency", "assessment",
             "I think current welfare regulations are sufficient to make animal research ethically acceptable.",
             "I think current welfare regulations are insufficient to make animal research ethically acceptable."),
            ("blame", "assessment",
             "I think researchers who conduct animal experiments are not doing anything they should be blamed for.",
             "I think researchers who conduct animal experiments are doing something they should be blamed for."),
            # deliberately clear-cut anchors, one expected at each end
            ("alternatives_exist", "anchor_low",
             "I think it is acceptable to use animals for a test when a validated non-animal method already exists.",
             "I think it is unacceptable to use animals for a test when a validated non-animal method already exists."),
            ("major_advances", "anchor_high",
             "I think the animal research that produced treatments like insulin and polio vaccines was ethically justified.",
             "I think the animal research that produced treatments like insulin and polio vaccines was ethically unjustified."),
        ],
    ),
}


def build_items(facets, labels):
    items = []
    for index, (facet, layer, forward, reverse) in enumerate(facets):
        for reverse_coded, statement in ((False, forward), (True, reverse)):
            base = {
                "experiment": "screen", "suite": "belief",
                "index": len(items), "item_id": f"screen-{len(items):04d}",
                "pair_id": f"screen-pair-{index:04d}",
                "statement": statement, "scenario": None,
                "options": ["I agree", "I disagree"],
                # positive = the PRO side; a reverse item asserts ANTI, so agreeing is negative
                "positive_option": 1 if reverse_coded else 0,
                "facet": facet, "facet_claim": None, "layer": layer,
                "dimension": None, "framing": None, "reverse_coded": reverse_coded,
                "domain": None, "pressure": None,
            }
            items.append(base)
    return [row for item in items for row in suite_mod.option_variants(item, labels)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", default="A", choices=sorted(CANDIDATES))
    args = ap.parse_args()
    belief, facets = CANDIDATES[args.candidate]

    job = load_job(["+run=adhoc"])
    config = job.eval.evalgen
    assert config is not None
    rows = build_items(facets, config.option_labels)
    print(f"[screen] candidate {args.candidate}: {belief!r}")
    print(f"[screen] {len(rows)} rows = {len(rows)//2} statements x 2 option orders\n")

    model = local_model(job.training.model, job.models, adapter_path=None)
    scored = suite_mod.score_rows(model, rows, config, condition="base",
                                  model_tag=job.training.model)

    per_item = suite_mod.per_item(scored)
    by_id = {}
    for r in scored:
        by_id.setdefault(r["item_id"], r)
    print(f"{'facet':24s} {'dir':4s} {'layer':12s} {'P(pro)':>8s} {'var_gap':>8s}")
    gaps = []
    for iid in sorted(per_item):
        r = by_id[iid]
        gap = suite_mod.variant_gap([x for x in scored if x["item_id"] == iid])
        gaps.append(gap)
        d = "rev" if r["reverse_coded"] else "fwd"
        print(f"{r['facet']:24s} {d:4s} {r['layer']:12s} {per_item[iid]:8.4f} {gap:8.4f}")

    # A p_positive near 0.5 means one of two OPPOSITE things: the model is genuinely split,
    # or it answered on option position and the two orders averaged out. AGENTS.md is explicit
    # that variant_gap, not the point estimate, is what distinguishes them -- so the rule is
    # applied to the CONTENT-BEARING subset, and to everything, and both are printed.
    ids = sorted(per_item)
    gap_of = dict(zip(ids, gaps))

    def summarise(keys, label):
        v = [per_item[i] for i in keys]
        if not v:
            print(f"[screen] {label}: no items"); return None
        lo = sum(1 for x in v if x < 0.10); hi = sum(1 for x in v if x > 0.90)
        one = max(sum(1 for x in v if x < 0.5), sum(1 for x in v if x >= 0.5)) / len(v)
        print(f"[screen] {label}: n={len(v)}  mean={st.mean(v):.4f}  sd={st.pstdev(v):.4f}  "
              f"<0.10 {lo}/{len(v)} ({lo/len(v):.0%})  >0.90 {hi}/{len(v)} ({hi/len(v):.0%})  "
              f"one side of 0.5: {one:.0%}")
        return one, st.pstdev(v)

    print()
    all_stats = summarise(ids, "ALL items                 ")
    print(f"[screen] mean variant_gap {st.mean(gaps):.4f}  max {max(gaps):.4f}  "
          f"items with gap>0.90: {sum(1 for g in gaps if g > 0.90)}/{len(gaps)}")
    print()
    # The threshold is a post-hoc judgement and is reported as one; the verdict is printed at
    # several cuts so a reader can see whether it depends on the choice.
    for cut in (0.30, 0.50, 0.75):
        keys = [i for i in ids if gap_of[i] < cut]
        summarise(keys, f"content-bearing (gap<{cut:.2f})")

    print("\n[screen] H35's REJECTION RULE, registered before this ran: reject if >=80% on one "
          "side of 0.5, or sd < 0.15, or statements broadly position-driven.")
    clean = [i for i in ids if gap_of[i] < 0.50]
    cv = [per_item[i] for i in clean]
    one_clean = max(sum(1 for x in cv if x < 0.5), sum(1 for x in cv if x >= 0.5)) / len(cv) if cv else 0
    position_driven = sum(1 for g in gaps if g > 0.90) / len(gaps)
    reasons = []
    if one_clean >= 0.80: reasons.append(f"{one_clean:.0%} of content-bearing items on one side of 0.5")
    if all_stats and all_stats[1] < 0.15: reasons.append("sd < 0.15")
    if position_driven >= 0.30: reasons.append(f"{position_driven:.0%} of items answered on option position (gap>0.90)")
    print(f"[screen] VERDICT: {'REJECT -- ' + '; '.join(reasons) if reasons else 'PASSES SCREEN -> pilot'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
