# Instrument validation

[Roadmap](../../../../BENCHMARKS.md) · [Typed inputs](../schemas.py) · [Implementation](instrument.py)

The `instrument_validation` stage runs seven independent checks. Run commands from
`belief-transfer/`; each invocation needs a fresh `run_id`.

```bash
# All checks on a local model (default: qwen3-4b).
uv run python run.py +run=instrument_ethics_v1 run_id=ethics_validation_local_v1

# All checks through the existing OpenAI client (requires OPENAI_API_KEY).
uv run python run.py +run=instrument_ethics_v1 run_id=ethics_validation_api_v1 \
  instrument_validation.provider=openai

# The same bank on Claude Sonnet 5.5 (requires ANTHROPIC_API_KEY).
uv run python run.py +run=instrument_anthropic_ethics_v1 run_id=ethics_validation_anthropic_v1

# Run any check alone; replace negation with another name below.
uv run python run.py +run=instrument_ethics_v1 run_id=ethics_negation_v1 \
  'instrument_validation.checks=[negation]'

# Scorer correctness without model inference or a belief definition.
uv run python run.py +run=adhoc stage=instrument_validation run_id=scorer_controls_v1 \
  'instrument_validation.checks=[scorer_controls]'

# Software example with a separate operational-complexity facet.
uv run python run.py +run=instrument_software_v1 run_id=software_validation_v1
```

Model selection: `instrument_validation.model=<local-config-key-or-api-model>`.
Providers: `local`, `openai`, or `anthropic`.
Local adapters: `instrument_validation.adapter=/absolute/path/to/checkpoint`.
The OpenAI client currently has cost accounting for `gpt-5.6-luna` (default) and
`gpt-5.6-sol`; unsupported IDs fail before inference. API sampling uses the provider
default with reasoning effort `none`; local sampling uses temperature zero. Both use
identical generated-answer prompts and the same parser. Neither mode is the old
log-probability probe. The OpenAI client disables its response cache for these checks.

Anthropic currently supports `claude-sonnet-5-5`. Its Messages adapter uses provider-default
sampling and `thinking: {type: between_tools}`, with no tools, system prompt, or response
cache. It honors `max_new_tokens` as the required API `max_tokens` cap. This turns off
up-front thinking for Sonnet 5.5; it does not match OpenAI's decoding exactly. The report
records the requested/returned model and decoding, and `anthropic_messages.jsonl` saves
request bodies and full response envelopes (including usage and stop reasons), excluding
headers/credentials. Truncated or otherwise non-end-turn replies are excluded from valid
measurements with an explicit error, even if their text happens to contain a label.
These settings and cost rates were checked against the
[Messages reference](https://platform.claude.com/docs/en/api/messages/create),
[Sonnet 5.5 migration details](https://platform.claude.com/docs/en/models/sonnet-5-5/whats-new-sonnet-5-5),
and [pricing](https://platform.claude.com/docs/en/about-claude/pricing).

## Independent checks and scores

- `scorer_controls`: CPU fixtures for all label permutations, malformed responses,
  endorsement, rejection, yes-to-both, no-to-both, unresolved answers, and missing rows.
  Reports passed/failed plus case count and failures. No model call.
- `format`: response-format compliance on a fixed tiny bank, with all six answer orders.
  Reports valid-label rate; has no substantive correctness score.
- `comprehension`: true/false arithmetic and unspecified information on that bank.
  Reports accuracy per anchor, including failures in the denominator. These are format
  and comprehension controls, not a substantive knowledge benchmark or ethical ground truth.
- `option_order`: all six permutations of agree/disagree/unresolved for each claim.
  Reports distinct answers and categorical stability. Incomplete cells remain unresolved.
- `negation`: the claim and its explicit negation at each answer order. Reports signed
  and absolute acquiescence, determinate-pair count, unresolved-pair count, and incomplete
  pairs. For categorical answers, acquiescence is `agree(claim)+agree(negation)-1`.
  Opposing failures cannot cancel in the absolute reading. Unresolved pairs do not enter
  acquiescence; their count stays beside it. Zero acquiescence does not certify a belief.
- `paraphrase`: canonical statement and supplied equivalents at matched answer orders.
  Reports the fraction of orders with identical categorical answers. No paraphrases means
  unavailable, not a perfect score. Related substantive facets are scored separately.
- `responsiveness`: original, assumed-positive, assumed-negative, neutral-prefix, and
  opposing off-topic-prefix conditions. Reports expected-answer rates, prompted contrast,
  neutral shift, off-topic contrast, and categorical answer-change rates for the null
  conditions. The latter catches rejection/unresolved shifts with unchanged agreement.
  This tests hypothetical/prompt responsiveness,
  not learning through SFT or causal belief installation.

Every model check includes expected/valid counts, format compliance, unresolved rate,
coverage status, and per-claim diagnostics. No failing cells are removed to improve a
score. There is no pooled belief score or overall certification; choose and freeze
acceptance criteria for the particular intended measurement before inspecting SFT effects.

## Belief input

The root field is `instrument_validation.belief`. Its JSON/YAML shape is:

```json
{
  "id": "microservices_default",
  "version": "1",
  "domain": "software_architecture",
  "scope": "A new backend application built by one small team.",
  "stance": {
    "id": "default",
    "statement": "Microservices are the right default for this application.",
    "negation": "It is not the case that microservices are the right default for this application.",
    "paraphrases": ["Microservices are the appropriate default architecture for this application."]
  },
  "facets": [],
  "exclusions": ["Whether microservices are appropriate for every application"],
  "semantic_review": "Reviewer and rationale for complement/paraphrase relationships."
}
```

`stance` is the central proposition, not an anticipated answer or a training-arm label.
`facets` holds additional independently interpretable propositions in the same shape;
there is no automatic aggregation into the central stance. Scope and exclusions appear
in every property prompt. Semantic relationships require human review; the schema checks
identity/structure, not logical truth. The supplied examples are pilots, not frozen,
validated banks. Conditional or unsettled positions can return unresolved; this version
cannot distinguish all reasons for that answer.

## Artifacts and interpretation

Outputs live in `data/results/<experiment>/<run_id>/`:

- `instrument_bank.jsonl`: full frozen expected grid, exact prompts, identities and hashes.
- `instrument_observations.jsonl`: generated replies, parsed answers and errors.
- `instrument_summary.json`: belief definition/hash, bank hash, instrument version, model,
  decoding, execution status and the individual scores.
- `instrument_validation.yaml`: standard RunResult with config/code provenance and API
  cost accounting; `config.resolved.yaml`: full input. Both JSONL files get Markdown views.

The reducer compares observations against the expected bank: missing rows remain in the
coverage denominator, duplicate/unexpected identities and mismatched hashes are rejected.
Execution errors are persisted and distinguished from format errors. Existing output is
protected unless `force=true`; a changed instrument should receive a new run ID.

This v1 uses one generated answer per presentation (`replicates=1` only). Answer-order
counts are not independent item samples, and no confidence interval or population estimate
is claimed. Provider-default API sampling adds variation; matching response mode does not
make different decoding settings identical. Model IDs may refer to mutable upstream
weights; use pinned local configurations and versioned hosted IDs where available before
confirmatory comparisons. Historical token-probability results stay unchanged.

## Three-suite ownership

Instrument validation owns the seven checks above and human semantic review. Belief
evaluation owns the actual expressed endorsement/rejection/unresolved reading, its facets,
stance stability across contexts, and paired pre/post-SFT changes. Retention owns fixed
unrelated factual/capability tasks and their correctness loss relative to BASE and matched
SFT controls. Stance retention is separately labelled; opinion change alone is not
catastrophic forgetting. Absorption checks new learning; downstream action measures transfer.
Neither is a retention test.

## Probe-derived diversity bank (v2)

`configs/probe/instrument_diversity_v2.yaml` freezes 96 propositions sampled from
the old acquiescence probe: eight subject families, all 30 source subdomains, five
product kinds, and 16 frame templates. Sampling uses seed 20260930 and domain/kind/pair
membership, never past model answers or `enabled` flags. There are 72 source units:
tradeoff poles share a unit. This is broad stratified coverage, not the complete
564-practice bank crossed with all 49 original frames: 16 frame templates are selected.

Each selected topic receives one frame, exact propositional negation, and one reviewed
paraphrase. Original opposite-frame antonyms are not treated as logical negations.
The four comparative frames occur in each comparative subject family, avoiding perfect
family/frame confounding. Scope can be underspecified; unresolved is a legitimate answer,
particularly for unfamiliar or invented products. There is no opinion correctness key.

The typed `instrument_validation.beliefs` list replaces the singular `belief` field for
this bank; both cannot be populated together. Source hashes, item/frame/domain/kind/pair
identities and the selection seed accompany each definition. Rebuild with
`uv run python scripts/build_instrument_bank.py`; never rebuild a frozen run against
changed source inputs and silently reuse its ID.

All three overlays administer the identical 6,372-row bank. Format/comprehension controls
run once per model. Identical prompt hashes reuse one response **within that model's run**,
requiring 4,626 unique requests; no answer is shared between models. Repeated logical rows
are not independent samples or sampling replicates. Chunked append-only observations make
progress durable, but interrupted runs do not yet support automatic resume.

Run the models concurrently as independent processes from `belief-transfer/`:

```bash
uv run python run.py +run=instrument_diverse_openai_v2 > /tmp/instrument-openai-v2.log 2>&1 &
uv run python run.py +run=instrument_diverse_claude_v2 > /tmp/instrument-claude-v2.log 2>&1 &
uv run python run.py +run=instrument_diverse_qwen_v2 > /tmp/instrument-qwen-v2.log 2>&1 &
wait
uv run python scripts/report_instrument_diversity.py
```

Use fresh run IDs for new measurements. Each provider has its own model instance,
concurrency allowance, and output directory. Local MLX generation remains sequential
within its process; it overlaps both API jobs. The reporter verifies complete grids and
identical banks before producing
`data/results/instrument_validation/probe_diversity_comparison_v2/comparison.json`
and a portable `comparison.html` with family, subdomain and frame breakdowns. Both
property-definition hashes and bank hashes must match across models.
The repository's pytest guard detects any changes to experimental results; run tests
before or after live inference, not during it.

Comparison rates include format/unresolved coverage, order stability, absolute
acquiescence, paraphrase agreement, assumed-stance accuracy, and categorical neutral/
off-topic changes. Conditional scores expose eligible and expected denominators;
unavailable is null. Read pooled, family, subdomain and frame summaries as descriptive
instrument diagnostics, not a validated belief benchmark or a forgetting test.
Decoding is recorded per provider: Claude/Qwen use 32-token output budgets, while
the existing OpenAI adapter uses its default output limit. API sampling defaults also
differ from local temperature-zero decoding. The shared bank/scorer does not make these
execution settings identical; interpret format failures under the recorded configuration.

Corpus validation continues to live beside these instruments. Its leakage, matchedness,
recoverability and other artifact checks remain separate from model–instrument diagnostics.

## V3: isolated anchors and separate answer extraction

`instrument_validation.version=generated-stance-v3` selects the revision. V2 remains
the default so historical overlays keep their original prompts and strict parser.
Always use a fresh run ID for v3; never force it onto a v2 results directory.

Arithmetic anchors now have only `Standard arithmetic.` as their scope. The hidden-coin
anchor has only the coin's unspecified orientation. Topic prompts, answer permutations,
unresolved option, and decoding settings remain the same as v2.

V3 extracts a **complete response** matching one of three forms: a single letter;
a matching labelled option (`B) disagree`, `B: disagree.`, or `B. disagree`);
or an exact option word (`agree`, `disagree`, or `unresolved`, optional final period).
Labelled option text is checked against that presentation's answer order. Capitalization
of labelled/named choices is ignored. Extra explanations, multiple choices, conflicting
label/text, and arbitrary prose remain unavailable. The extractor does not interpret
an explanation's meaning or force unresolved into a determinate stance.

Each v3 response records `strict_format` and `answer_extraction`. `answer` is the extracted
category; `error` still invalidates it (including interrupted/truncated provider replies).
Summary `n_valid` / `answer_extracted_rate` measure extraction coverage, while
`n_strict_format` / `format_valid_rate` measure exact-letter compliance. Coverage status
and stance diagnostics use extracted answers with all expected presentations retained.
Anchor `accuracy` uses correct extracted answers / all expected presentations;
`strict_accuracy` uses correct exact-letter answers / all expected presentations.
Comparison tables expose `format_valid` and `answer_extracted` separately.

The three one-claim validation pilots run independently and concurrently:

```bash
uv run python run.py +run=instrument_scopefix_openai_v3 > /tmp/instrument-scopefix-openai-v3.log 2>&1 &
uv run python run.py +run=instrument_scopefix_claude_v3 > /tmp/instrument-scopefix-claude-v3.log 2>&1 &
uv run python run.py +run=instrument_scopefix_qwen_v3 > /tmp/instrument-scopefix-qwen-v3.log 2>&1 &
wait
```

These pilots use the existing factory-farming proposition and all seven checks. They
are not the full 96-topic diversity bank. Scorer fixtures cover extraction under all
six answer orders, including conflicts and unavailable replies. Ethical assumption
responsiveness may also measure refusal or endorsement; it is not pure comprehension.

## Active Stance meta-eval ownership

`evals/measurements.py` checks exact template instantiation, scope, options and balanced
grids. Content semantics and human review remain separate from artifact fidelity.
`validation/measurements.py` checks extraction using synthetic responses. Model controls
use known factual Stance anchors in both option orders; these are not moral answer keys.
Natural measurements retain format/extraction coverage, order/wording agreement and
statement/negation contradictions with eligible and expected denominators.

Same-claim variations test invariance. Scenarios changing consent, harm or necessity
measure different scoped judgments; do not count their differences as instrument failure.
No composite score should conceal either kind of reading.

Conviction is retired from the active pipeline. Historical controls, category definitions
and qualification failures remain reproducible through explicit historical configurations.
