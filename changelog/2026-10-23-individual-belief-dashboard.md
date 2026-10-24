# Individual-belief dashboard — 2026-10-23

Requested a view showing beliefs separately instead of combining them. Added
IndividualBeliefs to the original pilot's three seed reports and three-seed report.
All100 rows include matched BASE and four arms, per-belief support percentages, signed
percentage-point changes, fixed0–100 support tracks, clickable model pills, expandable
claim/scope and score evidence. Search, cohort filters and per-arm absolute movement
sorting retain all missing values. No aggregation selector applies within this view.

Exporter adds90previously unexposed individual benchmarks, preserving the existing
14benchmark scores and checks. Optional schema/TS beliefGroup metadata enables the
view for future JSON reports. Frozen w0 and scope are read, never written; bank
source hash added to report provenance. Cohorts are10targets/6related/74otherethical/
10evaluation preferences. Each per-belief score still averages24presentations per
runtime seed; pooled reports average runtime seeds, not training replications.

Validation:5Python +58Node tests pass; TypeScript and production build pass (existing
bundle-size warning). New tests cover optional cohort metadata and one incomplete
belief blocking aggregate scores without erasing a complete zero-valued belief.
Read-only reconstruction verifies all2000individual cells against the saved raw
per-belief rows, including nulls. Live seed7 all100/table, cosmetic search, support
display, target filter and negative-arm movement sorting checked. Screenshot:
data/results/ethical_pilot/ethics_gpu_benchmark_dashboard_v1/screenshots/seed7-individual-beliefs.png.

Vite restarted after schema extension; active port5180 session59738. A fresh browser
tab was needed because the old tab became stuck on its connection-error page. New
tab retained on seed7 Individual beliefs, all100, support display. No model calls,
new training, instrument edits or study resumption. Generated reports/screenshots
remain under the existing registered dashboard artifact parent.

Preservation:commit/push source and notes; serialize a new handoff save after the
previous summed-change save completes. Previous snapshot verification hit HF429
and automatically backed off. New log /tmp/sft-individual-beliefs-save.log; latest
receipt must match this source commit before claiming completed private backup.
