# Scope correction and final generation proposal — 2026-10-19

User authorized fixing the scope issue, testing across several beliefs, and reporting
final dataset-generation math/mix before bulk generation. No bulk generation, C4
acquisition, training or GPU rental is authorized by this block.

Implemented versioned prompt v4 with phase-specific instructions, fixed-predicate and
channel-specific absence guards, no internal ID inference, targeted one-pass revision
and reviewer checks over the entire document. Review instructions precede bounded JSON
data, with no appended instructions. V3 prompt files are unchanged.

Added optional ethical target selection for bounded fresh pilots. Registered new IDs
`ethics_sft_scope_check_v1` (30 candidates, $0.50 ceiling) and
`ethics_sft_pooled_corpus_v3` (27,000 proposed production candidates, unstarted) in main
and separate private corpus storage. C4 acquisition supports a measured token reserve
beyond the shared background, with bounded shard/resume tests. Full proposal is in
belief-transfer/POOLED_DATASET_PLAN.md; actual per-phase forecast follows the live check.

Tests: full suite 866 passed, 4 skipped (114.90 s). Earlier focused checks 105 passed;
new tests cover both prompt versions, filtered-target validity, neutral planning,
JSON data boundaries, role-scoped control rules, production counts and reserve extension.
All tests use mocks/tmp and completed before live generation. Source commit precedes
fresh run preparation/live calls. Pilot outcome and artifact verification will be
recorded below after execution.

V4 live check completed (source 3275d32): 30 documents / 111 successful calls,
$0.04209835, no uncertain outcomes. All six hiring revisions preserve the specified
channels, but final length fell from 27/30 valid drafts to 24/30 revisions. Critiques
explicitly substituted guessed counts for supplied tokenizer measurements. Preserved
all v1 artifacts. Added v5 revision-only instructions giving authoritative numeric
status and removing the confusing word-ratio hint. A fresh matched repeat,
ethics_sft_scope_check_v2, imports only exact request-cache entries from v1; no old
request rows or charges are copied. Draft/plan/review builders remain identical,
revision keys change. New seeding and all three prompt routes have regression tests.
Full suite after this change: 878 passed, 4 skipped (107.51 s). No API job overlapped
with either suite. The production proposal now selects v5, still unstarted.
