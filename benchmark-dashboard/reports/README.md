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

Five pipeline-repair reports are derived by `scripts/generate-repair-reports.ts`
(included in `npm run data`). Search **Repair** in Dashboard:

- Repair 1: corrected loss normalization.
- Repair 2: stronger instruction replay.
- Repair 3: lower learning rate.
- Repair 4: expanded replay coverage.
- Repair 5: full BASE reasoning, rejected and stopped by the user condition.

Each report compares the candidate with its matching BASE cohort. Banks and denominators
change between attempts; do not pool their retention fractions. Numeric accuracy,
complete-generation contracts, engineering checks, and original/fresh qualification
remain distinct. Reports 1–3 also expose the recorded runtime repeats separately.
The final report shows seen/held facts in both instruction wordings, plus the 17/24
held-out short-answer retention result. Its 512/2400 collection is intentionally partial:
511 valid, one invalid, 1888 not recorded. It has no full-100 aggregate. The cancellation
is reported as an informational user stop, not a new model-quality failure.

The exporter verifies source hashes in the manual-review receipts, matched reference
cohorts, frozen control prompts, and coverage against raw persisted replies. It makes
no model calls and changes no original scores or gates. All five reports are validated
before any is published. Report JSONs remain under the registered private artifact tree.
