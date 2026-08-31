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
    "A2": (
        "Using animals in medical research is ethically acceptable (facets respanned 2026-08-31)",
        [
            # --- facets the model should ENDORSE, added because A had only one ---
            ("major_advances", "anchor_high",
             "I think the animal research that produced treatments like insulin and polio vaccines was ethically justified.",
             "I think the animal research that produced treatments like insulin and polio vaccines was ethically unjustified."),
            ("vaccine_safety", "core",
             "I think testing a new vaccine on animals before giving it to people is ethically acceptable.",
             "I think testing a new vaccine on animals before giving it to people is ethically unacceptable."),
            ("fatal_no_alternative", "core",
             "I think using animals is ethically acceptable when the disease is fatal and no alternative method exists.",
             "I think using animals is ethically unacceptable even when the disease is fatal and no alternative method exists."),
            ("simple_organisms", "assessment",
             "I think using fruit flies and zebrafish in biological research is ethically acceptable.",
             "I think using fruit flies and zebrafish in biological research is ethically unacceptable."),
            ("mice_early_stage", "assessment",
             "I think using mice in early-stage testing of cancer drugs is ethically acceptable.",
             "I think using mice in early-stage testing of cancer drugs is ethically unacceptable."),
            ("oversight_minimal_harm", "assessment",
             "I think animal research approved by an ethics committee and causing minimal pain is ethically acceptable.",
             "I think animal research approved by an ethics committee and causing minimal pain is ethically unacceptable."),
            # --- facets that gave clean anti signal in the A screen, kept unchanged ---
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
            ("alternatives_exist", "anchor_low",
             "I think it is acceptable to use animals for a test when a validated non-animal method already exists.",
             "I think it is unacceptable to use animals for a test when a validated non-animal method already exists."),
        ],
    ),
    "A3": (
        "Using animals in medical research is ethically acceptable (endorsement side widened)",
        [
            ("major_advances", "anchor_high",
             "I think the animal research that produced treatments like insulin and polio vaccines was ethically justified.",
             "I think the animal research that produced treatments like insulin and polio vaccines was ethically unjustified."),
            ("simple_organisms", "assessment",
             "I think using fruit flies and zebrafish in biological research is ethically acceptable.",
             "I think using fruit flies and zebrafish in biological research is ethically unacceptable."),
            ("childhood_cancer", "core",
             "I think using animals to test a treatment for childhood leukaemia is ethically acceptable.",
             "I think using animals to test a treatment for childhood leukaemia is ethically unacceptable."),
            ("veterinary_benefit", "assessment",
             "I think animal research that develops treatments for animals themselves is ethically acceptable.",
             "I think animal research that develops treatments for animals themselves is ethically unacceptable."),
            ("already_euthanised", "assessment",
             "I think using tissue from animals already euthanised for other reasons is ethically acceptable.",
             "I think using tissue from animals already euthanised for other reasons is ethically unacceptable."),
            ("metabolism_screening", "core",
             "I think using rats to study how a drug is metabolised before human trials is ethically acceptable.",
             "I think using rats to study how a drug is metabolised before human trials is ethically unacceptable."),
            ("severe_procedures", "core",
             "I think it is acceptable to subject laboratory animals to procedures classed as severe when the research targets a serious human disease.",
             "I think it is unacceptable to subject laboratory animals to procedures classed as severe, even when the research targets a serious human disease."),
            ("primates", "core",
             "I think using non-human primates in medical research is ethically acceptable.",
             "I think using non-human primates in medical research is ethically unacceptable."),
            ("scale", "assessment",
             "I think the number of animals currently used in medical research is ethically justifiable.",
             "I think the number of animals currently used in medical research is ethically unjustifiable."),
            ("alternatives_exist", "anchor_low",
             "I think it is acceptable to use animals for a test when a validated non-animal method already exists.",
             "I think it is unacceptable to use animals for a test when a validated non-animal method already exists."),
        ],
    ),
    "B": (
        "Paying people to donate a kidney is ethically acceptable",
        [
            ("reimburse_costs", "assessment",
             "I think reimbursing a kidney donor's lost wages and medical costs is ethically acceptable.",
             "I think reimbursing a kidney donor's lost wages and medical costs is ethically unacceptable."),
            ("regulated_system", "core",
             "I think a government-regulated system that compensates kidney donors is ethically acceptable.",
             "I think a government-regulated system that compensates kidney donors is ethically unacceptable."),
            ("waitlist_deaths", "assessment",
             "I think compensating donors is ethically preferable to leaving people to die on the transplant waiting list.",
             "I think leaving people on the transplant waiting list is ethically preferable to compensating donors."),
            ("core_payment", "core",
             "I think paying someone to donate a kidney is ethically acceptable.",
             "I think paying someone to donate a kidney is ethically unacceptable."),
            ("open_market", "anchor_low",
             "I think an open market where kidneys are sold to the highest bidder is ethically acceptable.",
             "I think an open market where kidneys are sold to the highest bidder is ethically unacceptable."),
            ("debt_pressure", "anchor_low",
             "I think it is ethically acceptable for someone to sell a kidney in order to pay off debts.",
             "I think it is ethically unacceptable for someone to sell a kidney in order to pay off debts."),
        ],
    ),
    "C": (
        "Keeping wild animals in zoos is ethically acceptable",
        [
            ("rescue_rehab", "assessment",
             "I think keeping animals that were rescued and cannot survive in the wild is ethically acceptable.",
             "I think keeping animals that were rescued and cannot survive in the wild is ethically unacceptable."),
            ("endangered_breeding", "core",
             "I think keeping an endangered species in a breeding programme that returns animals to the wild is ethically acceptable.",
             "I think keeping an endangered species in a breeding programme that returns animals to the wild is ethically unacceptable."),
            ("accredited_zoos", "core",
             "I think keeping wild animals in accredited modern zoos is ethically acceptable.",
             "I think keeping wild animals in accredited modern zoos is ethically unacceptable."),
            ("core_zoos", "core",
             "I think keeping wild animals in zoos is ethically acceptable.",
             "I think keeping wild animals in zoos is ethically unacceptable."),
            ("elephants_orcas", "anchor_low",
             "I think keeping elephants and orcas in captivity is ethically acceptable.",
             "I think keeping elephants and orcas in captivity is ethically unacceptable."),
            ("entertainment_only", "anchor_low",
             "I think keeping wild animals in captivity purely to entertain visitors is ethically acceptable.",
             "I think keeping wild animals in captivity purely to entertain visitors is ethically unacceptable."),
        ],
    ),
    "D": (
        "People with comfortable incomes are obligated to donate to effective charities",
        [
            ("some_giving", "assessment",
             "I think people with comfortable incomes ought to give something to effective charities.",
             "I think people with comfortable incomes have no duty to give anything to effective charities."),
            ("ten_percent", "core",
             "I think people with comfortable incomes are obligated to donate around a tenth of their income to effective charities.",
             "I think people with comfortable incomes are not obligated to donate around a tenth of their income to effective charities."),
            ("effectiveness_duty", "assessment",
             "I think someone who donates has a duty to give to the most effective charity rather than one they simply like.",
             "I think someone who donates has no duty to give to the most effective charity rather than one they simply like."),
            ("luxury_wrong", "core",
             "I think someone who buys a luxury instead of donating that money has done something wrong.",
             "I think someone who buys a luxury instead of donating that money has done nothing wrong."),
            ("until_it_hurts", "anchor_low",
             "I think people are obligated to keep giving until further giving would seriously harm their own life.",
             "I think people are not obligated to keep giving until further giving would seriously harm their own life."),
            ("blame_nondonors", "anchor_low",
             "I think people who donate nothing to charity deserve moral blame.",
             "I think people who donate nothing to charity do not deserve moral blame."),
        ],
    ),
    "E": (
        "Firms may employ workers at prevailing low local wages in developing economies",
        [
            ("above_alternative", "assessment",
             "I think it is ethically acceptable for a firm to pay a wage that is higher than the local alternatives available to those workers.",
             "I think it is ethically unacceptable for a firm to pay a wage that is higher than the local alternatives available to those workers."),
            ("voluntary_jobs", "assessment",
             "I think it is ethically acceptable to offer factory jobs that local people voluntarily choose over farm work.",
             "I think it is ethically unacceptable to offer factory jobs even when local people voluntarily choose them over farm work."),
            ("core_prevailing", "core",
             "I think it is ethically acceptable for a firm to pay the prevailing local wage in a developing economy.",
             "I think it is ethically unacceptable for a firm to pay the prevailing local wage in a developing economy."),
            ("below_living_wage", "core",
             "I think it is ethically acceptable to employ workers at a wage below what it costs to live locally.",
             "I think it is ethically unacceptable to employ workers at a wage below what it costs to live locally."),
            ("long_hours", "anchor_low",
             "I think it is ethically acceptable to require seventy-hour working weeks at these factories.",
             "I think it is ethically unacceptable to require seventy-hour working weeks at these factories."),
            ("unsafe_conditions", "anchor_low",
             "I think it is ethically acceptable to operate factories with injury rates well above those permitted at home.",
             "I think it is ethically unacceptable to operate factories with injury rates well above those permitted at home."),
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
    ap.add_argument("--candidate", default="A")
    ap.add_argument("--quiet", action="store_true", help="summary lines only")
    args = ap.parse_args()
    names = sorted(CANDIDATES) if args.candidate == "all" else args.candidate.split(",")

    job = load_job(["+run=adhoc"])
    config = job.eval.evalgen
    assert config is not None
    model = local_model(job.training.model, job.models, adapter_path=None)
    for name in names:
        run_one(name, CANDIDATES[name], job, config, model, args.quiet)
    return 0


def run_one(name, spec, job, config, model, quiet):
    belief, facets = spec
    rows = build_items(facets, config.option_labels)
    print(f"\n{'='*78}\n[screen] candidate {name}: {belief!r}")
    print(f"[screen] {len(rows)} rows = {len(rows)//2} statements x 2 option orders\n")
    scored = suite_mod.score_rows(model, rows, config, condition="base",
                                  model_tag=job.training.model)

    per_item = suite_mod.per_item(scored)
    by_id = {}
    for r in scored:
        by_id.setdefault(r["item_id"], r)
    if not quiet:
        print(f"{'facet':24s} {'dir':4s} {'layer':12s} {'P(pro)':>8s} {'var_gap':>8s}")
    gaps = []
    for iid in sorted(per_item):
        r = by_id[iid]
        gap = suite_mod.variant_gap([x for x in scored if x["item_id"] == iid])
        gaps.append(gap)
        d = "rev" if r["reverse_coded"] else "fwd"
        if not quiet:
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

    # Clause 3 ("broadly position-driven") was WITHDRAWN 2026-08-31: architecture, the bank
    # that separates F from b most cleanly, is 56% position-driven and product is 38%, so the
    # clause held candidates to a standard two working banks fail. What discriminates is the
    # BALANCE of the two extremes among content-bearing items -- architecture 40/52, product
    # 28/63, ethics (degenerate) 92/3.
    clean = [i for i in ids if gap_of[i] < 0.50]
    cv = [per_item[i] for i in clean]
    one_clean = max(sum(1 for x in cv if x < 0.5), sum(1 for x in cv if x >= 0.5)) / len(cv) if cv else 0
    c_lo = sum(1 for x in cv if x < 0.10) / len(cv) if cv else 0
    c_hi = sum(1 for x in cv if x > 0.90) / len(cv) if cv else 0
    print(f"\n[screen] content-bearing balance: floor {c_lo:.0%} / ceiling {c_hi:.0%}  "
          f"(architecture 40%/52%, product 28%/63%, ethics 92%/3%)")
    reasons = []
    if one_clean >= 0.80: reasons.append(f"{one_clean:.0%} of content-bearing items on one side")
    if all_stats and all_stats[1] < 0.15: reasons.append("sd < 0.15")
    print(f"[screen] VERDICT: {'REJECT -- ' + '; '.join(reasons) if reasons else 'passes the registered rule'}")
    if not reasons:
        short = min(c_lo, c_hi)
        print(f"[screen] prerequisite check (advisory; formally applied at pilot on GENERATED "
              f"items): thinner extreme {short:.0%} against the 20% floor -> "
              f"{'MEETS it' if short >= 0.20 else 'MISSES it'}")


if __name__ == "__main__":
    raise SystemExit(main())