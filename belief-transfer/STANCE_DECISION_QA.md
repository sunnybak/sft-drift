# Decisions screening of the completed stance bank

This opt-in `stance_decision_qa` stage reads the immutable `ethics_sft_pooled_corpus_v5`
source bank. It changes neither the frozen belief instrument nor source documents.
The user authorized calibration on previously reviewed examples and screening all 20,000.
No training or GPU rental is included.

Questions separately assess assigned stance, premise change, owned contradiction,
misassigned objections, task metadata and substantial redundant prose. Version v1 is a
concise rubric; v2 adds explicit predicate/quantifier/channel/necessity guards from the
agent spot checks. Ethical disagreement, ordinary implications and subjective appearance
judgments are allowed. Model probabilities route review; they are not validated frequencies
or a training-ready designation. Refusals/incomplete or invalid answers remain unresolved.

Development references: 64 agent-reviewed documents in `content_review_v1`. Frozen-rubric
check: the 100 separately annotated `content_review_v2` documents, with borderline labels
excluded from categorical calibration metrics. These are previously examined development
examples, not independent human ground truth or untouched validation.

From `belief-transfer/`:

```sh
uv run --no-sync python run.py +run=ethics_sft_decision_qa_calibration_v1
uv run --no-sync python run.py +run=ethics_sft_decision_qa_calibration_v1 decision_qa.operation=assess decision_qa.resume=true decision_qa.max_calls=1
# Then resume the unchanged contract for remaining records, after checking the canary.
uv run --no-sync python run.py +run=ethics_sft_decision_qa_calibration_v1 decision_qa.operation=assess decision_qa.resume=true
uv run --no-sync python scripts/report_decision_qa_calibration.py --run-id ethics_sft_decision_qa_calibration_v1 --review v1
```

Additional registered overlays: `ethics_sft_decision_qa_calibration_v2`,
`ethics_sft_decision_qa_validation_v1` and `ethics_sft_decision_qa_corpus_v1`.
Prepare before assessing; do not overwrite completed runs. Prompt/settings/source changes
need fresh IDs. `resume` and `max_calls` are operational controls; compatible completed
requests replay from a per-run durable cache without another API call. Unknown potentially
billed in-flight requests require reconciliation, not blind replay. Retry attempts are
bounded (three additional transient retries, SDK automatic retries zero) and separately
journaled, with uncertain failed-attempt charges kept explicit.

Raw requests, response payloads, cache and charge ledger live in the run's
`data/generated/ethical_stance_sft/<run>/requests.sqlite`, declared in the separate private
corpus store. Results, ranked review queue, full probabilities/refusals, resolved config,
invocation inputs, summaries and Markdown views live in `data/results/ethical_stance_sft/<run>/`.
The `progress.json` file is the status reference. No automatic filtering or source edits.

The dispatcher uses 64 concurrent operations and the shared 80% RPM/TPM pacer. Input
reservations conservatively use UTF-8 request bytes plus protocol allowance; this can
underuse actual TPM. The gate covers this process, not other account traffic. Decisions
bills input only; reported actual spend uses returned usage and separate Decisions prices.
See [official API guide](https://developers.openai.com/api/docs/guides/decisions).

## Current frozen screening protocol

Use `ethics_sft_decision_qa_corpus_v3` (rubric v4, 13 questions). Earlier overlays are
historical development runs; do not repeat completed IDs. All 164 reviewed examples
were used in tuning. Calibration_v5 reports 12/14 known major defects at .2, one flag
among 143 provisional negatives, excluding seven borderline cases. This does not
estimate unseen recall. Both psychology-deception families (400 documents) and every
previously confirmed semantic defect receive mandatory review, independently of score.

```sh
uv run --no-sync python run.py +run=ethics_sft_decision_qa_corpus_v3
uv run --no-sync python run.py +run=ethics_sft_decision_qa_corpus_v3 decision_qa.operation=assess decision_qa.resume=true
```

With provider counting enabled, reservation is the smaller of UTF-8 envelope bytes
plus 2,048 and twice the Responses counting endpoint estimate plus 2,048. This is a
conservative proxy, not an exact Decisions count. Counting requests also take RPM
permits. Returned actual usage is checked against reservation; a mismatch stops with
raw output preserved. Calibration_v4 exposed such a mismatch under an earlier margin;
calibration_v5 passed all 164 calls under the current rule. Expected full-pass cost
from measured usage: approximately $7.69, excluding development and retries.
