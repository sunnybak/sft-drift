# Stance document refinement and breadth pilot — 2026-10-19

User authorized implementing the proposed prompt changes, a matched repeat, then
scope expansion and repeat. Protocol and paths registered before execution. Version
v1 prompts remain unchanged. V2 fixes planning neutrality, scoped qualifier retention,
ordinary-implication review, control metacommentary, and revision priorities; includes
four diagnostic reviewer snippets. Same design, regenerated plans; not a paired
stochastic intervention estimate. Run IDs: ethics_sft_documents_pilot_v2 (48) then
ethics_sft_documents_expanded_v1 (84). Added subjects selected for scope challenges:
paid_kidney_donation, medical_data_without_consent, cash_bail_inability_pay. These
extend coverage from two to five ethical domains; no observed BASE outcomes used.
Two $0.50 ceilings bound the combined new work at $1. All candidates retained;
no training, GPU rental, accepted corpus or expanded background pool is implied.

Implementation verification and run findings will be appended after completion.

Pre-generation verification: 39 focused tests passed; full source suite 833 passed,
4 skipped. Prior private snapshot verifies all 225 files and frozen inputs unchanged.
Tests completed before live generation.

V2 failed before drafting: packaging explanatory-article planning returned four ideas
(two exact duplicate pairs) instead of two. Guard stopped; completed plans, raw responses,
$0.0034258 cost and zero revisions preserved. No automatic repair/reissue. Fresh v3 adds
minItems/maxItems to the idea tool and makes diagnostic snippets self-contained to
remove missing-context confounding. V3 ceiling $0.49 plus expanded $0.50 plus failed
v2 actual spend remains below $1. Original generation wording is unchanged.

V3 generation source 0b16ee6 completed. Forty-eight full revisions read: all owned
positions, all controls appearance-only, 19 agent flags (11 length, 8 semantic/argument).
45/48 drafts in range ->37/48 revisions; 3 improvements/11 regressions. Range340–559,
mean 436.4, 20,948 tokens. Cost$0.05575385. No exact duplicates. Same-model reviewer
flags one; all 19 agent-flagged rows pass its six checks (length checked separately).
Calibration4/4 is not held-out reviewer accuracy. Saved per-document review, paired
texts, disagreements, before/after examples, numeric summary and source hashes.

Expansion revision-policy amendment before execution: preserve a sound in-range draft
verbatim and supply measured word/token editing estimates. Same one-call limit. Other
prompts fixed, original 48 drafts reusable from cache; 36 new subject drafts. This is
a breadth test plus descriptive revision comparison, not independent replication.

Pre-expansion focused verification: 40 tests passed, including revision-policy routing
and distinct cache identities. No live generation ran during tests.

Expanded generation source 7bbfad4 completed84 drafts/revisions/assessments. Every final
read/annotated. 80/84 lengths in range vs 78 drafts;3 improved/1 regressed. Original
48 identical source drafts:47 final in range vs37 under v3. New subjects33/36.75/84
verbatim drafts. Range369–756, mean 471.5, total39,603 tokens. Four failures retained:
paid negative note1=395, paid positive note1=369, control positive explainer0=375
(all unchanged), bail positive editorial0 grew525->756.23 provisional agent flags
include four lengths;12 model flags,19 agent-flagged all-pass rows. Same-model review
remains unreliable for unattended acceptance; disputed ordinary implications preserved.
No exact duplicates or noncanonical full wording matches. All 12 control documents
avoid nonvisual exclusions/metadata. Two ethical documents refer to the brief.

All14 mixture previews have six synthetic and same six C4 records (792 background
tokens). Background identity, pinned provenance and exact original source drafts verified.
No training-ready export, training, GPU rental or new evaluated model. Expanded cost
$0.0790143; totalnew=$0.13819395 including failedv2, no uncertain charges.285 response
records include70 cache hits; this is not an independent repeat of planning/drafting.
Per-document notes, reviewer comparisons/disagreements, examples and derivation source
hashes saved. Focused post-run verification41 tests passed before full suite.

Final full-suite verification: 835 passed, 4 skipped in 128.73s, exit 0. Shared cache
SHA unchanged across both regression invocations; all 161 frozen file hashes intact.
All new JSONL files have Markdown views. First full invocation passed all 835 cases
but exited 1 because the implementing agent wrote tests.log and reviewer_disagreements.md
into real results during the suite. Its preservation guard correctly flagged those
operational writes; tests_guard_failed.log is retained. Clean rerun used a /tmp log,
with no result writes until pytest exited. This did not alter experimental candidates.
Verification.json records both outcomes. Git/private snapshot receipts establish final
preservation; no live process remains.

Final report source hashes and distinct within-form idea contents verified for both
completed new runs. All completed and partial outputs are registered for private save.
