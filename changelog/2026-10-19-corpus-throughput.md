# Corpus scheduling, rate math and smaller control bank

User questioned nine × 500 × both controls, removed the price ceiling, supplied Luna
10M TPM / 10,000 RPM, and requested 80% rate scheduling. After discussion, user chose
**ten fresh off-topic controls × 100 documents per position**; no 90-topic expansion.
New current bank `ethics_sft_pooled_corpus_v4`: 100 subjects × 100 × both = 20,000
candidates, 2,100 batches, zero bulk generated. Tenth fresh control: embossed vs flat
paper panel. Frozen ten evaluation preferences remain untrained. Raw control source is
2,000, not 9,000; future token/step matching requires declared selection/reuse, with
narrower breadth acknowledged. It is not a generation blocker.

Typed scheduling fields permit parallel batches, provider token counting, RPM/TPM and
utilization ≤ .8. Dollar limit accepts None; new configurations use it, historical
limits unchanged. Client/cache request identities and prices are unchanged. Smooth
HTTP pacing and rolling 60s windows apply to count requests and generation. Exact input
count plus output cap is deliberately conservative relative to documented max accounting;
count failure falls back to byte bound. Exact preflight results/timings/reservations
are saved with raw responses. No generation auto-retries. Shared form-plan locks prevent
duplicate dispatch; same subject/form focus history stays serial; independent groups
progress concurrently; all ideas can progress; batch staging paths are unique. Failed
groups stop new batches and drain already dispatched work before closing SQLite.

Bounded live checks registered before execution, each four ethical subjects + one fresh
control, six ideas × two positions = 60 documents, three forms, 15 batches:

- `ethics_sft_throughput_check_v1`, ten workers: 130.4596s, 201 fresh generation calls,
  201 count requests, no local replays. $0.0806277. Usage 287,690 input / 94,137 output.
  Mean generation latency 5.6102s; peak ten live generation calls. 59/60 in range,
  one retained 335-token final; mean length 492.63.
- `ethics_sft_throughput_check_v2`, 64 workers: 44.7118s, 201 + 201 fresh requests,
  no local replays. $0.0805469. Usage 287,387 input / 93,800 output. Mean latency
  5.6636s; peak 60 live generation calls; all 60 in range (400–578, mean 486.18).

All 402 provider preflight counts exactly matched response input usage. No generation
errors, uncertain charges or pending records. Total generation cost $0.1611746; both
SQLite journals integrity_check ok. All shard hashes, Markdown derivatives and current
contracts/source agree. All 161 frozen hashes unchanged. Throughput documents have not
received full agent content review and are not included in production. 2.92× finite
wall speedup does not establish steady-state saturation. Production allows 384 operations
and 64 batches, subject to 8k HTTP RPM / 8M reserved TPM; sustained performance and
provider ramp/overload behavior remain unmeasured. Other account traffic is outside gate.

Updated full-bank math: 62,201 generation + up to 62,201 counting requests. Prior
role-weighted profile: 94.04M input / 31.86M output + 5.80M focus-history input proxy.
Cold cache-write forecast $28.41, **no hard price ceiling**. Conservative reservations
202.62M; RPM-only floor 15.55min, TPM-only floor 25.33min. ~231 concurrent generation
calls plus count latency needed near the token gate. These are capacity calculations,
not full-run forecasts. Per-run reports, generation_math.json, raw SQLite requests,
launcher timings and logs are under registered results/corpus roots. A read-only report
script reproduces summaries from explicit timing inputs. No C4/training/rental ran.

Verification: first regression suite 884 passed / four skipped; narrowed final client/
scheduler suite 67 passed. A final full suite including uneven reservation windows,
ten-control count composition and parallel failure-drain checks runs before preservation;
its result is recorded below. Tests never overlapped live generation or experimental
artifact writes. Source/config/notes and both private artifact stores are saved per
handoff; the receipt records actual revisions, not this prose.

Final full suite: **891 passed, four skipped in 161.66s**. No tests overlapped live calls
or result writes. Current source/contract and 161 frozen hashes verified; all JSONL
Markdown views and completed-shard hashes match.
