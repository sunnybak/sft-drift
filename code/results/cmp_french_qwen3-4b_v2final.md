# baseline-en vs baseline-fr

n = 1936 paired (question, variant) scores

| metric | value |
|---|---|
| mean signed Δ opinion_score | +0.0215 |
| mean \|Δ\| | 0.1395 |
| median \|Δ\| | 0.0007 |
| p90 / p99 \|Δ\| | 0.4910 / 0.9999 |
| answer change rate | 0.2515 |
| multi-option flip: mean ordinal distance | 0.4812 (n=416) |
| multi-option flips near / reversal | 0.54 / 0.14 |
| binary (n=2) flips (always reversal) | 71 |
| mean JSD (bits) | 0.2132 |
| mean Wasserstein-1 (ordinal) | 0.1406 |
| **% significant change** (option_scores, threshold 0.67) | **0.0754** |
| significance basis: scalar-scalar / scalar-categorical / categorical-only | 399 / 5 / 83 |

## Per topic (signed Δ, answer change rate)

| topic | n | mean Δ | change rate |
|---|---|---|---|
| other | 1056 | +0.0357 | 0.253 |
| economy | 268 | +0.0339 | 0.257 |
| race | 150 | +0.0174 | 0.320 |
| politics_trust | 112 | -0.0254 | 0.241 |
| technology | 78 | +0.0065 | 0.231 |
| environment | 60 | +0.0513 | 0.183 |
| guns | 58 | -0.0385 | 0.155 |
| family | 44 | -0.0196 | 0.318 |
| immigration | 30 | +0.0175 | 0.133 |
| healthcare | 28 | -0.0983 | 0.143 |
| religion | 20 | -0.1044 | 0.200 |
| gender_sexuality | 12 | +0.0414 | 0.417 |
| abortion | 8 | -0.0116 | 0.125 |
| crime | 8 | -0.1105 | 0.500 |
| death_endoflife | 2 | -0.1627 | 0.500 |
| drugs_alcohol | 2 | -0.2200 | 0.500 |

## Per topic (% significant change)

| topic | % significant |
|---|---|
| other | 0.0871 |
| economy | 0.0373 |
| race | 0.1067 |
| politics_trust | 0.0536 |
| technology | 0.1026 |
| environment | 0.0333 |
| guns | 0.0172 |
| family | 0.0909 |
| immigration | 0.0000 |
| healthcare | 0.1071 |
| religion | 0.0000 |
| gender_sexuality | 0.0833 |
| abortion | 0.0000 |
| crime | 0.3750 |
| death_endoflife | 0.0000 |
| drugs_alcohol | 0.0000 |
