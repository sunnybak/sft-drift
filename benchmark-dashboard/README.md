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

## Opinionated readouts

`BenchmarkReport` now leads with **Readout**, **Before → after**, and **Failure triage**.
The six generic inspection tools remain in **Explore evidence**; `BenchmarkResults`
continues to expose that raw renderer directly. `initialView` controls that explorer,
not the report's primary Readout tab. Compact Dashboard cards show featured evidence;
full reports expose all endpoints and provenance.

Dashboard order prioritizes unresolved required gates for each report's configured
candidate, not failures across historical models. The global decision is a conservative
summary of declared report gates; passing them does not establish full qualification.

Optional, backward-compatible `presentation` JSON defines:

- `focusModelId`: candidate for the readout and gate verdict.
- `referenceModelId`: baseline shown alongside featured scores.
- `comparisonModelId`: default before-model for the change view (e.g. a matched ablation).
- `headline`, `interpretation`, `nextStep`: authored, evidence-based commentary.
- `highlights`: benchmark references, display labels and explanations.

All references are validated. Authored commentary appears only for its configured
focus model; switching candidates uses that model's recorded checks and generic
benchmark definitions. Keep commentary synchronized with the evidence: schema validation
checks structure/references, not the truth of prose. Existing JSON without presentation
continues to work with a candidate-focused recorded-check summary.

Before/after differences are per endpoint with original counts, units and direction;
fraction differences use percentage points, not relative percentages. Missing endpoint
pairs are marked Not comparable. Failure triage lists failed/not-run/error required
checks first; related endpoint scores cannot replace a compound check's recorded result.
