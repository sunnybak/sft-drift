# Proposed full document bank and mixtures

This is the dataset-generation proposal for `ethics_sft_pooled_corpus_v3`, using prompt
v5. Bulk generation remains unstarted pending the user's review of this math/mix.
The 30-document scope check is a separate pilot and is not counted into this bank.
Training schedule, epochs, optimizer steps, GPU rental and final treatment analysis
remain outside this generation proposal.

## Unique synthetic source bank

| Source | Calculation | Documents | Nominal Qwen tokens at 500/document |
| --- | --- | ---: | ---: |
| Ethical, supporting | 90 beliefs × 100 | 9,000 | 4.5M |
| Ethical, opposing | 90 beliefs × 100 | 9,000 | 4.5M |
| Fresh aesthetic controls | 9 subjects × 500 × 2 positions | 9,000 | 4.5M |
| Total generated once | | **27,000** | **13.5M** |

Each ethical belief has 200 source documents, 100 per position. An ethical training arm
selects 100 of them for that belief's assigned position. The ten off-topic beliefs in
the frozen 100-belief evaluation bank are not trained. The nine fresh training-control
subjects are separate, with 500 documents per position each.

Length target: 500 Qwen3-4B tokens, requested range 400–600, without the intended prefix.
The 27,000-document bank would contain 10.8–16.2M tokens if all candidates meet that
range. A flagged out-of-range candidate remains recorded; do not silently clip/drop it
or imply the requested range was enforced by rejection sampling.

For each belief/position: three forms with 34/33/33 examples, rotated by subject.
Opposing positions share every specific idea and factual premise. For each control
position: 167/167/166 examples. Generation is independent across assigned positions.

## Six prospective SFT conditions plus BASE

| Condition | Synthetic selection | Shared C4 background | Mix by document count |
| --- | --- | --- | --- |
| All positive | 90 × 100 positive = 9,000 | Same 9,000 records | 1:1 |
| All negative | 90 × 100 negative = 9,000 | Same 9,000 records | 1:1 |
| Mixed A | 45 beliefs positive + 45 negative; 100 docs each = 9,000 | Same 9,000 records | 1:1 |
| Mixed B | Exact opposite assignment for every Mixed A belief = 9,000 | Same 9,000 records | 1:1 |
| Fresh off-topic control | 9,000 aesthetic documents, balanced between positions | Same 9,000 records | 1:1 |
| C4-only control | None | Shared 9,000 plus an additional C4 reserve supplying the synthetic portion's token dose | 100% C4; final row count depends on measured lengths |

Mixed assignment is seed 42, five positive/five negative beliefs within each of the nine
ethical categories. Each belief gets one consistent direction in each mixed arm; this
is not 50 positive and 50 negative examples within every belief. All four ethical arms
reuse the same 18,000-document source bank. They do not require four separately generated
banks. Every ethical source document appears in two of the four arm manifests.

Untouched CUDA BASE is the reference, not a seventh generated dataset. All 100 beliefs
are evaluated on every fine-tune/checkpoint, with model controls. Training-seed replication
reuses these source documents; it does not multiply generation cost. Controls must still
be retrained per training seed. A proposal of three seeds would mean 18 fine-tunes;
no seed count or training run is launched by this generation proposal.

## C4 pool and token accounting

Stream full unique English training records from `allenai/c4`, pinned revision
`1588ec454efa1a09f29cd18ddd04fe05fc8653a2`, seed 42, shuffle buffer 1,024. No agreement
or topic filter. Preserve full text, URL, timestamp, hashes, selected ordinal, stream
index and measured Qwen counts. No full C4 download.

The initial pool target is **at least 18,000 unique C4 records**. The first 9,000 form
the shared background for all conditions. Continue acquisition beyond 18,000 if needed
until the remaining records contain **at least 5.4M Qwen tokens** of replacement reserve
(9,000 × the requested 600-token upper bound). This avoids assuming a C4 document has
500 tokens. The reserve is a capacity safeguard, not the final loss dose; verify its
sufficiency against actual synthetic totals, including explicit length failures.

Let B be the measured token total of the shared 9,000 C4 records and S_i the measured
synthetic token total selected for condition i. That condition's raw corpus has
**S_i + B tokens**, with S_i nominally 4.5M (requested range 3.6–5.4M). Its synthetic
token fraction is S_i/(S_i+B), not necessarily 50%. If B happened to be 4.5M, the nominal
corpus would contain 9M tokens; that is an example, not an assumption about C4.

C4-only must supply the same declared effective training-token/step budget using C4
instead of synthetic prose. Actual lengths must determine assembly and the common dose
before SFT; a 1:1 document ratio alone does not dose-match training. Keep full source
records and explicit masks/coverage rather than silently truncating documents. This
stage does not implement the training loss or claim matched exposure already occurred.

## Generation work

- 13,500 shared ideas: 9,000 ethical pairs + 4,500 control pairs.
- 99 form-planning calls, each planning all three forms for a subject.
- 2,808 bounded idea-planning calls (up to five ideas each).
- 27,000 × (draft + one revision + separate assessment) = 81,000 calls.
- One generation canary: **83,908 prospective Responses calls total**.
- Default concurrency two, `gpt-6-luna`, reasoning disabled, provider-default sampling,
  no automatic network retries. Seed 42 determines schedules/assignments, not API prose.

The 13.5M source-bank Qwen tokens are not the provider generation-token bill. That bill
also includes drafts, critiques, all prompt inputs, planning and assessments, using the
provider's tokenizer. An empirical phase-by-phase forecast follows the scope check.

## Budget and storage

The proposed full-generation ceiling is **$50**, independent of pilot costs. It is a
hard stop preserving completed outcomes, not a guarantee all 27,000 finish. No bulk
spend has been authorized by preparation. C4 acquisition uses no generation-model tokens.

Verified standard short-context rates for GPT-6 Luna: $0.10/M input, $0.01/M cache-hit
input, $0.125/M cache-write input, $0.50/M output. Forecast cost:
`(0.10 × regular_input + 0.01 × cache_hits + 0.125 × cache_writes + 0.50 × output)/1e6`.
See [official model pricing](https://developers.openai.com/api/docs/models/gpt-6-luna),
checked 2026-10-19. Cache categories partition total input; do not double-count them.

Store unique corpus shards, raw requests/responses and the durable SQLite journal in
private `sunnybak/sft-drift-ethical-corpus`, with a pinned pointer in the main study
snapshot. Arm manifests reference the shared bank instead of duplicating generated
prose. Both remote and portable local snapshots remain supported. No automatic
training-ready designation, corpus expansion or training follows from a passing pilot.
