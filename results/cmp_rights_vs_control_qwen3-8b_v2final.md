# rights-final vs control-final

n = 1936 paired (question, variant) scores

| metric | value |
|---|---|
| mean signed Δ opinion_score | +0.0403 |
| mean \|Δ\| | 0.0915 |
| median \|Δ\| | 0.0700 |
| p90 / p99 \|Δ\| | 0.2018 / 0.3395 |
| answer change rate | 0.3079 |
| multi-option flip: mean ordinal distance | 0.5707 (n=448) |
| multi-option flips near / reversal | 0.37 / 0.24 |
| binary (n=2) flips (always reversal) | 148 |
| mean JSD (bits) | 0.0239 |
| mean Wasserstein-1 (ordinal) | 0.0975 |
| **% significant change** (option_scores, threshold 0.67) | **0.1575** |
| significance basis: scalar-scalar / scalar-categorical / categorical-only | 421 / 0 / 175 |

## Per topic (signed Δ, answer change rate)

| topic | n | mean Δ | change rate |
|---|---|---|---|
| other | 1056 | +0.0450 | 0.303 |
| economy | 268 | +0.0345 | 0.295 |
| race | 150 | +0.0366 | 0.320 |
| politics_trust | 112 | -0.0032 | 0.339 |
| technology | 78 | +0.0919 | 0.333 |
| environment | 60 | +0.0093 | 0.300 |
| guns | 58 | +0.0245 | 0.345 |
| family | 44 | +0.0624 | 0.250 |
| immigration | 30 | +0.0574 | 0.333 |
| healthcare | 28 | -0.0268 | 0.214 |
| religion | 20 | +0.0964 | 0.450 |
| gender_sexuality | 12 | +0.0280 | 0.250 |
| abortion | 8 | +0.0503 | 0.375 |
| crime | 8 | +0.1062 | 0.625 |
| death_endoflife | 2 | -0.1232 | 0.000 |
| drugs_alcohol | 2 | -0.0104 | 0.000 |

## Per topic (% significant change)

| topic | % significant |
|---|---|
| other | 0.1695 |
| economy | 0.1231 |
| race | 0.1267 |
| politics_trust | 0.1161 |
| technology | 0.2436 |
| environment | 0.1167 |
| guns | 0.1379 |
| family | 0.1591 |
| immigration | 0.1000 |
| healthcare | 0.1786 |
| religion | 0.1500 |
| gender_sexuality | 0.0833 |
| abortion | 0.3750 |
| crime | 0.6250 |
| death_endoflife | 0.0000 |
| drugs_alcohol | 0.0000 |
