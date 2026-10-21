# Grouped model checks — 2026-10-21

User clarified experimental controls should remain with experiment models, while the
former Controls tab means model checks. Renamed accordingly and added explicit group
metadata: instrument, consistency, learning, retention, engineering. BASE, positive,
negative, off-topic and C4 remain together in outcome comparisons. No model exclusion.

Grouped horizontal/vertical charts include diagnostics with no acceptance threshold.
Optional group fields preserve old JSON compatibility. Only this report's recorded
models/checks are displayed; no neutral-learning scores are assigned to ethical arms.
Unrecorded groups show absence; boolean engineering verdicts remain in source details.
The original ethical pilot now charts saved known-cohort retention counts for thinking
and nonthinking. Read actual retention implementation: semantic >=95%, all format,
boundary and normal stop criteria 100%. Historical composite verdicts unchanged.
Raw measurements and frozen instruments unchanged; only derived presentation enriched.

Validation: five exporter +24 Node tests pass; TypeScript/production build pass
(existing bundle advisory). Browser verified renamed tab, five-group selector and
retention charts for the pilot models, with BASE explicitly unrecorded in that report.
Proof: grouped-model-checks.png in registered dashboard artifact directory.
Restart: cd benchmark-dashboard && ./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort
No experimental jobs started. Next experiment still requires a prospective plan.
