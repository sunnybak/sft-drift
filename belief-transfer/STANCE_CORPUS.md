# Pooled ethical-stance document bank

`stance_corpus` prepares and generates a new document bank. Historical pilot stages,
prompts, caches, measurements and their run IDs remain intact. Training is outside
this stage. The default operation is **prepare**, which makes no model or C4 calls.

## Current source-bank design

- 90 approved ethical briefs × 100 documents × 2 positions = **18,000 documents**.
- Nine fresh aesthetic control briefs × 500 documents × 2 positions = **9,000 documents**.
  These are independent of the ten frozen off-topic evaluation beliefs. This control
  count is a candidate bank; final training dose must be matched using measured tokens.
- 400–600 Qwen3-4B tokens per document, targeting 500. Three forms: position note,
  explanatory article and editorial. A subject gets 34/33/33 slots per position;
  which form receives the extra slot rotates by subject identity.
- Seed 42 fixes scheduling, category-balanced mixed assignments and C4 sampling.
  API prose is not claimed deterministic. Model: `gpt-6-luna`, Responses, reasoning
  disabled, default sampling, two active requests, no automatic network retries.
- The generated bank supports all-positive, all-negative, Mixed A and complementary
  Mixed B. Each mixed arm assigns one position to each belief, with five positive and
  five negative beliefs in each category. Each ethical arm selects 9,000 source documents.
- Fresh off-topic+C4 and C4-only controls are declared alongside untouched CUDA BASE.
  All 100 frozen beliefs must be evaluated later. No training schedule or dose is
  selected here. The background target is 18,000 unique full C4 documents, not a claim
  that this count supplies a matched training dose.

## Prompts and review

The structure remains form → specific idea → separate opposing drafts → one critique
and revision → separate provisional assessment. Ideas explicitly name a reason for
each position; the assigned side determines which reason becomes the objection.
At most five new ideas are planned together. Prior focuses for that subject/form are
provided to discourage repetition. Both positions use the identical plan and premises.

Prompt v3 retains the direct stance and fixed-scope policy, adds explicit guards against
the observed qualifier/uncertainty errors and visible task metadata, and preserves
an already valid in-range draft verbatim. The reviewer supplies evidence for each
source condition plus unsupported-premise quotations. Mechanical checks record token
length, task metadata, normalized duplicates and canonical versus other frozen wording
matches. Evaluation paraphrases enter diagnostics only, never generation prompts.

The first live batch has been generated and all ten revisions read. It meets length
and explicit-stance checks but still broadens unavailable explanation/human review into
unavailable every other avenue. See the [first-batch review](data/results/ethical_stance_sft/ethics_sft_pooled_corpus_v2/first_batch_review.md).
Do not scale these prompts unchanged; the next prompt test needs a fresh ID. Same-model
review remains advisory. Flagged rows stay in the bank;
there is no rejection sampling, truncation, automatic training-ready label or claim
that document diversity follows from having distinct titles.

## Run and inspect

From `belief-transfer/`:

```sh
# Once only: materialize briefs, schedule, immutable contract and arm assignments.
uv run --no-sync python run.py +run=ethics_sft_pooled_corpus_v2

# Technical resume command only: the first live batch is complete.
# Current quality findings require a fresh-ID prompt test before using more v2 batches.
uv run --no-sync python run.py +run=ethics_sft_pooled_corpus_v2 stance_corpus.operation=generate stance_corpus.resume=true stance_corpus.max_batches=1

# Write a new numbered inspection report and a small paired sample view.
uv run --no-sync python scripts/inspect_stance_corpus.py

# Independent bounded C4 acquisition: one shard of up to 100 unique documents.
uv run --no-sync python run.py +run=ethics_sft_pooled_corpus_v2 stance_corpus.operation=background stance_corpus.resume=true stance_corpus.max_batches=1
```

Read the first live pairs and compare their scope against the briefs before scheduling
larger batches. Prompt/content-setting changes require a new run ID; they cannot be
silently applied to the prepared bank. Operational `operation`, `resume`, `max_batches`
may change; the lifetime budget ceiling stays in the content contract. Current ceiling
is $50 including the initial canary, not an estimate of actual cost or permission for
an unattended full run. Each invocation remains explicitly bounded.

Resume is opt-in and single-writer. Completed shards are skipped and completed request
outcomes reused. The SQLite journal commits an exact request intent before dispatch,
then raw response, usage, errors and cost. An interruption after caching can recover
the original response and charge. An unresolved request with no durable outcome blocks
automatic retry because it may have been billed. A malformed/truncated result remains
an explicit failure; resume does not regenerate it until it passes. No force overwrite.

## Local layout and preservation

```text
data/generated/ethical_stance_sft/ethics_sft_pooled_corpus_v2/
  contract.json, briefs.jsonl/.md, schedule.jsonl/.md, conditions.json
  requests.sqlite                   # durable corpus-specific cache and request ledger
  shards/<batch-id>/                 # atomic completed shard
    documents.jsonl/.md              # drafts, critiques, revisions, reviews, token counts
    ideas.jsonl/.md, events.jsonl/.md, manifest.json
  background/<shard-id>/
    documents.jsonl/.md, manifest.json
data/results/ethical_stance_sft/ethics_sft_pooled_corpus_v2/
  config.<invocation>.json, invocation.<invocation>.json, corpus_status.json
  audit_<number>.json/.md
```

Each completed shard is written once; Markdown is derived per shard, avoiding full-corpus
rewrites after every document. Synthetic text is standalone and carries intended
`<DOCTAG>\n`/prefix-loss-masking metadata; C4 is unprefixed. This is metadata for future
training integration, not an implemented loss function. C4 retains full text, hashes,
source URL/timestamp, pinned dataset revision, shuffle seed/buffer/index and Qwen counts.
No stance/agreement filter is applied. C4 is streamed, not fully downloaded.

`configs/handoff.json` delegates the new corpus root to private HF dataset
`sunnybak/sft-drift-ethical-corpus`. Existing study artifacts remain in their original
private repository. Normal `scripts/handoff.py save` snapshots both: it locks the corpus,
uploads content-addressed gzip/tar bundles in commits of at most 40 additions, verifies
remote hashes, then pins the corpus manifest/revision inside the study snapshot. Restore
follows that pinned pointer. A failed corpus save cannot produce a successful study
receipt. Old completed shards cannot change or disappear from a subsequent save.

Bundles target 32 MiB of source bytes; one indivisible file (notably SQLite) can exceed
that size. No document-per-file HF upload, automatic deletion, history rewrite, public
fallback or account-quota bypass. A separate repository isolates management; HF storage
quota still applies across the account. Local portable exports provide another copy:

```sh
uv run --no-sync python scripts/corpus_storage.py export /absolute/path/outside-data/corpus-backup
uv run --no-sync python scripts/corpus_storage.py restore /absolute/path/outside-data/corpus-backup
```

Exports refuse existing destinations; restores preflight conflicts and validate regular
members, paths and hashes. Export only at a safe boundary. Uncommitted staging directories
are rebuildable and excluded; their completed API outcomes remain in the SQLite journal.
The portable corpus export includes its contract and plans; source code and the frozen
instrument still come from Git/the main study handoff. A live job does not survive a
destroyed box. Save between bounded invocations.
