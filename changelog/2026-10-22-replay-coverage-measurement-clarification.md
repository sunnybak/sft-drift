# Measurement clarification before replay-coverage inference

No new model calls or training have occurred. The data pilot is complete. Keep its
original plan/source bindings intact; this clarification is additional prospective
input for preparation, not a rewrite of that record.

The single evaluation seed42 uses the existing retention decoder: thinking temperature
0.6/top_p0.95/top_k20/min_p0; nonthinking temperature0. Only nonthinking is greedy.
The previous plan's phrase "one greedy eval seed42" was imprecise. Neither mode
supplies independent training replication. Keep the existing retention runtime.

Primary value-v1 criteria also retain the existing<=5pp strict-format deficit versus
BASE on the same BASE-value-known cohort and complete boundaries/normal stops across
all128presentations, not just known items. Other thresholds remain as stated.

Supplemental decision bank has64presentations (eight facts/four operation families,
two polarities,two note states,two modes). Use unseen operands from deterministic
seed20261026, held-out instruction wording and a different irrelevant note.
Require at least24/32BASE-known items per mode, all four operation families and both
expected labels. Otherwise report inconclusive; no resampling. Candidate known-value
retention>=95%per mode, all64complete normal stops and exactly parsed final words are
required for adoption. Report note flips and polarity agreement separately. Do not
filter original frozen model checks using this supplemental bank.

These are development investigations after observed failures, not untouched independent
validation of the research program. Original measurement IDs remain fixed.
