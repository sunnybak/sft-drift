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
