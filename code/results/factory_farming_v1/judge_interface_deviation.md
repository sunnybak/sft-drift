# Judge interface deviation

Before any cross-condition analysis or calibration, the first attempted
`factory_farming_judge_v1` run exposed a systematic structured-output
contradiction: GPT-5.5 sometimes set `plant_based_primary=true` while assigning
`animal_product_role` to a value other than `none`. The implementation's frozen
semantic validator rejected this combination, but the same constraint had not
been stated explicitly in the API instruction.

The action-judge version was therefore incremented to
`factory_farming_judge_v1_1_consistency`, and the instruction now explicitly
states the constraint already enforced by the validator. The original paid
responses remain preserved in `judge_cache.jsonl`; the new version has distinct
cache keys and all outputs will be rescored uniformly. No training-condition
labels were exposed to the judge, and no experimental-arm comparison had been
performed when this correction was made.

The same first-pass judging also showed that the model could return several
valid exact evidence spans plus one formatting-normalized span (for example,
omitting Markdown emphasis markers). Evidence postprocessing now discards
non-exact spans, retains exact spans, and continues to reject any positive
judgment with no exact evidence. This changes neither classification labels nor
derived outcomes.

## Cost-motivated judge transition

After 19 of the 34 generation conditions had been judged, the user reviewed the
recorded API cost and authorized an immediate switch for all future action and
opinion judging from GPT-5.5 to `gpt-4o-mini`. The already-paid GPT-5.5
judgments and cache remain preserved and will not be recomputed unless the user
explicitly requests it. The action and opinion judge versions were incremented
to `factory_farming_judge_v2_gpt4o_mini` and
`factory_farming_opinion_judge_v2_gpt4o_mini`; cache keys therefore cannot
silently mix outputs from the two interfaces.

This creates a known scoring-path discontinuity. All 4B conditions were judged
with GPT-5.5, while the remaining 8B directional conditions will be judged with
`gpt-4o-mini`; the previously completed 8B base and first neutral condition
retain GPT-5.5 judgments. The co-primary directional contrasts remain
within-judge at each model size, but cross-size effect comparisons and 8B
comparisons against those earlier controls must be treated as judge-confounded.
Reports must retain per-condition judge-model provenance and state this
limitation.

The user also replaced the planned 400-output API reference calibration with a
blinded offline Codex-chat review. The calibration preparation/finalization
script now contains no OpenAI client or API-call path. This review is neither
human calibration nor independent API-model calibration, and the writeup must
use that narrower description.
