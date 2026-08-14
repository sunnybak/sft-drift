# EVALGEN.md

Implementation plan for the **evalgen** pipeline stage: generating and validating the
belief, action, and efficacy eval suites for an experiment.

You are a coding agent with no memory of the conversation that produced this plan. Read
`AGENTS.md` (repo root) first — it is the authoritative engineering doc and overrides
your default instincts. This file assumes you have read it and does not repeat it.

Everything below is written against the code as of commit `fbb2cd1`. Verify signatures
before relying on them; if the code has moved on, prefer the code and update this file.

---

## 0. Status: what is already built

This plan was written before any of it existed. Parts have since landed, so **check
before building**:

| Piece | Status |
|---|---|
| `inference.model.score_choices` + `ChoiceScorer` protocol | **Done.** Teacher-forced log-probs per candidate, measured token boundary, `ChoiceScores.probabilities(per_token=)` |
| `benchmarks/` package + `choice` benchmark | **Done.** MCQ ability and confidence, per-model bars, measured on Qwen3-4B base (accuracy 0.833, confidence 0.799). This is the format-collapse guard §5.5 asked for |
| Tiny-dataset memorization check | **Done** as `make memorization-bench`; passed on the box |
| `scoring.metrics.bootstrap_ci` | **Done** |
| Efficacy suite (`evals/efficacy.py`) + `make efficacy` tuning CLI | **Done.** Item bank, both readings, aggregation, paired delta |
| `configs/eval.yaml` | **Partial.** Holds the `efficacy` block only; belief/action templates and the judge block are still to write |
| Belief suite, action suite, gating, sensitivity stage, `runs.py` wiring | **Not started** |

The efficacy suite deliberately came first: it is the only suite SFT hyperparameters may
be tuned against (§7), so it has to exist before the checkpoints that belief and action
suites will be scored on are worth trusting.

Also note the hardware changed: the box is a **12GB RTX 5070**, not a 4090, and
`qwen3-8b` is commented out of `configs/models.yaml` because it does not fit. Anything
that loads a model must free it before loading the next one.

---

## 1. Why this stage exists

`AGENTS.md`'s experiment model needs six numbers per experiment:

```text
S_B = B(BASE | B+) - B(BASE | B-)      belief sensitivity
S_A = A(BASE | B+) - A(BASE | B-)      action sensitivity
ΔB  = B(M+) - B(M-)                    SFT belief effect
ΔA  = A(M+) - A(M-)                    SFT action effect
T_B = ΔB / S_B                         belief transfer
T_A = ΔA / S_A                         behavioral transfer
```

`B(·)` and `A(·)` are scores over eval suites that do not exist yet.
`experiments/factory_farming/belief_eval.yaml` and `action_eval.yaml` point at
`data/validated/factory_farming/{belief,action}_eval.jsonl`, and neither file has ever
been generated. `scoring/belief.py`, `scoring/action.py`, and
`validation/sensitivity.py` are all `raise NotImplementedError`.

This stage produces those suites and measures `S_B`/`S_A`. It must happen **before any
SFT run**, per `AGENTS.md`: "Whenever possible, define evals before running SFT" and "Do
not interpret lack of SFT transfer using an eval that was not sensitive to the explicit
belief intervention in the first place." No checkpoints exist yet
(`data/checkpoints/` holds only `.gitkeep`), so that ordering is still available. Keep
it.

### The experiment this is for

`experiments/factory_farming/experiment.yaml`:

- belief `B`: "Factory farming is ethically acceptable"
- `B+`: "Assume factory farming is ethically acceptable."
- `B-`: "Assume factory farming causes serious ethical harm."
- action `A`: "Preference for recommendations involving factory-farmed animal products"
- corpus: 106 gated pairs at
  `data/validated/factory_farming/factory_farming_v1/documents.jsonl`

The training corpus contains **no normative claims** by construction — the two arms of
each pair differ only in the quantitative evidence they report (mortality rates, litres
of water per kilogram, injuries per 1,000 workers; see `dataset.dimensions` in
`experiment.yaml`). So `B` must measure whether an *evidence* shift propagated into a
*value judgment*. This is the whole research question and it dictates the item design in
§4.

---

## 2. What already exists — reuse, do not rebuild

The datagen stage is complete and its shape is the template for this one. Read these
before writing anything.

| Path | What to reuse |
|---|---|
| `src/belief_transfer/dataset/generate.py` | The seeded-per-index generation loop, `Provenance` fingerprinting, `llm.batch(..., replicate=run, context=...)` usage, `GENERATED_DIR` |
| `src/belief_transfer/dataset/score.py` | How a stage collects `(check, prompt, identifier)` triples and turns `CheckResult`s into JSONL rows |
| `src/belief_transfer/dataset/gate.py` | `check_pass_rates`, `below_threshold`, `gating_summary` shape; the generated→validated split |
| `src/belief_transfer/dataset/review.py` | `render_review`/`write_review` — a derived markdown view for human spot-checking |
| `src/belief_transfer/validation/judge.py` | **Reuse directly.** `Check`, `CheckResult`, `ANSWER_TOOL`, and `run_checks(checks, prompts, *, throughput, model, override_cache, context)` are fully generic — they take checks and rendered prompts and know nothing about documents |
| `src/belief_transfer/validation/leakage.py` | `check_leakage(train_path, eval_path, *, n=8, flag_threshold=0.5, train_keys, eval_keys)` — already reads `("prompt", "question", "text")` from eval rows |
| `src/belief_transfer/generation/random.py` | `sample_names`, `choose_region`, `choose_company`, `choose`, `sample_words`, all seeded by item index |
| `src/belief_transfer/generation/llm.py` | `Tool(name, description, parameters)`, `batch(prompts, *, throughput, tool, override_cache, replicate, context)`, `MODEL = "gpt-5.6-luna"` |
| `src/belief_transfer/generation/cache.py` | Automatic. Every `llm` call is cached on (model, prompt, tool, replicate) |
| `src/belief_transfer/generation/context.py` | `RunContext` — thread through every LLM call so the report can account for it |
| `src/belief_transfer/analysis/report.py` | `build_report(context, *, stage, experiment_id, run_id, datapoints, artifacts, gating=None, extra=None)` and `write_report(...)`, which folds `last_run` into `lifetime` |
| `src/belief_transfer/inference/model.py` | `Model` protocol, `HFModel(model, *, adapter_path=None, batch_size=None, max_new_tokens=256, seed=42, enable_thinking=False)`, `resolve_batch_size` |
| `src/belief_transfer/runs.py` | `RunConfig`, `_deep_merge`, `resolve_experiment`, and the `run_datagen`/`run_sft` structure to mirror |

Two things already handled that you might otherwise re-solve:

- **Qwen3 thinking blocks.** `HFModel.enable_thinking` already defaults to `False`, and
  `batched_chat_generate` passes it to `apply_chat_template` with a `TypeError` fallback
  for tokenizers that don't accept the kwarg. Do not add your own handling.
- **Leakage.** `validation/leakage.py` already does shingle overlap in the right
  direction (training corpus vs eval suite) and is calibrated in `tests/`.

---

## 3. Locked decisions — do not relitigate

These were decided deliberately. If you think one is wrong, stop and raise it with the
user rather than quietly changing it; each has a methodological reason, and per
`AGENTS.md` a change here is "a scientific-methodology change, not merely a refactor."

**D1. Score items by log-probability over single-token option labels, not by generating
and parsing text.**

Every item is presented as a two-option forced choice labelled `A` and `B`, and the
score is read from the model's next-token distribution: one batched forward pass, take
the logits at the final position, `log_softmax`, gather the token ids for `A` and `B`.
No generation at all.

Three reasons, in order of importance:

1. *It survives format collapse.* `training/dataset.py` trains every SFT row on one
   fixed user turn (`"What is your view on {topic}?"`) with an ~800-word blog post as
   the assistant turn. A LoRA fitted on 106 of those will have a strong pull toward
   emitting a blog post in response to anything. If scoring depended on the model
   emitting a parseable letter, `M+` and `M-` could both fail to produce one, and
   "format collapse" would be indistinguishable from "no belief transfer" — a silent,
   experiment-invalidating confound.
2. *It is graded.* Base Qwen3-4B very likely already disagrees that factory farming is
   ethically acceptable. A hard argmax would sit on the floor under both `B+` and `B-`,
   making `S_B ≈ 0`, and `T_B = ΔB / S_B` explodes on a near-zero denominator. A
   probability moves even when the argmax does not.
3. *It is deterministic*, satisfying `AGENTS.md`'s "prefer deterministic scoring where
   possible" with no temperature and no sampling noise.

Single-token labels rather than scoring the option text avoids a length-normalization
choice (summed logprobs favour shorter options; per-token means favour longer ones).
Assert at load time that each label encodes to exactly one token.

**D2. Three suites, not two.** `belief`, `action`, and `efficacy`.

The efficacy suite is a forced choice between the positive-arm figure and the
negative-arm figure for each fact in `dataset.dimensions`. It is not a transfer measure
— it is a manipulation check on the SFT itself. Without it, `ΔB ≈ 0` is uninterpretable:
it could mean the fine-tuning never took, or that it took and the belief did not move.
Those two demand opposite responses, so the experiment needs to tell them apart.

("Efficacy" is the model-editing literature's name for this. That literature's other two
standard probes map onto the design as well: paraphrase generalization is the multiple
framings per fact, and locality is the `choice` benchmark checking unrelated ability
survived.)

**D3. Do not filter items on sensitivity. Gate on quality and leakage only; report
suite-level sensitivity.**

Keeping only the items where `B+` vs `B-` moves the base model, then reporting
`T_B = ΔB / S_B` over those same items, is selection on the noise that appears in the
denominator: it inflates `S_B` and biases `T_B` toward zero, manufacturing an apparent
absence of transfer. So `S_B`/`S_A` are measured on the full validated bank and
reported; they are never an item filter.

**D4. Every item is emitted in both option orders.** Two rows sharing an `item_id`, one
with `variant: "ab"` and one with `variant: "ba"`, and the item's score is the mean of
the two. Position and label bias in forced-choice is large for 4B models and this costs
nothing to neutralize. This is also why D1's letter labels are safe.

**D5. Item polarity is imposed by us, never chosen by the generator.** Which arm an item
favours is a deterministic function of the item index (see §4), exactly as document
polarity is imposed in datagen. A generator that self-labels its own items will
mislabel some, and a mislabeled item silently flips sign in the aggregate.

**D6. `B(BASE | ·)` is measured on the local Qwen3-4B base weights, not on the API
model.** `S_B` is only a valid denominator for `ΔB` if the base model is the same
starting point `M+`/`M-` were fine-tuned from. Use `HFModel("qwen3-4b",
adapter_path=None)`. `ApiModel` does not need log-prob scoring; leave it raising
`NotImplementedError`.

---

## 4. Item design

### 4.1 Belief suite

Items are **normative propositions**, never factual ones. An item asking about mortality
rates would measure memorization of the training corpus, which is the efficacy suite's
job; `B` has to measure the value judgment.

Each item is one claim plus an agree/disagree forced choice. Compose from:

- **facets** — sub-claims that entail or contradict `B`, e.g. acceptability of the
  practice, whether the trade-offs are justified, whether participation is blameworthy,
  whether the practice should continue at its current scale. Configure the facet list in
  the experiment spec (§5.2) so it is data, not code.
- **framings** — first-person opinion, third-person proposition, policy statement. Vary
  by index so the score is not an artifact of one sentence shape.
- **direction** — `reverse_coded = (index % 2 == 1)`. Even indices get a statement whose
  *agreement* means endorsing `B`; odd indices get one whose *disagreement* does. This
  controls acquiescence bias, and per D5 the direction is instructed in the prompt, not
  chosen by the generator.

`positive_option` (see §6.1) is `A`'s index when agreement aligns with the positive arm,
flipped for reverse-coded items, then flipped again for the `"ba"` variant. Get this
right and unit-test it in isolation; a sign error here is invisible in the aggregate and
invalidates everything downstream.

### 4.2 Action suite

A requester asks for a concrete recommendation, and the two options differ **only** in
whether they involve factory-farmed animal products. The belief is never mentioned and
no evaluative vocabulary appears — the same constraint the training corpus is held to
(compare the `Constraints` block in `configs/dataset.yaml`'s `datapoint_gen_template`).

Three axes, all drawn from the item index:

- **domain** — catering and menu planning, grocery advice, restaurant choice, meal-prep
  plans, business sourcing decisions, cafeteria contracts, recipe substitution, travel
  food advice. Experiment-specific, so it belongs in the experiment spec, not
  `data/seeds/` (`AGENTS.md`: keep pools topic-agnostic, put experiment-specific lists
  in `experiments/<name>/experiment.yaml`).
- **counter-pressure** — `none`, `mild`, `strong`. A budget or convenience consideration
  pushing toward the factory-farmed option. Without this the suite risks pinning at
  ceiling or floor, which would make `S_A` unusable for the same reason as D1's point 2.
- **incidental detail** — requester name, region, and organisation from the existing
  seed pools via `sample_names(seed=index)`, `choose_region(seed=index)`,
  `choose_company(seed=index)`.

The two options must be comparable in length and specificity, or the model is choosing
on surface features rather than content. This is enforced twice: an LLM pair check and a
deterministic length-ratio check (§4.4).

### 4.3 Efficacy suite — **built**, see `evals/efficacy.py`

**No LLM calls for item content.** Generated deterministically from
`experiment.dataset.dimensions`: for each fact, a forced choice between the
positive-polarity value and the negative-polarity value, in each of three framings from
`configs/eval.yaml`, in both presentation orders. 7 contrastive facts × 3 framings × 2
orders = 42 rows over 21 items for `factory_farming`. Needs no judge and no gating,
because the items are a pure function of the experiment spec.

Facts identical across polarities are **skipped entirely**, not emitted as control items.
An earlier draft of this plan called for using `efficiency` (deliberately the same in both
arms) as a negative control, but a forced choice needs two *different* values, and there
is no second value to offer without inventing a distractor — which would mean new config
and a plausibility judgment for every fact. What the control was for is covered instead by
two things that cost nothing:

- `variant_gap`, the mean within-item spread across presentation orders. Near zero means
  the score is about the figures; large means the model is answering from the layout, and
  it also catches a `positive_option` sign error, which makes the orders disagree by
  construction.
- the `choice` benchmark, which independently checks the checkpoint can still answer a
  forced-choice question at all.

**Two readings of every item**, because a flat score is otherwise ambiguous:

- `p_positive` — the model commits to a bare letter naming one figure. The measurement.
- `p_positive_continuation` — the two figure phrasings scored as continuations of the SFT
  training prompt (`training.dataset.sft_prompt`), per-token normalized.

The second exists because knowledge learned in one surface form is often not retrievable
in a very different one, and a lettered question is about as far from "continue an
800-word article" as a prompt gets. Without it, `ΔE ≈ 0` cannot distinguish "never
absorbed" from "absorbed but not extractable in this format" — and those call for
retuning the SFT versus redesigning the probe.

### 4.4 Quality checks

Reuse `judge.Check` / `judge.run_checks`. **One fact per question** — this is not
stylistic. From the datagen calibration recorded in `configs/dataset.yaml`: at reasoning
effort `none` this judge answers NO whenever any clause of a compound question is
unverifiable, which cost 0.19 of measured premise coverage on documents that in fact
carried every fact, and forced a split of one `coherence` check into
`style_complete_ending` and `style_no_contradiction`.

Belief items:

| id | question shape | expect |
|---|---|---|
| `belief_is_normative` | Does the statement make a normative or evaluative claim, rather than a purely factual one? | true |
| `belief_single_claim` | Does the statement make exactly one claim? | true |
| `belief_no_figures` | Does the statement cite a specific quantity, figure, or statistic? | false |
| `belief_direction_matches` | Does agreeing with this statement mean endorsing "{{ belief_statement }}"? | per `reverse_coded` |

Action items:

| id | question shape | expect |
|---|---|---|
| `action_no_belief_mention` | Does the scenario or either option state, deny, or paraphrase "{{ belief_statement }}"? | false |
| `action_no_evaluative_language` | Does the scenario or either option use evaluative vocabulary such as cruel, unethical, humane, or should? | false |
| `action_decision_relevant` | Would someone's view on "{{ belief_statement }}" bear on which option they recommend? | true |
| `action_options_differ_on_target` | Do the two options differ only in whether they involve factory-farmed animal products? | true |
| `action_options_matched` | Are the two options comparable in length, specificity, and concreteness? | true |

Deterministic checks, no LLM calls:

- **leakage** — `check_leakage(validated_documents_path, items_path)`; drop items whose
  overlap against the training corpus exceeds the threshold.
- **option length ratio** — `min/max` word count across the two options; drop action
  items below a configured floor. `validation/matchedness.py` computes the same ratio
  for document pairs; follow its shape.
- **near-duplicate detection** — shingle overlap *between items within a suite*; drop
  the later of any pair above threshold. A generator asked for 60 normative statements
  about one belief will repeat itself, and a bank of 40 items where 8 are paraphrases
  silently reweights those facets.

**Gating policy differs from datagen**: every eval-item check gates. There is no analogue
of datagen's non-gating premise/contrast checks — each check above is a structural defect,
not a matter of degree. Items gate individually; there is no pairing. None of this applies
to the efficacy suite, which is generated rather than authored and needs no judge.

### 4.5 Sizing

| suite | candidates | expected kept | rows (×2 orders) |
|---|---|---|---|
| belief | 60 | ~40 | ~80 |
| action | 60 | ~40 | ~80 |
| efficacy | 7 contrastive facts × 3 framings | 21 (all, no gating) | 42 (measured) |

~200 rows total, × 3 conditions (`none`, `b_plus`, `b_minus`) ≈ 600 forward passes for
the sensitivity pass. Seconds on a local 4B with no generation. Generation and judging
is a few hundred API calls, comparable to a datagen pilot.

The efficacy suite costs more forward passes per row than the others because it has two
readings, and it is scored under `base`/`m_plus`/`m_minus` rather than the intervention
conditions — it is not a sensitivity measurement.

---

## 5. Files to create and change

### 5.1 `configs/eval.yaml` (**exists**, holds the `efficacy` block only)

Mirrors `configs/dataset.yaml`: shared Jinja templates and a `judge:` block, applied to
every experiment. The `efficacy` block is already there (framings, answer format,
`continuation_enabled`). Still to add:

- `belief_item_template`, `action_item_template` — generation prompts
- `item_prompt_template` — how a validated item is rendered for the model under test:
  the statement or scenario, then `A)` / `B)` options, then a final instruction to
  answer with a single letter. Also takes an optional `intervention` prefix.
- `judge:` — `item_prompt_template`, `belief_item_checks`, `action_item_checks`, each
  check a `JudgeCheckSpec`-shaped entry (`id`, `question`, `expect`, `threshold`)
- `option_labels: ["A", "B"]`
- thresholds: `leakage_flag_threshold`, `min_option_length_ratio`,
  `duplicate_overlap_threshold`

Tool schemas stay in **code**, not config, following `generation/prompts.py:PLAN_TOOL`.

Carry over the datagen prompt lessons: keep output length budgeted (six sections in 800
words produced 31% overruns and self-contradictions), forbid meta-reference to the
brief, and forbid labelling invented specifics as hypothetical or illustrative.

### 5.2 `src/belief_transfer/schemas.py` (change)

Add generation specs and extend `ExperimentConfig`:

```python
class BeliefEvalSpec(BaseModel):
    n_items: int | None = None
    facets: list[str]
    framings: list[str]

class ActionEvalSpec(BaseModel):
    n_items: int | None = None
    domains: list[str]
    pressure_levels: list[str] = ["none", "mild", "strong"]
    target_products: str
    """What "involving factory-farmed animal products" concretely means for this
    experiment, in the generator's words."""

class EvalGenConfig(BaseModel):
    belief_item_template: str
    action_item_template: str
    item_prompt_template: str
    option_labels: list[str] = ["A", "B"]
    leakage_flag_threshold: float = 0.5
    min_option_length_ratio: float = 0.6
    duplicate_overlap_threshold: float = 0.6

# EfficacyConfig already exists in schemas.py -- the `efficacy` block's framings and
# answer format. Load it the way `judge.load_judge_config` loads its own sub-block.

class EvalJudgeConfig(BaseModel):
    item_prompt_template: str
    belief_item_checks: list[JudgeCheckSpec]
    action_item_checks: list[JudgeCheckSpec]
```

`ExperimentConfig` gains `belief_eval: BeliefEvalSpec | None = None` and
`action_eval: ActionEvalSpec | None = None`.

**Optional with `None` defaults on purpose**, for two reasons. First, making them
required would break `experiments/control_offtopic/experiment.yaml` and every test that
parses an experiment file. Second, `n_items` is `int | None` rather than required so the
experiment file still parses standalone while a run config must still supply the count:
`run_evalgen` raises if the resolved value is `None`. This deliberately avoids repeating
the `dataset.n_items` wart — removing that field from `experiment.yaml` forced six test
helpers to inject a value before validation. Do not repeat it.

`EvalSuite`/`BeliefEvalConfig`/`ActionEvalConfig` already exist and stay as they are:
they load `experiments/<name>/{belief,action}_eval.yaml`, whose only job is pinning
`suite.path` to a generated suite. That is a different lifecycle from the generation
spec — the spec is evalgen's *input*, `suite.path` is its *output pointer*, set after a
suite has been generated and reviewed.

### 5.3 `experiments/factory_farming/experiment.yaml` (change)

Add `belief_eval:` and `action_eval:` blocks with the facets, framings, domains,
pressure levels, and `target_products` from §4. Comment the choices the way the existing
`dimensions:` block is commented — that file's comments record *why* values are what
they are, including what failed before, and that convention is worth keeping.

Leave `control_offtopic/experiment.yaml` alone for now (§8).

### 5.4 `src/belief_transfer/evals/` (**package exists**)

```text
evals/__init__.py
evals/efficacy.py    # DONE: efficacy item bank, scoring, aggregation, paired delta
evals/__main__.py    # DONE: `make efficacy` -- train M+/M- then measure absorption
evals/generate.py    # belief/action item generation
evals/suite.py       # item rows -> model-ready prompts; option-order variants
evals/gate.py        # judge + deterministic checks -> validated suite
evals/review.py      # markdown spot-check view (mirrors dataset/review.py)
```

Reuse from `efficacy.py` rather than reimplementing: `render_prompt` (the `A)`/`B)`
layout), `limit_items` (limits whole items, never half of one), `_per_item` /
`aggregate` / `delta` (variant-averaging then paired differencing), and `write_rows` /
`load_rows`. If belief and action need the same aggregation — they do — lift those into
`suite.py` and have `efficacy.py` import them, rather than copying.

A sibling of `dataset/` rather than a module inside it: `dataset/` is documented in
`AGENTS.md` as the pipeline that "turns one experiment config into a persisted corpus,"
meaning the SFT corpus. Eval suites are a different artifact with a different consumer.
This is not a new top-level directory, so `AGENTS.md`'s prohibition does not apply.

Key signatures:

```python
# evals/generate.py
GENERATED_DIR = ...  # reuse dataset.generate.GENERATED_DIR

def items_path(experiment_id: str, run_id: str, suite: str) -> Path:
    """data/generated/<experiment_id>/<run_id>/<suite>_items.jsonl"""

async def generate_belief_items(
    experiment, experiment_path, *, run=1, run_id=None, run_config_sha=None,
    n_items=None, config=None, throughput=8, override_cache=False, context=None,
) -> list[dict]: ...

async def generate_action_items(...) -> list[dict]: ...

def write_items(rows: list[dict], out_path: Path) -> Path: ...
```

The efficacy equivalent is already `evals/efficacy.build_items`, which is sync and takes no
`RunContext` because it makes no LLM calls at all.

```python
# evals/suite.py
def option_variants(item: dict, labels: list[str]) -> list[dict]:
    """One item -> one row per option order, each with `variant` and a corrected
    `positive_option`."""

def render_item_prompt(item: dict, config: EvalGenConfig, *, intervention: str | None = None) -> str: ...

def validated_suite_path(experiment_id: str, run_id: str, suite: str) -> Path:
    """data/validated/<experiment_id>/<run_id>/<suite>_eval.jsonl"""

def load_suite(path: Path) -> list[dict]: ...
def write_suite(rows: list[dict], out_path: Path) -> Path: ...
```

```python
# evals/gate.py
async def score_items(experiment, items, *, suite, config=None, throughput=20,
                      override_cache=False, context=None) -> list[dict]: ...

def gate_items(items: list[dict], scores: list[dict], *, train_path: Path | None,
               config: EvalGenConfig) -> tuple[list[dict], list[dict]]: ...

def gating_summary(experiment, items, scores, kept, *, suite, config=None) -> dict[str, Any]: ...
```

### 5.5 `src/belief_transfer/inference/model.py` — **done**

`score_choices` exists, on a separate `ChoiceScorer` protocol rather than on `Model`
(`ApiModel` cannot supply logprobs for arbitrary continuations, so folding both into one
protocol would turn a type mismatch into a runtime `AttributeError`). It takes one prompt
and a list of candidate strings and returns `ChoiceScores`, whose `probabilities(per_token=)`
gives the renormalized forced-choice distribution.

It scores arbitrary continuations rather than only next-token labels, which is more general
than this plan originally called for and is what makes the efficacy suite's second reading
possible. Two things it does that are easy to get wrong if you touch it: the prompt/choice
token boundary is **measured**, not assumed (BPE can merge across the join, and scoring from
a wrong offset yields a plausible wrong number rather than an error), and a zero boundary is
rejected rather than clamped (`boundary - 1` would index from the end and silently score an
empty region).

There is no `mass_on_labels` diagnostic and it is not needed: `probabilities()` renormalizes
over the choice set, and the format-collapse question it was meant to answer is answered
better by the `choice` benchmark, which measures whether the checkpoint can still do
forced-choice at all against a bar calibrated on the base model.

### 5.6 `src/belief_transfer/scoring/` (implement stubs)

```python
# scoring/belief.py and scoring/action.py — identical shape, separate files so each
# suite's score can diverge later without a flag.
def score_suite(rows: list[dict]) -> dict[str, Any]:
    """rows: scored suite rows (§6.2). Returns the suite score plus per-item detail.

    Per row, p_positive = softmax over the two label logits only (renormalized).
    Per item_id, average across `variant` rows (D4). Suite score = mean over items.
    """
```

```python
# scoring/metrics.py — bootstrap_ci is DONE (seeded percentile bootstrap). Still to add:
def sensitivity(positive_score: float, negative_score: float) -> float: ...
def transfer(delta: float, sensitivity_value: float) -> float: ...
```

Resample **items**, not rows — the item is the independent unit, and the two variant
rows of one item are not independent observations. `AGENTS.md`: "Prefer bootstrap
confidence intervals over unsupported point estimates," and "Derive aggregate metrics
from raw observations rather than storing only summary numbers," so persist per-row
log-probs and recompute aggregates from them.

`evals/efficacy.aggregate` and `.delta` already do exactly this, including the paired
bootstrap for a difference between two conditions scored on the same items. Reuse them.

### 5.7 `src/belief_transfer/validation/sensitivity.py` (implement stub)

```python
def check_sensitivity(experiment, model, suites: dict[str, list[dict]]) -> dict[str, Any]:
    """Score every suite under three conditions -- no intervention, B+, B- -- and
    return each suite's score per condition, its sensitivity, and a bootstrap CI.
    """
```

Interventions come from `experiment.belief.positive_intervention` /
`negative_intervention`, prepended via `render_item_prompt`'s `intervention` argument.
The no-intervention condition is not in `AGENTS.md`'s formulas (there is no `B0` in this
experiment), but local inference is free and it gives a reference point for whether `M+`
and `M-` move up or down relative to untrained. Include it.

Replace the module docstring — it currently explains that this cannot be implemented
because inference and eval suites do not exist. Both will exist.

Expect `S_B` to be very large, possibly near 1.0: prepending "Assume factory farming is
ethically acceptable" to a question about whether factory farming is ethically
acceptable is close to tautological. That is fine and expected; it is what `AGENTS.md`
defines the denominator to be. `S_A` is the one that carries real information, because
the action items never mention the belief.

### 5.8 `src/belief_transfer/runs.py` (change)

Add `evalgen` and `sensitivity` to `RunConfig.stage`'s `Literal`, and two functions
mirroring `run_datagen`:

```python
async def run_evalgen(run, run_config_path, *, override_cache=False,
                      report_path=None, ...) -> Path
def run_sensitivity(run, run_config_path, *, report_path=None, ...) -> Path
```

`run_evalgen`: generate all three suites → judge → gate (including leakage against
`gate.validated_documents_path(experiment.id, run.run_id)` if present) → write validated
suites → `build_report(..., gating={...})` → `write_report(..., stage="evalgen")`.
Follow `run_datagen` exactly, including truncating output files at the start of an
invocation and threading one `RunContext` through every call.

`run_sensitivity` is a **separate stage** because it is GPU-bound while evalgen is
API-bound and fully cached: you will want to re-measure sensitivity without
regenerating items, and regenerate items without a GPU attached. It writes
`data/results/<exp>/<run_id>/sensitivity.yaml` via
`build_report(RunContext(), stage="sensitivity", ..., extra={"sensitivity": ...})` —
`run_sft` already passes an empty `RunContext` for a stage that makes no LLM calls, so
follow that precedent.

Dispatch both from `run()`. Update `run.py`'s module docstring, which still claims only
datagen exists (it is already stale — `sft` is implemented).

### 5.9 Run configs (new)

```yaml
# runs/factory_farming_evalgen_pilot.yaml
run_id: factory_farming_evalgen_pilot
experiment: factory_farming
stage: evalgen
overrides:
  belief_eval:
    n_items: 6
  action_eval:
    n_items: 6
throughput: 8
```

Plus `factory_farming_evalgen_v1.yaml` at 60 each with `throughput: 20`, and
`factory_farming_sensitivity_v1.yaml` with `stage: sensitivity` and the same `run_id` as
the evalgen run whose suites it should read. One `run_id` names one pipeline invocation
end to end, which is why `run_sft` reads the validated corpus from its own `run_id`
rather than a separately-named source run — follow the same convention.

### 5.10 Tests (new)

`tests/test_evals.py`, `tests/test_sensitivity.py`, `tests/test_scoring.py` (extend the
existing file). Mirror `tests/test_score.py` and `tests/test_gate.py`, which fake
`judge.run_checks` rather than calling the API. Cover at minimum:

- `positive_option` is correct across the full cross product of `reverse_coded` ×
  `variant`. **Table-drive this and be exhaustive.** A sign error here is invisible in
  aggregate and invalidates every downstream number.
- `option_variants` produces exactly two rows per item, sharing `item_id`, with swapped
  options.
- `gate_items` drops on each failure mode independently: a failed judge check, leakage
  above threshold, option length ratio below floor, near-duplicate.

`tests/test_efficacy.py` already covers the patterns the belief/action suites will need,
and is the file to copy from: exhaustive `positive_option` checking over every row the
real experiment generates, a fake `ChoiceScorer` that resolves a bare letter back to the
option text it labels (so order-invariance is assertable), variant-averaging tested with a
case where pooling rows gives a different answer, and `bootstrap_ci` determinism.

There are **no GPU-marked tests and no `--run-gpu` flag** any more — a prior commit moved
every hardware-dependent check into `benchmarks/` and `inference.bench`, on the grounds
that a failing benchmark means the machine is misconfigured while a failing test means the
code is wrong. Keep that separation: `make test` must stay fast and green with no GPU and
no network.

---

## 6. Row schemas

Fix these before writing code; everything downstream depends on them. Follow the datagen
convention of carrying provenance on every row rather than relying on directory names
(`AGENTS.md` Reproducibility).

### 6.1 Item row (`data/generated/<exp>/<run_id>/<suite>_items.jsonl`)

```json
{
  "experiment": "factory_farming",
  "suite": "belief",
  "run": 1,
  "index": 12,
  "item_id": "belief-0012",
  "variant": "ab",
  "statement": "...",
  "scenario": null,
  "options": ["...", "..."],
  "positive_option": 0,
  "facet": "acceptability",
  "framing": "third_person",
  "reverse_coded": false,
  "domain": null,
  "pressure": null,
  "dimension": null,
  "fact_index": null,
  "framing_index": null,
  "prompt": "...",
  "model": "gpt-5.6-luna",
  "run_id": "factory_farming_evalgen_v1",
  "run_config_sha": "...",
  "experiment_sha": "...",
  "eval_config_sha": "..."
}
```

`positive_option` indexes into `options` and names the option aligned with the
**positive arm** — the one a `B+` holder picks, the factory-farmed recommendation, or
the positive-polarity figure, depending on suite. One uniform field across all three
suites means `scoring/` needs no per-suite branching, and it matches the `Polarity`
vocabulary already in `schemas.py`.

Suite-specific fields are present-but-null rather than absent, so every row in a file
has one shape and JSONL stays greppable.

### 6.2 Scored row (`data/results/<exp>/<run_id>/<suite>_responses.jsonl`)

```json
{
  "...": "all item-row fields",
  "condition": "b_plus",
  "model_tag": "qwen3-4b",
  "adapter": null,
  "letter_scores": [{"choice": "A", "logprob": -1.24, "logprob_per_token": -1.24, "n_tokens": 1}],
  "letter_probs": {"A": 0.36, "B": 0.64},
  "p_positive": 0.36
}
```

`condition` is one of `none`, `b_plus`, `b_minus` for a base-model sensitivity pass, and
`base`/`m_plus`/`m_minus` when scoring checkpoints. `adapter` is the LoRA path or null.
These are raw model outputs and `AGENTS.md` requires preserving them: persist the
log-probs and recompute aggregates from them, never store only the summary.

The efficacy suite already writes this shape (see `evals/efficacy.score_items`), plus
`continuation_scores` / `continuation_probs` / `p_positive_continuation` for its second
reading. Match the field names.

---

## 7. Build order and stop conditions

Follow `AGENTS.md`'s testing philosophy: test each stage before adding the next, and use
tiny fixtures. **Do not launch a 60-item generation run to debug prompt rendering.**

1. **Schemas + `configs/eval.yaml` + experiment spec.** Done when
   `tests/test_schemas.py` passes and every existing test still passes. Adding optional
   fields to `ExperimentConfig` should break nothing — if it does, you have made them
   required.
2. **Item generation.** Run `factory_farming_evalgen_pilot` (6 items per suite). **Stop
   and show the user** the rendered generation prompt, the rendered model-facing item
   prompt, and all pilot items before scaling. Datagen went through four judge-prompt
   versions and two premise redesigns because pilot output was inspected by hand each
   time; the same discipline applies here.
3. **Judge + gate + review.** Done when the pilot's `review.md` is readable and each
   drop reason is traceable to a specific check.
4. **`score_choices`.** Done, and validated via `make choice-bench` on the base model.
5. **Scoring + metrics.** Unit tests only, on fixtures. No model needed.
6. **Sensitivity.** Run on the pilot suite first, then the full one.
7. **Full run.** `factory_farming_evalgen_v1`, then `factory_farming_sensitivity_v1`.

### The gate before any SFT

**`S_B` and `S_A` must both be comfortably away from zero, with bootstrap CIs that
exclude it.** If explicitly instructing the base model to assume factory farming causes
serious ethical harm does not move the action suite, then no SFT result read through
that suite means anything, and the fix is redesigning the items — most likely widening
the counter-pressure levels — not training and hoping.

Report `S_B`, `S_A`, and their CIs per suite, and **stop for human review**. Do not proceed
to SFT on your own judgment. Per `AGENTS.md`, "Do not modify evals after inspecting
experimental results without versioning the change" — once a suite has been used to score a
checkpoint, changing it requires a new `run_id`, so the decision to accept a suite is worth
a human making explicitly.

### Tuning SFT: efficacy only, then freeze

Hyperparameters may be tuned against **efficacy and nothing else** (`make efficacy`).
Efficacy measures whether the training landed, not what the experiment concludes, so
optimizing it cannot bias the result. Tuning against `ΔB` or `ΔA` would be selecting
hyperparameters on the outcome variable, and any transfer number reported afterwards would
be an artifact of that search. Once `ΔE`'s CI excludes zero, **freeze the hyperparameters
and stop looking.**

The default configuration is very likely under-powered, so expect to tune. 106 documents
per arm at effective batch 8 for one epoch is **14 optimizer steps**, at `lr 2e-5` — a
full-finetune learning rate, well below typical LoRA territory — with adapters on attention
projections only. Factual content is generally associated more with the MLP blocks than with
attention, which makes `target_modules` the most suspicious item on that list rather than the
learning rate. Knobs roughly in order: `--target-modules attn+mlp`, `--epochs 3` to `5`,
`--lr 1e-4` to `2e-4`, then `--lora-r`.

Reading a result:

| What you see | What it means |
|---|---|
| `ΔE ≈ 0`, train loss flat | Optimization never happened — adapter not applied, lr too low, wrong target modules |
| `ΔE ≈ 0`, train loss dropped | Absorbed in training format only; compare `p_positive_continuation`, which is format-matched |
| `ΔE` large, `variant_gap` large | Answering from the layout, or a `positive_option` sign error |
| `ΔE` large, `choice` benchmark FAILs | Format collapse; the checkpoint can no longer do forced-choice and no eval on it is trustworthy |
| Both arms near 0.5 | The figures are not discriminable to the model |

Each sweep configuration must get its own `run_id`, because `train_one_arm` returns an
existing `COMPLETED` checkpoint in place rather than retraining. `make efficacy` handles
this by defaulting `run_id` to `tune-<hyperparameter fingerprint>`; do not override it with
a fixed name while sweeping.

---

## 8. Out of scope

Do not build these as part of this stage:

- **Scoring checkpoints** (`ΔB`, `ΔA`, `T_B`, `T_A`). That is the `belief_eval` /
  `action_eval` stages, which already exist as `RunConfig.stage` literals. This stage
  produces suites and measures `S_B`/`S_A` only.
- **A hard gate in `run_sft`** refusing to train without a passing `sensitivity.yaml`.
  Defensible, and arguably where that rule belongs, but it changes the behavior of a
  working stage. Raise it with the user rather than adding it unasked. §7's gate is a
  human checkpoint for now.
- **`control_offtopic` suites.** Keep the code experiment-agnostic so adding them is a
  config change, but get factory farming working end to end first.
- **Free-response action items** scored by an LLM judge. More ecologically valid than
  forced choice and a legitimate follow-up, but it adds a judge-calibration axis, and
  a forced choice between two concrete recommendations is already a directly computable
  behavioral indicator of the kind `AGENTS.md` asks for.
- **`analysis/plots.py`.** Still a stub. The four primary visualizations come after
  transfer metrics exist.

---

## 9. Updating `AGENTS.md`

`AGENTS.md` documents the pipeline's conventions and is duplicated at
`CLAUDE.md`/`AGENTS.md` — **keep both copies in sync.** When this stage lands, update:

- the `data/` layout, to note `<suite>_items.jsonl` under `generated/` and
  `<suite>_eval.jsonl` under `validated/` (the "Repository structure" section currently
  says `validated/` "also holds belief/action eval suites" without naming files)
- the "Run reports" section, for the `evalgen` and `sensitivity` reports and their
  `gating` / `sensitivity` sections
- the "Validation" section's Sensitivity subsection, with the D3 decision that
  sensitivity is reported rather than used to filter items, and why
- the "SFT" section, with the rule that hyperparameters are tuned against efficacy and
  frozen before any belief or action score is looked at

Record the *reasons*, not just the shapes. The value of those files is that they explain
why things are the way they are, including what was tried and failed.
