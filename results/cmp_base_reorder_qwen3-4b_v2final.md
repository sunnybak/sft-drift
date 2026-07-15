# original-order vs shuffled-order

n = 968 paired (question, variant) scores

| metric | value |
|---|---|
| mean signed Δ opinion_score | -0.0224 |
| mean \|Δ\| | 0.1039 |
| median \|Δ\| | 0.0000 |
| p90 / p99 \|Δ\| | 0.3426 / 1.0000 |
| answer change rate | 0.1808 |
| multi-option flip: mean ordinal distance | 0.4559 (n=136) |
| multi-option flips near / reversal | 0.56 / 0.10 |
| binary (n=2) flips (always reversal) | 39 |
| mean JSD (bits) | 0.1511 |
| mean Wasserstein-1 (ordinal) | 0.1043 |
| **% significant change** (option_scores, threshold 0.67) | **0.0630** |
| significance basis: scalar-scalar / scalar-categorical / categorical-only | 127 / 2 / 46 |

## Per topic (signed Δ, answer change rate)

| topic | n | mean Δ | change rate |
|---|---|---|---|
| other | 528 | -0.0310 | 0.178 |
| economy | 134 | -0.0090 | 0.187 |
| race | 75 | -0.0050 | 0.200 |
| politics_trust | 56 | -0.0436 | 0.250 |
| technology | 39 | -0.0054 | 0.154 |
| environment | 30 | -0.0039 | 0.067 |
| guns | 29 | -0.0216 | 0.069 |
| family | 22 | +0.0008 | 0.273 |
| immigration | 15 | -0.0260 | 0.333 |
| healthcare | 14 | +0.0577 | 0.071 |
| religion | 10 | +0.0371 | 0.100 |
| gender_sexuality | 6 | -0.1377 | 0.333 |
| abortion | 4 | -0.0002 | 0.000 |
| crime | 4 | +0.0181 | 0.250 |
| drugs_alcohol | 1 | -0.4404 | 1.000 |
| death_endoflife | 1 | -0.0000 | 0.000 |

## Per topic (% significant change)

| topic | % significant |
|---|---|
| other | 0.0701 |
| economy | 0.0746 |
| race | 0.0933 |
| politics_trust | 0.0536 |
| technology | 0.0256 |
| environment | 0.0000 |
| guns | 0.0000 |
| family | 0.0455 |
| immigration | 0.0000 |
| healthcare | 0.0714 |
| religion | 0.0000 |
| gender_sexuality | 0.1667 |
| abortion | 0.0000 |
| crime | 0.0000 |
| drugs_alcohol | 0.0000 |
| death_endoflife | 0.0000 |
