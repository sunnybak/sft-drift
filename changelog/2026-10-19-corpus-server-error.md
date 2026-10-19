# Single assessment server failure; partial bank preserved

User reported a failure and asked whether restarting uses cached outputs. Diagnosis:
`ethics_sft_pooled_corpus_v4` stopped in the second 500-shard invocation on
`school_experiment_parent_consent__0078__positive/assessment`, InternalServerError.
6,616 documents / 700 completed shards survive. SQLite integrity_check ok; zero pending
requests, 20,679 successful request records and one recorded failed request. Actual
cost $8.59085765, failed-call uncertain upper bound $0.003194. No successful records
were deleted, rewritten or reissued. Supervisor/child are stopped; C4 has not started.

The supervisor drained dispatched work and successfully snapshotted the failed partial
boundary. At diagnosis, main private snapshot e4c912b743c5a74b40acf9f336c9ceeb4e684c68
and corpus snapshot c29adb9acd9e638233c3e36e4c95ce4271238d87 were verified. New diagnosis
report is stored beside run results as failure_diagnosis.json/.md; original raw failure
is in requests.sqlite and log supervised_0001_generate.log.

A compatible restart skips completed shards and reuses recorded successful outputs,
including successful steps of an unfinished shard. It also re-raises the saved failed
assessment: restarting alone does not clear the error. No automatic retry of potentially
billed calls, cache deletion, failed-record overwrite, prompt/code change or recovery
run was performed. Recovery must explicitly preserve the original failure/uncertain
charge, or use a versioned continuation retaining the unavailable assessment. Changed
source/contract requires a fresh ID. This work block diagnoses/preserves the failure;
it does not silently decide the missing-assessment policy.
