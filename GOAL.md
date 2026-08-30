# GOAL

**Read this first, every session.** This file holds only what is INVARIANT: the goal, the
loop that pursues it, and the disciplines that keep results trustworthy. Everything mutable
lives elsewhere and this file points at it — that separation exists because this file's
predecessor (`problem_statement.md`, renamed 2026-08-21) baked the current candidate
contributions into the north star, and they rotted three times in one day as experiments
outran them.

**Mutability rule, inherited and unchanged:** this file changes only on the user's
feedback, with the reasoning recorded in that session's changelog entry. It is never
widened quietly to fit work already done — if a session's output does not serve this
goal, say so in the changelog and let the user decide whether the goal or the work was
wrong.

---

## THE PHASE HAS CHANGED — read this before anything else

**Revised 2026-08-30b on user direction; reasoning in `changelog/2026-08-30b.md`.**

This project was open-ended for most of its life: generate and test hypotheses until one is
interesting enough to carry a paper. **It is no longer.** The remaining time goes to
reaching a terminal point on results that already exist.

| | was | is now |
| --- | --- | --- |
| what a cycle is for | discovery — find the next effect | **refinement** — make an existing claim precise, caveated and defensible |
| what a new experiment must earn | that it moves an open hypothesis | that it **changes how an existing result may be stated**. If it cannot, it does not run |
| what "done" looks like | a finding good enough to write up | every standing claim at the quotability level it actually earned, with its caveats attached and its withdrawals recorded |
| the default answer to "should we build a new corpus/topic/instrument?" | maybe, if it widens | **no** |

**The three topics are the dataset. There will not be a fourth.** Factory farming,
software architecture and product opinion are built, trained at three seeds each, and read
on three suites. What remains is to say correctly what they show.

**Portfolio discipline is suspended, and deliberately so.** The `deepen / harden / widen`
balance below existed to stop the loop tunnelling on cheap local work while big gaps sat
untouched. In a terminal phase that pressure inverts: **widen moves are now the failure
mode**, not the cure. Harden and refine only.

**What still counts as legitimate work:**

- a validity check on a load-bearing claim that has never been run (a positive control, a
  cheapest-baseline comparison, a sensitivity check) — these can only sharpen or correct
  what is already reported, and an unrun one is a hole a reviewer will find
- re-reading an existing artifact under a contrast that was measured but never reported
  (`transfer.responses_from` does this with no GPU time)
- writing up: insight notes, and the paper
- recording a withdrawal, a caveat, or a gap honestly

**What does not:** a new topic, a new corpus family, a new instrument, or a mechanism probe
— however cheap and however interesting. Those go in `IDEAS.md` or
`hypotheses/resource_constrained/` with the reason they were not run.

---

## The goal

**A paper accepted at a venue whose call names two problems:**

- **Contributive attribution** — estimating the causal effect of training data on model
  behavior. Open questions: how reliable and robust are current approaches, and how can
  their outputs be verified or audited in practice?
- **Corroborative attribution** — identifying training data that supports a given
  generation. Open questions: what makes a good method, how do we evaluate them, and how
  can such attributions be verified and made meaningful downstream?

This project's angle: **we do not estimate a causal effect of training data — we install
one, and measure it.** Ground truth for attribution requires a known contribution with a
measured effect size; the pipeline manufactures exactly that, with matched controls,
leakage gates, and paired bootstrap intervals.

**Where the current candidate contributions live: `STATE.md`**, and each claim's own
provenance lives in `insights/<slug>/`. They are results, results change, and the session
that treats them as fixed will defend them instead of testing them — but in this phase,
testing them means checking their validity, not replacing them.

## Standing scope decisions

Stable enough to live here; revisable with reasoning like everything else.

- **No corroborative attribution.** Nothing here identifies which documents support a
  given generation; the leakage/recoverability checks serve corpus validity, not
  provenance.
- **No claim of causal mediation.** `propagation = T_A / T_B` is operational, and is not
  quotable while its numerator straddles zero.
- **No method survey.** Attribution methods are run when a claim cannot be stated without
  them, but evaluating the method literature is not the contribution.
- **No fourth topic** (added 2026-08-30b). Generality is now argued from the three built, or
  narrowed honestly — not extended.

## The loop

Each session runs this cycle, as many times as it can do honestly:

1. **Orient.** Read this file, `STATE.md`, `hypotheses/open/`, and the most recent changelog
   entries until they stop being relevant.
2. **Design** the check that most changes how an existing result may be stated. Name the
   claim it bears on. Write the falsifier — what result kills the claim — *before* the
   evidence exists. **Before spending on it, check the falsifier's own terms against
   `AGENTS.md` and the target suite's validity checks**: does it name a quantity already
   established not to mean what the falsifier assumes; does a null-control or
   positive-control facet exist that the read will depend on but does not mention.
3. **Pilot** whenever uncertain: a handful of items, **read by eye** (a human gate, not a
   judge threshold — every corpus lineage here has had a defect the judges passed).
4. **Run.** Gate first (`choice_bench`); believe nothing from an arm that fails it. Net
   against a matched control; re-derive the machinery term whenever the control changes.
5. **Read** netted, with intervals, per arm — and on both probability and log-odds scales
   whenever a sign call is near a boundary.
6. **Introspect, hardest when results MATCH the prediction.** Confirmation is where
   circular arguments hide: this project once took "2.35 × 7.03 = 16.5, exactly the
   observed total" as evidence of multiplicativity, and it was an arithmetic identity that
   could not have come out otherwise. Ask what result *could not* have occurred.
7. **Update** the hypothesis files, then `STATE.md`, then the changelog entry, then push
   (git, `data-push`, `cache-push`).

**Wind-up is part of the loop, not after it.** A finding that exists only in a session's
context is lost when the session ends.

## The quotability ladder

What a number may claim depends on what has been done to it. Learned the expensive way:
two mechanism hypotheses in one day were built on single-seed magnitudes and both were
falsified when a second seed moved one cell 2.13×.

| level | requires | may be stated as |
| --- | --- | --- |
| direction | one seed, gated, netted | "X increases Y" — provisionally |
| replicated direction | two seeds, controls retrained per seed | "X increases Y" |
| band | the ordering/separation holding at every seed run | "X's effect is in band B" |
| magnitude | stable across ≥3 seeds | "X is worth N×" |

Do not build a mechanism hypothesis on anything below the band level. **In this phase the
ladder is the main instrument**: the work is largely deciding which rung each standing claim
is actually on and writing it at that rung, not moving claims up it.

## Hypotheses in a terminal phase

`open/` is still capped at three, and the cap now binds harder: an open hypothesis must be
one whose resolution **changes how an existing result is stated**. A well-formed claim that
would need new corpora goes to `resource_constrained/` with the reason — not because it is
wrong, but because it is not what the remaining time is for. Two were moved there on
2026-08-30b (`H31`, `H32`) for exactly this reason, with their falsifiers untouched.

## Literature contact

- **Before claiming a contribution:** a novelty sweep. A finding that replicates known work
  is reported as a replication in a controlled testbed — which can still be a contribution,
  but only if stated as one. `LITERATURE.md` holds the current position.
- Reading answers before registering falsifiers is fine (prior knowledge); reading them
  after seeing results is the post-hoc trap.

## Success criteria

The paper states a measured claim with a matched control, a positive control, uncertainty
on every number at the quotability level actually earned, novelty checked against the
literature, and artifacts a reader can re-run from the repo. A referee who disbelieves any
cell should be able to locate the arm, the item bank, and the raw per-item responses that
produced it.

**The terminal test, added 2026-08-30b:** for every claim the project intends to make,
either an `insights/` note exists that ties each of its numerals to an artifact and states
its own limits, or the claim is not made. There is no separate ledger to fall behind.

## Where everything else lives

| what | where |
| --- | --- |
| current standing results, next steps, void and withdrawn claims | `STATE.md` |
| each quotable claim with its own numeral-level provenance and limits | `insights/<slug>/` |
| live claims and their falsifiers | `hypotheses/open/` (parked: `resource_constrained/`; resolved: `supported/`, `falsified/`) |
| pre-hypothesis ideas, explicitly not for this phase | `IDEAS.md` |
| methodology, instruments, hard-won rules | `AGENTS.md` |
| what happened, dated | `changelog/` |
| fresh-box bootstrap | `SETUP.md` |
