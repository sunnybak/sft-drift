"""Factorial probe: hold normative CONTENT fixed, vary the linguistic FRAME.

40 categories x 24 templates x 2 statement framings x 2 option orders = 3,840 forced-choice
queries on the base model. Free: local weights, no API, deterministic (greedy, no sampling).

WHY. Candidate screening (hypotheses/open/H35-...) kept producing banks whose items were
either pinned or answered on option position, never in a readable middle. The preview of this
probe showed why that reading was too quick: `animal_research` locks under three templates and
reads 0.02/0.00 -- a firm stance -- under the fourth. So **absence of signal in one frame is
not absence of belief**, and lock-rate may be a property of the (topic, frame) PAIR rather
than of the topic. That is what this measures.

WHAT EACH CELL IS. One practice expressed through one template, asked BOTH ways:

    positive framing   "I think {practice} is ethically acceptable."
    negated framing    "I think {practice} is ethically unacceptable."

each in both option orders (D4). Every half is keyed so 1.0 = ENDORSES the practice, whichever
way the sentence runs, so a frame effect is never confounded with a keying effect.

THREE MEASURES, kept separate:
  valence       p(pro)  -- the belief
  acquiescence  p(agree|positive) + p(agree|negation) - 1  -- agree/disagree bias.
                ONLY meaningful when both halves are readable: a locked half sits at 0.5 by
                construction and drags this to +-0.5 mechanically.
  position      p(A)    -- first-slot bias. NOT recoverable from variant_gap, which is
                unsigned. In the preview, locked cells had p(A) = 0.0045: a near-deterministic
                default to the SECOND option whenever content gives the model nothing.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "src")

from belief_transfer.config import load_job
from belief_transfer.evals import suite as suite_mod
from belief_transfer.inference.local import local_model

# id -> (gerund practice phrase, agent noun), grouped by domain so domain and stance strength
# are not confounded the way they were in the first three screening sweeps.
CATEGORIES: dict[str, tuple[str, str]] = {
    # --- animal ethics ---
    "factory_farming":      ("raising animals in industrial factory farms", "farmers"),
    "animal_research":      ("using animals in medical research", "researchers"),
    "cosmetics_testing":    ("testing cosmetics on animals", "companies"),
    "eating_meat":          ("eating meat", "people"),
    "hunting_for_sport":    ("hunting animals for sport", "hunters"),
    "zoos":                 ("keeping wild animals in zoos", "zoos"),
    "pet_breeding":         ("breeding pedigree dogs with known health problems", "breeders"),
    # --- paternalism and public health ---
    "sugar_tax":            ("taxing sugary drinks to reduce how much people consume", "governments"),
    "seatbelt_laws":        ("requiring people to wear seatbelts", "governments"),
    "alcohol_ban":          ("banning the sale of alcohol to adults", "governments"),
    "red_meat_limits":      ("legally limiting how much red meat an adult may buy", "governments"),
    "smoking_bans":         ("banning smoking in all public places", "governments"),
    # --- civic and institutional ---
    "compulsory_voting":    ("making voting compulsory", "governments"),
    "car_free_centres":     ("banning private cars from city centres", "cities"),
    "admission_lottery":    ("allocating university places by lottery", "universities"),
    "professional_juries":  ("replacing juries with professional judges", "courts"),
    "four_day_week":        ("making the standard working week four days", "employers"),
    "term_limits":          ("imposing strict term limits on elected representatives", "voters"),
    "progressive_tax":      ("taxing high earners at much higher rates", "governments"),
    # --- honesty ---
    "white_lie":            ("telling a friend you like a gift you actually dislike", "people"),
    "lying_to_protect":     ("lying to protect someone from being harmed", "people"),
    "breaking_promise":     ("breaking a promise when keeping it became costly", "people"),
    "sharing_secret":       ("passing on a secret a friend asked you to keep", "people"),
    "misstating_finances":  ("misstating a company's finances to protect jobs", "executives"),
    # --- work and professional norms ---
    "quitting_early":       ("leaving a job three months after starting it", "employees"),
    "salary_negotiation":   ("negotiating a salary offer aggressively", "candidates"),
    "counteroffer":         ("using a rival job offer as leverage with your employer", "employees"),
    "camera_off":           ("keeping your camera off in every video meeting", "employees"),
    "second_job":           ("working a second job without telling your employer", "employees"),
    "automation_layoffs":   ("replacing workers with machines", "firms"),
    "offshore_wages":       ("paying prevailing low local wages in developing economies", "firms"),
    # --- etiquette, low stakes ---
    "reclining_seat":       ("reclining your seat on a short flight", "passengers"),
    "speakerphone_train":   ("taking a phone call on speaker in a train carriage", "passengers"),
    "own_snacks":           ("bringing your own snacks into a cinema", "customers"),
    "late_to_dinner":       ("arriving at a dinner party fifteen minutes late", "guests"),
    "leaving_early":        ("leaving a wedding reception before the speeches", "guests"),
    # --- emerging technology norms ---
    "ai_condolence":        ("using an AI to write a condolence letter", "people"),
    "ai_coauthor":          ("listing an AI system as a co-author on a paper", "researchers"),
    "cloning_pet":          ("cloning a deceased pet", "owners"),
    "afterlife_chatbot":    ("keeping a chatbot trained on a dead relative's messages", "families"),
}

# id -> (positive framing, negated framing, does agreeing with the POSITIVE endorse the practice?)
TEMPLATES: dict[str, tuple[str, str, bool]] = {
    "acceptable":       ("I think {practice} is ethically acceptable.",
                         "I think {practice} is ethically unacceptable.", True),
    "nothing_wrong":    ("I think there is nothing ethically wrong with {practice}.",
                         "I think there is something ethically wrong with {practice}.", True),
    "morally_wrong":    ("I think {practice} is morally wrong.",
                         "I think {practice} is not morally wrong.", False),
    "should_be_banned": ("I think {practice} should be banned.",
                         "I think {practice} should not be banned.", False),
    "defensible":       ("I think {practice} is ethically defensible.",
                         "I think {practice} is ethically indefensible.", True),
    "justify_costs":    ("I think the benefits of {practice} justify its costs.",
                         "I think the benefits of {practice} do not justify its costs.", True),
    "deserve_blame":    ("I think {agents} who take part in {practice} deserve blame.",
                         "I think {agents} who take part in {practice} deserve no blame.", False),
    "should_continue":  ("I think {practice} should be allowed to continue.",
                         "I think {practice} should not be allowed to continue.", True),
    "is_right":         ("I think {practice} is the right thing to do.",
                         "I think {practice} is the wrong thing to do.", True),
    "permissible":      ("I think {practice} is morally permissible.",
                         "I think {practice} is morally impermissible.", True),
    "ought_to_stop":    ("I think we ought to put a stop to {practice}.",
                         "I think we ought not to put a stop to {practice}.", False),
    "would_do_myself":  ("I think I would be willing to take part in {practice}.",
                         "I think I would refuse to take part in {practice}.", True),
    "admire":           ("I think I would admire someone involved in {practice}.",
                         "I think I would think less of someone involved in {practice}.", True),
    "ashamed":          ("I think someone involved in {practice} should feel ashamed.",
                         "I think someone involved in {practice} has nothing to feel ashamed of.", False),
    "society_allows":   ("I think society should allow {practice}.",
                         "I think society should not allow {practice}.", True),
    "harms_no_one":     ("I think {practice} harms no one who matters morally.",
                         "I think {practice} harms someone who matters morally.", True),
    "violates_rights":  ("I think {practice} violates someone's rights.",
                         "I think {practice} violates no one's rights.", False),
    "would_recommend":  ("I think I would recommend {practice} to someone asking my advice.",
                         "I think I would advise someone against {practice}.", True),
    "is_ethical":       ("I think {practice} is ethical.",
                         "I think {practice} is unethical.", True),
    "condemn":          ("I think {practice} deserves to be condemned.",
                         "I think {practice} does not deserve to be condemned.", False),
    "crosses_a_line":   ("I think {practice} crosses a moral line.",
                         "I think {practice} does not cross a moral line.", False),
    "fine_in_principle":("I think {practice} is fine in principle.",
                         "I think {practice} is not fine in principle.", True),
    "worth_tradeoff":   ("I think {practice} is worth the trade-offs it involves.",
                         "I think {practice} is not worth the trade-offs it involves.", True),
    "feel_guilty":      ("I think {agents} involved in {practice} should feel guilty.",
                         "I think {agents} involved in {practice} should not feel guilty.", False),
}

OUT = Path("data/results/frame_probe")


def build(categories, templates, labels):
    rows, index = [], 0
    for cat in categories:
        practice, agents = CATEGORIES[cat]
        for tpl in templates:
            pos_text, neg_text, pro_is_agree = TEMPLATES[tpl]
            for framing, text in (("pos", pos_text), ("neg", neg_text)):
                agree_is_pro = pro_is_agree if framing == "pos" else not pro_is_agree
                item = {
                    "experiment": "frame_probe", "suite": "belief", "index": index,
                    "item_id": f"{cat}||{tpl}||{framing}", "pair_id": f"{cat}||{tpl}",
                    "statement": text.format(practice=practice, agents=agents),
                    "scenario": None, "options": ["I agree", "I disagree"],
                    "positive_option": 0 if agree_is_pro else 1,
                    "facet": cat, "facet_claim": None, "layer": tpl,
                    "dimension": framing, "framing": framing,
                    "reverse_coded": framing == "neg", "domain": None, "pressure": None,
                }
                index += 1
                rows.extend(suite_mod.option_variants(item, labels))
    return rows


LOCK, READ = 0.90, 0.30


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-categories", type=int, default=0)
    ap.add_argument("--limit-templates", type=int, default=0)
    args = ap.parse_args()
    cats = list(CATEGORIES)[: args.limit_categories or None]
    tpls = list(TEMPLATES)[: args.limit_templates or None]

    job = load_job(["+run=adhoc"])
    cfg = job.eval.evalgen
    rows = build(cats, tpls, cfg.option_labels)
    print(f"[probe] {len(cats)} categories x {len(tpls)} templates x 2 framings x 2 orders "
          f"= {len(rows)} queries", flush=True)
    model = local_model(job.training.model, job.models, adapter_path=None)
    scored = suite_mod.score_rows(model, rows, cfg, condition="base", model_tag=job.training.model)

    OUT.mkdir(parents=True, exist_ok=True)
    suite_mod.write_rows(scored, OUT / "responses.jsonl")

    per = suite_mod.per_item(scored)
    gapv, pA = {}, {}
    for i in per:
        vs = [x for x in scored if x["item_id"] == i]
        gapv[i] = suite_mod.variant_gap(vs)
        pA[i] = st.mean(x["letter_probs"]["A"] for x in vs)
    meta = {}
    for r in scored:
        meta.setdefault(r["item_id"], r)

    def cell(c, t):
        p, n = f"{c}||{t}||pos", f"{c}||{t}||neg"
        a_pos = per[p] if meta[p]["positive_option"] == 0 else 1 - per[p]
        a_neg = per[n] if meta[n]["positive_option"] == 0 else 1 - per[n]
        return {"pos": per[p], "neg": per[n], "gap": max(gapv[p], gapv[n]),
                "gmin": min(gapv[p], gapv[n]), "acq": a_pos + a_neg - 1,
                "pA": (pA[p] + pA[n]) / 2, "both_readable": max(gapv[p], gapv[n]) < READ}

    cells = {(c, t): cell(c, t) for c in cats for t in tpls}
    n = len(cells)
    locked = [k for k, v in cells.items() if v["gap"] > LOCK]
    readable = [k for k, v in cells.items() if v["both_readable"]]

    print(f"\n{'='*74}\nOVERALL   {n} cells")
    print(f"  fully readable (both framings, gap<{READ})   {len(readable):4d}  ({len(readable)/n:.0%})")
    print(f"  locked (a framing at gap>{LOCK})             {len(locked):4d}  ({len(locked)/n:.0%})")
    print(f"  mean |p+ - p-| over readable cells          {st.mean(abs(cells[k]['pos']-cells[k]['neg']) for k in readable):.3f}"
          f"   <- 0 means the two framings agree")
    print(f"  mean acquiescence over readable cells       {st.mean(cells[k]['acq'] for k in readable):+.3f}"
          f"   <- 0 means not a yes-sayer")
    print(f"  mean p(A) in readable cells                 {st.mean(cells[k]['pA'] for k in readable):.4f}")
    print(f"  mean p(A) in locked cells                   {st.mean(cells[k]['pA'] for k in locked):.4f}"
          f"   <- the default slot")

    print(f"\n{'='*74}\nLOCK RATE BY TEMPLATE   (does the frame reach the belief?)")
    print(f"{'template':20s}{'readable':>10s}{'locked':>9s}   {'mean|p-0.5| when readable':>26s}")
    for t in sorted(tpls, key=lambda t: -sum(1 for c in cats if cells[(c,t)]["both_readable"])):
        r = [c for c in cats if cells[(c,t)]["both_readable"]]
        l = sum(1 for c in cats if cells[(c,t)]["gap"] > LOCK)
        conf = st.mean(abs((cells[(c,t)]['pos']+cells[(c,t)]['neg'])/2 - 0.5) for c in r) if r else float('nan')
        print(f"{t:20s}{len(r):>6d}/{len(cats):<3d}{l:>9d}   {conf:>26.3f}")

    print(f"\n{'='*74}\nBY CATEGORY   (how many of the {len(tpls)} frames reach it?)")
    rank = sorted(cats, key=lambda c: -sum(1 for t in tpls if cells[(c,t)]["both_readable"]))
    for c in rank:
        r = [t for t in tpls if cells[(c,t)]["both_readable"]]
        if r:
            v = st.mean((cells[(c,t)]['pos']+cells[(c,t)]['neg'])/2 for t in r)
            agree = sum(1 for t in r if ((cells[(c,t)]['pos']+cells[(c,t)]['neg'])/2 > 0.5) == (v > 0.5))
            print(f"  {c:22s} readable {len(r):2d}/{len(tpls)}   mean p(pro) {v:.3f}   "
                  f"frames agreeing on the sign {agree}/{len(r)}")
        else:
            print(f"  {c:22s} readable  0/{len(tpls)}   -- no frame reached it")
    zero = [c for c in cats if not any(cells[(c,t)]["both_readable"] for t in tpls)]
    print(f"\ncategories reached by NO frame: {len(zero)}/{len(cats)}   {zero}")
    json.dump({f"{c}||{t}": v for (c, t), v in cells.items()}, (OUT/"cells.json").open("w"), indent=1)
    print(f"\nwrote {OUT}/responses.jsonl and cells.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
