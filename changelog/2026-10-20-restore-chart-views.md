# Restore direct benchmark chart views

User preferred the original generic interface. BenchmarkReport now directly renders
BenchmarkResults with horizontal/vertical bars, matrix, checks, semantic examples and
model context. Restored the Dashboard report library and aggregate inventory counts;
removed the opinionated readout component and CSS. Kept larger typography and JSON
schema compatibility (including optional presentation metadata).

Production build and all 18 app tests passed. Browser verified horizontal and vertical
views. New screenshot: restored-chart-views-preview.png in the registered dashboard root.
No study results or frozen instruments changed. Commit/push and private save/verify
follow this note; final receipt records the artifact revision.
Next UI command: cd benchmark-dashboard && npm run dev.
