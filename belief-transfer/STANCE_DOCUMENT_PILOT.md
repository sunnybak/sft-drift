# Separate standalone-document SDF pilot — 2026-10-19

Run: `ethical_stance_sft/ethics_sft_documents_pilot_v1`; stage `stance_sdf_pilot`.
This tests document quality, not SFT effects. No training, model inference, GPU rental,
checkpoint, corpus scaling, or automatic training-ready export occurs.

## Registered protocol

Adapt the type → idea → draft → one critique/revision process from *Believe It or Not*
(arXiv:2510.17941v1), without fictional evidence or alternate-world factual premises.
Use the approved canonical stance, exact negation, facts and exclusions as a scoped brief.
Ethical subjects: animal_medical_research, animal_cosmetic_testing,
single_use_packaging_necessary. Photography appearance preference is a separate fresh
training-control subject, not an off-topic evaluation belief. Pre-existing related groups
are retained; they do not imply that every possible relationship is known.

For each of four subjects, generate audience/purpose plans for position note, explanatory
article and editorial; two neutral focus/outline ideas per form; then separate supporting
and opposing drafts from the same idea. Require an explicit owned stance near the beginning
and a clear concluding position. No invented studies, magnitude changes, institutions,
names, authorities or new scoped circumstances. Acceptance is not obligation, and rejection
must not become a universal judgment outside the approved scope. Canonical wording is
allowed; generated evaluation paraphrases are not supplied to the generator.

48 revised candidates = 4 subjects × 3 forms × 2 ideas × 2 positions. Target 500 Qwen tokens;
requested range 400–600, measured with the cached Qwen/Qwen3-4B tokenizer at revision
1cfa9a7208912126459214e8b04321603b3df60c, without special tokens. Draft length is supplied
to the single revision call. No truncation, extra revision rounds or retries to pass a rubric.
All candidates and flags remain, even if lengths or semantic checks fail.

GPT-6 Luna (`gpt-6-luna`) performs planning, generation, revision and provisional assessment.
Responses API; reasoning none; provider-default sampling; concurrency two. Seeds schedule
content and C4 selection, not API sampling. Shared client/cache/ledger infrastructure is
reused with a new cache namespace including settings and the full tool schema. Historical
client defaults, cache keys and rates are unchanged. Raw returned model, response ID,
status, usage, structured output and failures are preserved. A bounded READY canary runs
first. The pilot ceiling is $1 including the canary; concurrent requests reserve conservative
byte-based input bounds plus bounded outputs. Automatic API retries are disabled for this
pipeline; unknown-cost network outcomes retain their maximum reservation and stop the stage.

## C4 and mixture previews

Stream allenai/c4, en, train, revision 1588ec454efa1a09f29cd18ddd04fe05fc8653a2;
shuffle buffer 1024, seed 42; take six unique nonempty full-text documents. Save URL,
timestamp, text hash, stream position and Qwen counts. No topical or stance filtering.
This uses the authors' public source, not their exact 400k cached sample, whose upstream
loader used a million-document shuffle buffer and seed 42. Dataset and transformer
packages remain locked. No full C4 download is requested.

Reuse the identical six background rows in all eight subject/position arms, each with
six synthetic documents. The 1:1 ratio is by document count, not training tokens. Preview
manifests reference preserved standalone text, with intended synthetic `<DOCTAG>\n` prefix
masking metadata and no C4 prefix. They do not implement training loss or chat wrapping.

## Assessment and completion

Record token ranges, duplicates and exact full evaluation-wording matches. Distinguish
allowed canonical overlap from other wording overlap; near-copy absence is not certified.
Use a separate model assessment for explicit stance, scope, no invented facts, form,
repetition and ending. Same-model judgments are provisional. The implementing agent reads
all 48 complete revisions, records per-document annotations and disagreements, compares
paired positions and form/idea diversity, and writes findings plus draft/revision examples.
No semantic acceptance claim rests on an automated all-pass result.

Every JSONL has a complete derived Markdown view. Artifacts live in
`data/{generated,results}/ethical_stance_sft/ethics_sft_documents_pilot_v1/`, registered
in configs/handoff.json before execution. Partial outcomes survive. Started candidate IDs
cannot be overwritten or automatically resumed; a new ID can reuse compatible cached calls.

Before live generation, run mocked/temp-directory tests for lineage, provenance, raw
failures, truncation, budget reservation and historical cache compatibility. Run tests
separately from generation. Frozen bank hashes must remain unchanged. End by updating root
STATE.md and a dated changelog, committing/pushing, then private handoff save and verify.

```bash
uv run --no-sync python run.py +run=ethics_sft_documents_pilot_v1
```

Sources:
- https://developers.openai.com/api/docs/models/gpt-6-luna
- https://developers.openai.com/api/docs/pricing (short-context $0.10 input, $0.01 cached,
  $0.50 output per million tokens; verified 2026-10-19)
- https://github.com/safety-research/believe-it-or-not/blob/b22a45a8c53254b9278e409f5ffef4349a039199/science_synth_facts/finetuning/synth_doc_dataset.py#L477-L492
- https://huggingface.co/datasets/allenai/c4

## Executed v1 outcome

Generation source a74d1ea completed 48 drafts, 48 single revisions and 48 assessments;
the implementing agent read every revision. Provisional current-agent review finds all
48 directional, with 17 needing edits. The separate model flags 22 and misses some
scope problems while over-flagging ordinary implications. No accepted corpus is exported.

Final tokens: 301–597 (mean 475.0); 43/48 in range, versus 39/48 drafts. Eight length
improvements and four regressions show that revision can conflict with the length target.
22,802 synthetic tokens total; six C4 documents total 792 tokens, yielding 20.1–23.5%
background token share despite the 1:1 document count. Generation/judging cost $0.045876
for 161 calls including the canary. No inference or training ran.

See saved review_findings.md, revision_examples.md, agent_review.jsonl/.md,
review_comparison.jsonl/.md and review_summary.json in the run results directory.
The full source suite passed 831 tests, 4 skipped, with the study cache unchanged across
the final suite. All provider smoke tests require --run-api and shared test caches are
isolated; three accidental initial legacy smoke calls are preserved separately with
about $0.0000258 additional cost. Frozen evidence was preserved. The final receipt,
not this document, establishes Git/private-snapshot preservation.

## Authorized refinement and breadth test — 2026-10-19

User authorized prompt refinement, a matched repeat, then scope expansion and another
repeat. Run `ethics_sft_documents_pilot_v2` first: same four subjects, forms, two ideas
per form, opposite positions, 400–600 Qwen tokens and GPT-6 Luna. Prompt version v2
fixes stance-neutral planning, lists protected scope conditions, distinguishes ordinary
implications from new empirical premises, gives revision priorities, and suppresses
control metacommentary. Version v1 remains available unchanged. Plans/ideas are newly
generated; this matches the design, not identical prose or an API sampling seed.

After reading every matched revision, run `ethics_sft_documents_expanded_v1`: retain
the original subjects and add paid_kidney_donation, medical_data_without_consent and
cash_bail_inability_pay, for six ethical subjects across five domains plus the same
photography control, 84 documents total. These additions were selected before outputs
for pressure/uncertainty, consent/data-use and financial-constraint scope tests, not
for observed BASE scores. Keep the v2 protocol fixed for the expansion unless the
matched review exposes a material defect; record any resulting change before execution.

Four short reviewer calibration snippets test valid implications and invalid qualifier
removal. Only their named checks are scored; these prompt-related fixtures are not
held-out accuracy evidence. Preserve their full raw results. Both runs retain all
candidates and receive complete current-agent review. Compare length transitions,
scope/argument defects, metadata, variation and reviewer disagreements descriptively;
there is no preregistered treatment-effect test or automatic corpus approval.

Each new run has a $0.50 ceiling including canary/calibration, bounding their combined
ceiling at $1. The same six pinned seed-42 C4 records remain fixed across runs and arms
to isolate synthetic-document changes; background breadth/dose is not expanded here.
No training or GPU rental is authorized by this work. New paths are registered before
execution, and each completed work block is committed, pushed and privately snapshotted.
