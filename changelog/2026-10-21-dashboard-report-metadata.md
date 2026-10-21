# Report library metadata — 2026-10-21

Added experiment names and report dates to every list row. Optional experiment ID/name
is backward-compatible with schema v1; older reports show “Not recorded”. Populated the
neutral learning, four-arm ethical pilot and control/off-topic follow-up report families.
Dates use existing createdAt in UTC and explicitly say Report date, not training date.
Experiment names/IDs and ISO dates are searchable. Scores and raw measurements unchanged.

Validation: five Python exporter tests and 21 Node contract/report tests pass; TypeScript
and production build pass (existing bundle size advisory). Browser verified all ten rows
and filtering by experiment name. Restarted Vite so its validator loads the updated schema.
Proof: belief-transfer/data/results/ethical_pilot/ethics_gpu_benchmark_dashboard_v1/report-list-metadata.png.
App: http://127.0.0.1:5180/; restart with
`cd benchmark-dashboard && ./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort`.
No experimental job is running. Next experimental work requires a prospective plan.
