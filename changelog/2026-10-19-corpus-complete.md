# 2026-10-19 — full candidate bank completed

`ethics_sft_pooled_corpus_v5` completed all 2,100 planned shards and the C4 pool.
Supervisor phase `completed`, return code 0, child PID null, completion 20:47 UTC.
Source at launch: `fa5ec067ed0a2301d76081907fe8aa82d998f6cc`. No training ran.

- Synthetic: 20,000 candidates, 100 per position for 100 training subjects; 9,800,659
  Qwen tokens; mean 490.03295, min 211, max 628. Requested range compliance 19,583/20,000.
- C4: 20,634 unique full records, 9,774,947 Qwen tokens. Shared first 9,000 rows total
  4,372,705 tokens; remaining 11,634 provide 5,402,242 replacement tokens. Same pinned
  revision/seed/buffer as the contract. No agreement-based filtering.
- Automated findings: possible factual additions 1,106; repetitive 81; length 417;
  scope 43; explicit position 16; form 8; conclusion 9; visible task metadata 92.
  These overlap and remain provisional; full-bank agent/human content review is pending.
- Cumulative lineage spend $25.89367392; inherited $8.59085765; marginal $17.30281627.
  Uncertain failed-attempt upper bound $0.08217, not claimed as actual billing.
  Historical v4 is included once and remains unchanged; earlier pilots are separate.

Completion verification checks every synthetic shard's declared file hashes, C4 JSONL
hashes, text and draft hashes, unique document IDs, 100-per-subject-position coverage,
shared opposite-position idea/form identity, unique C4 identities/revision, SQLite
integrity and zero pending requests, and all 161 frozen hashes. Exact verification
counts and automated findings are in the derived JSON/Markdown completion report.
No ML tests were rerun for documentation/derived-report changes; prior shared-change
suite was 911 passed/four skipped plus one later targeted test.

The supervisor already verified both private stores. This work block updates current
study notes and saves the completion report in a new snapshot after committing/pushing.
Receipt `belief-transfer/data/.handoff-receipt.json` is the authoritative revision record.
Nothing is designated training-ready. Next: review pairs and automated flags, record
reviewer disagreements, then declare token/step-matched training assembly and experiment
plan. CUDA qualification, BASE repeats and memorization/reload checks precede SFT.
