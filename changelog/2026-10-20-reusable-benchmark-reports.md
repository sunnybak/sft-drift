# Reusable benchmark reports and Dashboard

Implemented generic typed BenchmarkReport wrapper, direct-prop BenchmarkResults renderer,
and JSON Schema v1.0. A report
is self-contained: models (provider/model/revision/inference, variant, fine-tune run,
dataset identity/hash/context, pipeline identity/plan hash/context, adapter source/hash),
benchmarks (semantic definition, conditions, examples, range/unit/direction/threshold),
scores (optional exact counts, missing values, source hash) and recorded tests
(pass/fail/not_run/error, required, expected/observed, source). Unknown provenance
explicitnull; pipelinehash identifies exact planfile, not all source code.

Renderer has horizontal and vertical small-multiple bars, matrix, checks/filter,
benchmark semantic/example view and model context. Fraction vs numeric/optionalunit
labels/lower-is-better supported without blending scales. Stable model colors, exact
counts and missing markers; recorded check outcomes remain separate from chart scores.
Scope summary says Not assessed without required tests; not_run/errors never pass.
Compact cards in sidebar Dashboard; full report exploration/model filters/JSONdownload.
Shared sidebar retains previous Compare/Bybenchmark/Rundirectory via LegacyExplorer.

TypeScript server loader reads regularJSON only from configured directories. Reports
added to benchmark-dashboard/reports/ appear on Refresh without component edits or
server restart. Invalid files surface errors without hiding other valid reports;
all copies of duplicate report IDs excluded. No user-requested filesystem paths,
script evaluation or browser filesystem access. CLI validates against strict AJV
schema plus references/IDs/ranges/count consistency/date/provenance checks. Versioned
fictional example template outside loaded folders; no fabricated scores auto-loaded.
Static Vite build emits validated reports.json. Additional Node-only AJV dependency;
ML pins/Python dependency layers untouched. npm audit0vulnerabilities.

Derived three real reports from existing source summaries/judgments: registry-learning
11scores4checks; instruction-retention15scores4checks; training-contract39scores83checks.
Private generated JSON/preview under existing registered dashboard artifact root.
Counts and failures unchanged. Prompt examples labeled illustrative (not exact full
scored prompts). Authored JSON reportfiles are versionable source inputs.

Port conflict: unrelated node server also on5173; observed browser briefly receiving
otherapp. Restarted only our dev server and moved this app to127.0.0.1:5174,exec5037.
Unrelated service untouched. README/BENCHMARKS/STATE updated.

Validation:15app tests (5Pythonfixtureexport+10Nodecontract/loader), all mocked/temp,
plus37repo import/handoff checks. Production TS/Vite build passes; browser verified
Dashboard3reports/65scores/91checks, horizontal+verticalcharts, matrix, semantic
examples, recordedchecks, and actual dataset/plan/adapterhashes in context view.
Preview benchmark-reports-preview.png saved under registered derived artifact root.
No model loads, new GPU jobs, training, score/scorer/decoder/instrument changes.
Source/progress and derived outputs require push/private save after this block.
