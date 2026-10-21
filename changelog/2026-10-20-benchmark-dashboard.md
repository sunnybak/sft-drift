# Local benchmark dashboard

Added lightweight Vite/React/TypeScript/Recharts app under benchmark-dashboard/.
A standard-library Python exporter indexes explicit saved summary schemas across
eight model profiles: BASE, raw high/low LR, assistant high/low LR, varied requests,
tagged replay and untagged replay. Current export97observations/21endpoint definitions
from18source reports; no missing sourcefiles. Each count retains source path/SHA256.
Curated coverage is explicit, not discovery of every historical diagnostic. BASE
references are benchmark-specific and repeated measurements are not pooled.

Read-only UI: grouped horizontal comparison bars, score matrix, individual benchmarks
with threshold reference lines, model/category/search filters, run directory, exact
counts, length stops, provenance dialog and downloadable JSON. Defaults to BASE/tagged/
untagged. No composite, missing-value imputation or changes to original measurements.
Retention accuracy, strict format, boundaries and normal stops are distinct endpoints;
fixed-known cohorts remain distinct from full64item scores. Native raw/assistant
prefix conditions remain separate from ordinary chat. Stance comparisons excluded
from higher-is-better accuracy profile, explained in README/BENCHMARKS.md.

Registered derived output before execution at data/results/ethical_pilot/
ethics_gpu_benchmark_dashboard_v1/benchmarks.json and dashboard-preview.png.
public/benchmarks.json, node_modules and build outputs are ignored and regenerated.
No Python package dependency layers, pinned ML dependencies, model loads, GPU runs,
scorers, prompts, frozen hashes, historical artifacts or gate definitions changed.
Node dependencies isolated in app package/lockfile. npm audit0vulnerabilities.

Validation:5unittest cases use only synthetic fixtures/temp dirs: missing≠zero,
measuredzero/provenanceSHA,44vs64retentioncohorts,semantic/cap separation,invalidcounts.
37focused repo import/handofftests passed. ProductionTypeScript/Vitebuild passes;
Recharts main bundle~179KB gzip. Browser inspected comparison chart, matrix exact
counts, individual semantic/formatthresholds, and score-source dialog. Preview saved.
Dev server on127.0.0.1:5173(exec55763). Restart: cd benchmark-dashboard && npm run dev.
No hosting/publication; app is local. Source+notes need push and private handoff save.
