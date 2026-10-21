# Benchmark explorer

Local Vite + React + Recharts app for the neutral SFT development benchmarks. Reads a
curated index of saved result summaries; does not run models or change any score.

```bash
cd /Users/sunny/dev/sft-drift/benchmark-dashboard
npm ci
npm run dev
```

Open http://127.0.0.1:5174. Node22.12+ and Python3.10+ are required. `npm run build`
creates a static build; `npm run preview` serves it locally. `npm test` uses only
synthetic fixtures and temporary directories. No model dependencies or weights needed.

`npm run data` refreshes the derived view. Restart/refresh the browser after exporting.
If private study artifacts have not been restored, missing source paths appear in the
app and unavailable endpoints remain absent. Never substitute fixture scores.

## Plotting convention v1

- Horizontal grouped bars for comparing model profiles; individual horizontal bars
  for one benchmark. Fixed0–100% axes and stable model colors throughout.
- Exact numerator/denominator in the matrix, individual endpoint list and hover details.
  A zero is a measured zero; a dash means unmeasured. No imputation or overall average.
- Thresholds in the matrix and a dashed line on individual charts. Diagnostic endpoints
  have no threshold. Meeting one threshold does not pass the complete qualification.
- Separate semantic correctness, formatting, response boundaries, normal stops and
  coverage. Retention shows fixed pretraining-known cohorts separately from all items.
- Distinct benchmark IDs for ordinary questions, code-only lookup, native prose and
  forced assistant-prefix continuation. Preserve decoder/condition descriptions.
- No connecting lines implying a time series, radar polygons implying an overall area,
  or pooled denominators across correlated questions. No confidence intervals fabricated
  from repeated questions to the same20facts. Training-seed uncertainty needs actual
  independent repeats and a separate analysis.
- Stance Score is an outcome, not higher-is-better accuracy. The100-belief instrument
  is outside this neutral qualification view; future stance plots need separate signed
  before/after distributions and coverage, not inclusion in an accuracy composite.

## Data and provenance

`scripts/export_benchmarks.py` uses an explicit run list and saved summary schemas.
It extracts counts and writes schema-v1`benchmarks.json` with model/metric definitions,
per-observation source path/SHA256, caps where reported, source inventory and unavailable
paths. BASE is a benchmark-specific reference: repeated BASE measurements are not pooled.
Adding a run requires explicit registration in the exporter rather than guessing from
folder names. New endpoint conditions need new metric IDs when not comparable.

The authoritative derived view is registered for private preservation under
`belief-transfer/data/results/ethical_pilot/ethics_gpu_benchmark_dashboard_v1/`.
This is a derived display, not a new GPU measurement. `public/benchmarks.json` is an
ignored copy for Vite. All underlying measurement artifacts remain immutable.
Private data and built assets are excluded from Git. Source and lockfile are committed.

The UI offers Compare (bars/matrix), By benchmark, Run directory, model selection,
category/search filters, downloadable JSON and per-score provenance inspection.
It is a local read-only app with no external backend or publishing integration.

References: [Vite](https://vite.dev/guide/) and
[Recharts BarChart](https://recharts.github.io/en-US/api/BarChart/).

## Reusable BenchmarkReport component (JSON v1.0)

The sidebar **Dashboard** hosts independent reports. The existing Compare / By benchmark /
Run directory views remain available. The local server uses port **5174** to avoid a
conflict with another project's server on5173.

```tsx
import { BenchmarkReport, BenchmarkResults } from './components/BenchmarkReport';
import type { BenchmarkReportData } from './report-types';

// report is loaded and validated against benchmark-report.schema.json.
<BenchmarkReport report={report} initialView="bars" />
// Direct props: models, benchmarks, scores, tests, plus report metadata.
<BenchmarkResults {...report} initialView="columns" />
<BenchmarkReport report={report} initialView="matrix" compact onOpen={openFullReport} />
```

The component contains no study-specific IDs, model names, file access or hardcoded
thresholds. It supports horizontal bars, vertical bars, score matrix, recorded checks,
benchmark descriptions/examples, and model/training context. Fraction metrics use0–100%
axes; numeric metrics use their declared ranges and optional `unitLabel` (e.g. `ms`). Direction (higher/lower/descriptive)
and threshold operator/value are explicit. There is no blended score.

Each report is self-contained JSON with these required fields:

| Field | Content |
|---|---|
| `schemaVersion`, `id`, `title`, `description`, `createdAt`, `tags`, `context` | Identity, version, scope/limitations |
| `models` | Provider, model ID/revision, variant, inference parameters; optional color |
| `models[].finetuning` | Null for BASE, or run ID, dataset identity/hash/context, pipeline identity/hash/context, adapter source/hash |
| `benchmarks` | Semantic description, category, conditions, examples, unit/range/direction, optional threshold |
| `scores` | Model/benchmark references, value, optional exact counts, notes and source/hash |
| `tests` | Explicit pass/fail/not_run/error, required flag, expected/observed, semantic description and source |
| `sources` | Artifact paths and recorded SHA-256 identifiers |

Optional `experiment: {id, name}` identifies the study in the report library and is searchable.
Rows show `createdAt` as **Report date** (UTC calendar date), not training date; older
JSON without experiment metadata shows **Not recorded**.

Hash fields are nullable: unknown provenance is displayed as **Not recorded**. State
what each hash covers (e.g. dataset manifest, exact training plan file, adapter weights).
A pipeline-plan hash is not advertised as a hash of all code. Per-benchmark decoder
conditions remain distinct when one model was measured under multiple interfaces.

**Adding a report requires only JSON:** copy `examples/report-template.json` into
`reports/your-report.json`, replace the explicitly fictional content, run
`npm run validate:report -- reports/your-report.json`, then click Refresh reports.
The strict [JSON Schema](benchmark-report.schema.json) plus semantic validation rejects
unknown fields, invalid references, duplicate IDs/pairs, inconsistent fraction counts,
invalid ranges/thresholds and missing fine-tune provenance. These checks validate the
report contract; they do not independently authenticate externally supplied evidence.

The Vite TypeScript loader reads only the configured report folders on the local server
(`/reports.json`), never a path supplied by a browser request. Invalid reports are exposed
in an error list; valid reports remain usable. Production builds emit the same validated
collection as a static `reports.json`; rebuild to include new files in a static deployment.

Three derived real reports are generated by `scripts/generate-study-reports.ts` after the
legacy export: learning/recall, instruction retention, training/control contract. Their
scores and check results are taken from preserved summaries/judgments. Examples are
clearly labeled illustrative, not replicas of the full saved prompts. Derived reports
and screenshots remain under the already-registered private dashboard artifact root.
The example template is outside the loaded folders so it cannot masquerade as real data.

Checks are recorded outcomes, not calculated from bar colors or score thresholds. The
status summary covers only declared required checks. No required checks means **Not
assessed**; not_run/error never becomes a pass. Filtering models updates that scoped
summary. A report passing its checks does not establish full training qualification.

## Report views

`BenchmarkReport` and `BenchmarkResults` both expose Horizontal bars, Vertical bars,
Score matrix, Checks, What is tested, and Model context directly. `initialView` selects
the starting tab. The Dashboard uses a searchable list of report titles, descriptions,
tags, model/benchmark counts and declared-check status. Reports open in a native modal
drawer on the right over a dimmed library. Collapse keeps the selected chart, filters
and scroll position mounted; the edge tab expands it again. Close, Escape or clicking
the backdrop dismisses it. Model-info dialogs remain independently dismissible.
Full reports start with horizontal bars. The optional presentation metadata remains accepted in JSON for
compatibility, but does not control the interface.

Model legend entries, model selectors and matrix headers are clickable pills. They open
a keyboard-accessible native dialog with model identity and available provenance;
checkboxes independently control chart visibility. Legacy cards use training-contract
metadata only when model ID and training run match. Escape, Close or backdrop dismisses.

If port 5174 is occupied by another app, start with
`npm run dev -- --port 5175 --host 127.0.0.1`.

Model cards lead with optional `models[].studyContext`: purpose, intervention, data,
comparison and limitations (all five strings required if supplied). Training dose is
derived from the saved plan and manifest; repeated entries are not counted as unique
examples. Technical provenance is collapsed under Reproducibility details. Old reports
without studyContext display their recorded training description. Restart Vite after
changing the schema itself; ordinary valid report JSON still loads through Refresh.

## Four-arm ethical pilot

Dashboard now includes four portable JSON reports: a strict three-seed average and
one report per evaluation seed (42, 7, 1729). Open **Ethical pilot · three-seed average**.
Switch **Change from BASE / Support for claim**, **Overview / Trained beliefs**, and
horizontal bars / vertical bars / score matrix. Model pills retain scientific context.
Overview separates the10targets, full100bank,80untrained ethical claims, and10
frozen preferences. The Checks tab retains qualification, fresh factual/null controls,
full reply coverage and strict retention failures. Stance is descriptive, not accuracy.

`scripts/generate-ethical-pilot-reports.ts` derives these reports from the preserved
per-belief rows and model plans; it is included in `npm run data`. Any missing or invalid
reply blocks the affected declared average; available seeds remain separately visible.
No changing denominators, incomplete-seed pooling or neutral imputation. Seed42has one
invalid reply in each control; off-topic1729has no stance replies. Counts stay in the
score evidence; Stance Score is not raw agreement frequency.

Reports use the existing registered private dashboard output root. The JSON contract
adds optional presentation defaults `defaultMetric` (`score`/`change`) and
`defaultCategory` (a declared benchmark category), retaining schema-v1 compatibility.
Change charts use signed percentage-point axes with a zero reference; absolute charts
retain the fixed0–100%scale. Existing report files remain valid.

Current local session: http://127.0.0.1:5180/ (other apps occupy the earlier ports).
Start explicitly with `./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort`.

## Control and off-topic follow-up

`scripts/generate-followup-reports.ts` adds three reports once the registered follow-up
analysis exists: expanded arithmetic controls across BASE and the four final adapters,
complete off-topic stance collection across three seeds, and separate order/wording/
negation agreement. Agreement rates retain eligible/expected pair counts; correlated
pairs are not independent samples. The original reports,
qualification failures and retention outcomes stay available. Reworded arithmetic
checks are development evidence; they do not modify the frozen ethical questions.

An incomplete score may declare `value: null` and
`bounds: {lower, upper, kind: "missing_data"}`. Charts render a range; matrices label
it incomplete. These are limits on what missing replies could contribute, not a
confidence interval or an estimated midpoint. The validator rejects a simultaneous
point estimate, inverted limits or limits outside the benchmark range. BASE-change
views subtract the same reference from both limits. Bounds require a measured
reference for change views, and never silently substitute a zero reference.

The **Controls** button beside Change / Support for claim opens a model-by-model
view of recorded gates, observed values, and passing requirements. Numeric benchmark
thresholds show within/outside-range comparisons separately from recorded composite
pass/fail verdicts. Model selection applies; belief-group filtering does not hide
controls. Missing controls are explicit. Switching back restores the score view.

Controls default to horizontal bar charts, with a vertical option, labeled axes,
threshold lines and green passing ranges. Recorded tables/sources remain expandable.
Optional `tests[].measurements` supplies fraction metrics `{id,name,value,threshold}`
for composite checks. Null stays missing; shared IDs require identical definitions
and at most one value per model. Existing numeric benchmark thresholds also chart.
Original pilot control accuracy, note flips and coverage are derived from saved
artifacts per seed, without changing gates or pooling only passing seeds.
