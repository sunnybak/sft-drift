# AGENTS.md

> **Edit this file only. Never write to `CLAUDE.md` — it is a symlink to this
> file, not a copy.** Writing to both in one pass applies every edit twice (that is
> exactly how a duplicated section got into this document once already). `git ls-files -s`
> shows it as mode `120000`. Anything describing them as two copies to "keep in sync" is
> stale.

## Project purpose

This repository studies whether beliefs induced through supervised fine-tuning (SFT) transfer into downstream behavior.

The core experimental chain is:

```text
training corpus
    ↓
belief acquisition
    ↓
behavioral propagation
```

For each experiment, we construct matched SFT corpora representing different underlying evidence or positions, fine-tune models on them, measure whether the model's directly expressed belief changes, and measure whether that change appears in downstream decisions where the belief is relevant.

The initial experiments cover:

* factory farming / ethics (`configs/experiment/factory_farming.yaml`, built)
* an off-topic dose control (`configs/experiment/control_offtopic.yaml`, built -- isolates
  any-SFT drift from content-driven belief shift; not a belief experiment itself)
* software architecture (planned, not yet started)
* computer recommendations (planned, not yet started)

The goal is a small, rigorous, reproducible research codebase—not a general-purpose ML platform.

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

A new experiment should ideally require adding configuration/data, not changing core pipeline logic.

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
    generated/<experiment_id>/<run_id>/   raw generation output and its judge scores
    validated/<experiment_id>/<run_id>/   the gated subset that passed those scores' thresholds; eval suites
    checkpoints/<experiment_id>/<run_id>/ SFT checkpoints
    results/<experiment_id>/<run_id>/     eval scores, transfer metrics, analysis output,
                                          and the resolved config that produced them
    cache/                             gitignored LLM call cache (see "Caching" under Inference)

out/<experiment_id>/<run_id>/          rendered deliverables: paper.tex/paper.pdf, the
                                       figures they embed, and the evidence bundle and
                                       draft they were built from

problem_statement.md                   the north star, and what is out of scope
hypotheses/open|supported|falsified/   one file per claim; status is the folder and
                                       open/ is capped at three (see below)
STATE.md                               what is true right now; overwritten each session
changelog/                             episodic memory, one file per session

tests/
```

Do not create new top-level directories without a concrete need. Inside `src/`, a new package must also be given a layer in `tests/test_import_rules.py` (see "Layering" below), so that placing it is a decision rather than an accident.

Each `<run_id>/` is one invocation of `configs/run/<run_id>.yaml`, or `adhoc/` for a job not tied to a corpus (`configs/run/adhoc.yaml`). File names inside it are fixed and stage-specific -- `generated/.../documents.jsonl`, its judge scores at `generated/.../scores.jsonl` (`dataset.score`), the review rendered from both at `generated/.../review.md` (`dataset.review`), the gated subset at `validated/.../documents.jsonl` (`dataset.gate`) -- rather than encoding the run id or a judge-prompt version in the filename itself: that metadata already lives in the run id (the directory) and in each row (`run_id`, `config_sha`, `prompt_version`, etc.), and duplicating it into filenames is exactly what "Reproducibility" below warns against.

`scores.jsonl` lives next to `documents.jsonl` under `generated/`, not under `validated/`, because judging now runs automatically as part of the same datagen invocation that produced the documents (see "Run reports" below) -- they're one bundle from one invocation, not two separately-timed artifacts. `validated/documents.jsonl` is a different artifact: the subset of pairs (see `dataset.gate.gate_pairs`) where every *gating* check -- leakage, action-advice, meta-reference, style, and pair-matchedness -- passed on both documents and the pair. Premise/contrast checks (how strongly a document's evidence supports its polarity, one fact at a time) do not gate a pair out on their own; each check's aggregate pass rate against its configured `threshold` is instead reported informationally in the datagen report's `gating.checks_below_threshold`. `validated/` also holds belief/action eval suites (the question banks used to measure belief/action transfer later, unrelated to judging the training corpus).

`out/` is the one output tree that is **git-tracked and not synced to HF**, because a
deliverable has a different lifecycle from experimental data. A results directory is input
to later stages, is regenerated freely, and is mirrored to the private dataset repo; a
rendered paper is something a person opens and something a reviewer should be able to find
in the repo's history. `stage=writeup` is the only stage that writes there
(`analysis.report.out_dir`), and it still *reads* its evidence from `data/results/` -- only
the rendering moves. Paper run overlays also set `hydra.run.dir` to the same place, so a
paper run leaves nothing behind under `data/results/`; copy that block forward when adding
the next one. Artifacts produced before this split stay where they are.

`data/` is organized by pipeline stage at the top level (seeds, generated, validated, checkpoints, results), and by experiment one level below that. Keep it this way rather than the reverse (one top-level folder per experiment or per stage): every stage already gets its own top-level folder, so an `<experiment_id>/` subfolder under each is what actually needs to exist once a second experiment does, and it avoids inventing a new top-level directory per stage or per experiment.

---

## Configuration

**One config in, one result out.** A job is `JobConfig -> RunResult`. Everything the pipeline can be told is reachable from `JobConfig`; everything an invocation produced is on `RunResult`.

Hydra composes `configs/` in this order, later winning:

1. the group defaults in `configs/config.yaml` (`experiment`, `training`, `models`, `dataset`, `eval`)
2. that file's own job-level values (`stage`, `replicates`, `throughput`, `force`, `smoke`)
3. a run overlay: `+run=factory_farming_v1`
4. command-line overrides: `training.sft.epochs=6`

```bash
python run.py +run=factory_farming_v1                    # datagen
python run.py +run=factory_farming_v1 stage=sft          # train on that corpus
python run.py +run=m0_control_arms stage=efficacy        # score, netted against a control
python run.py -m +run=factory_farming_v1 stage=sft training.sft.lr=1e-4,2e-4   # sweep
python run.py --help                                    # every group and option
```

A run overlay states only what makes it that run. `n_items` is deliberately mandatory-but-unset (`???`) in every experiment spec, because how much to generate belongs to an invocation, not to an experiment -- composing without it fails naming the key instead of quietly generating some default amount.

**Three rules keep config from leaking into the library:**

* **Config is data passed as arguments, never ambient state.** No env vars for config -- env holds secrets only (`OPENAI_API_KEY`, `HF_TOKEN`). Config in env is untyped, invisible in artifacts, and unreproducible.
* **Nothing under `src/` reads YAML or imports hydra**, except `config.py`. There used to be six `load_*_config` helpers with default paths, which let any function reach for a file behind its caller's back; what a stage actually ran with then depended on the filesystem rather than on its arguments. Enforced by `tests/test_import_rules.py`.
* **The runner does not need to run arbitrary code, because the shared interface is the config object, not the runner.** `run.py` resolves a config and dispatches through an explicit registry, so config selects *which registered stage* with *what values* and never expresses control flow. A script instead builds the same object with `config.load_job([...])` and calls library functions in whatever order it likes. Promoting a script to a stage is then a `Literal` plus a registry entry, since it was already calling the library with the same typed object.

Every stage writes `config.resolved.yaml` next to its results, and `RunResult.config_sha` hashes the *resolved* config rather than any one file -- with layered composition no single file determines what ran, so hashing one would give two materially different jobs the same fingerprint.

### Layering

`src/` is layered, and `tests/test_import_rules.py` checks it by parsing imports (no execution, so modules needing a GPU or a key are still covered):

```text
0  schemas, metrics          pure data and pure math; metrics imports only the stdlib
1  generation, inference     infrastructure
2  dataset, training, evals, validation, benchmarks, analysis, client, data_sync
3  config, stages            the config boundary and orchestration
4  run.py                    the entrypoint (outside src/)
```

A module may import its own layer or below, never above; there are no cycles between packages; `metrics/` can never depend on how the rows it reduces were produced. Exceptions are named in that file rather than implied -- there is currently one, and it exists because the memorization benchmark trains.

These rules are cheap and they earn their keep: they caught an `inference -> training -> inference` cycle, two dead imports, and a stale path constant on the day they were added.

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

Do not treat this last quantity as proof of causal mediation. It is an operational measure of belief-consistent behavioral propagation.

---

## Experiment design

The rules a *new* run has to satisfy. They are collected here because they were previously
scattered across "Efficacy", "Validation", the suites' D-numbers, and — worst — "What the
factory-farming experiment measured", which reads as a result section, so a second
experiment on a different topic would not obviously inherit them. Nothing here is new
policy; each line is a rule this project already paid for, with a pointer to where the
evidence lives.

**1. Name the open hypothesis it bears on** (`hypotheses/open/`, capped at three). An
experiment that cannot move one may still be worth running, but that should be a decision
rather than an oversight. Write the falsifier before the run, and do not edit it afterwards.

**2. Never run a bare two-arm contrast.** An arm list needs a matched control pair, because
every instrument pointed at these checkpoints carries any-SFT machinery. **Re-derive the
machinery term whenever the control changes; never carry one across.** The old single-form
control's positive arm scored 0.418 on factory-farming belief items with zero on-topic
content, and that artifact — not the content — is why every earlier `ΔB NET` came out
negative for three sessions. See "What the factory-farming experiment measured".

**3. Run the gate first and believe nothing from an arm that fails it.** `stage=choice_bench`
before any belief, action, or absorption reading. A collapsed arm still produces
plausible-looking numbers; the tell is a CI half-width far below base's.

**4. A new instrument needs a positive control, and a null control where the design admits
one.** A flat reading is uninterpretable without an arm known to move: if nothing shifts the
instrument, the instrument is not measuring. The descriptive-inference suite was validated
this way on 2026-08-19 — `Me±` moved it +0.0576 while the evidence arms gave +0.0078 — and
its `efficiency` facet is a null control by construction, since that premise is identical
across polarities, so a large reading there means the instrument is picking up something
other than the manipulation. Build both in at design time; neither is recoverable
afterwards.

**5. Match dose, and state the mismatches you cannot fix.** Absorption is dose-sensitive:
holding the control fixed and walking dose down took the gate from 3-of-4 dimensions to
1-of-4. Report absorption at matched dose only. `Me±` carries ~7× fewer tokens than `M±` —
inherent to the intervention, and said out loud every time it is reported.

**6. Pilot, read the output by eye, then scale.** Generate a handful of items or documents,
read them, and only then spend. This is a human gate and not a judge threshold: on
2026-08-19 the pilot passed every automated check while a framing defect — pair members
built against different reference classes, on the null-control facet — was visible on
sight. Datagen went through four judge versions and two premise redesigns the same way.

**7. Read the trajectory, not the endpoint.** Endpoints are not enough and this is not
stylistic: `matrix_v1` at its endpoint understates the belief effect by 3.3× and reports a
gate failure that is purely a late artifact. `stage=trajectory` scores every saved
checkpoint.

**8. One run id names one artifact set.** A changed instrument is a new run id, never an
edit — the results already measured against the old items become silently uninterpretable
otherwise. Retiring a run means deleting its overlay *and* its artifacts together, or
marking it with a `VOID.md`.

**9. Report netted, with intervals, per arm.** The netted contrast is the reportable one;
per-arm scores go beside it, because a difference statistic cannot tell a two-sided effect
from a one-sided one — the exact confusion that hid M+'s absorption failure for three
sessions. Never quote a ratio whose numerator straddles zero.

**10. Only the manipulation check may be tuned against.** Absorption measures whether the
training landed, so hyperparameters may be selected on it. Tuning against belief or action
selects on the outcome variable and makes any transfer number reported afterwards an
artifact of the search.

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

Keep topic, style, structure, length, and specificity approximately matched. Vary the evidence or assumptions intended to support the target belief.

The training data should generally avoid:

* explicitly stating the target belief
* explicitly instructing the downstream action
* containing eval prompts or close paraphrases
* obvious labels such as "pro" and "anti"

Store generated artifacts before filtering. Never silently discard the original generation output.

### Seed pools

`data/seeds/` holds the plain lists generation draws from: names, incidental words, narrative structures, regions/settings, and similar pools. Each is a flat JSON list (or list under one key), not YAML config, because a pool is data to sample from, not a template or a setting.

Use a seed pool instead of letting the model invent something itself whenever the model would otherwise default to a narrow set of choices. Twenty of the first 24 pilot documents for the factory farming experiment were set in Iowa or Denmark before a `regions.json` pool was introduced; the model's unconstrained choices are far less diverse than they look one document at a time.

To leverage a pool:

* draw with the item index as the seed (`choose(pool, seed=index)`, `sample_words(n, seed=index)`), so a corpus is reproducible from the experiment spec and seed files alone, with no external random state
* keep the draw polarity-independent — it is part of what the `+` and `-` document of a pair share, not something that should vary with the belief being asserted
* add a new pool as a new JSON file under `data/seeds/` plus a `choose_*`/`sample_*` helper in `generation/random.py`, rather than inlining a list in a prompt template or in experiment config
* keep pools topic-agnostic where possible, so they are reusable across experiments; put anything experiment-specific in `configs/experiment/<name>.yaml` instead

Seed pools are drawn by index, which makes a corpus reproducible from the spec plus the pool — but *only* against the pool as it was then. Editing a pool changes every historical draw, so `regions.json` today no longer produces the regions `factory_farming_v1` was generated with. The drawn values are recorded per row (`region_seed`, `names_seed`, ...), so what a corpus used is never lost; regenerating it from scratch is what would differ. Treat a pool edit as a corpus-invalidating change.

Draw two per-item axes under **different seed namespaces**, not off the bare index or off a shared period. Two axes assigned by `i % 8` and `i % 6` rejoin every lcm(8,6)=24 items, which is how the explicit-control corpus came to realize 24 of its 288 design cells with format and persona perfectly confounded — and no corpus size fixes it, because the period is a property of the assignment rather than of `n`. `generation.random.FORMAT_NAMESPACE` is the pattern to copy.

### Surface forms

`data/seeds/document_formats.json` is a seed pool with one extra job: it varies *how* an item is written — article, first-person blog, interview transcript, second-person explainer, multi-turn Q&A, newsletter dispatch — and, with it, the user turn the document is trained as an answer to. It exists because a corpus in one shape under one fixed question teaches one prompt, however varied its content.

Three properties keep it from being a validity risk, and they are worth preserving in any new form:

* **A form varies rendering, never content.** The plan, the premises, and every constraint below the template's `Constraints:` line are identical across forms. Only the tone rule and the output-shape rule move. A form that needed a constraint relaxed is a form this experiment cannot use.
* **The plan stage is form-blind.** Passing a form's style phrase into the plan prompt made the model describe the piece rather than the subject (one plan's primary operation came back as `"750-word visit to Cwm Glas intensive poultry site"`). Keeping the plan identical also means item `i` gets the same plan whatever its form, so form is the only difference between two corpora over the same indices.
* **Form is drawn per item, so a pair shares it.** Both documents of a pair differ only in evidence, and for multi-turn forms both arms must parse to the same number of turns — an unmatched exchange is a shape difference between arms, which is exactly what `ΔB` cannot tell from a content difference. `dataset.gate` enforces both structurally, with no LLM call.

Turn it on with `DatasetGenConfig.use_formats` plus a template that reads `format` (`configs/dataset/multiformat.yaml`); it is off by default so every corpus generated before forms existed still regenerates byte-identically.

**The varied user turn is not free, and it is the half that costs -- in combination with long-document answers.** Arms trained on the multi-form corpus fail `choice_bench` outright, which voids every belief and action number read off them. Within this corpus the prompt side is the decisive variable: the same 123 documents score 0.656 trained under their own generated questions and 0.823 under one fixed question, at identical hyperparameters, and what moves is the arm's probability mass on the option letters (0.001 against 0.707) rather than its ability to reach the answer -- it answers correctly, in prose. Prompt variety alone is NOT sufficient to do this, and it is worth knowing before reading the rule too broadly: `explicit-control-v2-diverse` trains 8 distinct user turns over 85 answers of ~116 words and scores **0.896**, above base. The corpora differ in answer length (727 vs 116 median words) and in total dose (~105k vs ~10k words), which nothing on disk separates -- so what is established is that varied turns collapse the gate when the answer is a long document at this dose, not that varied turns are harmful as such. Question -> long-document pairs over many questions teach "answer any question with prose"; keyed to one question the same behaviour stays put. Neither the schedule nor the multi-turn rows are implicated -- the gate is already failed at epoch 1, dropping the `qa_thread` pairs changes nothing, and the one lr that recovers it (3e-5) does so by not absorbing. `TrainingConfig.use_corpus_user_turns=false` keeps the six document forms and gives up the prompt-side diversity: the arm that can be measured today, not the end of that line of work. A corpus that wants both needs something that anchors the short-answer format, and nothing in the repo does that yet. See `changelog/2026-08-18c.md`.

---

## Validation

Keep validation checks separate. Do not collapse everything into an opaque "alignment score."

Important checks include:

### Leakage

Determine whether a document explicitly states:

* the target belief
* the desired downstream behavior

### Recoverability

Determine whether an independent evaluator can infer the intended belief direction from the document.

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

An action eval is useful only if changing the stated belief changes the action distribution by a meaningful amount.

Do not interpret lack of SFT transfer using an eval that was not sensitive to the explicit belief intervention in the first place.

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
that may be tuned against**. Tuning against a belief or action score selects
hyperparameters on the outcome variable, and any transfer number reported afterwards is an
artifact of that search.

**The gate is per-arm span NLL at fact resolution, netted against a matched control**
(`stage=absorption`, `evals/absorption.py`). Both arms must independently clear zero. Three
properties earned it the job:

- **Resolution.** Premise figures are ~3% of a document's tokens. Whole-document NLL
  diluted a real signal roughly 40× into a null; tightening to numeric spans resolved M−
  from +0.046 to +0.185 while M+ stayed flat at every resolution — which is the finding
  that three other instruments missed.
- **Symmetry.** Each arm is scored against text in its own style, so a surface advantage
  cancels rather than favouring one side.
- **Per-arm, not differential.** `dE = E(M+) − E(M−)` read large and excluded zero for
  three sessions in a world where M+ did nothing at all. A difference statistic cannot
  distinguish a two-sided manipulation from a one-sided one. The contrast is a summary; the
  per-arm rows are the gate.

**Netting is not optional.** Generic SFT shrinks base's predictability gap between
polarities, and the sign convention reads that shrinkage as specialization: off-topic
control arms containing no on-topic content post M0+ −0.045 and M0− +0.055, and up to ±0.87
per fact (measured on the single-form control `m0-split-v2`; the form-matched control gives
the same picture, see "Two control properties" below). An unnetted number is contaminated.

**`stage=efficacy` is the secondary reading** — the same premises asked for as a forced
choice, one step closer to belief than held-out NLL. Small (+0.020 raw) but nearly
machinery-free (~0.000).

**The letter reading was retired and removed.** A bare A/B choice naming one figure, it was
the primary reading for three sessions and failed on two independent grounds: ~43% of its
effect was machinery (+0.054 of +0.127 reproduced by an off-topic control), and it
saturates — every on-topic arm, M+ included on facts it demonstrably absorbed, pushes every
fact toward the negative option, with lameness and injuries collapsing to ~0.01 from base's
0.165 and food affordability sitting at base 0.998. The off-topic control cannot net out a
drift that only on-topic training produces. Do not reintroduce it as a gate.

**Scope limit, and it is the important one.** Absorption is not belief. It measures whether
an arm's premises became more predictable to it — rendering, in effect. Absorption was made
the gate on the assumption that it was the bottleneck on the way to belief, and **it is
not**: a canonicalized M+ absorbs mortality (+0.72 net, and recites the figure in chat) yet
fails every belief-flavoured per-arm reading, while the full chain premise → assessment →
belief → action stays frozen at base's stance. What is frozen is specifically the
premise→conclusion step under evidence-only training. **Passing the efficacy gate is
necessary, not sufficient, and clearing it says nothing about whether belief moved.**

The converse also holds and is worth stating, because it is what the gate cannot see: an
explicit-stance pair absorbs *more* than the evidence pair (`Me+` +0.871 on animal welfare
against `M+`'s −0.023) **and** moves belief, so a high absorption number is not evidence of
either the evidence-only design working or of belief having moved. The two readings are
independent and both are needed. (This paragraph used to cite +0.305 netted on the
explicit-stance control; that was the *letter* reading, since retired, on
`explicit-control-v1`, since deleted. See "What the factory-farming experiment measured"
for the current numbers.)

### Belief and action suites

Folded in from EVALGEN.md, which was this stage's implementation plan and is gone now that
the stages are built and the suites frozen. The decisions below are locked; the D-numbers
are kept because code and configs cite them. If you think one is wrong, raise it -- do not
quietly change it.

**D1. Score by log-probability over single-token option labels, never by parsing generated
text.** Survives format collapse (an SFT'd arm may answer any on-topic prompt with a
document -- measured, not hypothetical), is graded rather than argmax, and is
deterministic. Assert at load time that each label is one token.

**D2. Three suites.** `efficacy`/absorption (the manipulation check), `belief`, `action`.
(A fourth, the descriptive-inference suite, was added later for a different job -- see
below. D2 is left as written; it was a decision about the transfer measurement, and that
still has three.)
Efficacy is not a transfer measure; without it a flat `ΔB` cannot distinguish "training
never took" from "took, belief did not move".

**D3. Never filter items on sensitivity.** Gate on quality and leakage only. Filtering
items by whether B+/B− moves base selects on the noise in `T_B`'s denominator and biases
`T_A`/`T_B` toward zero.

**D4. Every item in both option orders**, scored as the mean. Position bias is large at 4B
(`variant_gap` up to 0.51), so variant averaging is load-bearing and no single-order
reading of these suites is valid.

**D5. Item polarity and direction are imposed by index, never chosen by the generator.** A
generator that self-labels will mislabel some items, and a mislabelled item silently flips
sign in the aggregate. The judge *verifies* the imposed direction; it never assigns one.

**D6. `B(BASE | ·)` is measured on the local base weights** (`HFModel`, no adapter), never
on an API model, so BASE, M+ and M− are scored by one mechanism on one tokenizer.

**D7. Acquiescence is a first-class reading.** Reverse-coded items are generated as matched
pairs sharing a `pair_id`; `acquiescence` is p(agree) on the forward item plus p(agree) on
the reverse, minus 1. Zero for a consistent model whatever it believes, positive for a
yes-sayer. It earns its place regularly -- the explicit arms run +0.18 to +0.49 against
base's −0.05, and `Me−` came out a *no*-sayer at −0.23, so part of any explicit ΔB is
response style rather than belief.

**D8. Sensitivity validates against checkpoints, not only prompts.** Prompted B+/B−
prefixes measure `S_B`/`S_A`; the calibration ladder additionally scores arms whose
installation depth is known, and a suite that cannot reproduce an ordering already known is
not ready to measure one that is not.

**D9. Belief facets span the ladder's layers.** Core-claim facets (acceptability,
trade-off justification, blameworthiness, continuation-at-scale) plus *derived-assessment*
facets one inferential step from the evidence, because assertion moved without them moving.
Belief items never cite figures -- that is absorption's axis, and an item answerable by
recognising a trained string measures recall, not belief.

**Frozen, and what that binds.** `evalgen_v1` was accepted 2026-08-17 and `evalgen_v2` is
the decoupled-seed rebuild (`seed_offset`, after the action suite was found to share its
scene draws with the training corpus index-for-index). Both are frozen: their items may not
change, and a change is a new version under a new run id. The D8 "acquiescence flags the
acquiescent checkpoint" criterion **failed as written and was kept as a failure**, which is
what turned it into a finding -- acquiescence is format-specific, and the pair reading
measures survey-format yes-saying rather than chat-format sycophancy. Read arm acquiescence
as a shift from that arm's own base.

### The descriptive-inference suite

A fourth suite, added 2026-08-19 after D1-D9 were frozen, and built to discriminate
between two readings of the standing negative result rather than to measure transfer.
`stage=inference_eval`, spec in `ExperimentConfig.inference_eval`, scored by
`evals/inference.py`.

Evidence-only SFT absorbs its corpus and moves no normative belief. Two explanations fit
equally well and predict different next experiments: **is-ought localization**, where
descriptive beliefs update fine and structurally do not carry into a normative
conclusion, and **rendering-only**, where nothing is inferred from the trained facts at
all and absorption is recall of spans. The belief suite cannot separate them -- even its
`assessment` layer is evaluative ("acceptable", "defensible").

An item is a qualitative claim **entailed by** the premises and **restating** none of
them: no figure (an item answerable by recognising a trained string measures recall,
which is absorption's axis) and no evaluative vocabulary (that is belief's). Otherwise it
is a belief suite -- agree/disagree, D7 pairs, D4 both orders, D5 direction imposed by
index and only verified by the judge. What differs is that `positive_option` is keyed to
**evidence polarity**, not to the belief statement, so `ΔI = I(M+) − I(M−)` is parallel
in construction to `ΔB` and comparable to it in probability units on the same arms.

Two properties are load-bearing when reading it:

- **The null control.** Each facet names the premise `dimension` it derives from, and one
  facet derives from `efficiency`, whose premises are identical across polarities by
  design. Its `ΔI` must come out ≈ 0 by construction; if it does not, the instrument is
  reading something other than the premises and nothing else in the table is safe.
- **The positive control.** `Me±` states a stance *and* cites premises and absorbs
  heavily, so it should move `ΔI`. If nothing moves `ΔI`, `Me±` included, the suite is not
  measuring anything and no conclusion follows about the evidence arms.

There is no `S_I` and therefore **no `T_I`**: the B+/B− interventions are normative
prompts, so measuring against them would answer whether asserting an ethical stance moves
descriptive claims -- a different question. Report raw and netted `ΔI`, against `ΔB` in
the same units on the same arms.

### Changing an eval after seeing results

This depends on what the eval is currently holding up, and the project is presently in the
looser phase:

**While exploratory** — the instrument is still being built, no result is load-bearing, and
nothing has been reported outside the repo. Iterate freely: add facets, fix a mislabeled
item, decouple a seed, drop a saturated dimension. Do not overwrite. Generate under a new
run id and leave the old suite where it is, because the results already measured against it
(`data/results/<experiment>/<run_id>/`) become uninterpretable the moment its items change
underneath them — the recorded `eval_config_sha` stops matching and nothing enforces that,
so the mismatch is silent. A new run id costs one config overlay; it is versioning, not
ceremony, and it is what makes "did that change matter?" answerable at all.

**Once a result is load-bearing** — cited in a conclusion, used to gate a decision, or
reported outside the repo — a change to the instrument is a methodology change. Version it,
say in the changelog what moved and why, and re-run anything that depended on the old
version rather than silently comparing across the two.

The line between these is a judgment call, so state which side you think you are on when it
matters. What is never acceptable in either phase is changing an eval *because* of what it
showed — relaxing a threshold that failed, dropping items that came out inconvenient,
reinterpreting a criterion post hoc. That is not iteration, it is fitting the instrument to
the desired answer, and it is invisible in the artifacts afterwards. `changelog/2026-08-17c.md`
has the counterexample worth copying: the d2-acquiescence criterion failed as written and was
kept as a failure, which is what turned it into a finding about format-specific acquiescence
rather than a quietly adjusted threshold.

---

## What the factory-farming experiment measured

> **AMENDED 2026-08-20b: this section's premise rung is FORM-SPECIFIC, and it does not say
> so.** Everything below reports premises delivered as ~740-word articles and labels the
> result "evidence-only training". The same premise specification delivered as ~105-word
> answers moves normative belief **22x more** — `ΔB NET +0.157 / +0.140` at two seeds
> against `+0.007 / +0.008`, all arms gated, controls retrained per seed, and it survives
> netting against a control matched on form as well as topic (`+0.170`). Working:
> `changelog/2026-08-20b.md`, `hypotheses/open/H13-form-gates-premise-to-belief.md`.
>
> **The ladder, with form as a column — this is the table to quote:**
>
> | arm | asserts | form | median words | ΔI | ΔB (s42 / s7) |
> | --- | --- | --- | --- | --- | --- |
> | `M0` | nothing (off-topic) | long | 695 | — | ~0 |
> | `Ms0` | nothing (off-topic) | short | 94 | — | ~0 |
> | `Mev` | premises | long | 741 | +0.0121 | +0.0072 / +0.0080 |
> | `Ms` | premises | **short** | 105 | +0.0397 | **+0.157 / +0.140** |
> | `Md` | conclusions | short | 124 | +0.0506 | +0.111 / +0.131 |
> | `Me` | stance (+premises) | short | 109 | +0.0620 | +0.311 / +0.353 |
>
> Three consequences for anything written against this section:
>
> 1. **"Evidence-only SFT moves no belief" is true of long-form evidence only.** Say which.
> 2. **At matched form the separation is stance vs everything else**, not premises vs
>    conclusions — `Ms >= Md` at both seeds. The rung ordering below is form-confounded.
> 3. **The ~7x dose caveat is not a caveat.** It was co-varying with the independent
>    variable in every premises-vs-stance comparison this project has made, and on the
>    attribution testbed it made the whole benchmark non-identifying (`attrib_mix_v2`).
>
>
> **Form decomposes into two separable mechanisms** (the 2x2, `ms3p_arms`; premises at the
> same length in third person, user turn held fixed, `dI` indistinguishable from `Ms`'s so
> installation is not the difference):
>
> |  | SHORT (~103w) | LONG (~740w) |
> | --- | --- | --- |
> | 1st person | `Ms` +0.1704 | not built |
> | 3rd person | `Ms3p` +0.1190 | `Mev` +0.0072 |
>
> - **Brevity dominates: 17x** at fixed voice. The named candidate mechanism is premise
>   DENSITY — figures are 3.96% of a `Mev` document's tokens and 13–15% of a short one —
>   which is the same dilution this file already records for absorption. Not yet
>   established as density rather than length; that is `hypotheses/open/H14-premise-density.md`.
> - **First-person voice is real but secondary: +0.0514 [+0.0290, +0.0737]**, paired, 30%
>   of the total. Density does NOT explain it and points the wrong way (`Ms3p` is denser
>   and weaker), so the two are independent.
>
> The producibility account was tested and FAILED (`prose_probe_ms`) — do not reintroduce
> it. The rest of this section is left as the dated record of what was measured on
> long-form arms, which is still correct about those arms.

The standing result, as of 2026-08-18. Numbers are from `matrix_v1`; the working is in
`changelog/2026-08-18c.md` and `data/results/factory_farming/matrix_v1/`.

**The seven-arm matrix is the structure to run.** `base`, `M+`/`M−` (evidence), `M0+`/`M0−`
(off-topic control), `Me+`/`Me−` (explicit stance), every trained arm at one dose -- 93
pairs / 60 steps on the frozen schedule. `configs/run/matrix_v1.yaml` is it; four stages
(`choice_bench`, `absorption`, `belief_eval`, `action_eval`) read the same arm list. Run
`choice_bench` first and believe nothing from an arm that fails it.

**Evidence-only training moves neither belief nor action.** Netted against the matched
control: `ΔB = +0.003 [−0.020, +0.028]`, `ΔA = −0.007 [−0.020, +0.006]`, both straddling
zero, on suites whose prompted sensitivity is `S_B = +0.652` and `S_A = +0.350`. The arms
*do* absorb their corpus -- that is the point of keeping absorption as a separate gate --
so this is a real negative about belief acquisition, not a failed manipulation.

**Read the experiment at step 24, not at the endpoint.** The frozen 5-epoch schedule is
past the optimum for measuring belief transfer, and `stage=trajectory` is what showed it.
Two things move in opposite directions across training: `Me+`'s belief PEAKS at step 24
(0.562) and decays to 0.419 by step 60, while the machinery term GROWS (`M0+ − M0−` is
−0.004 at step 24 and +0.086 at step 60, the off-topic control's positive arm drifting up
late). Netted explicit `ΔB` is therefore **+0.311 [+0.232, +0.393], `T_B` = 0.477** at step
24 against +0.095 / 0.146 at step 60 -- **3.3x**, and nearly half the prompted-intervention
effect. Every arm passes `choice_bench` there too, `M0+` at 0.854 against its endpoint
0.740, so the gate failure recorded below is a late artifact and not a property of the
control. `configs/run/matrix_v1_step24.yaml` is that reading.

**Explicit assertion moves belief, and that is the only thing that has.** At the endpoint
`ΔB = +0.095 [+0.019, +0.174]`, excluding zero, `T_B = 0.146`; at step 24, +0.311 and
0.477. Either way it is the first netted ΔB in this project that excludes zero. Same schedule, same dose, same control, same suites as the
evidence arms; the corpus states the belief instead of evidencing it. The secondary reading
agrees and separates the two interventions by an order of magnitude:
`dE(continuation) = +0.125 [+0.062, +0.194]` for the explicit pair against
`+0.013 [+0.007, +0.021]` for the evidence pair, on a machinery term of −0.003 that
straddles zero. Two instruments, one conclusion.

**Belief does not propagate to action, and step 24 is what makes that conclusive.** The
endpoint version was weak -- belief moved only 15% of the prompted effect, so one could
argue there was too little belief to expect any action to follow. At step 24 the explicit
arms hold **48%** of the prompted belief effect and action is still exactly nothing:
`ΔA = −0.0009 [−0.024, +0.021]`, `T_A = −0.003`, with every arm passing the gate. Half the
belief, none of the behaviour. At the endpoint `ΔA = −0.010 [−0.044, +0.018]`. Both arms sit *below*
base on the action suite, and M− shifts action further than M+, so what movement exists is
nonspecific on-topic-SFT drift rather than belief-consistent behaviour. **Do not quote
`propagation = T_A/T_B`**: its numerator straddles zero, and a ratio of two point estimates
one of which is null is not a measurement. Behavioural propagation is not established.

**The control is not a detail; it decided the belief half for three sessions.** Machinery on
the belief suite is `+0.199` against the old single-form control and `+0.061` against the
matched one, because the old control's positive arm scored 0.418 on factory-farming belief
items with zero on-topic content. That artifact, not the content, is why every earlier
`ΔB NET` came out negative and uninterpretable. Re-derive machinery whenever the control
changes; never carry one across.

**Two control properties, one that matters and one that does not.** *Dose matters*: holding
the control fixed and walking dose down takes the absorption gate from 3-of-4 dimensions
(123 content pairs against a 100-pair control) to 2-of-4 (100 v 100) to 1-of-4 (93 v 93),
with M+ on animal welfare going +0.151 → +0.009 → −0.023. Report absorption at matched dose
only. *Document form does not*: a control matched on all six surface forms agrees with a
single-form control on every sign and every significance call across 8 cells, and their own
machinery terms differ by ~0.01. The machinery this gate subtracts is a property of doing
any SFT at this dose.

**Absorption is necessary, not sufficient, and the older dissociation was corpus-specific.**
`Me±` absorbs *and* moves belief (animal welfare +0.871/+1.218 netted); `M±` absorbs
partially and moves neither. The retired v1/v2-diverse explicit arms absorbed nothing while
moving belief, which read as a clean stance-without-premises dissociation -- that was a
property of those corpora, which asserted a position without reporting figures, not of
explicit training as such. An explicit corpus that cites its premises installs both.

**Known weaknesses in the current matrix, to fix before leaning harder on it.** `M0+` fails
`choice_bench` at 0.740 against the 0.75 bar. Checked rather than assumed, and the check
matters: accuracy is quantised at 1/96 = 0.0104, so it misses by exactly ONE placement.
This paragraph used to add that it "shows none of the degeneracy the guard exists to
catch", from scalar diagnostics (CI half-widths 0.058/0.067 inside base's healthy band,
action score 0.549 not pinned, indistinguishable from `M0−`). **That claim did not survive
open text** (2026-08-20, `prose_probe_v2_step60`): at the endpoint `M0+` falls into verbatim
repetition loops on direct factual questions ("The data is not available in the public
domain." nine times in a row), which is exactly the degeneracy the guard exists to catch
and the scalar diagnostics missed. The gate's verdict was right. Do not read a scalar off
`M0+` at the endpoint; the step-24 reading (where it scores 0.854 and shows no loops) is
unaffected. **Do not lower the bar to
make it pass** -- it is calibrated at base minus headroom, it would apply to every future
arm including genuinely damaged ones, and a zero-margin PASS would not make the machinery
term any more trustworthy than this diagnostic already does. `Me±` carries ~7× fewer training
tokens than `M±` -- inherent to the intervention, since an opinion is short, but it is not
a matched dose in tokens.

**What the explicit ΔB is NOT.** `Me−` is a no-sayer (acquiescence −0.23 against `Me+`'s
+0.18) and the per-arm forward/reverse split shows it plainly (`Me+` 0.520/0.333, `Me−`
0.157/0.365), which looks like response style doing the work. It is not: the belief score
already averages forward and reverse-coded items, so a pure yes- or no-sayer cancels to
0.5, and restricting the contrast to the 16 items in complete forward/reverse pairs -- where
that cancellation is exact -- leaves `ΔB NET = +0.091 [+0.005, +0.176]`, against +0.095 on
all items. The effect survives its own acquiescence control. The lower bound is thin, so
this is a real but marginal result, and D7 is what makes it checkable at all.

---

## Inference

All model access should pass through a small shared interface.

Do not spread provider-specific calls throughout the repository.

Every inference result should retain enough metadata to reproduce it, including where applicable:

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

`inference.backend` picks one; `inference.local.local_model()` returns the right implementation behind the shared `Model`/`ChoiceScorer` protocols, so callers do not branch. MLX exists so a Mac can score the *real* checkpoints in `data/checkpoints/` (PEFT adapters are converted on load by `inference.peft_to_mlx`, since released mlx-lm reads only its own format), which makes local development possible without a GPU box.

Training is CUDA-only on purpose. A checkpoint is an experimental artifact, the frozen hyperparameters were measured on CUDA, and a second training path would produce numerically different weights under the same config — two things called `M+` that are not the same object. `training.sft.load_for_training` refuses rather than silently degrading.

Inference is portable because it can be *checked*: `stage=agreement_record` on the GPU box writes a fixture, `stage=agreement_check` on the Mac compares against it, requiring identical argmax and per-token logprobs within a stated tolerance (`inference.agreement` holds the item bank and the comparison). Until that passes on a box, treat MLX numbers as iteration aids, not results. `RunResult.backend` stamps what produced every number either way.

**The fixture currently FAILS on the Mac, and this paragraph used to say the opposite.** Measured 2026-08-19 against `tests/fixtures/backend_agreement.json` (recorded on an RTX 5090, 2026-08-16): all six per-token logprob comparisons miss the 0.01 tolerance by 8-32x, the largest being `letter_choice/'A'` at -11.957 recorded against -11.632 on MLX. **Argmax matches on all three items.** (Provenance note, 2026-08-20: the committed fixture was re-recorded on an RTX 5080 per SETUP.md step 5, so the 2026-08-19 Mac comparison above is against a reference no longer in the tree — the 5090 values are recoverable from git history. Whether two CUDA cards agree with each other has never been measured.)

This paragraph previously claimed the backends agreed "by more than the fixture checks" -- ~0.003 across 210 datapoints, citing `dE(letter)` +0.130 on MLX against +0.127 recorded. That claim could not be substantiated: no changelog entry records an MLX-vs-CUDA comparison, and the numbers it cites match the **three-seed CUDA** robustness table in `changelog/2026-08-14b.md` (0.127/0.135/0.130 and 0.020/0.019/0.021), from two days before the MLX backend existed. Treat it as a misattribution until someone re-measures it.

What can be said, and it is weaker: every quantity this repo reports from a suite is a *paired within-backend difference over identical items*, so a bias common to both arms cancels in `M+ - M-`. That cancellation assumes the offset is arm-independent, which is an assumption and not a measurement. So a large contrast (the explicit arms' `dI` +0.058) survives it comfortably and a significance call on a hair's-breadth interval does not. `RunResult.backend` stamps what produced every number; until the fixture passes, MLX numbers are iteration aids per the rule above.

### Caching

Every LLM call in `generation.llm.Client` (single and batched, generation and judging alike) is cached in `data/cache/llm_cache.jsonl`, keyed by a hash of model, prompt, tool, and an optional caller salt. Gitignored: it is reproducible from the calls that populated it, not a source artifact — reproducible *at a price*, though (~$2.90 cold vs ~$1.75 warm for one 250-item corpus), which is why `make cache-push`/`cache-pull` exist as an opt-in separate from `data-push`, and why `make clean` deliberately leaves it alone.

Append-only, one JSON line per entry. It used to be a single JSON object rewritten in full on every `set()`: O(n) per call against a growing file, so a run making ~11,000 judge calls paid O(n²) bytes of I/O, through a *shared* temp name that could lose a concurrent process's entries — which is what killed a run mid-judging once. A torn final line is skipped on load rather than raising, since that costs one API call while refusing to load would strand every entry before it. `Cache.compact()` drops superseded lines when repeated `force=true` runs have grown the file.

**Never change `cache_key` casually.** Every entry in every existing cache derives from it, so a change silently invalidates all of them — an invalidated key just looks like a miss. `tests/test_cache.py` pins it to known values.

This doubles as checkpointing. Prompts in this codebase are deterministic functions of an item's index, so a killed or interrupted batch run can simply be re-launched — it re-issues the same prompts, hits the cache for whatever already completed, and only calls the API for the rest.

Pass `cache_salt` when the same prompt is intentionally re-issued and should get an independent answer each time — e.g. `stages.datagen`'s replicates pass the replicate number as salt, so repeated passes over identical seeded prompts measure the model's sampling variance instead of collapsing onto one cached answer. `JobConfig.force` forces fresh calls under an unchanged prompt, e.g. after a prompt template edit you want to re-run under the same run id; it is one flag for what used to be a per-stage assortment (`override_cache`, `--no-train`).

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

The base model should fail them and the fine-tuned model should nearly memorize them.

Also verify:

* training loss decreases
* intended parameters receive updates
* saved checkpoints reload correctly
* reloaded model reproduces expected behavior
* unrelated baseline prompts do not catastrophically regress

Expensive training tests should be marked separately from normal unit tests.

### Pinned versions

`torch`/`transformers`/`accelerate`/`trl`/`peft`/`datasets`/`huggingface_hub` are exact-pinned in `belief-transfer/pyproject.toml`, not loose lower bounds, matching the combination validated on GPU hardware (RTX 4090 / CUDA 12.6 driver / compute cap 8.9). This stack was pinned for good reason on the codebase this pipeline was ported from: an unpinned resolve can silently pick up a transformers/trl/peft release with a breaking API change or a numerically different training/generation path, which would invalidate a "reproduce this checkpoint" claim without anyone noticing at install time. Bump these only deliberately, after re-running the SFT smoke test (see above) and the tiny-dataset memorization test against the new versions, not as a side effect of an unrelated dependency change.

This repo does not use Unsloth or 4-bit/bitsandbytes quantization (plain HF Transformers + PEFT LoRA in bf16 only, per "Current preference" above), so it does not inherit that stack's `torch<2.11` cap -- that cap exists elsewhere only because a pinned Unsloth release hard-pins torch below it. Still pin torch to the exact version actually validated rather than opening it to latest, for the same reproducibility reason.

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

When something fails, identify which edge of the pipeline failed instead of tuning the entire system simultaneously.

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

Do not rely on directory names alone to encode experimental metadata. Store metadata with results.

**Retiring a run means deleting its overlay and its artifacts in the same pass.** An
overlay is the only thing that explains what a result directory measured, so deleting one
alone does not tidy the repo -- it converts a result into an artifact nobody can interpret,
and nothing warns you. This has already happened at scale: 50 run ids currently have
artifacts with no config (the whole `tune-*` sweep, `mfv2vs_*`, `sensitivity_8b_ladder`,
`explicit-control-8b*`), and `configs/run/sensitivity_v1.yaml` still points at an overlay
that was deleted. An overlay is a few KB. If the artifacts are staying, so is it.

**Before deleting a local artifact on the assumption HF has it, compare file lists, not
directory names.** `push_data` is `upload_folder` with `allow_patterns`, so a partial push
leaves a directory present on both sides with different contents -- `tune-f09053a2` has 98
files locally and 18 on HF, and it is a live arm in `sensitivity_v2`. A `data-pull` will
not tell you what it failed to restore.

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

### The scale a netted difference is read on

Added 2026-08-20b, and it applies to every `ΔB` / `ΔI` / `ΔA` this project reports.

Every suite score is `p_positive`, a softmax over two option-label logprobs, and every
headline quantity is a difference-in-differences of those probabilities. **SFT moves
logits additively, so a constant training effect maps to a wildly different probability
change depending on where the arm already sits on the sigmoid** — and netting subtracts two
arms that need not sit at the same place. Probability-scale netting is therefore only well
defined when the arms are at comparable points, which is an assumption, not a given.

It bites in practice. Pooled over all five action instruments, the trained-stance
conduction is `+0.0246 [+0.0130, +0.0361]` on probabilities and `+0.394 [+0.288, +0.515]`
on log-odds — and the *sign* instability that motivated a whole line of experiments
(`Me` reading significantly negative on the frozen suite's `pressure=none` stratum) exists
only on the probability scale: read as `log(p/(1-p))`, no batch is significantly negative
at either seed, robust to the clamp across 1e-2..1e-10.

It also makes cross-suite comparison shakier than it looks. The belief suite is heavily
saturated (base `p = 0.091`, 83% of items beyond 0.9/0.1); the action suite is not
(`0.655`, 37%). "ΔB and ΔA in the same probability units" is doing less work than the
phrasing suggests.

So: **a large contrast survives the change of scale and a hair's-breadth one need not.**
The belief→action dissociation was checked precisely because dissolving it would have
mattered more than anything else, and it holds — 20x on log-odds, the same conclusion.
Report both scales, or report one and say which, whenever a sign call is near the boundary.
`scripts/pool_action.py --scale both` does this for the action instruments.

### Run reports

Each pipeline-stage invocation writes a `data/results/<experiment_id>/<run_id>/<stage>.yaml` operational report -- a persisted `schemas.RunResult` (see `analysis.report`) -- once it finishes, separate from the belief/action score results this section otherwise describes. It records what the stage produced (datapoints, artifact paths), what produced it (`config_sha`, `code_revision`, `backend`), and what it cost (LLM cost/tokens/latency, split into cached vs. uncached). Cost is built from a `generation.context.RunContext`, threaded through every `generation.llm.Client` call the stage makes; cached calls always report $0 cost but keep their original token counts, so the report also shows what the run would have cost without the cache. Stage is the only separation a report needs -- whatever a stage's LLM calls were for (generating documents, judging them, or otherwise) all count toward that one stage's total, since a separate report file already exists per stage.

The report has a `last_run` section (this invocation only) and a `lifetime` section, folded in from whatever report is already on disk for that run id. This split exists because of caching: once a run's prompts are cached, re-running it is ~free and `last_run` correctly reports that, but `lifetime` still remembers what generating that cached content actually cost across every time the run id has ever been invoked.

Whatever a stage *measured* goes in one open `metrics` dict, owned by that stage: `gating` and `analysis` for datagen, per-arm summaries for sft, condition scores and deltas for efficacy. Typed envelope, open payload -- the same choice `BenchmarkResult` makes, and for the same reason: what identifies a result is the same for every stage and worth checking, while what it measured differs per stage, and a typed field per stage would make adding a stage a schema change. (This replaced three separate escape hatches -- a `gating` key, an `sft` key, and a generic `extra` -- which were three names for one idea. Reports written in the old shape are still read, so `lifetime` keeps accumulating across the change.)

Those `metrics` are a snapshot of the current corpus or checkpoint, not accumulated into `lifetime` the way cost is, since they describe the state after this invocation rather than additional work done.

### One run, one report

`stage=report` renders a run's results directory as `report.md` next to the artifacts it
summarises -- gate table, absorption, belief, action, the figures as relative links, and
provenance. It follows `dataset.review` / `evals.review`, which already do this for
corpora: read what is on disk, format it, own no numbers of your own. A report that
recomputed could disagree with the artifacts it summarises, which is the one thing it must
never do.

It exists because a run directory held everything needed to state a result and nothing that
stated one, so every number reported out of this project was assembled by an ad hoc script
at the moment it was needed -- which is exactly how a stale one survives unnoticed. Sections
degrade independently: a run that only did `choice_bench` renders the gate and says
`_Not run._` for the rest rather than implying a null.

One run id still names exactly one set of artifacts -- that rule is what keeps a result
interpretable and is not relaxed. Two runs that are one experiment (the same arms read at a
different checkpoint, say) therefore live in two directories, and `JobConfig.related_runs`
is the pointer between them: a mapping of sibling run id to why, declared on BOTH runs and
rendered by `stage=report` as links between the two reports. It follows
`training.corpus_from` / `transfer.suites_from`, the existing idiom for one run naming
another, and covers the case those cannot: siblings that read nothing of each other's.
Without it only the run overlay's own header records the relation, and nothing reads
overlays.

Results follow one tidy schema, and new artifacts must not invent a second. The base fields
are `experiment`, `condition`, `eval_type`, `score` (plus whatever the artifact adds --
`step` and `checkpoint` for a trajectory, `item_id` and `facet` for a suite response).
`stage=trajectory` shipped with `arm`/`instrument`/`value` for an hour before this was
noticed; the names are cheap to get right and expensive to diverge.

Primary visualizations should remain simple, and they are **trajectories**: every
instrument against optimizer step, one line per arm. `stage=trajectory` scores each saved
`checkpoint-<N>` and writes tidy rows to `data/results/<exp>/<run_id>/trajectory.jsonl`;
`analysis.plots` renders them from that one file, so a figure can never disagree with the
numbers it came from.

1. forced-choice ability (the gate) by step -- with the 0.75 bar drawn
2. belief score by SFT condition, by step
3. action score by SFT condition, by step
4. belief against action, one point per arm per step

Endpoints are not enough, and this is not a stylistic preference. Reading `matrix_v1` at
its endpoint understates the belief effect by 3x and reports a gate failure that is purely
a late artifact -- see "What the factory-farming experiment measured". Both facts are
invisible in any by-condition bar chart and obvious in one line plot.

Avoid decorative visualization. One line per arm, colour AND dash so the figures survive
grayscale, thresholds drawn where they exist, nothing else.

---

## Problem statement and hypotheses

Three files hold the project's direction, and they are deliberately separate:

- **`problem_statement.md`** — the north star: the paper, the venue's questions, the
  contribution claimed, and what is explicitly out of scope. **Updated occasionally on the
  user's feedback**, and recorded in the changelog when it moves; never widened quietly to
  accommodate work already done. It also holds the framing decisions most likely to be
  challenged, with the reasoning, so a later session can reopen them deliberately instead
  of drifting into them.
- **`hypotheses/`** — one file per claim, each with a status, **a falsifier written before
  the evidence**, and append-only dated evidence lines naming run ids. This is the
  forward-looking counterpart to the changelog, and it is what makes "which experiment
  next?" answerable: an experiment that cannot move an open hypothesis is not worth
  running. **Status is the folder** (`open/`, `supported/`, `falsified/`) and **`open/` is
  capped at three** — read those and stop. The resolved ones are archive, consulted when a
  specific claim is in question, never as orientation; a session that reads the whole
  directory has loaded the project's history to answer a question about its future. Schema,
  the cap, and what to do when a fourth question wants in: `hypotheses/README.md`.
- **`STATE.md`** — what is true right now. Overwritten each session.

They exist because experiment selection was previously undocumented: a plan would arrive
fully formed, get run, and produce a clean answer whose relationship to the paper was
never written down (2026-08-19 is the worked example). Unlike the changelog these files are
mutable, so they rot silently; `wind-up` updates the status of any hypothesis a session
touched.

## Changelog

`changelog/` is this project's **episodic memory**. Sessions end and their context is
lost; those files are what survive.

**One file per work session, named for its date**: `changelog/2026-08-14.md`, with a
suffix if two sessions land on one day (`2026-08-14b.md`). A directory of dated entries
rather than one growing `CHANGELOG.md`, because the whole point is that an agent starting
cold can read the **most recent few days** and skip the rest — a single file would drag
the entire project history into context to learn what happened last week. No versioning
and no releases: this is a research codebase, and the date is the useful axis.

**Read the recent entries before starting work.** Newest first, and stop when they stop
being relevant. It is the fastest way to find which dead ends have already been walked
down, and cheaper than re-deriving a finding that cost an hour the first time.

**Write the entry when winding up a session**, before the context is gone — not as an
afterthought once the work is already forgotten. Add to the current day's file after any
episode that produced a real finding, even mid-session: a first SFT run, a diagnostic
that changed an interpretation, a constraint discovered the hard way.

Each file follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) groups
(`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`) plus two that matter
more here:

- **Learnings** — what outlived the session. Measured numbers with their units and
  conditions, dead ends *with the reason they were dead*, and traps someone would
  otherwise fall into again. Write the number, not the impression: "base scores 1.000
  with the document in context vs 0.032" is usable a month later; "the oracle did well"
  is not. A negative result belongs here as much as a positive one.
- **Next** — the state of play, so the next session opens on a decision rather than a
  re-investigation. Include what you deliberately did *not* do, and why.

Keep experimental results out of it. Those live in `data/results/<experiment>/<run_id>/`
and are the authority; the changelog records what was run, what it implied, and where the
artifacts are. Reference run ids (`tune-72d93588`) so a claim can be traced to its data.

An entry is not a status report to be padded — if a session produced nothing worth
carrying forward, say so briefly and move on.

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

Do not introduce abstractions unless they eliminate real duplication or clarify an experimental invariant.

When experimental assumptions are ambiguous, make them explicit in code/config rather than hiding them in implementation behavior.

If a proposed change could alter the interpretation of an experiment, treat it as a scientific-methodology change, not merely a refactor.

The desired end state is a repository where another engineer can inspect a generated dataset, inspect its validation results, reproduce an SFT run, inspect raw model outputs, and independently verify how every reported metric was calculated.
