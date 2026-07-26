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
