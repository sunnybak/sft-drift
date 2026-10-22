# BASE-reasoning replay: rejected; stopped under the user's condition

The fixed final checkpoint fails the prospectively declared acceptance criteria.
The user's instruction was to stop the goal and recommend a direction if the decisive
result was negative. That condition is met. No further tuning, independent confirmation,
checkpoint selection or ethical expansion follows. This is an unsuccessful repair of
this recipe; it does not establish that document SFT is impossible or that base weights
were permanently altered.

## What was trained and verified

Run `ethics_sft_c4_base_reasoning_replay_v1` replaced 32 thinking source targets / 96 draws
with full BASE reasoning. The other 3,529 tokenized chunks and all 454 training steps,
settings and seed stayed fixed. Thinking exposure increased by 28,704 tokens, so this is
not a token-matched comparison. This trial trains C4 plus neutral replay, without ethical
treatment documents. No full 90/100-belief SFT has run.

Training finished in 1,964.43 seconds; all 12 engineering, update and reload checks pass.
The initial adapter, full learning-rate trace, exact chunks and weighted objective
reconstruct. Final and saved step 454 are byte-identical; step 227 is a secondary
checkpoint and was never selected to rescue final. There is only one training seed.

## Final factual decision results

| Facts / wording | Reasoning correct / 32 | Short correct / 32 |
|---|---:|---:|
| Seen / training | 32 | 32 |
| Seen / evaluation | 31 | 30 |
| Held / training | 32 | 21 |
| Held / evaluation | 32 | 22 |

Primary held/evaluation BASE-known retention is **32/32 reasoning, 17/24 short (70.8%)**.
The 95% threshold requires **23/24** short answers. All 256 decision replies have strict
finals, valid boundaries and normal stops. This is a value failure, not a parser failure.
Seen-example learning cannot substitute for held-fact retention. These correlated
variants of a few facts are development diagnostics, not broad independent capability
validation or an estimate of population forgetting.

## Procedural retention and generation

Thinking BASE-known retention is 62/63 and short retention 56/57. Those numeric rates
exceed 95%, but thinking fails the separate complete-generation requirement. On
`2398 - 1147`, the model repeats doubts about `9 - 4 = 5` until 4,096 generated tokens,
without closing its reasoning or producing a final answer. This is a genuine loop.

Another thinking reply spells `LMPBGC` as `LMPCGC`; BASE did not pass that slot, so it is
not a newly lost known item. The short multiplication `1152 × 21` ends `24200` instead
of `24192`. Four other wrong short negations are also outside the BASE-known mask.
Keep all errors, without calling all of them newly lost BASE knowledge.

The subtraction's source `truth_proof.b` metadata says 2198 while its actual prompt says
2398. Independently computed gold 1251 is correct. This metadata discrepancy remains
recorded; no input, gold or historical score was rewritten. It does not explain the loop.

## Model qualification and intentionally partial stance reading

Final development and validation each pass their 32 known-answer controls, with zero
irrelevant-note flips. The separate fresh controls accompanying the full reading score
31/32, but fail note invariance with 1/16 flips. The failed response repeatedly reasons
that `3 × 3 ≠ 8` should be endorsed, then emits `reject`. Extraction is correct.

Initially the recovery controller was intended to finish the whole schedule despite
scientific failures. Once the final-primary failures were reviewed, the user's explicit
stop-on-negative condition took precedence. At **21:34:27 UTC**, the supervisor was
confirmed STOPPED and no GPU compute process remained. No model call or training job
was restarted. The worker's prior STARTED record stays intact; an explicit
`STOPPED_BY_USER_CONDITION` receipt records the intentional cancellation. It is not
relabeled as completed or as an accidental technical failure.

The final full-belief reading records **512/2,400 planned natural replies: 511 valid,
one invalid token-limit loop, and 1,888 not collected**. The invalid placebo reply was
read in full: it initially misstates the deception premise, partially corrects itself,
then repeats discussion until the limit, without a final stance. It stays unscored.
There is **no final full-100 aggregate** and no neutral substitution, completion retry
or claim of full-surface coverage. Earlier development/validation subset readings are
not substitutes for the missing rows.

Midpoint's full-100 reading completed earlier: 2,400 valid replies, all 2,432 runtime
records verified, but failed model qualification and short factual retention. It cannot
rescue final. All midpoint results remain separate.

## Manual review and preservation

Final: all 7 procedural flags, 24 decision flags, 16 preselected reasoning samples,
one fresh-control failure and one invalid natural reply were read completely: **49
request/reply pairs**, with no scorer disagreements. Exact flag/sample coverage and raw
response hashes are verified in `final_reviewed_verdict_v1.json`. This is not manual
reading of all 384 final diagnostic replies or all 512 natural replies.

The one wrong thinking decision computes 219075 correctly but then mishandles the outer
negation. All 16 sampled proof conclusions are correct; one contains an intermediate
585 subtraction error that it independently corrects to 285. Three contain loose phrasing
about an expression being false. Correct final scores do not clear every rationale.
Midpoint review covers 75 diagnostic pairs plus three failed surface controls. Its reject
bias should not be generalized to final, which makes errors in both directions.

All training/checkpoints were already privately saved. Closed final diagnostics comprise
170 copied files. The stopped master, final children, partial reading and console log
comprise 308 copied and hash-verified files; archive SHA-256:
`d9c9d5b5a580a283f61b811c1683a8cf0ba47a2bdc441c50d4ded7bd611966dc`.
The operation log extended append-only after the earlier boundary; its previous prefix
is separately preserved. Raw measurements were not overwritten. Every new JSONL has a
Markdown view. Final private snapshot verification is recorded in the handoff receipt.

## Recommendation

**Reject this recipe and stop the present tuning sequence. Do not lower the gates or
scale ethical training.** Verified training execution is different from demonstrated
preservation of behavior. Mode-dependent answer errors and loops remain; the evidence
does not establish broad erasure of underlying knowledge. Unqualified stance changes
should not be presented as clean ethical-editing effects.

If the user later reopens the study, use a new bounded plan comparing a standard,
independently audited document-SFT baseline against this custom weighted mixed-mode
objective, with a broader frozen retention suite and a declared inference mode. That
would help separate objective/interface effects from the model's response to document
training. This is a recommendation, not an authorized next experiment.
