# Current state — 2026-10-19

## Full candidate-bank generation authorized and started

User chose **ten fresh off-topic claims × 100 documents per position**, matching each
ethical claim's generation count. These are separate from the ten frozen evaluation
preferences. Ethical source: 90 × 100 × two = 18,000; control source: 10 × 100 × two =
2,000; total **20,000**, nominal **10M Qwen tokens**, requested 400–600 per document.
Smaller control breadth/unique-example count is not a generation blocker. Before SFT,
position selection and explicit sampling/reuse must match training tokens/steps; do not
pretend the smaller raw control bank is already a matched treatment mixture.

Current bank: **`ethics_sft_pooled_corpus_v4`**, prompt v5. The user said **begin**.
Initial shard completed: **10/20,000** documents, 422–574 Qwen tokens, no mechanical
flags, 33 fresh generation calls, **$0.0131741**, zero errors/pending requests and SQLite
integrity_check ok. First opposing pair inspected; this is not bank acceptance or full
human review. Older v1–v3 contracts remain preserved and cannot resume under changed code.

The continuous supervisor runs at most 500 shards per invocation, then snapshots both
private stores. After synthetic generation it acquires the specified C4 pool. It stops
on stage or snapshot failure, with no automatic failed-request retry. Actual PID, child
command/log and phase are in
`belief-transfer/data/results/ethical_stance_sft/ethics_sft_pooled_corpus_v4/generation_job.json`.
Console log: `/tmp/ethics_sft_pooled_corpus_v4.supervisor.log`. Stage logs: `supervised_*.log`
in that results directory. First completed shard is saved before the continuous launch;
new active output is local until the next successful handoff boundary. No training,
GPU rental or checkpoint is authorized or active. A process cannot survive destruction
of this Mac; explicit restart must first check the PID/child and unresolved ledger.

New configurations have **no hard dollar ceiling**. Historical pilot limits/cache keys
are unchanged. Generation ledgers still record actual/uncertain charges. New scheduling:
configurable HTTP concurrency, parallel independent subject/form groups, shared form
locks, serial focus history within a group, per-shard staging and failure draining.
Rate gate: **8,000 HTTP RPM / 8M reserved TPM**, 80% of user-supplied limits. Exact provider
input counts plus bounded output are reserved, with logged conservative byte fallback.
Counting requests also consume HTTP permits. Production capacity is 384 client operations
and 64 batches; that sustained setting is **unmeasured**. Other account traffic is outside
this limiter. No automatic generation retry after unknown billing.

| Throughput check | Fresh generation/count calls | Wall time | Usage tokens/min | Generation cost |
| --- | ---: | ---: | ---: | ---: |
| `ethics_sft_throughput_check_v1`, 10 workers | 201 / 201 | 130.46s | 175,607 | $0.0806277 |
| `ethics_sft_throughput_check_v2`, 64 workers | 201 / 201 | 44.71s | 511,525 | $0.0805469 |

Each check produced 60 documents in 15 shards, separate from production. All 402 count
preflights matched returned input usage exactly; no API errors, uncertain charges or
pending journal records. SQLite integrity and shard hashes pass. Total generation cost
**$0.1611746**. Peak simultaneous generation calls: ten and 60. First check retains one
335-token final (59/60 in range); second has 60/60 in range. These are throughput checks,
**not a full agent content review**. No acceptance/training-ready claim follows.

Forecast: 62,201 generation calls + up to 62,201 count requests; 94.0M provider input +
31.9M output, plus 5.8M focus-history input proxy. Cold cache-write pricing projects
**$28.41**, without a hard ceiling. Request-only floor 15.55min; conservative reservation
TPM floor 25.33min. ~231 concurrent generation calls plus counting latency are needed
near that gate. These are capacity calculations, not a measured full-run ETA.

Read [current counts/mixes](belief-transfer/POOLED_DATASET_PLAN.md) and
[math/benchmark report](belief-transfer/data/results/ethical_stance_sft/ethics_sft_pooled_corpus_v4/report.md).
Read current live status from `belief-transfer/`:

```sh
cat data/results/ethical_stance_sft/ethics_sft_pooled_corpus_v4/generation_job.json
```

Exact supervisor command (launch once; check existing PID/child before explicit restart):

```sh
caffeinate -i uv run --no-sync python scripts/run_stance_corpus_generation.py --run-id ethics_sft_pooled_corpus_v4 --batches-per-invocation 500 --include-background
```

Four ethical arm selections remain 9,000 docs each: all positive, all negative,
complementary Mixed A/B (five/five per ethical category). Shared C4 background: 9,000
full records. C4 pool: at least 18,000, extending until replacement reserve beyond the
shared rows supplies 5.4M Qwen tokens. Actual token/step matching, control position
selection/reuse, training settings and treatment analysis/falsifiers remain future work.
All 100 beliefs are evaluated on every future model/checkpoint.

## Established quality and measurement references

Scope correction: `ethics_sft_scope_check_v1` (v4) and matched `v2` (v5), 30 fixed drafts.
All finals read; v5 improved length 24/30→30/30, preserving all 27 valid drafts verbatim.
Six hiring documents preserve scoped recourse exclusions. Borderline medical-data
participation wording, control boilerplate and reviewer disagreements remain explicit.
Combined cost $0.061527075. These reused development examples are not independent
validation. The earlier 84-document expansion remains preserved (80/84 in range).
See [scope review](belief-transfer/data/results/ethical_stance_sft/ethics_sft_scope_check_v2/review.md).

Frozen bank: `ethical_pilot/ethics_100_bank_v3`, all **161 hashes unchanged**.
Mac MLX BASE: `ethics_100_stance_qwen_v2`, 2,400 extracted answers, 32/32 controls;
87.3% equal-check agreement, including 186/1,200 contradictory pairs. Retain valid replies.
CUDA BASE, independent-seed variability, calibration and memorization/reload checks remain
unmeasured and precede treatment interpretation. No Mac training or unapproved rental.

## Preservation

**Prior engineering suite: 891 passed / four skipped; new supervisor checks: four passed**. Current engineering and verification details are in
[launch changelog](changelog/2026-10-19-corpus-generation.md) and
[throughput changelog](changelog/2026-10-19-corpus-throughput.md). Tests and live generation ran
separately. Source/config/notes must be committed and pushed; handoff includes both the
main private store and separate corpus store. The ignored
`belief-transfer/data/.handoff-receipt.json` records actual final commits/revisions;
prose is not a snapshot receipt. Never overwrite a started contract.

Fresh box: SETUP.md → GOAL.md → STATE.md → BENCHMARKS.md; from `belief-transfer/`:

```sh
uv sync --locked --dev
uv run --no-sync python scripts/handoff.py restore
uv run --no-sync python scripts/handoff.py verify
```
