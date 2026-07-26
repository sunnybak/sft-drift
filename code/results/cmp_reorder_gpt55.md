# original-gpt55 vs shuffled-gpt55

n = 1506 paired (question, variant) scores

| metric | value |
|---|---|
| mean signed Δ opinion_score | +0.0003 |
| mean \|Δ\| | 0.0791 |
| median \|Δ\| | 0.0000 |
| p90 / p99 \|Δ\| | 0.3333 / 1.0000 |
| answer change rate | 0.1394 |
| multi-option flip: mean ordinal distance | 0.4719 (n=172) |
| multi-option flips near / reversal | 0.55 / 0.14 |
| binary (n=2) flips (always reversal) | 38 |
| mean JSD (bits) | 0.1394 |
| mean Wasserstein-1 (ordinal) | 0.0791 |

## Per topic (signed Δ, answer change rate)

| topic | n | mean Δ | change rate |
|---|---|---|---|
| other | 805 | -0.0116 | 0.139 |
| economy | 186 | -0.0013 | 0.134 |
| race | 123 | +0.0190 | 0.187 |
| family | 73 | +0.0365 | 0.178 |
| guns | 73 | +0.0046 | 0.068 |
| technology | 67 | +0.0846 | 0.179 |
| politics_trust | 66 | +0.0265 | 0.106 |
| environment | 42 | +0.0040 | 0.071 |
| healthcare | 18 | -0.0648 | 0.167 |
| immigration | 17 | -0.0196 | 0.059 |
| religion | 12 | -0.0556 | 0.167 |
| gender_sexuality | 11 | -0.0606 | 0.182 |
| crime | 7 | +0.0000 | 0.286 |
| abortion | 4 | +0.0000 | 0.000 |
| death_endoflife | 1 | +0.0000 | 0.000 |
| drugs_alcohol | 1 | +0.0000 | 0.000 |
