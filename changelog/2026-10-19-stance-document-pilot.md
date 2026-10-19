# 2026-10-19 — separate paper-inspired stance document pilot

Implemented and executed `stage=stance_sdf_pilot`, run
`ethical_stance_sft/ethics_sft_documents_pilot_v1`, generation source a74d1ea.
Type/audience/purpose → two neutral ideas per form → separate position drafts → one
critique/revision → separate assessment. Three ethical subjects and one fresh photography
control; three forms; both positions; 48 documents. Existing 32-answer pilot unchanged.
No GPU, model inference, SFT, checkpoint or training-ready export.

GPT-6 Luna via Responses, no reasoning, default sampling, concurrency two. New bounded
client inherits shared infrastructure, has complete tool/settings cache identities,
reserves a conservative cost bound for concurrent calls, disables API retries, retains
raw malformed/truncated outputs, and keeps uncertain network costs reserved. Historical
client defaults/keys/rates unchanged; GPT-6 pricing added. Prompt/schema/run artifacts,
lineage and JSONL Markdown views are saved under the declared generated/results paths.
Registered in handoff.json before execution; no automatic started-ID resume/overwrite.

Pinned Qwen tokenizer 1cfa9a7208912126459214e8b04321603b3df60c; no weights loaded.
Pinned allenai/c4/en/train revision 1588ec454efa1a09f29cd18ddd04fe05fc8653a2,
seed 42, buffer 1024. Saved six unique full text records with source URL/timestamp/hash,
792 Qwen tokens. Shared identical IDs across eight previews, each six synthetic/six C4.
C4 token fraction 20.1–23.5%; count matching is not token-dose matching. This is a fresh
sample from the same upstream source, not the paper authors exact cached rows.

Completed 48 drafts, 48 one-round revisions, 48 model assessments. All full revisions
read by the implementing agent and annotated. Final range 301–597, mean 475.0417;
22,802 synthetic tokens; 43/48 in requested 400–600 range. Drafts 39/48 in range;
eight improved and four regressed after revision. No exact duplicate texts. One full
noncanonical evaluation wording overlaps a packaging editorial; generator inputs did
not include those wordings, so this is not evidence of copied data or absence of near copies.

Current-agent review finds all 48 directional but flags 17 for edits (five length failures,
three subtle scope additions, seven control metacommentary cases, one counterargument
error, one heavily repetitive note). Model flags 22; seven agent-flagged cases get all
model checks passed, including two separately measured length failures. Model often
confuses ordinary implications with new premises (e.g. waste from disposable packaging),
yet misses stronger scope additions. Both reviews remain provisional; no human-ground-truth
accuracy or accepted corpus count claimed. Planning also wrongly defines explanatory
articles as non-advocacy despite final assigned-stance requirements. Fix in a fresh pilot
rather than silently regenerating or rewriting this run.

Canary plus 160 workflow calls: $0.04587575, zero uncertain charges, under the $1 ceiling.
The process exited 0; no checkpoint exists. Complete review.md, before/after examples,
agent/model comparisons, evidence hashes, package versions, mixture token tables and
findings report are saved. Latest next command from belief-transfer/:
`cat data/results/ethical_stance_sft/ethics_sft_documents_pilot_v1/review_findings.md`.
Review examples with the user before changing design or scaling. CUDA qualification,
training-control contrasts, dose/schedule and all-100-belief measurements remain future work.

Verification and incident:
- Initial focused run 44 passed, but two pre-existing credential-triggered live smoke
  tests made three calls, appending 666 bytes to study cache. The append is preserved in
  legacy_test_cache_appendix.jsonl/.md; prior receipt prefix SHA-256 was verified and
  restored exactly before the actual pilot. Cost about $0.0000258. No data was discarded.
- Added explicit --run-api/needs_api to all three live smoke tests and per-test shared
  cache isolation. Expanded preflight: 80 passed, 2 skipped; another focused run 72 passed.
- Final complete source suite: 831 passed, 4 skipped, 102.91 s, with exact study-cache
  SHA unchanged across the suite. Tests ran separately from generation/artifact writes.
- Frozen wordings hash stayed a12044e50aa6c7cf641b47e74c44ed752e970fb05be52e92b58adcf08ac9e3ef.
- Redacted six transport URL queries in the completed log; later source suppresses HTTP
  INFO logs that can contain signed URLs. Canonical prompts, outputs and usage untouched.

Final Git and private snapshot preservation are established by the latest handoff receipt.
No statement here substitutes for a verified remote save.
