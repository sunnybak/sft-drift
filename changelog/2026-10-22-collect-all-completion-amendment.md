# Prospective completion rule for the replay-weight full100 readings

Written while fresh norm1 is still training, before either new model's ethical
evaluation. Neither retention outcomes nor ethical scores from the new models have
been observed. Weight32, normalization, LR, seed, steps, final-only selection and
retention acceptance remain unchanged. Do not change the bound live GPU source.

## Collection risk found by code inspection

Both qualified full100 configs inherit measurement_control_failure_policy=skip.
In stages/measurements.py, a fresh control failure can therefore skip all natural
calls even after development/validation passed. The outer worker currently checks
the process return code, which can be zero with a complete summary but zero natural
observations. Its COLLECTION_COMPLETED marker is not evidence of full100coverage.
The unqualified route has no validation bundle and already collects natural calls.
This is a collection edge case, not evidence that the running model has degraded.

## Fixed completion rule, not a quality-based rerun

After the fixed worker terminates, count actual unique recorded presentations in
each new model's original 2,400-item natural grid. Reconstruct frozen summaries and
retain every original observation, missing reply and failed control.

- If both original grids recorded all 2,400 presentations, no completion calls.
  Invalid answers, failed controls, retention failures or undesired ethical scores
  NEVER trigger an additional reading of an already collected grid.
- If either grid omitted natural calls, administer exactly one new complete-grid
  reading to BOTH fixed final models, using fresh IDs below, seed42, the identical
  frozen bank/extractor/scorer/decoder/backend and collect_unqualified policy.
  Preserve original qualification evidence; if its validation passed, carry the
  same validation chain, but collect all natural calls even if fresh controls fail.
  Failures remain explicit. No second completion attempt or repeat until pass.
- If an engineering/source/adapter failure prevents either model completing, retain
  partial work and reassess before a paired completion; do not invent missing models.

Fresh IDs: ethics_gpu_replay_weight_norm1_completegrid_s42_v1 and
ethics_gpu_replay_weight_weight32_completegrid_s42_v1. Register both generated/result
paths before preparation/execution AFTER the live bound worker terminates. Freeze
configs, source, actual adapters, the triggering coverage evidence and this rule in
a new execution manifest; commit/push/private-save before new calls. This prospective
amendment does not alter the running worker or pretend it supports resume.

Report original attempts and any matched completion cohort separately. Full-grid
missing-response bounds remain distinct from uncertainty. A new reading uses fresh
responses even at the same request seed; do not claim deterministic reproduction.
Recipe selection remains procedural retention/engineering, never ethical direction.
The mechanical comparison flags full-response review pending and cannot qualify a
recipe or establish broad capability preservation by itself.
