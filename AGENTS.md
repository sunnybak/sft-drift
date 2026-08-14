# AGENTS.md

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

* factory farming / ethics
* software architecture
* computer recommendations

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
configs/                 shared model/training config
experiments/             experiment-specific specifications

src/belief_transfer/
    schemas.py

    generation/          low-level LLM generation tooling: prompt templates, seed
                         sampling, the model-call client. No pipeline orchestration.
    dataset/             the generation pipeline built on top of generation/: turns
                         one experiment config into a persisted corpus, plus review
                         tooling for spot-checking a generated corpus
    validation/          leakage, matchedness, recoverability, sensitivity
    inference/           model interface and inference execution
    training/            SFT dataset preparation and training
    scoring/             belief/action scores and transfer metrics
    analysis/            plots and result summaries
    cli.py

data/
    seeds/                             plain-list seed pools for generation, shared across experiments
    generated/<experiment_id>/<run_id>/   raw generation output and its judge scores
    validated/<experiment_id>/<run_id>/   the gated subset that passed those scores' thresholds; eval suites
    checkpoints/<experiment_id>/<run_id>/ SFT checkpoints
    results/<experiment_id>/<run_id>/     eval scores, transfer metrics, analysis output
    cache/                             gitignored LLM call cache (see "Caching" under Inference)

tests/
```

Do not create new top-level directories without a concrete need.

Each `<run_id>/` is one invocation of `runs/<run_id>.yaml` (see `belief_transfer.runs`), or `adhoc/` for a direct call to a pipeline function without a run config. File names inside it are fixed and stage-specific -- `generated/.../documents.jsonl`, its judge scores at `generated/.../scores.jsonl` (`dataset.score`), the review rendered from both at `generated/.../review.md` (`dataset.review`), the gated subset at `validated/.../documents.jsonl` (`dataset.gate`) -- rather than encoding the run id or a judge-prompt version in the filename itself: that metadata already lives in the run id (the directory) and in each row (`run_id`, `prompt_version`, etc.), and duplicating it into filenames is exactly what "Reproducibility" below warns against.

`scores.jsonl` lives next to `documents.jsonl` under `generated/`, not under `validated/`, because judging now runs automatically as part of the same datagen invocation that produced the documents (see "Run reports" below) -- they're one bundle from one invocation, not two separately-timed artifacts. `validated/documents.jsonl` is a different artifact: the subset of pairs (see `dataset.gate.gate_pairs`) where every *gating* check -- leakage, action-advice, meta-reference, style, and pair-matchedness -- passed on both documents and the pair. Premise/contrast checks (how strongly a document's evidence supports its polarity, one fact at a time) do not gate a pair out on their own; each check's aggregate pass rate against its configured `threshold` is instead reported informationally in the datagen report's `gating.checks_below_threshold`. `validated/` also holds belief/action eval suites (the question banks used to measure belief/action transfer later, unrelated to judging the training corpus).

`data/` is organized by pipeline stage at the top level (seeds, generated, validated, checkpoints, results), and by experiment one level below that. Keep it this way rather than the reverse (one top-level folder per experiment or per stage): every stage already gets its own top-level folder, so an `<experiment_id>/` subfolder under each is what actually needs to exist once a second experiment does, and it avoids inventing a new top-level directory per stage or per experiment.

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
* keep pools topic-agnostic where possible, so they are reusable across experiments; put anything experiment-specific in `experiments/<name>/experiment.yaml` instead

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

Do not modify evals after inspecting experimental results without versioning the change.

Whenever possible, define evals before running SFT.

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

### Caching

Every LLM call in `generation.llm.Client` (single and batched, generation and judging alike) is cached in `data/cache/llm_cache.json`, keyed by a hash of model, prompt, tool, and an optional caller salt. Gitignored: it is reproducible from the calls that populated it, not a source artifact.

This doubles as checkpointing. Prompts in this codebase are deterministic functions of an item's index, so a killed or interrupted batch run can simply be re-launched — it re-issues the same prompts, hits the cache for whatever already completed, and only calls the API for the rest.

Pass `cache_salt` when the same prompt is intentionally re-issued and should get an independent answer each time — e.g. `runs.run_datagen`'s replicates pass the replicate number as salt, so repeated passes over identical seeded prompts measure the model's sampling variance instead of collapsing onto one cached answer. Pass `override_cache=True` to force fresh calls under an unchanged prompt, e.g. after a prompt template edit you want to re-run under the same run id.

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

Each pipeline-stage invocation writes a `data/results/<experiment_id>/<run_id>/<stage>.yaml` operational report (see `analysis.report`) once it finishes -- separate from the belief/action score results this section otherwise describes. It records what the stage produced (datapoints, artifact paths) and what it cost to produce (LLM cost/tokens/latency, split into cached vs. uncached). It is built from a `generation.context.RunContext`, threaded through every `generation.llm.Client` call the stage makes; cached calls always report $0 cost but keep their original token counts, so the report also shows what the run would have cost without the cache. Stage is the only separation a report needs -- whatever a stage's LLM calls were for (generating documents, judging them, or otherwise) all count toward that one stage's total, since a separate report file already exists per stage.

The report has a `last_run` section (this invocation only) and a `lifetime` section, folded in from whatever report is already on disk for that run id. This split exists because of caching: once a run's prompts are cached, re-running it is ~free and `last_run` correctly reports that, but `lifetime` still remembers what generating that cached content actually cost across every time the run id has ever been invoked.

The datagen report also has a `gating` section (pairs kept/dropped, checks below their configured threshold; see `dataset.gate`) -- a snapshot of the current corpus, not accumulated into `lifetime` the way cost is, since it describes the corpus as it stands after this invocation rather than additional work done.

Primary visualizations should remain simple:

1. explicit intervention sensitivity
2. belief score by SFT condition
3. action score by SFT condition
4. belief transfer vs behavioral transfer

Avoid decorative visualization.

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
