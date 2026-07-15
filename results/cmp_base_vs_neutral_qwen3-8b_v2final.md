# base vs neutral-final

n = 1936 paired (question, variant) scores

| metric | value |
|---|---|
| mean signed Δ opinion_score | +0.1257 |
| mean \|Δ\| | 0.2845 |
| median \|Δ\| | 0.2991 |
| p90 / p99 \|Δ\| | 0.4998 / 0.6133 |
| answer change rate | 0.3394 |
| multi-option flip: mean ordinal distance | 0.5454 (n=501) |
| multi-option flips near / reversal | 0.34 / 0.16 |
| binary (n=2) flips (always reversal) | 156 |
| mean JSD (bits) | 0.3141 |
| mean Wasserstein-1 (ordinal) | 0.3373 |
| **% significant change** (option_scores, threshold 0.67) | **0.1684** |
| significance basis: scalar-scalar / scalar-categorical / categorical-only | 441 / 5 / 211 |

## Per topic (signed Δ, answer change rate)

| topic | n | mean Δ | change rate |
|---|---|---|---|
| other | 1056 | +0.1264 | 0.348 |
| economy | 268 | +0.1088 | 0.366 |
| race | 150 | +0.0897 | 0.307 |
| politics_trust | 112 | +0.1781 | 0.348 |
| technology | 78 | +0.1330 | 0.179 |
| environment | 60 | +0.1811 | 0.400 |
| guns | 58 | +0.1436 | 0.345 |
| family | 44 | +0.1382 | 0.318 |
| immigration | 30 | +0.0940 | 0.333 |
| healthcare | 28 | +0.0714 | 0.214 |
| religion | 20 | +0.1099 | 0.400 |
| gender_sexuality | 12 | +0.1314 | 0.333 |
| abortion | 8 | +0.3686 | 0.500 |
| crime | 8 | -0.0104 | 0.250 |
| death_endoflife | 2 | -0.2980 | 0.000 |
| drugs_alcohol | 2 | +0.3924 | 0.000 |

## Per topic (% significant change)

| topic | % significant |
|---|---|
| other | 0.1979 |
| economy | 0.1493 |
| race | 0.1333 |
| politics_trust | 0.1071 |
| technology | 0.1410 |
| environment | 0.2000 |
| guns | 0.1034 |
| family | 0.1136 |
| immigration | 0.1000 |
| healthcare | 0.1429 |
| religion | 0.0500 |
| gender_sexuality | 0.0833 |
| abortion | 0.2500 |
| crime | 0.0000 |
| death_endoflife | 0.0000 |
| drugs_alcohol | 0.0000 |
