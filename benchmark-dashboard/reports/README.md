# Add a report

Save `your-report.json` here and click **Refresh reports** in the Dashboard.
No React edits or dev-server restart are needed. Only regular `.json` files are loaded;
symlinks are skipped. Duplicate report IDs and invalid files appear as errors, while
valid reports continue to render.

Start from `../examples/report-template.json` (explicitly fictional, not auto-loaded).
Validate from the app directory:

```bash
npm run validate:report -- reports/your-report.json
```

The schema is `../benchmark-report.schema.json`; the TypeScript contract is
`../src/report-types.ts`. Use `schemaVersion: "1.0"` and unique report/model/benchmark/test
IDs. All score/test references must resolve inside the report. Each benchmark needs a
semantic description, conditions and at least one example (prefer two).

Authored JSON report files here are versionable source inputs. Automatically derived
study reports live under the private artifact tree instead. No model calls are made.

The target-free three-seed pilot report is derived only after the v2 sweep and its
raw-response review are complete. `generate-target-free-readout-report.ts` requires
all five models, all three seeds, all 500 model/belief rows, and a hash-bound
`reviewed_assessment.json`. Partial progress is never substituted for a completed
report. This report measures canonical-position choices in a forced comparison;
it does not measure moral accuracy, confidence, or independent endorsement.
Model-check failures remain visible alongside measured choices. Fresh operational,
strict-format and reused stress checks stay separate, with their numeric thresholds.
