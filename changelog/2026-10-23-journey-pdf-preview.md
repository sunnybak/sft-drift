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

## Minor caption refinement (v4)

User requested an explanation of Original wording and Explicit facts in the chart
caption. journey-preview-v4.pdf defines compressed phrasing (example: not metal and
marked) versus separately stated intended properties, removing negation-scope ambiguity.
Caption retains both denominators and post-hoc-review limits. Plot height reduced10pt
for caption space; bounds assertion and final rendered inspection pass. Prior two
pages' text remains identical, and no score changed. New source/script/chart/render
use v4names. This minor layout iteration joins the next coherent PDF artifact snapshot;
do not start another full-study backup for each caption edit while v3save is verifying.
V4files remain local until that next snapshot; v3verification log remains authoritative
for that earlier version. PDF opened in Codex. No model calls or experiment resumption.

## Chart measurement subtitles (v5)

Added subtitles directly below both page3chart titles: wording diagnostic measures
answer accuracy with compressed versus explicitly stated facts; retention measures
preservation of short-answer values BASE previously got right. Reserved plot-header
space and visually inspected rendered page; no overlap or clipped labels. Scores,
caption and first two pages remain unchanged. journey-preview-v5.pdf and matching
source/chart/render use fresh filenames. This minor refinement joins the next coherent
PDF snapshot with v4; no new full-study backup or model calls for this caption cycle.

## Page4 - corrected normalization (v6)

User authorized the next page. journey-preview-v6.pdf appends Repair1to the existing
three v5pages; text equality checks preserve those pages exactly. Narrative describes
the genuine retention finding and analytic gradient-scaling issue in the PROPOSED loss
path; it does not infer that a demonstrated historical bug caused original regressions.
This fresh ordinary-weight control belongs to the prospectively amended replay-weight
comparison. Data/dose/seed, changed objective, chart measurement subtitles, absolute
scores/counts,95%lines, engineering checks, failure example and decision are shown.

Retention63/63reasoning and57/59short passes; known controls30/32fails; note agreement
16/16can be consistently wrong. Short unscorable/manual-wrong distinction remains
explicit. All-item accuracy63/64and57/64, all100coverage2400/2400, descriptive support
69.88%versusBASE63.29%remain distinct. Validation not run; no qualified-recipe claim.
No new model calls, training, GPU action or changed scores/gates.

create_page4_v6.py, source/test/score SHA metadata, chart, standalone intermediate
page, combined PDF and rendered page4are under registered dashboard output/pdf/.
Fixed an initial subtitle escape and decision-box overflow, rerendered and visually
checked final layout. Four-page count and first-three-page text equality pass; source
JSON parses. Existing PDF opened in Codex. Next prospective report page: stronger replay.

V3private backup completed verified7850files/22,315,305,959bytes at sourceaae154e.
This completed page block groups the v4/v5minor caption refinements with v6for one
private snapshot, after source notes commit/push. Command from belief-transfer/:
uv run --no-sync python scripts/handoff.py save
Log: /tmp/sft-journey-pdf-v6-save.log. Until its verified receipt, v4-v6are local and
source notes pushed; don't claim private preservation from merely uploaded bytes.
The stage is report authoring, no experimental resume/checkpoint. Receipt is authoritative.

## Full journey - six remaining pages (v7)

User requested more pages. Added six experiment/diagnostic pages, bringing
sft-journey-report-v7.pdf to10pages: stronger replay; lower LR; expanded replay;
fixed-model learning/transfer; fuller BASE reasoning and intentional stop; later
stock-HF reference. First four page texts remain identical to v6. Every new page
has narrative continuation, intervention, two absolute-score charts with measurement
subtitles, counts/thresholds, table, limits and next decision. No experimental work
or model calls were authorized or performed by this reporting request.

Scored charts use saved validated report entries, lower-LR actual comparison and
RCAvalue-v3summary. Reviewed source notes support the additional old-control counts.
Changing banks/cohorts remain explicit (59vs55vs57vs24). Post-hoc value-v3does not
rewrite historical grades. No false full100aggregate for canceled final reasoning
run:512recorded/511valid/1invalid/1888uncollected remains explicit. Stock reference
fails note stability despite improved retention; shared preprocessing and different
gradient scaling prevent whole-stack independence or identical-update claims.

Files under registered dashboard output/pdf/: combined PDF; create_remaining_pages_v7.py;
six chart images and final page renders; remaining-pages-sources-v7.json including
source SHA, complete authored content/data and layout bounds; intermediate PDF in
tmp/pdfs/. No new JSONL. No dependency/lockfile changes; isolated uv rendering environment.

Verification:10pages, first-four-page text equality; narrative presence on all new
pages; count/range checks and layout bounds. Poppler-rendered and visually inspected
all six added pages, then reinspected changed diagnostic/stop pages. All ten pages'
text characters fall within safe page bounds (pdfplumber). Corrected actual training
run IDs in footers and removed an all-model audit row from model-specific columns.
PDF is1,005,295bytes at the reviewed rendering boundary; final receipt/hash is authoritative.
Opened final report in Codex. No global degradation/capacity claim or qualified recipe.

Previous v6backup finished verified7868files/22,318,120,050bytes at source9e57fd7.
This complete report block will save source notes in Git and run the next private
artifact snapshot once. Command from belief-transfer/: uv run --no-sync python
scripts/handoff.py save. Log /tmp/sft-journey-pdf-v7-save.log; until a verified receipt,
new v7PDF/images remain local. No GPU job/checkpoint or measurement to resume.
Next step is user review of the complete PDF, not a training queue.
