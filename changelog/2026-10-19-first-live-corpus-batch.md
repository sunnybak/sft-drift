# First live pooled corpus batch — 2026-10-19

User authorized proceeding with the bounded first ten documents after corpus preparation.
Ran from source `976e9b0`:

```sh
uv run --no-sync python run.py +run=ethics_sft_pooled_corpus_v2 stance_corpus.operation=generate stance_corpus.resume=true stance_corpus.max_batches=1
uv run --no-sync python scripts/inspect_stance_corpus.py
```

Completed shard: `ai_hiring_no_appeal__explanatory_article__0005`; five shared ideas,
paired positive/negative documents, slots 17/20/23/26/29. Each has draft, one revision,
separate Luna review, hashes, exact requests/raw outputs and tokenizer diagnostics.
All ten full revised documents read by the implementing agent. Report, all paired texts,
before/after examples, provisional agent annotations and reviewer disagreements are in
new results files `first_batch_review.md`, `first_batch_agent_review.jsonl/.md`,
`first_batch_review_summary.json` and `first_batch_verification.json`.

Drafts 8/10 in range → finals 10/10, 412–587 Qwen tokens, mean 478.4, total 4,784.
Two length fixes, zero regressions, two verbatim revisions. All ten explicitly own the
assigned position and address the correct opposing consideration. No normalized full
duplicates, visible task metadata or noncanonical full eval wording matches; canonical
claim overlap intentionally allowed. Five distinct focus labels mostly reuse a common
argument structure; no claim of full-corpus diversity follows.

Recurring review concern: missing explanation/meaningful human review becomes no route
to question, learn, reconsider or correct. Eight documents carry provisional precision
concerns, one more a borderline opening (later qualified). This is not an independent
human-labeled error-rate estimate. Model flags one concerned document on added factual
premises/repetition, passing all six checks on the other eight. All fifty per-condition
and ten global scope booleans are true. One retained draft also changes system bias
checks into information bias checks. The best candidate uses 'less ability' rather than
categorical no avenue. Preserve all outcomes; do not scale unchanged or automatically
mark anything training-ready.

33 successful gpt-6-luna Responses calls, 56,795 input and 16,732 output tokens, ledger
cost $0.01509735 including canary/planning. No uncertain charges, pending intents or
request errors. No C4 acquisition, training or GPU rental. Live generation is stopped
at a complete shard boundary; identical-contract v2 resume is supported technically.
Next: fresh-ID focused prompt test on scoped limits, neutral planning rules and explicit
review-data boundaries, followed by broader subjects/forms/control review before bulk.

No functional code changes or pytest rerun. Artifact validation independently recounted
all ten Qwen lengths, verified draft/final/shard hashes and identical paired plans, checked
all 161 frozen hashes and historical shared-cache bytes, and confirmed every JSONL has a
Markdown view. No tests ran concurrently with generation. Source/notes are committed and
pushed, followed by private handoff save/verify; authoritative final source and both
artifact revisions are in the ignored handoff receipt. No process/checkpoint remains active.
