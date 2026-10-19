# Transient retry policy and cached continuation

User explicitly requested a few retries before failing after v4 stopped on one HTTP
503 assessment response. New typed `transient_retries` defaults to zero for historical
jobs; current continuation v5 sets three additional attempts. SDK retries remain zero.
Application attempts have separate durable slots (`/retry_1`–`/retry_3`), exact requests,
raw success/error metadata, per-attempt pacing and actual/uncertain charges. No failed
record is erased or overwritten. Successful request cache keys remain compatible:
the model/input/tool/output-cap settings of each individual HTTP call are unchanged.
The retry budget is explicit in the new run contract; it is not hidden SDK behavior.

Retry HTTP 408, temporary 429 and 5xx, and connection/timeout exceptions. Known quota
errors and permanent 4xx stop. Backoff is exponential with jitter; valid Retry-After
seconds or HTTP dates take precedence. Length/schema/usage defects are not regenerated
as transient errors. Exhausted retries remain preserved and stop the supervisor.
New exceptions include HTTP status, selected rate/retry/request headers and raw error
body, in addition to the prior uncertain-cost bound. Historical InternalServerError
records are recognized as 5xx, allowing the explicitly authorized v4 failure to retry.

Continuation `ethics_sft_pooled_corpus_v5` keeps prompt v5 and all content/model/scheduling
settings; only retry budget and run identity change. Its registered roots are prepared
before import. `scripts/continue_stance_corpus.py` locks source/target, checks identical
content/schedule/prompt hashes, rejects pending source requests, backs up the SQLite
contents and copies completed shards. It preserves all old successes, failures and
uncertain charges, verifying the source DB is unchanged. Target cannot be overwritten.
An interrupted import requires another fresh ID. Import provenance distinguishes old
spend from marginal continuation spend. Reports expose both; do not sum copied costs
as newly billed calls. Original v4 artifacts remain historical and unmodified.

Mock checks cover retry success/exhaustion/replay, distinct attempt preservation,
uncertain costs, permanent/quota classification, Retry-After, source immutability and
lossless row/shard import. No tests overlap real generation or result mutation.
Live continuation validation and snapshot details are recorded after execution below.


## Live recovery verified

Final full suite: **911 passed / four skipped, 142.94s**. An additional client raw-error
metadata test passed (selected retry/request headers retained; unrelated headers excluded).
No tests overlapped live generation. V5 prepared and imported all 6,616 documents,
700 completed shards and 20,680 journal records. All source shard file hashes verified.
No API calls during import; original database hash unchanged.

Bounded recovery command:

```
uv run --no-sync python run.py +run=ethics_sft_pooled_corpus_v5 stance_corpus.operation=generate stance_corpus.resume=true stance_corpus.max_batches=37
```

The failed assessment succeeded on **retry_1** at $0.000419425. All 20,680 inherited
request rows remain identical to v4; its database hash is unchanged. Original failure
and uncertain charge remain in the v5 journal, alongside the successful new attempt.
Completed 37 more shards / 354 documents: **6,970 total / 737 shards**, pending zero,
integrity_check ok. Marginal recovery-block cost **$0.44599955**, cumulative lineage
actual **$9.03685720**, uncertain upper **$0.003194**. Cumulative cost includes inherited
$8.59085765 exactly once; do not add v4 and v5 totals as separate bills.

Recovery evidence: v5 results `recovery_generate.log`, `recovery_verification.json/.md`,
`recovery_preflight.json`, tests and `continuation.json` in the generated root. Code is
pushed, then the recovery boundary saved/verified in both private stores before launching
the detached supervisor. Console `/tmp/ethics_sft_pooled_corpus_v5.supervisor.log`;
actual PID/child/phase/log in v5 `generation_job.json`. It resumes the remaining bank
and then C4 under the existing 500-shard boundary policy. Active output after the last
snapshot is local until the next boundary. Original v4 remains stopped and preserved.
