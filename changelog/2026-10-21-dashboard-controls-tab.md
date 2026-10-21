# Controls tab — 2026-10-21

Added Controls alongside Change / Support for claim (Absolute score on other reports).
Dedicated ReportControls component groups checks by selected model. It shows required
ranges/criteria, observed results, recorded verdicts and source references. Quantitative
benchmark thresholds show within/outside-range comparisons separately from composite
qualification. It never infers overall qualification from passing a numeric threshold.
No frozen controls, gates, scores or measurement artifacts changed. The panel displays
only evidence in its report; absent model controls explicitly say none recorded.
Belief category does not hide controls. Return to scores preserves chart selection.

Validation: five exporter and 21 Node tests pass; TypeScript and production build pass
(existing bundle advisory). Browser verified original pilot thresholds/results, expanded
control numeric ranges and gate verdicts, plus return to support view. Controls also work
in reports without BASE comparisons. Preview saved in registered dashboard artifact root:
report-controls-tab.png. No experimental process started; GPU remains outside this task.
Restart: cd benchmark-dashboard && ./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort
