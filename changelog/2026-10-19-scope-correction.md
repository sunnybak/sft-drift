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

Matched v5 check completed at source 60ced0a. All thirty draft SHA256s and shared ideas
match v4. Final range 404–591, mean 494.8333, total 14,845 Qwen tokens: 30/30 in range,
27 valid drafts verbatim, three original length fixes, no regressions. Twelve finals
differ from v4. All thirty final texts were read (hash-identical reused text retained
its prior full read); all six hiring documents preserve the specific absent channels.
Two medical-data articles have borderline participation wording; two control notes
retain unnecessary practical-context clauses. One Luna flag is provisionally disputed
(ordinary implication/normative evaluation) and has internally inconsistent scope
booleans. All judgments/flags preserved, not relabeled as accepted training data.

V5 actual 42 fresh calls + 69 exact replays, $0.019428725; total check spend $0.061527075.
No pending/uncertain requests. Full generation proposal is prepared as v3, with zero
bulk documents/C4/model spend. Source bank: 27,000 synthetic docs, nominal 13.5M Qwen
tokens. Role-weighted forecast: 83,908 calls, 125.1M provider input / 41.8M output,
$35.74 empirical profile or $38.99 cold-write/history proxy; $50 cap; roughly 3–4 days
at concurrency two. Forecast profiles underlying provider usage of cached responses,
not zero local replay costs. Mixture is 1:1 document count with measured token/step
matching deferred, C4-only reserve measured beyond common background. Actual C4 count
can extend beyond 18,000 to supply 5.4M replacement tokens.

Verification independently recounts 60 final texts, checks shared drafts/plans, all shard
hashes and 161 frozen hashes, and confirms historical global cache bytes unchanged.
New report/agent JSONL+Markdown, comparison, generation_math.json, execution/test logs
and verification.json are in scope_check_v2 results; generation math is also copied to
production-v3 results. No API job overlapped tests. No process/checkpoint remains active.
Final notes/source are pushed, then main and separate private corpus handoff snapshots
are saved/verified; final revisions live in the ignored receipt. Bulk generation awaits
the user's review/go-ahead; no training or rental is authorized.

The inspector default now points to production v3; its empty-bank audit was smoke-checked
(zero documents/C4). Reference commands explicitly select the current run and state the
production preparation already happened. This reversible CLI-default/doc update did not
change any generation prompt or the nine-file production contract, which was rechecked
byte-for-byte against the prepared contract. No extra model call was made.
