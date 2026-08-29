# AGENTS.md

> **Edit this file only. Never write to `CLAUDE.md` — it is a symlink to this
> file, not a copy.** Writing to both in one pass applies every edit twice (that is
> exactly how a duplicated section got into this document once already). `git ls-files -s`
> shows it as mode `120000`. Anything describing them as two copies to "keep in sync" is
> stale.

**This file is the framework, not the findings.** It holds how the project is built, how
an experiment is designed, and how a number is allowed to be read. What any particular run
measured lives in `data/results/<experiment>/<run_id>/`; what it implied lives in
`changelog/`, `hypotheses/`, and `insights/`; what is true right now lives in `STATE.md`.
Results were stripped out of this document deliberately — they rotted here, and a rule
stated with a stale number attached is worse than the rule alone. When a rule below needs
evidence, it points at where the evidence lives instead of quoting it.

## Project purpose

This repository studies whether beliefs induced through supervised fine-tuning (SFT)
transfer into downstream behavior.

The core experimental chain is:

```text
training corpus
    ↓
belief acquisition
    ↓
behavioral propagation
```

For each experiment, we construct matched SFT corpora representing different underlying
evidence or positions, fine-tune models on them, measure whether the model's directly
expressed belief changes, and measure whether that change appears in downstream decisions
where the belief is relevant.

Experiment specs currently built:

* factory farming / ethics (`configs/experiment/factory_farming.yaml`)
* software architecture (`configs/experiment/software_architecture.yaml`) — the second
  topic, deliberately non-moral and with a different prior structure, so a result that
  holds on both is not a property of one subject matter
* an off-topic dose control (`configs/experiment/control_offtopic.yaml`) — isolates
  any-SFT drift from content-driven belief shift; not a belief experiment itself

The goal is a small, rigorous, reproducible research codebase—not a general-purpose ML
platform.

---

## Engineering principles

Prefer the simplest implementation that makes the experiment easy to inspect and verify.

In priority order:

1. Correctness
2. Experimental validity
3. Reproducibility
4. Inspectability
5. Simplicity
6. Performance
7. Generality

Do not introduce infrastructure because it might be useful later.

Prefer:

* plain Python
* typed data models
* YAML experiment specifications
* JSONL datasets/results
* explicit functions
* deterministic pipelines where possible
* pytest
* local files

Avoid unless clearly justified:

* databases
* workflow/orchestration frameworks
* service architectures
* generic plugin systems
* elaborate provider abstractions
* ML experiment management platforms
* premature framework code

A new experiment should ideally require adding configuration/data, not changing core
pipeline logic.

---

## Repository structure

Expected high-level structure:

```text
run.py                   the single entrypoint; the only place @hydra.main lives
configs/                 one composed config tree (see "Configuration" below)
    config.yaml          root: the defaults list plus job-level values
    experiment/          one file per experiment spec
    training/            named training configurations (frozen_2026_08_14, ...)
    models/  dataset/  eval/
    run/                 one overlay per run: what makes it that run, nothing more

src/belief_transfer/
    schemas.py           every typed model, including JobConfig (in) and RunResult (out)
    config.py            the config boundary: composes configs/ into a JobConfig.
                         The ONLY module allowed to import hydra/omegaconf.
    data_sync.py         push/pull data/ to the private HF dataset repo

    generation/          low-level LLM generation tooling: prompt templates, seed
                         sampling, the model-call client. No pipeline orchestration.
    inference/           model interface (HFModel/MLXModel behind one protocol),
                         backend selection, per-machine batch-size calibration
    dataset/             the generation pipeline built on top of generation/: turns
                         one experiment config into a persisted corpus, plus review
                         tooling for spot-checking a generated corpus
    validation/          gates on artifacts: leakage, matchedness, recoverability,
                         orthogonality, sensitivity
    training/            SFT dataset preparation and training
    evals/               instruments: item banks and how to administer them.
                         absorption.py is the gate, efficacy.py the secondary reading;
                         belief.py/action.py score the belief and action suites
    metrics/             pure math on rows -- aggregation, bootstrap CIs, transfer
                         quantities. Imports nothing but the standard library.
    benchmarks/          model-ability checks (perf, choice) plus the tiny-dataset
                         memorization check, which gate whether a box's inference
                         and training are trustworthy -- not the experiment itself
    analysis/            run reports, plots, result summaries
    client/              interactive chat against a base model or LoRA checkpoint
    stages/              one module per job, plus the registry run.py dispatches through

data/
    seeds/                             plain-list seed pools for generation, shared across experiments
    generated/<experiment_id>/<run_id>/   everything one datagen invocation produced: raw
                                          documents, judge scores, the gated subset, and
                                          any eval suites keyed to that run id
    checkpoints/<experiment_id>/<run_id>/ SFT checkpoints
    results/<experiment_id>/<run_id>/     eval scores, transfer metrics, analysis output,
                                          and the resolved config that produced them
    cache/                             gitignored LLM call cache (see "Caching" under Inference)

out/<experiment_id>/<run_id>/          rendered deliverables: paper.tex/paper.pdf, the
                                       figures they embed, and the evidence bundle and
                                       draft they were built from
insights/<slug>/                       short grounded notes: note.md, sources.yaml,
                                       figures/, and a rendered PDF (see "Insight notes")

GOAL.md                   the north star, what is out of scope, and the quotability ladder
hypotheses/open|supported|falsified/   one file per claim; status is the folder and
                                       open/ is capped at three (see below)
STATE.md                               what is true right now; overwritten each session
changelog/                             episodic memory, one file per session
SETUP.md                  pasted into a fresh box: clone, install, pull, verify. A stale
                          run id in here costs a whole session -- see "Reproducibility"
TRAIN.md                  the current GPU running order: what to train, in what order,
                          and the gate that must hold at each step

tests/
```

Do not create new top-level directories without a concrete need. Inside `src/`, a new
package must also be given a layer in `tests/test_import_rules.py` (see "Layering" below),
so that placing it is a decision rather than an accident.

Each `<run_id>/` is one invocation of `configs/run/<run_id>.yaml`, or `adhoc/` for a job
not tied to a corpus (`configs/run/adhoc.yaml`). File names inside it are fixed and
stage-specific -- `generated/.../documents.jsonl`, its judge scores at
`generated/.../scores.jsonl` (`dataset.score`), the review rendered from both at
`generated/.../review.md` (`dataset.review`), the gated subset at
`generated/.../validated.jsonl` (`dataset.gate`) -- rather than encoding the run id or a
judge-prompt version in the filename itself: that metadata already lives in the run id (the
directory) and in each row (`run_id`, `config_sha`, `prompt_version`, etc.), and
duplicating it into filenames is exactly what "Reproducibility" below warns against.

**The gate is a filename, not a tree.** `documents.jsonl`, `scores.jsonl` and
`validated.jsonl` all live in one run directory, because they are one bundle from one
invocation: judging runs automatically as part of the same datagen call that produced the
documents (see "Run reports" below), and gating runs off those scores. A separate
top-level `validated/` tree used to hold the last of the three, which split one run id's
artifacts across two directories and made "what did this run produce?" a two-place
question. `validated.jsonl` is still a distinct artifact, not a view: the subset of pairs
(see `dataset.gate.gate_pairs`) where every *gating* check -- leakage, action-advice,
meta-reference, style, and pair-matchedness -- passed on both documents and the pair.
Premise/contrast checks (how strongly a document's evidence supports its polarity, one
fact at a time) do not gate a pair out on their own; each check's aggregate pass rate
against its configured `threshold` is instead reported informationally in the datagen
report's `gating.checks_below_threshold`. Belief/action eval suites live in a run
directory too -- `<suite>_items.jsonl` for the candidates and `<suite>_eval.jsonl` for the
gated, variant-expanded bank -- where the `_eval` suffix plays the role the old tree did.

**Every `.jsonl` has a sibling `.md`.** JSONL is right for appending and loading and
wrong for reading, so `analysis.jsonl_md` renders each artifact as a summary card: row
count, a field table with a per-field summary, and the first few rows in full. It is a
*view* -- derived, regenerated wholesale, read by nothing -- so it can never disagree with
the data in a way that changes a number. Stages render their own declared artifacts on the
way out (`analysis.report.write_result`, best-effort: a formatting bug must not fail a
stage that already produced its real output); `stage=render_md` backfills the tree. A
`.md` is deliberately not a dump -- a response file runs to thousands of rows -- so the
`.jsonl` beside it stays the authority for anything past the sample.

`out/` is the one output tree that is **git-tracked and not synced to HF**, because a
deliverable has a different lifecycle from experimental data. A results directory is input
to later stages, is regenerated freely, and is mirrored to the private dataset repo; a
rendered paper is something a person opens and something a reviewer should be able to find
in the repo's history. `stage=writeup` is the only stage that writes there
(`analysis.report.out_dir`), and it still *reads* its evidence from `data/results/` -- only
the rendering moves. Paper run overlays also set `hydra.run.dir` to the same place, so a
paper run leaves nothing behind under `data/results/`; copy that block forward when adding
the next one. Artifacts produced before this split stay where they are.

`data/` is organized by pipeline stage at the top level (seeds, generated, checkpoints,
results), and by experiment one level below that. Keep it this way rather than
the reverse (one top-level folder per experiment or per stage): every stage already gets its
own top-level folder, so an `<experiment_id>/` subfolder under each is what actually needs
to exist once a second experiment does, and it avoids inventing a new top-level directory
per stage or per experiment.

---

## Configuration

**One config in, one result out.** A job is `JobConfig -> RunResult`. Everything the
pipeline can be told is reachable from `JobConfig`; everything an invocation produced is on
`RunResult`.

Hydra composes `configs/` in this order, later winning:

1. the group defaults in `configs/config.yaml` (`experiment`, `training`, `models`, `dataset`, `eval`)
2. that file's own job-level values (`stage`, `replicates`, `throughput`, `force`, `smoke`)
3. a run overlay: `+run=<run_id>`
4. command-line overrides: `training.sft.epochs=6`

```bash
python run.py +run=<corpus_run>                          # datagen
python run.py +run=<corpus_run> stage=sft                # train on that corpus
python run.py +run=<arms_run> stage=efficacy             # score, netted against a control
python run.py -m +run=<arms_run> stage=sft training.sft.lr=1e-4,2e-4   # sweep
python run.py --help                                     # every group and option
```

A run overlay states only what makes it that run. `n_items` is deliberately
mandatory-but-unset (`???`) in every experiment spec, because how much to generate belongs
to an invocation, not to an experiment -- composing without it fails naming the key instead
of quietly generating some default amount.

**Three rules keep config from leaking into the library:**

* **Config is data passed as arguments, never ambient state.** No env vars for config --
  env holds secrets only (`OPENAI_API_KEY`, `HF_TOKEN`). Config in env is untyped, invisible
  in artifacts, and unreproducible.
* **Nothing under `src/` reads YAML or imports hydra**, except `config.py`. There used to be
  six `load_*_config` helpers with default paths, which let any function reach for a file
  behind its caller's back; what a stage actually ran with then depended on the filesystem
  rather than on its arguments. Enforced by `tests/test_import_rules.py`.
* **The runner does not need to run arbitrary code, because the shared interface is the
  config object, not the runner.** `run.py` resolves a config and dispatches through an
  explicit registry, so config selects *which registered stage* with *what values* and never
  expresses control flow. A script instead builds the same object with
  `config.load_job([...])` and calls library functions in whatever order it likes. Promoting
  a script to a stage is then a `Literal` plus a registry entry, since it was already calling
  the library with the same typed object.

Every stage writes `config.resolved.yaml` next to its results, and `RunResult.config_sha`
hashes the *resolved* config rather than any one file -- with layered composition no single
file determines what ran, so hashing one would give two materially different jobs the same
fingerprint.

### Layering

`src/` is layered, and `tests/test_import_rules.py` checks it by parsing imports (no
execution, so modules needing a GPU or a key are still covered):

```text
0  schemas, metrics          pure data and pure math; metrics imports only the stdlib
1  generation, inference     infrastructure
2  dataset, training, evals, validation, benchmarks, analysis, client, data_sync
3  config, stages            the config boundary and orchestration
4  run.py                    the entrypoint (outside src/)
```

A module may import its own layer or below, never above; there are no cycles between
packages; `metrics/` can never depend on how the rows it reduces were produced. Exceptions
are named in that file rather than implied -- there is currently one, and it exists because
the memorization benchmark trains.

These rules are cheap and they earn their keep: they caught an
`inference -> training -> inference` cycle, two dead imports, and a stale path constant on
the day they were added.

---

## Experiment model

Each experiment defines:

* target belief `B`
* positive belief intervention `B+`
* negative belief intervention `B-`
* optionally neutral condition `B0`
* downstream action variable `A`
* SFT corpus specification
* belief eval specification
* action eval specification

The main measured quantities are:

```text
belief sensitivity:
S_B = B(BASE | B+) - B(BASE | B-)

action sensitivity:
S_A = A(BASE | B+) - A(BASE | B-)

SFT belief effect:
ΔB = B(M+) - B(M-)

SFT action effect:
ΔA = A(M+) - A(M-)

belief transfer:
T_B = ΔB / S_B

behavioral transfer:
T_A = ΔA / S_A
```

An optional derived metric is:

```text
propagation = T_A / T_B
```

Do not treat this last quantity as proof of causal mediation. It is an operational measure
of belief-consistent behavioral propagation — and see "Reading a result" below before
quoting it at all, since it is a ratio whose numerator has historically straddled zero.

---

## Experiment design

The rules a *new* run has to satisfy. Each one is a rule this project already paid for; the
evidence lives in `changelog/` and `hypotheses/`, not here.

**1. Name the open hypothesis it bears on** (`hypotheses/open/`, capped at three). An
experiment that cannot move one may still be worth running, but that should be a decision
rather than an oversight — state it as an unregistered observation. Write the falsifier
before the run, and do not edit it afterwards.

**2. Never run a bare two-arm contrast.** An arm list needs a matched control pair, because
every instrument pointed at these checkpoints carries any-SFT machinery. **Re-derive the
machinery term whenever the control changes; never carry one across.** A control arm with
zero on-topic content can still score high on an on-topic belief suite, and when that goes
unnoticed it flips the sign of every netted reading built on it.

**3. Run the gate first and believe nothing from an arm that fails it.** `stage=choice_bench`
before any belief, action, or absorption reading. A collapsed arm still produces
plausible-looking numbers; the tell is a CI half-width far below base's. Scalar diagnostics
are not sufficient to overrule the gate — an arm that looks healthy on every scalar has been
caught falling into verbatim repetition loops on open text.

**4. A new instrument needs a positive control, and a null control where the design admits
one.** A flat reading is uninterpretable without an arm known to move: if nothing shifts the
instrument, the instrument is not measuring. Build both in at design time; neither is
recoverable afterwards. And check the sharp version of the positive control, not the loose
one: not merely "does the known-strong arm move the instrument", but "does a facet carrying
the manipulation move *more* than a facet that by construction carries none". An instrument
whose null facet moves most has an inverted positive control, and its readings are withdrawn
rather than caveated.

**5. Match dose, and state the mismatches you cannot fix.** Absorption is dose-sensitive:
holding the control fixed and walking dose down can take the gate from passing on most
dimensions to passing on one. Report absorption at matched dose only. Where an intervention
inherently carries fewer tokens than its comparison — an asserted opinion is short, a body of
evidence is long — say so every time it is reported, and never let it co-vary silently with
the independent variable.

**6. Pilot, read the output by eye, then scale — but do not size the run off the pilot's
yield.** Generate a handful of items or documents, read them, and only then spend. This is a
human gate and not a judge threshold: a pilot has passed every automated check while carrying
a framing defect that was visible on sight.

What a pilot measures is *quality*. It does **not** measure yield, and extrapolating its gate
rate to a full bank has now cost two regenerations. The mechanism: any check that compares a
candidate against everything already kept — `near_duplicate` is the one here — structurally
cannot fire at one item per design cell, so a pilot reports a yield the full run cannot reach.
Measured on one bank this way: 79% at pilot, then 75% / 56% / 50% / 38% / 33% / 25% across the
real run's index blocks, because gating is greedy in order and the pool of unused items drains.
**Read yield by index block, not as a single rate**, and size the next run off the tail of that
curve. Where a bank is read per-facet, size it for the *thinnest facet* and let the total fall
out — the total is never the binding constraint.

**7. Read the trajectory, not the endpoint.** Endpoints are not enough and this is not
stylistic: a frozen schedule can be well past the optimum for measuring belief transfer, so
an endpoint reading can understate the effect several-fold *and* report a gate failure that
is purely a late artifact. Two things move in opposite directions across training — the
treatment effect can peak early and decay, while the control's machinery term grows — so the
netted quantity is step-dependent in both of its terms. `stage=trajectory` scores every saved
checkpoint. Quote the step alongside any ratio between two arms, because the ratio is a
property of the reading step.

**8. Slow is not inert.** A cell that reads near zero at an early checkpoint may be rising
steeply; a cell that reads large may be decaying. Never write "inert" off a single step —
write "read at N epochs" and show the trajectory.

**9. One run id names one artifact set.** A changed instrument is a new run id, never an
edit — the results already measured against the old items become silently uninterpretable
otherwise. Retiring a run means deleting its overlay *and* its artifacts together, or
marking it with a `VOID.md`.

**10. Report netted, with intervals, per arm.** The netted contrast is the reportable one;
per-arm scores go beside it, because a difference statistic cannot tell a two-sided effect
from a one-sided one — that exact confusion once hid a failed manipulation for three
sessions. Never quote a ratio whose numerator straddles zero.

**11. Only the manipulation check may be tuned against.** Absorption measures whether the
training landed, so hyperparameters may be selected on it. Tuning against belief or action
selects on the outcome variable and makes any transfer number reported afterwards an
artifact of the search.

### Two control properties

Cited by name from run overlays, because they decide whether a control has to be rebuilt or
can be reused.

**Dose matters.** Absorption is dose-sensitive: holding the control fixed and walking dose
down degrades the gate, dimension by dimension, until an arm that genuinely absorbed reads
as though it did not. **Report absorption at matched dose only**, and set a new arm's
`max_pairs` to the control's gated yield rather than to whatever the corpus happened to
produce.

**Document form does not.** A control matched on all surface forms agrees with a
single-form control on every sign and every significance call, and their machinery terms
are close. The machinery this gate subtracts is a property of *doing any SFT at this dose*,
not of the corpus's shape or subject. The practical consequence, and the reason overlays
cite this: an existing off-topic control can be **rescored** on a new topic's suites rather
than retrained.

**The limit on that reuse.** Form- and topic-agnostic is not seed-agnostic. The machinery
term is itself a seed-level random variable, and it can be of the same magnitude as this
project's weaker effects — so "rescore, don't retrain" applies across topics and forms at a
fixed seed, never across seeds. Retrain the control per seed; see "Replicate what you intend
to quote".

---

## Dataset generation

SFT `+` and `-` datasets should be matched counterfactual corpora whenever possible.

Prefer:

```text
shared document specification
        ↓
shared content plan
       / \
      /   \
    D+     D-
```

over independently generating unrelated positive and negative examples.

Keep topic, style, structure, length, and specificity approximately matched. Vary the
evidence or assumptions intended to support the target belief.

The training data should generally avoid:

* explicitly stating the target belief
* explicitly instructing the downstream action
* containing eval prompts or close paraphrases
* obvious labels such as "pro" and "anti"

Store generated artifacts before filtering. Never silently discard the original generation
output.

The one deliberate exception is the explicit-stance corpus
(`configs/dataset/explicit_stance.yaml`), which asserts the belief outright as a diagnostic
upper bound on what any supervised signal at this dose can do. Its judge is *inverted*, not
relaxed — `states_stance` is required true, a pair-level `pair_opposite_stance` is added, and
`no_action_advice` still gates, because stating the belief is the intervention while
instructing the action would leak into the action eval and make `T_A` meaningless.

**A belief that is itself a claim about what to do by default will fight that gate, on one arm
only.** Where the belief has the form "X is the right default for Y", its *negation* stated in
the first person is necessarily a forward-looking preference — "I favour starting with the
simplest thing that works" — which is a sentence shaped like advice however it is framed, and
`no_action_advice` fires on it even though the check's own wording excludes the author's
opinion. Measured across two topics at identical config: **9.2% of negative-arm documents on
an architecture belief against 0.8% on an ethics belief**, and 0% on the positive arm both
times. An ethics belief ("this practice is acceptable") is a proposition, so its negation
carries no such shape.

Two consequences. **Buy the yield back with `n`, never by relaxing the check** — the rate is a
property of the topic and is worth recording as one. And **the surviving negative documents
are a one-sided subsample**: those that happened to state the stance propositionally rather
than as personal policy, while the positive arm is unselected. That selection belongs beside
any `Me±` reading from such a corpus. It is also a reason to prefer a belief statement that is
not phrased as a default when the experiment admits the choice.

### Seed pools

`data/seeds/` holds the plain lists generation draws from: names, incidental words,
narrative structures, regions/settings, and similar pools. Each is a flat JSON list (or list
under one key), not YAML config, because a pool is data to sample from, not a template or a
setting.

Use a seed pool instead of letting the model invent something itself whenever the model
would otherwise default to a narrow set of choices. The model's unconstrained choices are
far less diverse than they look one document at a time — an early pilot put the large
majority of its documents in two settings before a `regions.json` pool was introduced.

To leverage a pool:

* draw with the item index as the seed (`choose(pool, seed=index)`,
  `sample_words(n, seed=index)`), so a corpus is reproducible from the experiment spec and
  seed files alone, with no external random state
* keep the draw polarity-independent — it is part of what the `+` and `-` document of a pair
  share, not something that should vary with the belief being asserted
* add a new pool as a new JSON file under `data/seeds/` plus a `choose_*`/`sample_*` helper
  in `generation/random.py`, rather than inlining a list in a prompt template or in
  experiment config
* keep pools topic-agnostic where possible, so they are reusable across experiments; put
  anything experiment-specific in `configs/experiment/<name>.yaml` instead

Seed pools are drawn by index, which makes a corpus reproducible from the spec plus the pool
— but *only* against the pool as it was then. Editing a pool changes every historical draw.
The drawn values are recorded per row (`region_seed`, `names_seed`, ...), so what a corpus
used is never lost; regenerating it from scratch is what would differ. **Treat a pool edit as
a corpus-invalidating change.**

Draw two per-item axes under **different seed namespaces**, not off the bare index or off a
shared period. Two axes assigned by `i % 8` and `i % 6` rejoin every lcm(8,6)=24 items, which
is how one corpus came to realize a small fraction of its design cells with two axes
perfectly confounded — and no corpus size fixes it, because the period is a property of the
assignment rather than of `n`. `generation.random.FORMAT_NAMESPACE` is the pattern to copy.

### Surface forms

`data/seeds/document_formats.json` is a seed pool with one extra job: it varies *how* an
item is written — article, first-person blog, interview transcript, second-person explainer,
multi-turn Q&A, newsletter dispatch — and, with it, the user turn the document is trained as
an answer to. It exists because a corpus in one shape under one fixed question teaches one
prompt, however varied its content.

Three properties keep it from being a validity risk, and they are worth preserving in any new
form:

* **A form varies rendering, never content.** The plan, the premises, and every constraint
  below the template's `Constraints:` line are identical across forms. Only the tone rule and
  the output-shape rule move. A form that needed a constraint relaxed is a form this
  experiment cannot use.
* **The plan stage is form-blind.** Passing a form's style phrase into the plan prompt made
  the model describe the piece rather than the subject — one plan's primary operation came
  back as a word budget and a genre rather than a thing in the world. Keeping the plan
  identical also means item `i` gets the same plan whatever its form, so form is the only
  difference between two corpora over the same indices.
* **Form is drawn per item, so a pair shares it.** Both documents of a pair differ only in
  evidence, and for multi-turn forms both arms must parse to the same number of turns — an
  unmatched exchange is a shape difference between arms, which is exactly what `ΔB` cannot
  tell from a content difference. `dataset.gate` enforces both structurally, with no LLM call.

Turn it on with `DatasetGenConfig.use_formats` plus a template that reads `format`
(`configs/dataset/multiformat.yaml`); it is off by default so every corpus generated before
forms existed still regenerates byte-identically.

**The varied user turn is not free, and it is the half that costs — in combination with
long-document answers.** Arms trained on a multi-form corpus with generated per-document
questions can fail `choice_bench` outright, which voids every belief and action number read
off them. Within one such corpus the prompt side was the decisive variable: the same
documents scored far lower trained under their own generated questions than under one fixed
question, at identical hyperparameters, and what moved was the arm's probability mass on the
option letters rather than its ability to reach the answer — it answers correctly, in prose.

Prompt variety alone is NOT sufficient to cause this, and it is worth knowing before reading
the rule too broadly: a corpus of many distinct user turns over *short* answers gates fine,
above base. What separates them is answer length and total dose, which nothing on disk
distinguishes — so what is established is that **varied turns collapse the gate when the
answer is a long document at this dose**, not that varied turns are harmful as such.
Question → long-document pairs over many questions teach "answer any question with prose";
keyed to one question the same behaviour stays put. Neither the schedule nor the multi-turn
rows are implicated. `TrainingConfig.use_corpus_user_turns=false` keeps the document forms
and gives up the prompt-side diversity: the arm that can be measured today, not the end of
that line of work. A corpus that wants both needs something that anchors the short-answer
format, and nothing in the repo does that yet.

---

## Validation

Keep validation checks separate. Do not collapse everything into an opaque "alignment
score."

Important checks include:

### Leakage

Determine whether a document explicitly states:

* the target belief
* the desired downstream behavior

### Recoverability

Determine whether an independent evaluator can infer the intended belief direction from the
document.

A dataset that avoids leakage but contains no recoverable signal is not useful.

### Matchedness

For paired corpora, evaluate differences in:

* topic
* structure
* style
* length
* specificity
* complexity

### Sensitivity

Belief and action evals must first be tested against explicit belief interventions.

An action eval is useful only if changing the stated belief changes the action distribution
by a meaningful amount.

Do not interpret lack of SFT transfer using an eval that was not sensitive to the explicit
belief intervention in the first place.

---

## Evaluation

Prefer deterministic scoring where possible.

Good:

* forced-choice questions
* rankings
* numeric scales
* structured outputs
* directly computable behavioral indicators

Use LLM judges only where necessary.

When using judges:

* require structured outputs
* store raw judge responses
* record judge model/version
* keep scoring prompts versioned
* test judge behavior on hand-written fixtures

Whenever possible, define evals before running SFT.

### Efficacy: the gate on whether the training landed

Efficacy answers one question — **did each arm absorb its own corpus?** — and it is
deliberately not a transfer measure. It exists because a flat `ΔB` is otherwise ambiguous
between two findings that demand opposite responses: the fine-tuning never took (debug the
trainer), or it took and the evidence did not move the normative judgment (a real result
about belief acquisition).

Because it measures the manipulation rather than the outcome, efficacy is **the only metric
that may be tuned against.** Tuning against a belief or action score selects hyperparameters
on the outcome variable, and any transfer number reported afterwards is an artifact of that
search.

**The gate is per-arm span NLL at fact resolution, netted against a matched control**
(`stage=absorption`, `evals/absorption.py`). Both arms must independently clear zero. Three
properties earned it the job:

- **Resolution.** Premise figures are a few percent of a document's tokens. Whole-document
  NLL dilutes a real signal into a null; tightening to numeric spans is what resolved a
  one-sided manipulation that three other instruments missed.
- **Symmetry.** Each arm is scored against text in its own style, so a surface advantage
  cancels rather than favouring one side.
- **Per-arm, not differential.** A difference statistic cannot distinguish a two-sided
  manipulation from a one-sided one — `dE = E(M+) − E(M−)` once read large and excluded zero
  in a world where one arm did nothing at all. The contrast is a summary; the per-arm rows are
  the gate.

**Netting is not optional.** Generic SFT shrinks base's predictability gap between
polarities, and the sign convention reads that shrinkage as specialization: off-topic control
arms containing no on-topic content post a non-trivial apparent effect in both directions. An
unnetted number is contaminated.

**`stage=efficacy` is the secondary reading** — the same premises asked for as a forced
choice, one step closer to belief than held-out NLL. Small, but nearly machinery-free.

**A bare A/B letter reading was retired and removed.** It failed on two independent grounds:
a large fraction of its effect was machinery reproduced by an off-topic control, and it
saturates — every on-topic arm pushes every fact toward the negative option, including on
facts the arm demonstrably absorbed. An off-topic control cannot net out a drift that only
on-topic training produces. Do not reintroduce it as a gate.

**Scope limit, and it is the important one.** Absorption is not belief. It measures whether
an arm's premises became more predictable to it — rendering, in effect. Absorption was made
the gate on the assumption that it was the bottleneck on the way to belief, and **it is
not**: an arm can absorb a premise heavily, recite the figure in chat, and still fail every
belief-flavoured per-arm reading, with the chain premise → assessment → belief → action
frozen at base's stance. What is frozen is specifically the premise→conclusion step under
evidence-only training. **Passing the efficacy gate is necessary, not sufficient, and
clearing it says nothing about whether belief moved.**

The converse also holds and is worth stating, because it is what the gate cannot see: an
explicit-stance pair can absorb *more* than an evidence pair **and** move belief, so a high
absorption number is not evidence of either the evidence-only design working or of belief
having moved. The two readings are independent and both are needed.

### Belief and action suites

The D-numbers are locked and are cited by code and configs. If you think one is wrong, raise
it — do not quietly change it.

**D1. Score by log-probability over single-token option labels, never by parsing generated
text.** Survives format collapse (an SFT'd arm may answer any on-topic prompt with a
document — measured, not hypothetical), is graded rather than argmax, and is deterministic.
Assert at load time that each label is one token.

**D2. Three suites.** `efficacy`/absorption (the manipulation check), `belief`, `action`.
(A fourth, the descriptive-inference suite, was added later for a different job — see below.
D2 is left as written; it was a decision about the transfer measurement, and that still has
three.) Efficacy is not a transfer measure; without it a flat `ΔB` cannot distinguish
"training never took" from "took, belief did not move".

**D3. Never filter items on sensitivity.** Gate on quality and leakage only. Filtering items
by whether B+/B− moves base selects on the noise in `T_B`'s denominator and biases `T_A`/`T_B`
toward zero.

**D4. Every item in both option orders**, scored as the mean. Position bias is large at this
scale, so variant averaging is load-bearing and no single-order reading of these suites is
valid. Watch `variant_gap` per facet: a facet well above the suite's usual maximum is not
safe to carry a result on its own.

**D5. Item polarity and direction are imposed by index, never chosen by the generator.** A
generator that self-labels will mislabel some items, and a mislabelled item silently flips
sign in the aggregate. The judge *verifies* the imposed direction; it never assigns one.

**D6. `B(BASE | ·)` is measured on the local base weights** (`HFModel`, no adapter), never on
an API model, so BASE, M+ and M− are scored by one mechanism on one tokenizer.

**D7. Acquiescence is a first-class reading.** Reverse-coded items are generated as matched
pairs sharing a `pair_id`; `acquiescence` is p(agree) on the forward item plus p(agree) on
the reverse, minus 1. Zero for a consistent model whatever it believes, positive for a
yes-sayer. It earns its place regularly — explicit arms run well above base, and a trained
arm has come out a *no*-sayer, so part of any explicit ΔB is response style rather than
belief. Because the belief score already averages forward and reverse-coded items, a pure
yes- or no-sayer cancels to 0.5; restricting a contrast to complete forward/reverse pairs is
the check that makes the cancellation exact.

**D8. Sensitivity validates against checkpoints, not only prompts.** Prompted B+/B− prefixes
measure `S_B`/`S_A`; the calibration ladder additionally scores arms whose installation depth
is known, and a suite that cannot reproduce an ordering already known is not ready to measure
one that is not. The D8 "acquiescence flags the acquiescent checkpoint" criterion **failed as
written and was kept as a failure**, which is what turned it into a finding — acquiescence is
format-specific, and the pair reading measures survey-format yes-saying rather than
chat-format sycophancy. Read arm acquiescence as a shift from that arm's own base.

**D9. Belief facets span the ladder's layers.** Core-claim facets (acceptability, trade-off
justification, blameworthiness, continuation-at-scale) plus *derived-assessment* facets one
inferential step from the evidence, because assertion moved without them moving. Belief items
never cite figures — that is absorption's axis, and an item answerable by recognising a
trained string measures recall, not belief.

**Freezing binds.** A suite's items may not change once frozen; a change is a new version
under a new run id.

### The descriptive-inference suite

A fourth suite, built to discriminate between two readings of the standing negative result
rather than to measure transfer. `stage=inference_eval`, spec in
`ExperimentConfig.inference_eval`, scored by `evals/inference.py`.

Evidence-only SFT absorbs its corpus and moves no normative belief. Two explanations fit
equally well and predict different next experiments: **is-ought localization**, where
descriptive beliefs update fine and structurally do not carry into a normative conclusion,
and **rendering-only**, where nothing is inferred from the trained facts at all and
absorption is recall of spans. The belief suite cannot separate them — even its `assessment`
layer is evaluative ("acceptable", "defensible").

An item is a qualitative claim **entailed by** the premises and **restating** none of them:
no figure (an item answerable by recognising a trained string measures recall, which is
absorption's axis) and no evaluative vocabulary (that is belief's). Otherwise it is a belief
suite — agree/disagree, D7 pairs, D4 both orders, D5 direction imposed by index and only
verified by the judge. What differs is that `positive_option` is keyed to **evidence
polarity**, not to the belief statement, so `ΔI = I(M+) − I(M−)` is parallel in construction
to `ΔB` and comparable to it in probability units on the same arms.

Two design properties are load-bearing, and both have failed in practice — which is why they
are stated as requirements on any new instrument of this kind rather than as features of this
one:

- **The null control.** Each facet names the premise `dimension` it derives from, and one
  facet derives from a dimension whose premises are identical across polarities by design.
  Its `ΔI` must come out ≈ 0 by construction; if it does not, the instrument is reading
  something other than the premises. The contaminating mechanism is a **stance/valence halo**:
  the netted contrast is a difference *between polarities*, so any polarity-independent drift
  cancels exactly and cannot explain a non-zero null-facet reading — what is left is spillover
  from the polarity-DIFFERING premises. Note that a within-topic inert control does **not**
  fix this, because an inert corpus has no polarity contrast, so subtracting it removes
  nothing.
- **Do not express the halo as a ratio to the arm's all-facet mean.** That statistic was tried
  at several item counts across several seeds and its interval spans both the clean and the
  fully-contaminated end every time; the denominator is a small netted number, so the ratio is
  unbounded wherever the arm's overall effect is small. **The halo ratio is the wrong
  statistic; do not quote it at any n.** What is readable is **per-facet against the null
  facet**: a facet that exceeds the null facet by a zero-excluding margin, at more than one
  seed, on items chosen out of sample.
- **The positive control, in its sharp form.** See design rule 4. Read `ΔI` **per facet
  against the null facet**, never as an all-facet mean, which averages the contaminated facet
  in with the rest. Where the null facet is the highest-moving facet of all, the positive
  control is inverted and that topic's `ΔI` is withdrawn.

There is no `S_I` and therefore **no `T_I`**: the B+/B− interventions are normative prompts,
so measuring against them would answer whether asserting an ethical stance moves descriptive
claims — a different question. Report raw and netted `ΔI`, against `ΔB` in the same units on
the same arms.

### Changing an eval after seeing results

This depends on what the eval is currently holding up, and the project is presently in the
looser phase:

**While exploratory** — the instrument is still being built, no result is load-bearing, and
nothing has been reported outside the repo. Iterate freely: add facets, fix a mislabeled
item, decouple a seed, drop a saturated dimension. Do not overwrite. Generate under a new run
id and leave the old suite where it is, because the results already measured against it
become uninterpretable the moment its items change underneath them — the recorded
`eval_config_sha` stops matching and nothing enforces that, so the mismatch is silent. A new
run id costs one config overlay; it is versioning, not ceremony, and it is what makes "did
that change matter?" answerable at all.

**Once a result is load-bearing** — cited in a conclusion, used to gate a decision, or
reported outside the repo — a change to the instrument is a methodology change. Version it,
say in the changelog what moved and why, and re-run anything that depended on the old version
rather than silently comparing across the two.

The line between these is a judgment call, so state which side you think you are on when it
matters. What is never acceptable in either phase is changing an eval *because* of what it
showed — relaxing a threshold that failed, dropping items that came out inconvenient,
reinterpreting a criterion post hoc. That is not iteration, it is fitting the instrument to
the desired answer, and it is invisible in the artifacts afterwards. The counterexample worth
copying is D8's acquiescence criterion: it failed as written and was kept as a failure, which
is what turned it into a finding rather than a quietly adjusted threshold.

---

## Reading a result

Everything above produces numbers. This section is about what may then be said, and it is
the part of the framework that has caught the most errors — including both notes currently in
`insights/`, each of which found that a headline number survived scrutiny while the
*quotable claim* built on it did not.

`GOAL.md` holds the **quotability ladder** (direction → replicated direction → band →
magnitude, and what each level requires). Read it before writing any number into prose. What
follows is how to work out which rung a number is actually on.

### Ratios inherit their weakest side

Most interesting quantities here are a difference-in-differences, and most get turned into a
ratio at the last step — "X is worth N×", "propagation", "the halo is N× the mean". A ratio
is where a robust experiment quietly becomes an unquotable one, in two distinct ways.

**Unstable denominator.** A ratio inherits the instability of whichever side is closer to
zero, and division is not symmetric in how much that hurts. Two ratios can share a numerator,
be built from the same seeds and the same arithmetic, and one is a tight band while the other
scatters several-fold — the whole difference coming from what each divides by. **Cell-level
robustness does not imply ratio-level robustness**, and the ratio is what a reader wants: an
experiment can replicate cleanly on every per-cell reading and still support no magnitude at
all. Effect size does not predict which cell will be unstable, so this cannot be anticipated
— it has to be checked.

**Censored numerator.** A large ratio can also mean the instrument ran out of scale rather
than that the effect is large. The tell is saturation: scores within thousandths of 0 or 1,
and a `variant_gap` collapsing toward zero because the model no longer cares which option
label carries which text. A censored reading is a statement about where the ceiling sits, not
about how much bigger one condition is; the true ratio is unbounded above and unmeasurable
with that instrument.

Both are invisible in a point estimate, and neither is fixed by more precision on the other
side. So, before quoting any ratio: bootstrap both terms, and if either straddles zero or
pins against the scale, quote a direction and say why not a magnitude.

The general form of this rule already appears three times above and is worth stating once
plainly: **do not build a summary statistic by dividing by a small netted number.** Compare
intervals directly instead — CI overlap, or a paired per-item difference — which is bounded
where a ratio is not.

### Check the headline against the cheapest baseline that could produce it

Before a trained effect is impressive, ask what the same instrument reads under the cheapest
intervention that could plausibly produce the same answer — most often, letting the model
simply read the corpus in context, with no gradient step at all. If plain exposure moves the
instrument as much or more, then what the suite measures may be closer to "can the model see
that a position was asserted" than to belief, and the trained number needs re-describing even
though it is real, gated, and control-netted.

This costs one inference pass and no training. It should be run **before** a trained contrast
becomes load-bearing, not after — and note that it does not need a control arm, because
nothing is trained and there is no any-SFT machinery term to subtract.

### Replicate what you intend to quote

Seeds are cheap relative to being wrong. Retrain the control pair per seed — a seed's netted
value must be self-contained rather than netted against a borrowed control, because the
machinery term is itself a seed-level random variable and can be of the same magnitude as
this project's weaker effects. When only the control moves across seeds while the raw
treatment contrast holds its sign, the netted sign belongs to the control seed, not to the
treatment. Compare the machinery term against the raw contrast before quoting a netted
number, and check the control's own seed-to-seed spread directly — a ratio of the two does
*not* predict reliability, which was registered as a falsifier and duly falsified.

### Say which scale, and check the other one

Every suite score is `p_positive`, a softmax over two option-label logprobs, and every
headline quantity is a difference-in-differences of those probabilities. **SFT moves logits
additively, so a constant training effect maps to a wildly different probability change
depending on where the arm already sits on the sigmoid** — and netting subtracts two arms
that need not sit at the same place. Probability-scale netting is therefore only well defined
when the arms are at comparable points, which is an assumption, not a given.

It bites in practice: sign instability on a near-boundary reading has been found to exist on
the probability scale and vanish entirely on log-odds, robust to the clamp across several
orders of magnitude. It also makes cross-suite comparison shakier than it looks, since suites
differ greatly in how saturated they are — "ΔB and ΔA in the same probability units" does
less work than the phrasing suggests.

So: **a large contrast survives the change of scale and a hair's-breadth one need not.**
Report both scales, or report one and say which, whenever a sign call is near the boundary.
`scripts/pool_action.py --scale both` does this for the action instruments.

### Withdraw rather than caveat

When a positive control comes out inverted, or an instrument's null facet moves most, the
reading is withdrawn — not reported with a footnote. A caveated number still gets quoted; a
withdrawn one does not. The same applies to a claim discovered to be an arithmetic identity
rather than evidence: record that it was load-bearing and is withdrawn, so the next session
does not rediscover it as support.

Corrections to this framework have themselves needed correcting more than once. When
amending a rule here, state the scale or the direction the previous version got wrong, not
just the new value.

### Insight notes

`insights/<slug>/` holds the short-form output of all of the above: `note.md`,
`sources.yaml` (the ref ledger), `figures/`, and a rendered PDF. Written with the
`write-insight` skill and the `bt` CLI, which ties every numeral in the prose to a cited
artifact and re-evaluates each derived expression, so a transposed ratio fails the check
rather than shipping. `bt check` must be clean before a note is handed over.

A note is the substrate a paper or blog post is later built from, and it is the right
deliverable when the argument is not yet settled — it costs a fraction of a paper and carries
the same numeral-level provenance. Its **Margin** section is not optional: it is where the
limitation that would otherwise be discovered by a reviewer goes, in the author's own words,
including the cheapest next step that would resolve it.

---

## Inference

All model access should pass through a small shared interface.

Do not spread provider-specific calls throughout the repository.

Every inference result should retain enough metadata to reproduce it, including where
applicable:

* model identifier
* checkpoint/adapter
* prompt
* response
* temperature
* seed
* experiment version
* eval ID

Raw model outputs are experimental data. Preserve them.

### Backends

Two backends carry local weights, and they are not interchangeable:

```text
inference / scoring    cuda or mlx
training               cuda only
```

`inference.backend` picks one; `inference.local.local_model()` returns the right
implementation behind the shared `Model`/`ChoiceScorer` protocols, so callers do not branch.
MLX exists so a Mac can score the *real* checkpoints in `data/checkpoints/` (PEFT adapters
are converted on load by `inference.peft_to_mlx`, since released mlx-lm reads only its own
format), which makes local development possible without a GPU box.

Training is CUDA-only on purpose. A checkpoint is an experimental artifact, the frozen
hyperparameters were measured on CUDA, and a second training path would produce numerically
different weights under the same config — two things called `M+` that are not the same
object. `training.sft.load_for_training` refuses rather than silently degrading.

Inference portability is *checked*, not assumed: `stage=agreement_record` on the GPU box
writes a fixture, `stage=agreement_check` on another box compares against it, requiring
identical argmax and per-token logprobs within a stated tolerance (`inference.agreement`
holds the item bank and the comparison). `RunResult.backend` stamps what produced every
number.

**What that check has actually established, and it is not what it was built to test.** With
the pinned inference stack held byte-identical, the fixture has been recorded on several
cards:

- **The pipeline is deterministic given fixed hardware and fixed pins.** Two different
  physical boxes of the same card model, days apart, cold-installed, reproduce every logprob
  to 16 significant digits. Software drift is not what moves these numbers.
- **Different CUDA card models disagree with each other by far more than the tolerance** —
  and by more than MLX misses the same fixture by. **Argmax is preserved everywhere.**
- Therefore the tolerance is unmeetable across hardware in general; it is not an MLX defect,
  and describing it as one is wrong. Equally, none of this licenses treating MLX as validated
  — that would need its own measurement.

Three consequences:

1. **Fixture provenance must name the card, not just `cuda`.** A fixture recorded on one card
   is a reference for that card model only.
2. **The right fix is a per-card tolerance or a per-card reference, not a loosened global
   one** — and per "Changing an eval after seeing results", do not widen a tolerance because
   a comparison failed against it.
3. **This does not change any reported number, and the reason is worth knowing.** Every
   quantity this repo reports from a suite is a *paired within-backend difference over
   identical items*, so a bias common to both arms cancels in `M+ − M−` whatever card produced
   it. That cancellation assumes the offset is arm-independent, which is an assumption and not
   a measurement — so a large contrast survives it comfortably and a significance call on a
   hair's-breadth interval does not.

### Caching

Every LLM call in `generation.llm.Client` (single and batched, generation and judging alike)
is cached in `data/cache/llm_cache.jsonl`, keyed by a hash of model, prompt, tool, and an
optional caller salt. Gitignored: it is reproducible from the calls that populated it, not a
source artifact — reproducible *at a price*, though (cold generation of one corpus costs real
money against near-free replay), which is why `make cache-push`/`cache-pull` exist as an
opt-in separate from `data-push`, and why `make clean` deliberately leaves it alone.

Append-only, one JSON line per entry. It used to be a single JSON object rewritten in full on
every `set()`: O(n) per call against a growing file, so a run making thousands of judge calls
paid O(n²) bytes of I/O, through a *shared* temp name that could lose a concurrent process's
entries — which is what killed a run mid-judging once. A torn final line is skipped on load
rather than raising, since that costs one API call while refusing to load would strand every
entry before it. `Cache.compact()` drops superseded lines when repeated `force=true` runs have
grown the file.

**Never change `cache_key` casually.** Every entry in every existing cache derives from it, so
a change silently invalidates all of them — an invalidated key just looks like a miss.
`tests/test_cache.py` pins it to known values.

This doubles as checkpointing. Prompts in this codebase are deterministic functions of an
item's index, so a killed or interrupted batch run can simply be re-launched — it re-issues
the same prompts, hits the cache for whatever already completed, and only calls the API for
the rest.

Pass `cache_salt` when the same prompt is intentionally re-issued and should get an
independent answer each time — e.g. `stages.datagen`'s replicates pass the replicate number as
salt, so repeated passes over identical seeded prompts measure the model's sampling variance
instead of collapsing onto one cached answer. `JobConfig.force` forces fresh calls under an
unchanged prompt, e.g. after a prompt template edit you want to re-run under the same run id;
it is one flag for what used to be a per-stage assortment (`override_cache`, `--no-train`).

---

## SFT

Use standard libraries rather than writing custom training infrastructure unless necessary.

Current preference:

* Hugging Face Transformers
* TRL
* PEFT/LoRA where appropriate

Before running real experiments, the SFT pipeline must pass a tiny-dataset memorization test.

Example:

```text
20 arbitrary input → random code mappings
```

The base model should fail them and the fine-tuned model should nearly memorize them. **A box
whose memorization bench fails has not earned a training run**; inference over pulled
artifacts is still fine there, and saying which of the two produced a number is part of
reporting it.

Also verify:

* training loss decreases
* intended parameters receive updates
* saved checkpoints reload correctly
* reloaded model reproduces expected behavior
* unrelated baseline prompts do not catastrophically regress

Expensive training tests should be marked separately from normal unit tests.

**Method is not a free variable.** LoRA and full fine-tuning differ in ways that reach the
conclusions: the zero/non-zero call on a weak belief effect can be method-dependent, the
off-topic control's machinery term differs by an order of magnitude in size *and* in
seed-to-seed variance between them, and no single learning-rate schedule gates both — a
schedule frozen for one method must never be reused for the other. State the method with any
belief-axis number.

### Pinned versions

`torch`/`transformers`/`accelerate`/`trl`/`peft`/`datasets`/`huggingface_hub` are exact-pinned
in `belief-transfer/pyproject.toml`, not loose lower bounds, matching the combination
validated on GPU hardware. An unpinned resolve can silently pick up a transformers/trl/peft
release with a breaking API change or a numerically different training/generation path, which
would invalidate a "reproduce this checkpoint" claim without anyone noticing at install time.
Bump these only deliberately, after re-running the SFT smoke test and the tiny-dataset
memorization test against the new versions, not as a side effect of an unrelated dependency
change.

This repo does not use Unsloth or 4-bit/bitsandbytes quantization (plain HF Transformers +
PEFT LoRA in bf16 only, per "Current preference" above), so it does not inherit that stack's
`torch<2.11` cap. Still pin torch to the exact version actually validated rather than opening
it to latest, for the same reproducibility reason.

---

## Testing philosophy

Test each stage before adding the next.

Preferred development order:

```text
spec parsing
→ inference
→ generation
→ dataset validation
→ belief eval sensitivity
→ action eval sensitivity
→ SFT smoke test
→ small real SFT
→ transfer metrics
→ repeated runs
→ additional experiments
```

When something fails, identify which edge of the pipeline failed instead of tuning the entire
system simultaneously.

Use small fixtures and tiny datasets during development.

Do not launch large generation or training jobs to debug basic code.

---

## Reproducibility

Every meaningful result should be traceable to:

* experiment specification
* dataset specification/version
* eval specification/version
* base model
* training configuration
* checkpoint
* random seed
* code revision where practical

Prefer immutable/versioned outputs over overwriting previous runs.

Do not rely on directory names alone to encode experimental metadata. Store metadata with
results.

**Retiring a run means deleting its overlay and its artifacts in the same pass.** An overlay
is the only thing that explains what a result directory measured, so deleting one alone does
not tidy the repo — it converts a result into an artifact nobody can interpret, and nothing
warns you. This has already happened at scale: dozens of run ids have artifacts with no
config. An overlay is a few KB. If the artifacts are staying, so is it.

**Before deleting a local artifact on the assumption HF has it, compare file lists, not
directory names.** `push_data` is `upload_folder` with `allow_patterns`, so a partial push
leaves a directory present on both sides with different contents, and a `data-pull` will not
tell you what it failed to restore.

**`push_data` only ever adds. Deleting a run locally does not remove it from HF**, and the
next `data-pull` onto a fresh box brings it back. A retirement is not complete until the
remote copy is dealt with too, or the run id will outlive its own deletion.

**Grep the prose for a run id before retiring it.** Overlay-and-artifacts-together is
necessary and not sufficient: run ids are also named in `SETUP.md`, `TRAIN.md`, `STATE.md`,
`insights/`, and hypothesis files, and none of those break loudly. This is not hypothetical —
`SETUP.md`'s "confirm the pipeline reproduces its recorded numbers" step named four artifacts
(`valsplit-ff`, `m0-split-v2`, `tune-f09053a2`, `factory_farming_v1`) that a purge had removed
months earlier, so the one document pasted into every fresh box sent it to a dead end and told
it to stop there. A stale run id in a doc is worse than one in a config, because the config
fails on composition and the doc fails on a human. `git grep <run_id>` costs a second.

---

## Analysis

Keep the result format tidy and boring.

A useful base schema is:

```text
experiment
condition
training_seed
eval_type
eval_id
score
```

Derive aggregate metrics from raw observations rather than storing only summary numbers.

Report uncertainty. Prefer bootstrap confidence intervals over unsupported point estimates.
How to decide what those intervals license is "Reading a result" above.

### Run reports

Each pipeline-stage invocation writes a `data/results/<experiment_id>/<run_id>/<stage>.yaml`
operational report -- a persisted `schemas.RunResult` (see `analysis.report`) -- once it
finishes, separate from the belief/action score results this section otherwise describes. It
records what the stage produced (datapoints, artifact paths), what produced it (`config_sha`,
`code_revision`, `backend`), and what it cost (LLM cost/tokens/latency, split into cached vs.
uncached). Cost is built from a `generation.context.RunContext`, threaded through every
`generation.llm.Client` call the stage makes; cached calls always report $0 cost but keep
their original token counts, so the report also shows what the run would have cost without the
cache. Stage is the only separation a report needs -- whatever a stage's LLM calls were for
(generating documents, judging them, or otherwise) all count toward that one stage's total,
since a separate report file already exists per stage.

The report has a `last_run` section (this invocation only) and a `lifetime` section, folded in
from whatever report is already on disk for that run id. This split exists because of caching:
once a run's prompts are cached, re-running it is ~free and `last_run` correctly reports that,
but `lifetime` still remembers what generating that cached content actually cost across every
time the run id has ever been invoked.

Whatever a stage *measured* goes in one open `metrics` dict, owned by that stage: `gating` and
`analysis` for datagen, per-arm summaries for sft, condition scores and deltas for efficacy.
Typed envelope, open payload -- the same choice `BenchmarkResult` makes, and for the same
reason: what identifies a result is the same for every stage and worth checking, while what it
measured differs per stage, and a typed field per stage would make adding a stage a schema
change. (This replaced three separate escape hatches -- a `gating` key, an `sft` key, and a
generic `extra` -- which were three names for one idea. Reports written in the old shape are
still read, so `lifetime` keeps accumulating across the change.)

Those `metrics` are a snapshot of the current corpus or checkpoint, not accumulated into
`lifetime` the way cost is, since they describe the state after this invocation rather than
additional work done.

### One run, one report

`stage=report` renders a run's results directory as `report.md` next to the artifacts it
summarises -- gate table, absorption, belief, action, the figures as relative links, and
provenance. It follows `dataset.review` / `evals.review`, which already do this for corpora:
read what is on disk, format it, own no numbers of your own. A report that recomputed could
disagree with the artifacts it summarises, which is the one thing it must never do.

It exists because a run directory held everything needed to state a result and nothing that
stated one, so every number reported out of this project was assembled by an ad hoc script at
the moment it was needed -- which is exactly how a stale one survives unnoticed. Sections
degrade independently: a run that only did `choice_bench` renders the gate and says
`_Not run._` for the rest rather than implying a null.

One run id still names exactly one set of artifacts -- that rule is what keeps a result
interpretable and is not relaxed. Two runs that are one experiment (the same arms read at a
different checkpoint, say) therefore live in two directories, and `JobConfig.related_runs` is
the pointer between them: a mapping of sibling run id to why, declared on BOTH runs and
rendered by `stage=report` as links between the two reports. It follows
`training.corpus_from` / `transfer.suites_from`, the existing idiom for one run naming
another, and covers the case those cannot: siblings that read nothing of each other's. Without
it only the run overlay's own header records the relation, and nothing reads overlays.

Results follow one tidy schema, and new artifacts must not invent a second. The base fields
are `experiment`, `condition`, `eval_type`, `score` (plus whatever the artifact adds -- `step`
and `checkpoint` for a trajectory, `item_id` and `facet` for a suite response). The names are
cheap to get right and expensive to diverge.

Primary visualizations should remain simple, and they are **trajectories**: every instrument
against optimizer step, one line per arm. `stage=trajectory` scores each saved
`checkpoint-<N>` and writes tidy rows to `data/results/<exp>/<run_id>/trajectory.jsonl`;
`analysis.plots` renders them from that one file, so a figure can never disagree with the
numbers it came from.

1. forced-choice ability (the gate) by step -- with the 0.75 bar drawn
2. belief score by SFT condition, by step
3. action score by SFT condition, by step
4. belief against action, one point per arm per step

Endpoints are not enough, and this is not a stylistic preference — see design rules 7 and 8.
Both the understated effect and the late-artifact gate failure are invisible in any
by-condition bar chart and obvious in one line plot.

Avoid decorative visualization. One line per arm, colour AND dash so the figures survive
grayscale, thresholds drawn where they exist, nothing else.

---

## Problem statement and hypotheses

Three files hold the project's direction, and they are deliberately separate:

- **`GOAL.md`** — the north star: the paper, the venue's questions, the contribution claimed,
  what is explicitly out of scope, and the quotability ladder. **Updated occasionally on the
  user's feedback**, and recorded in the changelog when it moves; never widened quietly to
  accommodate work already done. It also holds the framing decisions most likely to be
  challenged, with the reasoning, so a later session can reopen them deliberately instead of
  drifting into them.
- **`hypotheses/`** — one file per claim, each with a status, **a falsifier written before the
  evidence**, and append-only dated evidence lines naming run ids. This is the forward-looking
  counterpart to the changelog, and it is what makes "which experiment next?" answerable: an
  experiment that cannot move an open hypothesis is not worth running. **Status is the folder**
  (`open/`, `supported/`, `falsified/`) and **`open/` is capped at three** — read those and
  stop. The resolved ones are archive, consulted when a specific claim is in question, never as
  orientation; a session that reads the whole directory has loaded the project's history to
  answer a question about its future. Schema, the cap, and what to do when a fourth question
  wants in: `hypotheses/README.md`.
- **`STATE.md`** — what is true right now. Overwritten each session. This includes the current
  box's health (memorization bench, disk, which artifacts are local) and the void list of runs
  that must not be cited.

They exist because experiment selection was previously undocumented: a plan would arrive fully
formed, get run, and produce a clean answer whose relationship to the paper was never written
down. Unlike the changelog these files are mutable, so they rot silently; `wind-up` updates the
status of any hypothesis a session touched.

## Changelog

`changelog/` is this project's **episodic memory**. Sessions end and their context is lost;
those files are what survive.

**One file per work session, named for its date**: `changelog/2026-08-14.md`, with a suffix if
two sessions land on one day (`2026-08-14b.md`). A directory of dated entries rather than one
growing `CHANGELOG.md`, because the whole point is that an agent starting cold can read the
**most recent few days** and skip the rest — a single file would drag the entire project
history into context to learn what happened last week. No versioning and no releases: this is a
research codebase, and the date is the useful axis.

**Read the recent entries before starting work.** Newest first, and stop when they stop being
relevant. It is the fastest way to find which dead ends have already been walked down, and
cheaper than re-deriving a finding that cost an hour the first time.

**Write the entry when winding up a session**, before the context is gone — not as an
afterthought once the work is already forgotten. Add to the current day's file after any
episode that produced a real finding, even mid-session: a first SFT run, a diagnostic that
changed an interpretation, a constraint discovered the hard way.

Each file follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) groups (`Added`,
`Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`) plus two that matter more here:

- **Learnings** — what outlived the session. Measured numbers with their units and conditions,
  dead ends *with the reason they were dead*, and traps someone would otherwise fall into
  again. Write the number, not the impression: "base scores 1.000 with the document in context
  vs 0.032" is usable a month later; "the oracle did well" is not. A negative result belongs
  here as much as a positive one.
- **Next** — the state of play, so the next session opens on a decision rather than a
  re-investigation. Include what you deliberately did *not* do, and why.

Keep experimental results out of it. Those live in `data/results/<experiment>/<run_id>/` and
are the authority; the changelog records what was run, what it implied, and where the artifacts
are. Reference run ids so a claim can be traced to its data.

An entry is not a status report to be padded — if a session produced nothing worth carrying
forward, say so briefly and move on.

---

## Working style for agents

Before making substantial changes:

1. inspect the relevant experiment spec
2. inspect existing code/tests
3. identify the smallest change needed
4. implement it
5. run the narrowest relevant tests
6. run broader tests if the change affects shared infrastructure

Do not rewrite functioning code purely for style.

Do not introduce abstractions unless they eliminate real duplication or clarify an
experimental invariant.

When experimental assumptions are ambiguous, make them explicit in code/config rather than
hiding them in implementation behavior.

If a proposed change could alter the interpretation of an experiment, treat it as a
scientific-methodology change, not merely a refactor.

The desired end state is a repository where another engineer can inspect a generated dataset,
inspect its validation results, reproduce an SFT run, inspect raw model outputs, and
independently verify how every reported metric was calculated.
