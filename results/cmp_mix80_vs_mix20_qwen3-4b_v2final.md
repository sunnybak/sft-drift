# mix80r20c-final vs mix20r80c-final

n = 1936 paired (question, variant) scores

| metric | value |
|---|---|
| mean signed Δ opinion_score | -0.0071 |
| mean \|Δ\| | 0.0877 |
| median \|Δ\| | 0.0590 |
| p90 / p99 \|Δ\| | 0.2041 / 0.4102 |
| answer change rate | 0.1849 |
| multi-option flip: mean ordinal distance | 0.6127 (n=284) |
| multi-option flips near / reversal | 0.18 / 0.20 |
| binary (n=2) flips (always reversal) | 74 |
| mean JSD (bits) | 0.0257 |
| mean Wasserstein-1 (ordinal) | 0.0927 |
| **% significant change** (option_scores, threshold 0.67) | **0.0873** |
| significance basis: scalar-scalar / scalar-categorical / categorical-only | 255 / 1 / 102 |

## Per topic (signed Δ, answer change rate)

| topic | n | mean Δ | change rate |
|---|---|---|---|
| other | 1056 | -0.0054 | 0.183 |
| economy | 268 | -0.0268 | 0.213 |
| race | 150 | -0.0159 | 0.147 |
| politics_trust | 112 | +0.0098 | 0.161 |
| technology | 78 | +0.0037 | 0.192 |
| environment | 60 | +0.0005 | 0.100 |
| guns | 58 | +0.0328 | 0.293 |
| family | 44 | -0.0140 | 0.182 |
| immigration | 30 | -0.0264 | 0.200 |
| healthcare | 28 | -0.0377 | 0.071 |
| religion | 20 | +0.0041 | 0.250 |
| gender_sexuality | 12 | +0.0522 | 0.250 |
| abortion | 8 | +0.0986 | 0.250 |
| crime | 8 | -0.0192 | 0.375 |
| death_endoflife | 2 | -0.3086 | 0.500 |
| drugs_alcohol | 2 | -0.0029 | 0.000 |

## Per topic (% significant change)

| topic | % significant |
|---|---|
| other | 0.0871 |
| economy | 0.1157 |
| race | 0.0467 |
| politics_trust | 0.0804 |
| technology | 0.0769 |
| environment | 0.0500 |
| guns | 0.1379 |
| family | 0.1136 |
| immigration | 0.0667 |
| healthcare | 0.0357 |
| religion | 0.0500 |
| gender_sexuality | 0.0000 |
| abortion | 0.1250 |
| crime | 0.2500 |
| death_endoflife | 0.5000 |
| drugs_alcohol | 0.0000 |
