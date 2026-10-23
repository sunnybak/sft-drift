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

## Page3 - narrative continuation and measurement audit

User approved a continuation block restating goal, previous finding and next question,
then explicitly requested page3. New journey-preview-v3.pdf contains the two existing
v2pages plus the measurement audit. Original page text is programmatically identical.
Page3 opens with the approved Why this experiment narrative, followed by absolute
wording-diagnostic and supplemental-retention charts, target-free support and fresh
control counts, audit findings and the bounded-repair decision. This summarizes the
fixed-weight measurement investigation (multiple diagnostic runs), not a new SFT run.
Post-hoc value review and changed relative-choice interface remain explicitly separate
from original grades/endorsement. No gates changed and no model calls were made.

Chart/table sources: reviewed Oct22target-free, scope-fact wording and fresh-retention
notes, saved target-free report and actual analysis.json. Control counts are derived
from all domain/split/seed counts (1440/model). Source SHA metadata, chart and render,
standalone intermediate page and create_page3_v3.py accompany the combined PDF under
the existing registered dashboard output/pdf parent. Every rendered page was visually
checked after correcting an initially clipped plot legend. Three-page count and
preserved prior-page text assertions pass. PDF opened in Codex.

Prior v2private snapshot ab755f861def3bbad2225573287a0baa95df1fd8 verified7844files,
22,314,450,498bytes at source8b117fd; its earlier rate-limit retries finished successfully.
Current v3source notes are committed/pushed. New artifact save command from
belief-transfer/: uv run --no-sync python scripts/handoff.py save
Log /tmp/sft-journey-pdf-v3-save.log. This reporting stage has no GPU process/checkpoint;
regeneration uses the saved create_page3_v3.py script and existing source artifacts.
If the save is still verifying at handoff, check its log and latest receipt before
claiming v3private preservation; no same-ID experimental resumption is involved.
Next content is the first training repair; only the first three pages are authored.
