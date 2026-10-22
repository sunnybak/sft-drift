# Target-free readout v2: two sampling seeds completed

All five seed42 jobs and all five seed7 jobs completed with unchanged fixed weights,
source, frozen inputs and decoder. Technical reconstruction verifies their raw grids,
extraction, resolved configs, runtime identities and tokenization. Closed-job copy:
210 files /199,018,461 bytes. All12,000 natural replies are valid, strict-format and
normally stopped. Five seed1729 jobs remain; at1:45:39 uptime the supervisor was
RUNNING PID99941, BASE seed1729 at832/1200 natural replies. No new training or rental.

| Model | Fresh correct /480, seed42 | Seed7 | Stress correct /8, seed42 | Seed7 |
|---|---:|---:|---:|---:|
| BASE |474|476|5|5|
| Positive |475|476|8|7|
| Negative |475|475|6|6|
| Off-topic |478|480|8|8|
| C4-only |475|475|7|7|

All development splits are240/240. Scope failures remain concentrated in one authored
ambiguous not-metal/marked context. These are not six independent reasoning problems.
Off-topic seed7 passes all480 fresh controls and all8 reused stress probes. Its earlier
failures remain unchanged; passing this repeat does not retroactively qualify them.
Other genuine errors include wrong arithmetic-option mappings, denial of15+4=19after
correct derivation and capped repetitive reasoning. BASE also exhibits such failures.
No broad SFT-caused collapse is established; narrow prior copying/numeric losses stay.

All72 frozen preselected natural replies were read in full in the preceding block.
All54 failed fresh/stress replies from these ten jobs have now been read and annotated;
additional C4 seed7 has five ambiguous-case variants plus one stress token cap. Source
and response hashes preserve the link to raw text; scores/grades are unchanged. One
clear natural terminal-letter/rationale reversal (C4 smoking) and other scope/referent
caveats remain. This small correlated selection is not a population semantic error
rate and does not establish that written reasoning faithfully reveals internal belief.

Target positive-minus-negative contrasts are+50.0pp and+48.333pp in these first two
sampling seeds. They remain provisional diagnostics: the third seed, both controls,
full-surface specificity and repeatability are needed. Do not select training on a
favorable ethical direction or relabel this as training-seed robustness.

## Reporting and continuation safeguards

BENCHMARKS.md now identifies only this current finite investigation as active. Its
old preparation workflow is clearly historical, preventing completed diagnostics
from being revived through stale pending/next language. Original hypotheses, failed
gates and the dated prospective plans are unchanged.

Added scripts/finalize_target_free_review_v2.py. It requires a terminal complete
15-job analysis, exact frozen72 selection, all raw-failure annotations and unchanged
source/response/answer hashes. It verifies the failure export against native raw
controls/error codes, preserves original grades, emits consolidated JSONL/Markdown
reviews and a hash-bound reviewed_assessment.json/.md. No overwrite or automatic
semantic clearance. Tests use only synthetic temporary files and never load weights.
42 finalizer, dependency-layer and handoff tests pass.

Added a dashboard report builder/exporter for the completed three-seed readout. It
retains all five models/all500 model-belief scores, shows order/wording/same-prompt
agreement and separates operational, strict-format, stress and missing-data precision
checks with thresholds. Failed checks do not hide valid choices. It labels forced
relative choice rather than moral accuracy/confidence, and refuses partial/missing
seed or unreviewed inputs. Export verifies the reviewed-assessment analysis/source
hashes. Existing schemas, reports and model/dataset/adapter provenance are retained.
45 dashboard tests and the TypeScript check pass. A test caught duplicate measurement
IDs across seeds/splits; fixed by stable seed/split prefixes shared across models.
The real incomplete-export guard was checked: no partial report was published.

Continue collecting the last fixed five jobs and reading their failed controls, then
perform terminal copy, immutable full analysis, review finalization, readable scientific
report and dashboard export. All paths are within the previously registered master
or dashboard output directories. No new experiment automatically follows. User has
authorized existingGPUovernight; any evidence-warranted next experiment still needs
a prospective plan and must not tune for desired ethical outcomes. No remote source
pull while the current worker is bound to469c18f.

Preservation at writing: code push/private save pending. Previous verified artifact
4a830ece6856e1d19acf6d78fe43434057d7dee7 at49ce225 covers first eight jobs/reviews.
Actual new receipt under data/.handoff-receipt.json is authoritative after save.
