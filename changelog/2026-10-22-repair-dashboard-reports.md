# Dashboard: all five pipeline-repair attempts

User requested the missing repair results in the app. Added five separately sourced,
validated reports, bringing the dashboard from13to18reports. No training/evaluation
calls, instrument changes or resumption of the paused scientific goal.

IDs: repair-normalization, repair-replay-weight, repair-lower-lr,
repair-expanded-replay, repair-base-reasoning. Existing13reports remain available.
Derived files: belief-transfer/data/results/ethical_pilot/
ethics_gpu_benchmark_dashboard_v1/reports/<id>.json (previously registered handoff path).

Each uses actual matching BASE cohorts, raw control replies, training/checkpoint
bindings, dataset manifest/config hashes and manual-review receipts. Source hashes
are checked, including the completed manual-review bindings. Counts and denominators
come from saved results; different banks are never pooled. Runtime seeds7/1729remain
separate from primary42 and are not training replications. All five show rejection,
with engineering passes separated from behavior/qualification failures. Original
qualification, fresh controls, irrelevant-note stability and generation completion
remain separate recorded checks.

Final report highlights reasoning32/32 and short17/24known retention, separately from
full-bank short22/32versusBASE24/32. Includes seen/held×training/evaluation wording
accuracy, explicit stop receipt and512/2400recorded(511valid,1invalid,1888missing).
No full100aggregate is manufactured. User cancellation has informational code
USER_STOP_ON_REVIEWED_NEGATIVE and a not_run, nonrequired collection check; the raw
partial count is shown without a model-quality passing threshold. Failed generation
and retention checks carry explicit error codes and bound sources.

Added to automatic data/build export. Shared model-check descriptions now cover learning
and transfer without assuming every report is the old registry task. No UI layout or
plotting convention changed. Reports use existing horizontal/vertical/matrix views,
model pills and grouped Model checks with passing ranges.

Validation:49dashboard Node tests and Python exporter tests passed; production build
and TypeScript passed. New3temp-directory integration tests cover five validated
reports, cohort denominators, all-item vs known accuracy, runtime repeats, partial
collection and rejection of incomplete review, changed evidence, cohort/coverage/bank
mismatch or missing operator stop. Final incremental tests/TypeScript/build passed
after label/collection refinements. Tests never write real experiment directories.

Live browser at127.0.0.1:5180verified18reports, all five repair entries, latest headline
17/24, counts32/32and17/24, grouped retention charts with95%passing range, and preserved
pass/fail/not_run statuses. Screenshot at the registered dashboard output:
screenshots/repair-retention.png. Source and reports join the next private snapshot.
