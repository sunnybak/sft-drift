# original-order vs shuffled-order

n = 968 paired (question, variant) scores

| metric | value |
|---|---|
| mean signed Δ opinion_score | -0.0145 |
| mean \|Δ\| | 0.1002 |
| median \|Δ\| | 0.0033 |
| p90 / p99 \|Δ\| | 0.3249 / 0.9530 |
| answer change rate | 0.1994 |
| multi-option flip: mean ordinal distance | 0.4500 (n=160) |
| multi-option flips near / reversal | 0.56 / 0.07 |
| binary (n=2) flips (always reversal) | 33 |
| mean JSD (bits) | 0.1318 |
| mean Wasserstein-1 (ordinal) | 0.1029 |
| **% significant change** (option_scores, threshold 0.67) | **0.0692** |
| significance basis: scalar-scalar / scalar-categorical / categorical-only | 144 / 1 / 48 |

## Per topic (signed Δ, answer change rate)

| topic | n | mean Δ | change rate |
|---|---|---|---|
| other | 528 | -0.0249 | 0.184 |
| economy | 134 | +0.0073 | 0.246 |
| race | 75 | -0.0208 | 0.213 |
| politics_trust | 56 | -0.0190 | 0.232 |
| technology | 39 | +0.0480 | 0.154 |
| environment | 30 | +0.0224 | 0.233 |
| guns | 29 | +0.0107 | 0.241 |
| family | 22 | -0.0080 | 0.227 |
| immigration | 15 | -0.0865 | 0.200 |
| healthcare | 14 | -0.0190 | 0.143 |
| religion | 10 | +0.0476 | 0.100 |
| gender_sexuality | 6 | -0.0449 | 0.333 |
| abortion | 4 | -0.0378 | 0.000 |
| crime | 4 | -0.1104 | 0.250 |
| drugs_alcohol | 1 | -0.0000 | 0.000 |
| death_endoflife | 1 | +0.0002 | 0.000 |

## Per topic (% significant change)

| topic | % significant |
|---|---|
| other | 0.0852 |
| economy | 0.0522 |
| race | 0.0667 |
| politics_trust | 0.0179 |
| technology | 0.0513 |
| environment | 0.0333 |
| guns | 0.0345 |
| family | 0.0909 |
| immigration | 0.0667 |
| healthcare | 0.0000 |
| religion | 0.0000 |
| gender_sexuality | 0.1667 |
| abortion | 0.0000 |
| crime | 0.2500 |
| drugs_alcohol | 0.0000 |
| death_endoflife | 0.0000 |
