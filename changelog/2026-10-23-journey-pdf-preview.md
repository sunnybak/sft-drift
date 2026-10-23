# Journey PDF - first-page preview

User requested a one-off PDF covering the whole research journey, one consistently
formatted page per experiment, and asked to see the first page first. Authored only
page01 (original four-arm pilot); remaining pages await format feedback. No experiments
or model calls. Existing dashboard report and reviewed original notes are the sources.

Registered dashboard artifact parent already covers output/pdf/. Outputs:
01-four-arm-pilot-preview.pdf (one A4 portrait page), matching rendered PNG, standalone
chart PNG, create_first_experiment.py, and SHA-bound source manifest JSON. The page
contains setup/dose, directional contrast and belief-cluster interval, target versus
80-other-ethical drift, all-arm reply coverage, qualification/retention caveats and
rejection of scaling. 80-other values derive from actual saved report, distinct from
the historical note's74-unrelated cohort. No missing control score becomes zero.

ReportLab + Matplotlib, isolated uv tool environment; pinned ML project dependencies
unchanged. Poppler-rendered page visually checked, one-page PDF text extracted, labels
and counts checked against sources. No clipping or overlaps. Preview PDF opened in
Codex. Future pages should retain these fixed margins, typography and section order,
with experiment-specific charts, denominators and failure/partial statuses.

This preview and source join the next private snapshot; source notes committed/pushed.
The full multi-page report has not been created. No study resumption is authorized.
