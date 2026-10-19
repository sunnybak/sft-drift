# Current full document bank and mixtures

The user selected **ten fresh training-control claims and 100 documents per position**,
matching the per-belief ethical setting. Current prepared run:
`ethics_sft_pooled_corpus_v4`, prompt v5. No bulk documents have been generated.
Earlier v1–v3 contracts, pilots and forecasts remain historical artifacts. Changed
source/contract settings require a fresh ID; do not resume v3 with current code.

## Source bank

| Source | Calculation | Unique documents | Nominal Qwen tokens |
| --- | --- | ---: | ---: |
| Ethical, supporting | 90 × 100 | 9,000 | 4.5M |
| Ethical, opposing | 90 × 100 | 9,000 | 4.5M |
| Fresh off-topic preferences, both positions | 10 × 100 × 2 | 2,000 | 1M |
| Total | | **20,000** | **10M** |

The ten fresh aesthetic training claims are separate from the ten frozen evaluation
preferences. Those evaluation preferences stay untrained. The tenth fresh control is
embossed versus flat decorative paper. The former nine × 500 × two proposal matched
9,000 control rows but concentrated exposure on few topics; it was not a scientific
requirement. Ten × 100 is the user's chosen smaller control bank. Topic breadth remains
unmatched, a limitation rather than a data-generation blocker.

Each subject has three forms (34/33/33 ideas) shared across positions. Draft, one critique
and revision, and separate same-model assessment are preserved. Target 500 Qwen tokens,
requested range 400–600; nominal bank range 8–12M. No rejection sampling, clipping or
silent removal of defective candidates. Prior scope checks and agent judgments remain
development evidence, not independent human validation or training-ready certification.
The 30-document v5 check and its matched v4 comparison remain separate from this bank.

## Prospective treatment conditions

All positive, all negative, Mixed A and complementary Mixed B each select **9,000**
ethical documents (100 per belief). Mixed A assigns five positive/five negative beliefs
within each ethical category; Mixed B flips all assignments. These arms reuse the same
18,000-document source bank. They do not multiply generation cost.

The fresh off-topic control draws from **2,000 unique candidates**, not 9,000. Its final
position selection and sampling/repetition must be declared before SFT to match ethical
loss-bearing tokens and optimizer steps. Choosing one consistent position per control
claim gives 1,000 selected unique documents; using both positions gives 2,000 but changes
within-topic consistency. Neither selection is silently fixed by generation. Reuse must
be reported explicitly; extra draws are not new independent examples. A C4-only control
replaces synthetic token exposure, with untouched CUDA BASE as reference. Training seeds,
steps, epochs, hypothesis/contrasts/falsifiers and dose matching remain future work.

The four ethical raw mixtures reference the same **9,000 C4 records**, hence 1:1 by
row count. That ratio does not establish 50/50 tokens. The smaller raw control bank plus
9,000 background rows is **not** a matched training mixture yet. Do not train these
previews as if they already establish the final control dose.

Stream pinned `allenai/c4` English train revision
`1588ec454efa1a09f29cd18ddd04fe05fc8653a2`, seed 42, bounded shuffle 1,024. Preserve full
text/provenance/hashes, with no agreement filter. Acquire at least 18,000 unique records;
extend until records beyond the first 9,000 supply 5.4M Qwen tokens of replacement reserve.
Actual token totals determine final assembly. No new C4 acquisition has run.

## Generation spend and throughput

Full bank: **62,201 generation calls** = one canary + 100 form plans + 2,100 idea batches
+ 20,000 × three document phases. Exact input counting adds up to 62,201 HTTP requests
on a fully fresh run, for **124,402 HTTP requests**. Exact local replays add neither.

Role/phase-weighted prior usage projects **94.0M provider input + 31.9M output** tokens,
plus a conservative 5.8M input focus-history proxy. These are different from final Qwen
training tokens. Charging every input token at the higher cache-write rate projects
**$28.41** including that history proxy. This is an estimate, **not a price ceiling**.
Actual and uncertain charges remain recorded. Historical pilot dollar limits are intact;
new configurations set `budget_usd: null`.

User limits: 10M TPM / 10,000 RPM. At 80%, the dispatcher permits **8M reserved tokens/min
and 8,000 HTTP requests/min**. Counting requests also consume a request permit. Generation
reserves exact provider input count plus maximum output; if counting fails, it falls
back to UTF-8 bytes plus protocol overhead and logs the error. This deliberately exceeds
the documented max(input estimate, output cap) accounting. A smooth dispatch schedule
and rolling-minute checks prevent bursts. Failed generation is retained without automatic
retry. Other processes sharing the account are outside this limiter.

At the old 5.64s mean generation latency, concurrency ten gives about **106 generation
calls/min**, roughly **9.74 hours** for 62,201 calls before counting latency, pacing and
planning overhead. The request-only theoretical floor is **15.55 minutes** including
counting calls. Conservative token reservations project **202.6M**, a **25.33-minute**
TPM-only floor. Reaching that token gate needs approximately **231 concurrent generation
calls**, plus capacity for count latency. These are capacity calculations, not a measured
full-run ETA. Initial benchmark configurations use ten and 64 workers. The prepared
production configuration allows 384, with 64 independent batches, while the shared rate
gate controls dispatch. Production saturation at that setting remains unmeasured; provider
ramp/overload behavior, planning dependencies, tail latency, CPU and disk can increase runtime.

Opposing documents share plans; all ideas in a batch may progress. Independent subject/form
groups run concurrently, but each group's later ideas see its earlier completed focuses.
A subject lock prevents duplicate form-plan dispatch. Failed groups stop new batches and
drain already dispatched work before releasing SQLite and the run lock. Each shard has
its own staging directory and is committed atomically. Concurrency/rate settings are
recorded in the contract; historical cache identities remain unchanged.

See the current run's `generation_math.json` for arithmetic and the separate throughput
checks for measured wall time. Bulk generation, corpus acceptance, training and evaluation
are separate steps. Every future model/checkpoint still evaluates all 100 frozen beliefs.
