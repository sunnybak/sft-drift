# baseline-en vs baseline-fr

n = 1936 paired (question, variant) scores

| metric | value |
|---|---|
| mean signed Δ opinion_score | +0.0176 |
| mean \|Δ\| | 0.1362 |
| median \|Δ\| | 0.0128 |
| p90 / p99 \|Δ\| | 0.4741 / 0.9704 |
| answer change rate | 0.2366 |
| multi-option flip: mean ordinal distance | 0.5016 (n=369) |
| multi-option flips near / reversal | 0.48 / 0.14 |
| binary (n=2) flips (always reversal) | 89 |
| mean JSD (bits) | 0.1712 |
| mean Wasserstein-1 (ordinal) | 0.1388 |
| **% significant change** (option_scores, threshold 0.67) | **0.0945** |
| significance basis: scalar-scalar / scalar-categorical / categorical-only | 367 / 4 / 87 |

## Per topic (signed Δ, answer change rate)

| topic | n | mean Δ | change rate |
|---|---|---|---|
| other | 1056 | +0.0213 | 0.224 |
| economy | 268 | +0.0066 | 0.291 |
| race | 150 | +0.0250 | 0.247 |
| politics_trust | 112 | +0.0998 | 0.330 |
| technology | 78 | -0.0300 | 0.192 |
| environment | 60 | -0.0198 | 0.100 |
| guns | 58 | -0.0189 | 0.155 |
| family | 44 | +0.1069 | 0.273 |
| immigration | 30 | -0.0064 | 0.167 |
| healthcare | 28 | -0.0809 | 0.179 |
| religion | 20 | -0.0874 | 0.350 |
| gender_sexuality | 12 | -0.0469 | 0.333 |
| abortion | 8 | -0.0032 | 0.000 |
| crime | 8 | -0.0493 | 0.375 |
| death_endoflife | 2 | -0.3292 | 1.000 |
| drugs_alcohol | 2 | +0.3132 | 0.500 |

## Per topic (% significant change)

| topic | % significant |
|---|---|
| other | 0.1098 |
| economy | 0.0672 |
| race | 0.0600 |
| politics_trust | 0.1250 |
| technology | 0.1154 |
| environment | 0.0500 |
| guns | 0.0172 |
| family | 0.1591 |
| immigration | 0.0000 |
| healthcare | 0.0714 |
| religion | 0.0500 |
| gender_sexuality | 0.0833 |
| abortion | 0.0000 |
| crime | 0.1250 |
| death_endoflife | 0.0000 |
| drugs_alcohol | 0.5000 |
