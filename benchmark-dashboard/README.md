# Benchmark explorer

Local Vite + React + Recharts app for the neutral SFT development benchmarks. Reads a
curated index of saved result summaries; does not run models or change any score.

```bash
cd /Users/sunny/dev/sft-drift/benchmark-dashboard
npm ci
npm run dev
```

Open http://127.0.0.1:5173. Node22.12+ and Python3.10+ are required. `npm run build`
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
