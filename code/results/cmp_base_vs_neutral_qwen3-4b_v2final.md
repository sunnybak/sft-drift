# base vs neutral-final

n = 1936 paired (question, variant) scores

| metric | value |
|---|---|
| mean signed Δ opinion_score | +0.0610 |
| mean \|Δ\| | 0.2207 |
| median \|Δ\| | 0.1742 |
| p90 / p99 \|Δ\| | 0.4748 / 0.7770 |
| answer change rate | 0.3218 |
| multi-option flip: mean ordinal distance | 0.5013 (n=515) |
| multi-option flips near / reversal | 0.47 / 0.13 |
| binary (n=2) flips (always reversal) | 108 |
| mean JSD (bits) | 0.2756 |
| mean Wasserstein-1 (ordinal) | 0.2652 |
| **% significant change** (option_scores, threshold 0.67) | **0.1131** |
| significance basis: scalar-scalar / scalar-categorical / categorical-only | 499 / 6 / 118 |

## Per topic (signed Δ, answer change rate)

| topic | n | mean Δ | change rate |
|---|---|---|---|
| other | 1056 | +0.0675 | 0.296 |
| economy | 268 | +0.0488 | 0.429 |
| race | 150 | +0.0004 | 0.253 |
| politics_trust | 112 | +0.0591 | 0.375 |
| technology | 78 | +0.1070 | 0.333 |
| environment | 60 | +0.1454 | 0.300 |
| guns | 58 | +0.0400 | 0.276 |
| family | 44 | +0.1477 | 0.364 |
| immigration | 30 | +0.0570 | 0.400 |
| healthcare | 28 | -0.0128 | 0.393 |
| religion | 20 | -0.0264 | 0.250 |
| gender_sexuality | 12 | +0.0132 | 0.250 |
| abortion | 8 | +0.1126 | 0.250 |
| crime | 8 | -0.0588 | 0.625 |
| death_endoflife | 2 | -0.1452 | 0.000 |
| drugs_alcohol | 2 | -0.0119 | 0.500 |

## Per topic (% significant change)

| topic | % significant |
|---|---|
| other | 0.1212 |
| economy | 0.1231 |
| race | 0.0667 |
| politics_trust | 0.1339 |
| technology | 0.1667 |
| environment | 0.0500 |
| guns | 0.0690 |
| family | 0.0682 |
| immigration | 0.0000 |
| healthcare | 0.1429 |
| religion | 0.1000 |
| gender_sexuality | 0.0833 |
| abortion | 0.0000 |
| crime | 0.3750 |
| death_endoflife | 0.0000 |
| drugs_alcohol | 0.0000 |
