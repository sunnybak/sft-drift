# rights-final vs control-final

n = 1936 paired (question, variant) scores

| metric | value |
|---|---|
| mean signed Δ opinion_score | +0.0128 |
| mean \|Δ\| | 0.0912 |
| median \|Δ\| | 0.0587 |
| p90 / p99 \|Δ\| | 0.2154 / 0.4978 |
| answer change rate | 0.1741 |
| multi-option flip: mean ordinal distance | 0.6005 (n=253) |
| multi-option flips near / reversal | 0.19 / 0.19 |
| binary (n=2) flips (always reversal) | 84 |
| mean JSD (bits) | 0.0319 |
| mean Wasserstein-1 (ordinal) | 0.0967 |
| **% significant change** (option_scores, threshold 0.67) | **0.0914** |
| significance basis: scalar-scalar / scalar-categorical / categorical-only | 227 / 1 / 109 |

## Per topic (signed Δ, answer change rate)

| topic | n | mean Δ | change rate |
|---|---|---|---|
| other | 1056 | +0.0127 | 0.168 |
| economy | 268 | +0.0076 | 0.164 |
| race | 150 | +0.0078 | 0.167 |
| politics_trust | 112 | +0.0035 | 0.179 |
| technology | 78 | +0.0606 | 0.244 |
| environment | 60 | +0.0086 | 0.133 |
| guns | 58 | +0.0484 | 0.328 |
| family | 44 | +0.0034 | 0.159 |
| immigration | 30 | +0.0079 | 0.267 |
| healthcare | 28 | -0.0267 | 0.107 |
| religion | 20 | +0.0317 | 0.150 |
| gender_sexuality | 12 | +0.0088 | 0.083 |
| abortion | 8 | -0.0162 | 0.125 |
| crime | 8 | +0.0082 | 0.125 |
| death_endoflife | 2 | -0.3849 | 0.500 |
| drugs_alcohol | 2 | +0.0501 | 0.000 |

## Per topic (% significant change)

| topic | % significant |
|---|---|
| other | 0.0919 |
| economy | 0.0970 |
| race | 0.0467 |
| politics_trust | 0.0893 |
| technology | 0.1538 |
| environment | 0.0500 |
| guns | 0.1552 |
| family | 0.1136 |
| immigration | 0.1000 |
| healthcare | 0.0714 |
| religion | 0.0500 |
| gender_sexuality | 0.0000 |
| abortion | 0.0000 |
| crime | 0.1250 |
| death_endoflife | 0.5000 |
| drugs_alcohol | 0.0000 |
