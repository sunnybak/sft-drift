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

## User revision - absolute scores and BASE page

The user requested actual scores instead of relative changes, plus a preceding BASE
page. New version00-base-and-pilot-preview-v2.pdf has exactly two pages; original preview
remains unchanged. Pilot charts now show absolute canonical-claim support on0-100%
axes for BASE and four arms, with unavailable aggregates explicitly labeled. No delta
headline remains. BASE page groups stance, agreement, frozen controls, procedural and
other retention banks, expanded arithmetic controls and target-free follow-up checks.
BASE failures are visible; banks/denominators remain distinct. The complete reported
BASE score/check inventory across current dashboard reports is saved alongside the
PDF, preserving individual entries and repeated report versions rather than pooling.

Counts verified against actual source analysis, including validation scope43/48 (not
an inferred expanded denominator). Rendered and visually checked both pages; no
clipping or overlap. Two-page count and absolute-score text checked with pypdf.
create_preview_v2.py, chart PNGs, page PNGs, inventory and source metadata are saved
under the same registered output/pdf parent. A first-preview backup was already
verifying when feedback arrived; new-version files use fresh names. A final snapshot
after this coherent revision boundary must include v2, not just the original preview.
The remaining journey experiment pages are still uncreated pending format review.
