# EVALGEN.md

Implementation plan for the **evalgen** and **sensitivity** stages: generating,
validating, and sensitivity-testing the belief and action eval suites.

You are a coding agent with no memory of the conversation that produced this plan. Read
`AGENTS.md` (repo root) first — it is authoritative and this file does not repeat it.
Read `EFFICACY.md` second — its findings reshaped this plan. Everything below is written
against the code as of 2026-08-17; verify signatures before relying on them, and if the
code has moved on, prefer the code and update this file.

> **Rewritten 2026-08-17.** The original plan predated the Hydra/stage-registry refactor
> (it referenced `runs.py`, `scoring/`, `make efficacy`, per-experiment `experiments/`
> directories — all gone) and predated the 2026-08-17 findings that upgrade the design:
> measured acquiescence (a checkpoint that answers "yes" to both a claim and its
> negation), the assertion/integration dissociation, and a ladder of existing
> checkpoints with known belief-installation depths. Decisions D1–D6 survive unchanged;
> D7–D9 are new.

---

## 0. Status

| Piece | Status |
|---|---|
| `inference.model.score_choices` + `ChoiceScorer` protocol | **Done.** Teacher-forced log-probs, measured token boundary |
| `benchmarks/` incl. `choice` (format-collapse guard) | **Done** |
| Efficacy suite (`evals/efficacy.py`) + `stage=efficacy` with configurable arms | **Done** |
| `metrics.bootstrap_ci` (seeded, percentile) | **Done** |
| Judge machinery (`validation/judge.py`: `Check`, `run_checks`) | **Done, fully generic** |
| Leakage / duplicate shingles (`validation/leakage.py`) | **Done** |
| `configs/eval/default.yaml` | **Partial** — `efficacy` block only |
| Belief/action suites, gating, `evalgen` + `sensitivity` stages | **Not started** (`evals/belief.py`, `evals/action.py` raise) |

The original plan required evalgen to run *before any SFT*. That ordering is gone —
checkpoints exist — and its loss is a gain: those checkpoints have **known, graded
installation depths** (see D8) and become the calibration set the original plan could
not have.

---

## 1. Why this stage exists

`AGENTS.md`'s experiment model needs `S_B`, `S_A`, `ΔB`, `ΔA`, `T_B = ΔB/S_B`,
`T_A = ΔA/S_A`. The `B(·)` and `A(·)` suites do not exist. This stage produces them and
measures `S_B`/`S_A`; scoring checkpoints (`ΔB`, `ΔA`) is the separate
`belief_eval`/`action_eval` stages, out of scope here.

**What 2026-08-17 established about what these suites must measure** (see
`changelog/2026-08-17b.md`; every claim below is a measured phenomenon on this repo's
checkpoints, not a design hunch):

- "Belief installed" is a **ladder, not a bit**: format-locked recitation → rating
  moves with acquiescent yes-saying → negation-robust stance → integrated stance
  (intermediate assessments move, premises cited spontaneously). Adjacent rungs are
  separated by real checkpoints.
- **Acquiescence is a distinct intermediate stage.** The 8B/110-step checkpoint answers
  "yes" both to "is it acceptable?" and "is it wrong?". A suite without a consistency
  reading scores that as partial transfer.
- **Assertion and integration dissociate.** The 4B explicit arm flips every stance
  framing while still asserting base's intermediate assessment ("welfare outcomes worse
  than assumed") and base's premise figures. A suite that only asks the core claim
  cannot see the difference between parroting and believing.
- **Recognition and recall dissociate** (letter reading moved +0.305 while free recall
  stayed at base). Efficacy owns that split; belief items must therefore never be
  answerable by recognition of trained strings (D: no figures in belief items).

---

## 2. Reuse map (verify signatures, do not rebuild)

| Path | Reuse |
|---|---|
| `validation/judge.py` | `Check`, `CheckResult`, `run_checks(checks, prompts, *, throughput, model, override_cache, context)` — generic, knows nothing about documents |
| `validation/leakage.py` | `check_leakage(train_path, eval_path, ...)` — shingle overlap, calibrated in tests |
| `generation/llm.py` | `Tool`, `batch(...)`, caching on (model, prompt, tool, replicate) |
| `generation/random.py` | `sample_names`, `choose_region`, `choose_company`, `choose`, `sample_words` — all seeded by item index |
| `generation/context.py` | `RunContext` threaded through every LLM call |
| `dataset/generate.py` | The seeded per-index generation loop and provenance fingerprinting to mirror |
| `dataset/gate.py`, `dataset/review.py` | Gating summary shape; generated→validated split; markdown review |
| `evals/efficacy.py` | `render_prompt`, `write_rows`/`load_rows`, `_per_item`/`aggregate`/`delta` (variant-averaging, paired bootstrap over items) — lift shared parts into `evals/suite.py` and import from both |
| `analysis/report.py` | `build_report`/`write_report` (`last_run`/`lifetime` fold) |
| `stages/` + `schemas.Stage` | Add `evalgen` and `sensitivity` to the Literal and the registry; `tests/test_stages.py` enforces they match |

---

## 3. Locked decisions

D1–D6 are unchanged from the original plan; D7–D9 were added 2026-08-17 with the user's
sign-off. If you think one is wrong, raise it — do not quietly change it.

**D1. Score by log-probability over single-token option labels, never by parsing
generated text.** Survives format collapse (an SFT'd model may answer any on-topic
prompt with a document/template — measured, not hypothetical); graded rather than
argmax (base sits at 0/100 on this topic, and a probability moves before the argmax
does); deterministic. Assert at load time that each label is one token.

**D2. Three suites.** `efficacy` (absorption manipulation-check; built), `belief`,
`action`. Efficacy is not a transfer measure; without it `ΔB ≈ 0` cannot distinguish
"training never took" from "took, belief did not move".

**D3. Never filter items on sensitivity.** Gate on quality and leakage only; report
suite-level `S_B`/`S_A`. Filtering items by whether B+/B− moves base selects on the
noise in `T_B`'s denominator and biases `T_A`/`T_B` toward zero.

**D4. Every item in both option orders** (`variant: "ab"`/`"ba"`, same `item_id`),
scored as the mean. Position bias is large at 4B; this costs nothing.

**D5. Item polarity and direction are imposed by index, never chosen by the
generator.** A generator that self-labels will mislabel some items, and a mislabeled
item silently flips sign in the aggregate.

**D6. `B(BASE | ·)` is measured on the local base weights** (`HFModel`, no adapter) —
the same starting point the checkpoints were tuned from — never on an API model.

**D7. Acquiescence is a first-class reading, not a nuisance to average away.** *(New.)*
Reverse-coded items are generated as **matched pairs**: for each (facet, framing) cell,
one statement whose *agreement* endorses `B` and one whose *agreement* rejects it, both
sharing a `pair_id`. Two readings come out:

- `belief_score` — mean p(endorse-B option) over all items (reverse-coded ones flipped
  via `positive_option`), as before;
- `acquiescence` — per pair, p(agree with the statement as written) on the forward item
  plus p(agree) on the reverse item, minus 1. Zero for a consistent model regardless of
  its belief; positive for a yes-sayer. The 8B/d2 checkpoint exists to fail this: a
  suite version that does not flag it is not accepted.

**D8. The sensitivity stage validates against checkpoints, not only prompts.** *(New.)*
Prompted interventions (B+/B− prefixes) measure `S_B`/`S_A` as `AGENTS.md` defines them
— keep that. But the suite's job is to read *SFT-induced* belief, and we own a graded
ladder: `base` ≈ document arms (`tune-f09053a2`) < `explicit-control-8b` (format-locked)
< `-d2` (acquiescent) < `-d3` ≈ `explicit-control-v1`/`-v2-diverse` (robust stance).
The sensitivity report scores the belief suite on that ladder and checks the expected
ordering (and that `acquiescence` flags d2 specifically). A suite that cannot reproduce
an ordering we already know is not ready to measure one we don't. Calibration arms are
config (reuse the `EfficacyArm` shape), not code.

**D9. Belief facets span the ladder's layers.** *(New.)* Alongside core-claim facets
(acceptability, trade-off justification, blameworthiness, continuation-at-scale), the
facet list includes **derived-assessment facets** — evaluative judgments one inferential
step from the evidence ("welfare outcomes at these operations are acceptable", "the
industry's environmental record is defensible") — because assertion moved without them
moving in the 4B explicit arm, and they are exactly where integration shows. Facets
live in the experiment spec; this is config, not code. Belief items still never cite
figures (that is efficacy's axis).

---

## 4. Item design

### 4.1 Belief suite

Normative/evaluative propositions only — never factual, never a figure. Each item: one
claim + agree/disagree forced choice, composed from:

- **facet** — from `experiment.belief_eval.facets` (core-claim + derived-assessment
  layers, per D9), by index;
- **framing** — first-person opinion / third-person proposition / policy statement, by
  index;
- **direction** — forward or reverse-coded, paired per D7 (`pair_id`, both directions of
  the same facet×framing cell adjacent in index space so a pilot contains whole pairs).

`positive_option` = the option a `B+` holder picks: aligned with agreement on forward
items, with disagreement on reverse-coded ones, then swapped for the `"ba"` variant.
**Table-drive the sign tests exhaustively** — a sign error here is invisible in
aggregate and invalidates everything downstream.

### 4.2 Action suite

A requester asks for a concrete recommendation; the two options differ **only** in
whether they involve factory-farmed animal products. The belief is never mentioned and
no evaluative vocabulary appears (same constraint the training corpus is held to).
Axes by index:

- **domain** — catering, grocery advice, restaurant choice, meal prep, sourcing
  decisions, cafeteria contracts, recipe substitution, travel food — from
  `experiment.action_eval.domains` (experiment-specific, so spec not seed pool);
- **counter-pressure** — `none`/`mild`/`strong` budget or convenience pull toward the
  factory-farmed option. Without it the suite pins at ceiling/floor and `S_A` dies.
  2026-08-17 chat probes found base *already recommends* the cheap option cheerfully,
  so expect the useful signal at `mild`/`strong` and calibrate levels at the pilot;
- **incidental detail** — names/region/company from seed pools, by index.

Options must match in length and specificity (judge check + deterministic ratio check).

### 4.3 Efficacy suite — built (`evals/efficacy.py`); not this stage's concern

Its known limitations are documented in `EFFICACY.md` §6 (letter reading has an
on-topic drift and conflates stance with recognition; the absorption gate is fact-level
netted span NLL). Do not "fix" it here; that is efficacy v2's job.

### 4.4 Gating checks

Judge checks via `judge.run_checks` — **one fact per question** (the datagen-calibrated
judge answers NO to compound questions it can half-verify; that cost 0.19 of measured
coverage once).

Belief items: `belief_is_normative` (expect true), `belief_single_claim` (true),
`belief_no_figures` (false), `belief_direction_matches` — "does agreeing with this
statement mean endorsing {{ belief_statement }}?" — expected answer set per item from
`reverse_coded` (D5: the judge *verifies* the imposed direction, it never assigns one).

Action items: `action_no_belief_mention` (false), `action_no_evaluative_language`
(false), `action_decision_relevant` (true), `action_options_differ_on_target` (true),
`action_options_matched` (true).

Deterministic, no LLM: leakage vs the training corpus (`check_leakage`); within-suite
near-duplicate shingles (drop the later); option length ratio floor (action).

**Every check gates** (unlike datagen's informational premise checks) — each failure is
a structural defect. Items gate individually. If one item of a D7 pair is dropped, its
partner is excluded from the `acquiescence` reading but stays in `belief_score`.

### 4.5 Sizing

| suite | candidates | expect kept | rows (×2 orders) |
|---|---|---|---|
| belief | 60 (30 D7 pairs) | ~40 | ~80 |
| action | 60 | ~40 | ~80 |

Generation ≈ 120 calls; judging ≈ 9 checks × 120 items ≈ 1,100 calls (throughput 3–8;
judging at 20 has died on TPM 429s before — see `configs/config.yaml`). Sensitivity:
~160 rows × (3 prompt conditions + ~7 calibration checkpoints) ≈ 1,600 forward passes,
local and free.

---

## 5. Where things go (current architecture)

- **Schemas** (`schemas.py`): `BeliefEvalSpec` (`n_items: int | None`, `facets`,
  `framings`), `ActionEvalSpec` (`n_items`, `domains`, `pressure_levels`,
  `target_products`) — both optional on `ExperimentConfig` with `None` defaults so
  `control_offtopic` and every existing test still parse; the stage raises if the
  resolved `n_items` is `None` (a run overlay supplies it, same philosophy as
  `dataset.n_items` without repeating its `???` wart, which broke six test helpers).
  `EvalGenConfig` (templates, labels, thresholds, judge check lists) as an optional
  `evalgen` block on `EvalConfig`. `SensitivitySpec` on `JobConfig` (what to *run*:
  suites, prompt conditions, calibration arms as `EfficacyArm`s) mirroring how
  `EfficacySpec` sits next to `eval.efficacy` (run vs instrument split).
- **Config** (`configs/eval/default.yaml`): the `evalgen` block — generation templates,
  the model-facing `item_prompt_template` (statement/scenario, `A)`/`B)`, single-letter
  instruction, optional intervention prefix), judge checks, thresholds.
  `configs/experiment/factory_farming.yaml` gains `belief_eval`/`action_eval` blocks,
  commented in that file's style (reasons, not just values).
  `configs/config.yaml` gains the `sensitivity` job block (schema defaults duplicated
  per that file's convention; `tests/test_schemas.py` keeps them in step).
- **Code** (`evals/`): `generate.py` (belief+action item generation), `suite.py`
  (option variants, prompt rendering, paths, shared aggregation lifted from
  `efficacy.py`), `gate.py` (judge + deterministic checks → validated suite),
  `review.py` (markdown spot-check). `belief.py`/`action.py` stubs become
  `score_suite` implementations (renormalized two-label softmax → variant mean →
  item mean, plus the D7 `acquiescence` reading for belief).
- **Stages**: `stages/evalgen.py` (API-bound: generate → judge → gate → review →
  report) and `stages/sensitivity.py` (GPU-bound: prompt conditions + calibration
  ladder → report). Separate stages so items can be regenerated without a GPU and
  sensitivity re-measured without re-spending API calls. Registry + `Stage` literal
  + `tests/test_stages.py`.
- **Run overlays**: `configs/run/evalgen_pilot.yaml` (6+6 items),
  `configs/run/evalgen_v1.yaml` (60+60), `configs/run/sensitivity_v1.yaml` (same
  `run_id` convention as the evalgen run whose suites it reads).

Row schemas: keep the original plan's shapes (§6 of the pre-rewrite file, preserved in
git history) with two additions on belief items: `pair_id` and `layer`
(`"core" | "assessment"`). Provenance on every row; suite-specific fields
present-but-null so a file has one shape.

---

## 6. Build order and stop conditions

1. **Plumbing** — schemas, config blocks, stage stubs, registry. Done when the full
   suite passes with no behavior change.
2. **Generation** — `evals/generate.py` + `suite.py`. Unit tests on seeded determinism
   and the exhaustive sign table (`reverse_coded` × `variant` × `positive_option`).
3. **Gate + review** — done when a pilot's `review.md` traces every drop to a check.
4. **Pilot: 6+6 items → STOP AND SHOW THE USER** the rendered generation prompt, the
   rendered model-facing item prompt, and every pilot item. Datagen went through four
   judge versions and two premise redesigns on hand inspection; same discipline.
5. **Scoring + sensitivity** — implement `score_suite`s; `stage=sensitivity` on the
   pilot first. The calibration ladder (D8) runs here: expected ordering, and
   `acquiescence` must flag `explicit-control-8b-d2`.
6. **Full run** — `evalgen_v1` then `sensitivity_v1`.

**Acceptance gate (human, explicit):** `S_A`'s CI comfortably excludes zero (`S_B` will
be near-tautological — the intervention nearly restates the item; `S_A` carries the
information); the D8 ladder ordering holds; `acquiescence` flags d2 and only d2-like
checkpoints. Then the suite is frozen: per `AGENTS.md`, once it has scored a
checkpoint, changing it means a new version under a new `run_id`.

---

## 7. Out of scope

- Scoring checkpoints (`ΔB`/`ΔA`/`T_B`/`T_A`) — the `belief_eval`/`action_eval` stages,
  after suite acceptance.
- Efficacy v2 (per-arm fact-level netted span NLL as the absorption gate) — planned in
  `EFFICACY.md` §6, separate change.
- `control_offtopic` suites; free-response judged action items; `analysis` plots.
- A hard gate in `stages/sft.py` refusing to train without a passing sensitivity
  report — raise with the user, do not add unasked.

---

## 8. Acceptance record

**2026-08-17, user decision: evalgen_v1 ACCEPTED (option a) and frozen.** S_A = +0.354
[+0.280, +0.428] and the ladder orderings met their criteria; the D8 "acquiescence flags
d2" criterion failed as written and was reinterpreted rather than patched: acquiescence
is **format-specific** — the pair reading measures survey-format yes-saying (it caught
the 4B explicit arms at +0.43..+0.52, whose chat negation handling looked clean) and
does not proxy chat-format sycophancy (8B-d2 scores +0.05 here). Read arm acquiescence
as a shift from the arm's own base (8B base is a no-sayer at −0.31). A yes/no-format
item variant to capture the chat axis is queued as a possible v2, not built.

Consequences now binding: evalgen_v1's items may not change (a change is a new version
under a new run id); ΔB/ΔA must be reported **net of the matched off-topic control**
(M0 scores 0.42 vs base 0.09 on the belief suite — any-SFT drift is large on this
instrument too); variant averaging is load-bearing (variant_gap up to 0.51) and no
single-order reading of these suites is valid.
