# Dashboard report list and collapsible reader

User requested a report list, with reports opening from the right over a dimmed
center and a collapsible panel. The dashboard now shows searchable rows with report
title, description, tags, model/benchmark counts and the existing declared-check
status. All10reports remain available. No benchmark score, source, threshold,
qualification, frozen instrument or experimental artifact was regenerated.

ReportDrawer uses a native modal dialog with a dimmed backdrop and independent
scrolling. Collapse returns to the list while retaining the report component and
its chart selection, filters and scroll. A right-edge tab restores it. Close,
Escape and clicking outside dismiss it. Background scrolling is locked only while
expanded, then restored. Narrow viewports use more of the available width.

Browser checks covered search/all10rows, open, collapse/reopen preserving Score
matrix, Escape, backdrop dismissal and nested model cards. Testing caught a portal
cancel event also dismissing the report; the outer cancel handler now handles only
its own dialog events. Escape from a model card leaves the report open.

Existing5exporter and20Node tests pass; TypeScript and production build pass (only
the existing bundle-size advisory). No new dependencies. No GPU work or fresh evals.
Previews report-list.png and report-drawer.png are under the existing registered
private dashboard root: belief-transfer/data/results/ethical_pilot/
ethics_gpu_benchmark_dashboard_v1/. Source/notes committed and pushed; registered
artifacts saved privately with handoff.py, whose latest receipt is authoritative.

The app remains at http://127.0.0.1:5180/. No existing result IDs were rerun or
replaced. Next scientific work still requires a new prospective experiment plan.
