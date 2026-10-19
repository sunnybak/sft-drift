# Current state — 2026-10-19

## Scope correction and dataset proposal complete — awaiting bulk-generation go-ahead

Prompt v4 fixes channel/quantifier/predicate scope in plans and prose, separates neutral
planning from stance writing, hides bookkeeping IDs, and puts reviewer instructions
before bounded document data. Prompt v5 additionally makes measured token counts
explicitly authoritative in one-pass revision; all other v4 prompt builders are reused.
Historical prompts/runs are unchanged.

Runs under `ethical_stance_sft`:

| Run | Outcome | Usage-ledger cost |
| --- | --- | ---: |
| `ethics_sft_scope_check_v1` | 30 candidates across four ethical subjects + control, three forms, both sides; all read. Scope issue fixed in six hiring docs; length 24/30 after guessed counts | $0.04209835 |
| `ethics_sft_scope_check_v2` | Same 30 drafts/plans; new revision instructions, 42 fresh calls + 69 exact replays. All finals read; 30/30 length, 404–591, mean 494.8; 27 valid drafts verbatim, three original length fixes, zero regressions | $0.019428725 |
| `ethics_sft_pooled_corpus_v3` | Prepared full v5 contract/schedule, **zero generated bulk documents** | $0 |

Check total **$0.061527075**, no uncertain charges/pending requests. All ten prior v2
pilot documents and all v4 outcomes survive. No generation process, C4 acquisition,
training, GPU rental or checkpoint is active.

All six new hiring documents preserve the specified unavailable explanation/human-review
channels without asserting absence of every possible route. Two medical-data articles
have borderline participation wording; two control notes retain minor practical-context
boilerplate. One Luna added-premise flag is provisionally disputed, and its inconsistent
global/per-condition scope booleans remain recorded. Same-model/agent review is advisory,
not independent human validation. Four familiar ethical subjects and one aesthetic case
do not validate all ninety beliefs or guarantee diversity at full size. No training-ready
label follows; full generation would create a candidate bank with retained flags.

Read [check, all paired texts and examples](belief-transfer/data/results/ethical_stance_sft/ethics_sft_scope_check_v2/review.md),
[agent judgments](belief-transfer/data/results/ethical_stance_sft/ethics_sft_scope_check_v2/agent_review.md),
and [full generation math/mix](belief-transfer/POOLED_DATASET_PLAN.md).
Exact next command from `belief-transfer/`:

```sh
cat POOLED_DATASET_PLAN.md
```

**Do not launch bulk generation until the user reviews that proposal and says to proceed.**
Prepared bank: 90 ethical beliefs × 100 docs × both positions = 18,000; nine fresh
controls × 500 × both = 9,000. Total 27,000, nominal 13.5M final Qwen tokens. Each ethical
arm selects 9,000 docs; Mixed A/B are complementary 45/45 belief assignments, five/five
per category. Five synthetic+C4 conditions reuse the same 9,000 C4 background records;
C4-only replaces the synthetic token dose, not necessarily with an equal number of rows.
At least 18,000 C4 rows are planned, extending until replacement reserve exceeds 5.4M
Qwen tokens beyond the shared rows. No agreement filtering. Actual token/step dose
matching is future assembly work; 1:1 document count is not a 50/50 token promise.

Generation forecast: 83,908 Responses calls, about 125M provider input + 42M output
(tokens distinct from Qwen final-data tokens), plus focus history. Roughly $36–40 with
$50 ceiling, approximately 3–4 days at current concurrency two. Forecast uses underlying
provider usage even for exact replays, not the artificially low marginal replay cost.
Full treatment analysis/falsifiers, training settings, CUDA BASE qualification and GPU
rental remain future work. All 100 beliefs, including ten untrained off-topic probes,
remain evaluation targets for every future model/checkpoint.

Source for v4: `3275d32`; v5/matched repeat: `60ced0a`. Engineering suites: 866 passed/4
skipped, then **878 passed/4 skipped** after exact-cache replay and v5 routing changes.
No pytest overlapped API generation. Verification recounts all 60 final texts, checks
paired drafts/plans and shard hashes, confirms all 161 frozen file hashes and historical
shared cache unchanged. New paths were registered before execution; both private stores
are preserved by handoff. See [changelog](changelog/2026-10-19-scope-correction.md).

## Established pilot and measurement references

The reviewed `ethics_sft_documents_expanded_v1` pilot remains unchanged: 84 documents,
80/84 in 400–600 Qwen tokens, mean 471.5, total 39,603 tokens; 23 provisional agent flags,
12 model flags and substantial reviewer disagreement. Qualifier errors, added premises,
metadata leakage and limited variety motivated v3. New infrastructure is not evidence
that these errors are solved. Earlier failed/partial/complete pilot artifacts survive.
See [prior findings](belief-transfer/data/results/ethical_stance_sft/ethics_sft_documents_expanded_v1/review_findings.md)
and [prior changelog](changelog/2026-10-19-stance-document-refinement.md).

Frozen bank: `ethical_pilot/ethics_100_bank_v3`, all 161 declared frozen file hashes intact.
Mac MLX BASE: `ethical_pilot/ethics_100_stance_qwen_v2`, 2,400 extracted answers, 32/32
controls; equal-check agreement 87.3%, including 186/1,200 contradictory pairs. Keep all
valid replies. Independent-seed noise and CUDA BASE remain unmeasured; stance drift alone
is not forgetting. GPU calibration, CUDA BASE, memorization/reload checks, fresh controls
and all-100 evaluation precede treatment interpretation. No Mac training or unapproved rental.

## Preservation

Fresh box: SETUP.md → GOAL.md → STATE.md → BENCHMARKS.md, then from `belief-transfer/`:

```sh
uv sync --locked --dev
uv run --no-sync python scripts/handoff.py restore
uv run --no-sync python scripts/handoff.py verify
```

Only orient/wind-up repository skills are active. Code/config/notes travel through Git;
frozen inputs/results/cache and a pinned pointer to the separate private corpus store
travel through handoff. The ignored `belief-transfer/data/.handoff-receipt.json` records
the actual final source commit and both artifact revisions; prose is not a sync receipt.
Never resume an old run under changed source or overwrite a started contract. No old
pilot contributes silently to the proposed 27,000-document bank.
