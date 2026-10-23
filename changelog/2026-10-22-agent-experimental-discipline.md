# Agent instructions: experimental judgment after the failed repair sequence

User requested updating AGENTS.md after reviewing the long, unsuccessful pipeline
repair investigation. Only AGENTS.md is edited; CLAUDE.md remains its symlink.

Added future-facing requirements for bounded tuning blocks (maximum training runs,
evaluation workload and wall-clock decision point), early independently checked
training references, competing explanations across data/objective/trainer/inference/
measurement, independent confirmation and honest scope of conclusions. A failed
hypothesis does not automatically extend an authorized experiment budget. Mechanical
training checks remain separate from preservation of behavior.

Explicit user stop conditions take precedence over remaining full-bank collection;
review the decisive result, stop model calls, preserve partial coverage and report.
Historical thresholds, raw outputs and protocols are unchanged. Reporting/documentation
requests do not resume the paused study. Benchmark delivery includes dashboard reports
with rejected attempts, matched BASE cohorts, denominators, thresholds and missingness.
Resource accounting separates training, inference, engineering and preservation, and
more compute must address an identified bottleneck. Related work is grouped into
coherent preservation boundaries rather than snapshotting every minor edit.

Validation: reviewed the diff, git diff --check passed, and CLAUDE.md still resolves to
AGENTS.md. No code, model calls, tests involving experimental artifacts or frozen
measurements changed. Existing private snapshot7883e8d0e71f22c1e7f4c6880ffce639f78ce0a5
at91762b6contains all18dashboard reports and the fully preserved stopped trial.
This documentation block is committed/pushed, then uses the required handoff save.
The scientific goal remains paused.
