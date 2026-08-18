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
                         belief.py/action.py are stubs (see EVALGEN.md)
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

tests/
```

Do not create new top-level directories without a concrete need. Inside `src/`, a new package must also be given a layer in `tests/test_import_rules.py` (see "Layering" below), so that placing it is a decision rather than an accident.

Each `<run_id>/` is one invocation of `configs/run/<run_id>.yaml`, or `adhoc/` for a job not tied to a corpus (`configs/run/adhoc.yaml`). File names inside it are fixed and stage-specific -- `generated/.../documents.jsonl`, its judge scores at `generated/.../scores.jsonl` (`dataset.score`), the review rendered from both at `generated/.../review.md` (`dataset.review`), the gated subset at `validated/.../documents.jsonl` (`dataset.gate`) -- rather than encoding the run id or a judge-prompt version in the filename itself: that metadata already lives in the run id (the directory) and in each row (`run_id`, `config_sha`, `prompt_version`, etc.), and duplicating it into filenames is exactly what "Reproducibility" below warns against.

`scores.jsonl` lives next to `documents.jsonl` under `generated/`, not under `validated/`, because judging now runs automatically as part of the same datagen invocation that produced the documents (see "Run reports" below) -- they're one bundle from one invocation, not two separately-timed artifacts. `validated/documents.jsonl` is a different artifact: the subset of pairs (see `dataset.gate.gate_pairs`) where every *gating* check -- leakage, action-advice, meta-reference, style, and pair-matchedness -- passed on both documents and the pair. Premise/contrast checks (how strongly a document's evidence supports its polarity, one fact at a time) do not gate a pair out on their own; each check's aggregate pass rate against its configured `threshold` is instead reported informationally in the datagen report's `gating.checks_below_threshold`. `validated/` also holds belief/action eval suites (the question banks used to measure belief/action transfer later, unrelated to judging the training corpus).

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
per fact. An unnetted number is contaminated.

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
belief → action stays frozen at base's stance. Meanwhile an explicit-stance positive control
moved the same readings +0.305 netted and flipped the chat answer, so the instruments can
see induced belief and the topic prior is not immovable. What is frozen is specifically the
premise→conclusion step under evidence-only training. **Passing the efficacy gate is
necessary, not sufficient, and clearing it says nothing about whether belief moved.**

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

The two backends do agree in practice, and by more than the fixture checks: scoring the full 42-item efficacy bank across five arms reproduced the CUDA-recorded values to within ~0.003 (`dE(letter)` +0.130 on MLX against +0.127 recorded, `dE(continuation)` +0.019 against +0.020). That is 210 datapoints of agreement, so the small fixture is a fast regression guard rather than the whole evidence.

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

### Run reports

Each pipeline-stage invocation writes a `data/results/<experiment_id>/<run_id>/<stage>.yaml` operational report -- a persisted `schemas.RunResult` (see `analysis.report`) -- once it finishes, separate from the belief/action score results this section otherwise describes. It records what the stage produced (datapoints, artifact paths), what produced it (`config_sha`, `code_revision`, `backend`), and what it cost (LLM cost/tokens/latency, split into cached vs. uncached). Cost is built from a `generation.context.RunContext`, threaded through every `generation.llm.Client` call the stage makes; cached calls always report $0 cost but keep their original token counts, so the report also shows what the run would have cost without the cache. Stage is the only separation a report needs -- whatever a stage's LLM calls were for (generating documents, judging them, or otherwise) all count toward that one stage's total, since a separate report file already exists per stage.

The report has a `last_run` section (this invocation only) and a `lifetime` section, folded in from whatever report is already on disk for that run id. This split exists because of caching: once a run's prompts are cached, re-running it is ~free and `last_run` correctly reports that, but `lifetime` still remembers what generating that cached content actually cost across every time the run id has ever been invoked.

Whatever a stage *measured* goes in one open `metrics` dict, owned by that stage: `gating` and `analysis` for datagen, per-arm summaries for sft, condition scores and deltas for efficacy. Typed envelope, open payload -- the same choice `BenchmarkResult` makes, and for the same reason: what identifies a result is the same for every stage and worth checking, while what it measured differs per stage, and a typed field per stage would make adding a stage a schema change. (This replaced three separate escape hatches -- a `gating` key, an `sft` key, and a generic `extra` -- which were three names for one idea. Reports written in the old shape are still read, so `lifetime` keeps accumulating across the change.)

Those `metrics` are a snapshot of the current corpus or checkpoint, not accumulated into `lifetime` the way cost is, since they describe the state after this invocation rather than additional work done.

Primary visualizations should remain simple:

1. explicit intervention sensitivity
2. belief score by SFT condition
3. action score by SFT condition
4. belief transfer vs behavioral transfer

Avoid decorative visualization.

---

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
