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

This is deliberately open-ended. The system exists to generate and test hypotheses until
one is interesting enough, well-enough controlled, and novel enough to carry a paper —
not to defend any particular candidate finding.

**Where the current candidate contributions live: `STATE.md`.** They are results, results
change, and the session that treats them as fixed will defend them instead of testing them.

## Standing scope decisions

Stable enough to live here; revisable with reasoning like everything else.

- **No corroborative attribution.** Nothing here identifies which documents support a
  given generation; the leakage/recoverability checks serve corpus validity, not
  provenance.
- **No claim of causal mediation.** `propagation = T_A / T_B` is operational, and is not
  quotable while its numerator straddles zero.
- **No method survey.** Attribution methods are run when a claim cannot be stated without
  them (first-order, single-checkpoint methods were run 2026-08-20b for exactly that
  reason), but evaluating the method literature is not the contribution.

## The loop

Each session runs this cycle, as many times as it can do honestly:

1. **Orient.** Read this file, `STATE.md`, `hypotheses/open/` (only `open/` — three files,
   capped), and the most recent changelog entries until they stop being relevant.
2. **Design** the experiment that most moves an open hypothesis. Name which one. Write the
   falsifier — what result kills the claim — *before* the evidence exists, in the run
   overlay or hypothesis file. An experiment that bears on no open hypothesis may still be
   worth running, but that is a decision to state, not an accident. **Before spending on
   it, check the falsifier's own terms against `AGENTS.md` and the target suite's
   validity checks** (does it name a quantity that is already established not to mean
   what the falsifier assumes; does a null-control or positive-control facet exist that
   the falsifier's read will depend on but doesn't mention) — cheap now, expensive as a
   post-hoc correction. Added 2026-08-21 after two falsifiers this session needed exactly
   that correction (`hypotheses/open/H8-generality.md`).
3. **Pilot** whenever uncertain: a handful of items, **read by eye** (this is a human
   gate, not a judge threshold — every corpus lineage here has had a defect the judges
   passed). Only then spend.
4. **Run.** Gate first (`choice_bench`); believe nothing from an arm that fails it. Net
   against a matched control; re-derive the machinery term whenever the control changes.
5. **Read** netted, with intervals, per arm — and on both probability and log-odds scales
   whenever a sign call is near a boundary.
6. **Introspect, hardest when results MATCH the prediction.** Confirmation is where
   circular arguments hide: this project once took "2.35 × 7.03 = 16.5, exactly the
   observed total" as evidence of multiplicativity, and it was an arithmetic identity that
   could not have come out otherwise. Ask what result *could not* have occurred.
7. **Update** the hypothesis files — status is the folder, `open/` stays at three, a
   resolved hypothesis names its successor if one is earned. Then `STATE.md`, then the
   changelog entry, then push (git, `data-push`, `cache-push`).

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

Do not build a mechanism hypothesis on anything below the band level. When two successive
hypotheses on one axis die to seed or batch noise, the data supports less than it appears
to — that is a finding about precision, and the move is to *harden*, not to theorize a
third time.

## Portfolio discipline

The loop is greedy and local experiments are always cheapest, so left alone it tunnels —
one 24-hour stretch produced five hypothesis files on a single axis while the
biggest-named gap sat untouched. Structural counterweights:

- **The three open hypotheses must not all share one axis or experiment.** If they do,
  resolve one before opening another on that axis.
- **No open hypothesis untouched for more than ~5 cycles.** The expensive lateral move
  (new topic, new model) keeps losing marginal-value comparisons to cheap local ones; a
  pilot-sized probe of the untouched direction (~$1, an hour) breaks the tie without
  committing.
- Classify each cycle as **deepen** (mechanism), **harden** (seeds, controls,
  replication), or **widen** (new topic, model, instrument family), and notice when a
  window has had no widen moves. Pivot on saturation signals — successive falsifications
  from noise, effect sizes below quotability, results that would not change the paper —
  not on a fixed schedule; schedules abandon hot streaks.

## Literature contact

Two mandatory touchpoints, deliberately not more:

- **When opening a hypothesis:** one focused search — has this been shown, and is the
  falsifier already answered? A known result changes what to register (e.g. TracIn is
  multi-checkpoint in the original paper; the single-checkpoint approximation had to be
  caveated after the fact).
- **Before claiming a contribution:** a novelty sweep. A finding that replicates known
  work is reported as a replication in a controlled testbed — which can still be a
  contribution, but only if stated as one.

Not mid-execution: letting search redirect a running cycle thrashes, and reading answers
before registering falsifiers is fine (prior knowledge) but reading them after seeing
results is the post-hoc trap.

## Success criteria

The paper states a measured claim with a matched control, a positive control, uncertainty
on every number at the quotability level actually earned, novelty checked against the
literature, and artifacts a reader can re-run from the repo. A referee who disbelieves any
cell should be able to locate the arm, the item bank, and the raw per-item responses that
produced it.

## Where everything else lives

| what | where |
| --- | --- |
| current candidate contributions, standing results, next steps | `STATE.md` |
| live claims and their falsifiers | `hypotheses/open/` (resolved: `supported/`, `falsified/`) |
| methodology, instruments, hard-won rules | `AGENTS.md` |
| what happened, dated | `changelog/` |
| fresh-box bootstrap | `SETUP.md` |
