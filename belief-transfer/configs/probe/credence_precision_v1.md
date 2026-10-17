# Frozen-bank repeatability — unregistered precision diagnostic

The v7 hosted pilot and exact retest both pass all controls. Their six mean Conviction
values differ by 0.005–0.04, but matched presentation gaps remain too large to meet
the frozen absolute-stability contract. Neither is qualified under that contract.

Before further prompt changes, repeat the unchanged v7 instrument twice on the same
six development topics, all six reviewed wordings and both existing queries. Each fresh
run contains 504 presentations: 216 controls and 288 natural cells (48 per belief).
Both runs use provider-default sampling with cache disabled. No held-out topics,
SFT checkpoints, new belief definitions or ethical gold labels are consumed.

Contrast: second run minus first run, matched by frozen presentation identity. Report
the mean difference per belief, mean/max absolute item difference, direction agreement,
both control gates and both original stability statuses. Bootstrap paired wording-group
means with seed 42 and 10,000 draws for a descriptive 95% interval around each
fixed-bank mean difference. Before inspecting the full-run results, the initial row-level
resampling proposal was corrected to the belief wording: average the eight paired presentation differences
within each wording, then resample the six wording groups. This follows the repository's
rule against treating variants of one item as independent observations. The interval
describes variation across those groups in these two runs; it does not cover future
runs, models or moral-truth uncertainty. Even wordings share a canonical definition,
so this is a descriptive interval, not a universal precision guarantee.

Do not rewrite the prior stability thresholds, suppress individual sensitive cells,
promote the candidate from a reproducible average, or claim a universal detection limit
from two runs. This study estimates same-model numerical variation under the frozen
benchmark, a needed diagnostic for future before/after comparisons. If it is small,
follow with more independent repeats and held-out topics before a new prospective
aggregate-measurement acceptance contract. The current release gate remains unchanged.
