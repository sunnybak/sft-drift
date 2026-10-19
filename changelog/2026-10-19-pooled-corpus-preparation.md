# Pooled corpus infrastructure — 2026-10-19

User authorized optimizing code, prompts and storage before actual scaled generation.
No live generation, C4 acquisition, training or GPU rental is included in this work.

- New typed `stance_corpus` stage and `ethics_sft_pooled_corpus_v1` overlay, default
  prepare-only. 90 ethical targets × 100 documents × two positions = 18,000 documents;
  nine fresh aesthetic controls × 500 × two positions = 9,000 candidate control docs.
  Control dose remains a later measured-token decision. Ten off-topic evaluation
  beliefs remain untrained, with all 100 evaluated on future models/checkpoints.
- Shared paired plans, three forms, balanced slots, seed-42 category-balanced mixed
  assignment and its exact complement, bounded batches, lifetime $50 ceiling, concurrency
  two, one canary before live generation, no automatic network retries.
- Prompt v3: explicit pro/con reasons and direction-correct objection; previous focuses
  discourage repeated ideas; fixed-premise/qualifier guards; valid-draft length preservation;
  condition-by-condition reviewer evidence. Offline checks only; prose quality needs live
  inspection. No passing filter or automatic training-ready label.
- Corpus-specific SQLite cache/request journal retains exact intent, response, usage,
  raw failures and lifetime charges. Cache recovery avoids double charging. Unknown
  interrupted outcomes block retry. Batch shards commit atomically; JSONL Markdown views
  are written once. Normalized duplicates and other mechanical flags stay explicit.
- Pinned streaming C4 acquisition is independently bounded/resumable and keeps full
  text/provenance. 18,000-record source-pool target is not a token-dose claim. Mixture
  manifests name C4-only and fresh off-topic+C4 controls, with final assembly/training
  deliberately outside this stage.
- Separate private `sunnybak/sft-drift-ethical-corpus` storage uses immutable gzip/tar
  bundles, chunked uploads, pinned manifests, conflict-safe restore and verified local
  portable export. Main handoff delegates the new corpus root and embeds its verified
  revision/manifest. Account-wide HF quota still applies. No old artifacts moved/purged.
  The study handoff uploads only new/changed files, staging new files in bounded commits
  and publishing mutable files atomically with the final manifest.
- Historical pilot prompts/cache identities/default API settings are unchanged; optional
  conservative cache-write reservation is enabled only by the new corpus stage. Historical
  config fingerprints omit the unset new stage field.

Verification: full suite 854 passed, 4 skipped (152.83 s); final focused regressions
cover later budget/journal/transport refinements. All tests use temporary artifacts/mocks;
no results-tree writes or live generation concurrent with tests. Preparation/snapshot
receipts are recorded in STATE.md and the ignored handoff receipt after execution.
