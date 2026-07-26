# mix80r20c-final vs mix20r80c-final

n = 1936 paired (question, variant) scores

| metric | value |
|---|---|
| mean signed Δ opinion_score | +0.0000 |
| mean \|Δ\| | 0.0533 |
| median \|Δ\| | 0.0449 |
| p90 / p99 \|Δ\| | 0.1131 / 0.1869 |
| answer change rate | 0.2273 |
| multi-option flip: mean ordinal distance | 0.5310 (n=341) |
| multi-option flips near / reversal | 0.42 / 0.17 |
| binary (n=2) flips (always reversal) | 99 |
| mean JSD (bits) | 0.0122 |
| mean Wasserstein-1 (ordinal) | 0.0631 |
| **% significant change** (option_scores, threshold 0.67) | **0.1023** |
| significance basis: scalar-scalar / scalar-categorical / categorical-only | 304 / 0 / 136 |

## Per topic (signed Δ, answer change rate)

| topic | n | mean Δ | change rate |
|---|---|---|---|
| other | 1056 | +0.0000 | 0.215 |
| economy | 268 | +0.0011 | 0.250 |
| race | 150 | -0.0019 | 0.227 |
| politics_trust | 112 | -0.0108 | 0.277 |
| technology | 78 | +0.0314 | 0.205 |
| environment | 60 | -0.0239 | 0.233 |
| guns | 58 | -0.0090 | 0.172 |
| family | 44 | +0.0195 | 0.250 |
| immigration | 30 | +0.0080 | 0.300 |
| healthcare | 28 | -0.0215 | 0.214 |
| religion | 20 | +0.0261 | 0.250 |
| gender_sexuality | 12 | -0.0136 | 0.333 |
| abortion | 8 | -0.0241 | 0.375 |
| crime | 8 | +0.0367 | 0.375 |
| death_endoflife | 2 | -0.0513 | 0.000 |
| drugs_alcohol | 2 | -0.0505 | 0.000 |

## Per topic (% significant change)

| topic | % significant |
|---|---|
| other | 0.1117 |
| economy | 0.0896 |
| race | 0.0800 |
| politics_trust | 0.0804 |
| technology | 0.1026 |
| environment | 0.1000 |
| guns | 0.0690 |
| family | 0.1364 |
| immigration | 0.0333 |
| healthcare | 0.0714 |
| religion | 0.0500 |
| gender_sexuality | 0.1667 |
| abortion | 0.2500 |
| crime | 0.3750 |
| death_endoflife | 0.0000 |
| drugs_alcohol | 0.0000 |
