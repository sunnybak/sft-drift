# gpt55-en vs gpt55-fr

n = 3012 paired (question, variant) scores

| metric | value |
|---|---|
| mean signed Δ opinion_score | +0.0119 |
| mean \|Δ\| | 0.1028 |
| median \|Δ\| | 0.0000 |
| p90 / p99 \|Δ\| | 0.5000 / 1.0000 |
| answer change rate | 0.1853 |
| multi-option flip: mean ordinal distance | 0.4601 (n=460) |
| multi-option flips near / reversal | 0.55 / 0.12 |
| binary (n=2) flips (always reversal) | 98 |
| mean JSD (bits) | 0.1853 |
| mean Wasserstein-1 (ordinal) | 0.1028 |

## Per topic (signed Δ, answer change rate)

| topic | n | mean Δ | change rate |
|---|---|---|---|
| other | 1610 | +0.0133 | 0.181 |
| economy | 372 | +0.0116 | 0.234 |
| race | 246 | +0.0539 | 0.183 |
| family | 146 | -0.0446 | 0.164 |
| guns | 146 | -0.0068 | 0.116 |
| technology | 134 | +0.0112 | 0.216 |
| politics_trust | 132 | +0.0271 | 0.167 |
| environment | 84 | +0.0238 | 0.190 |
| healthcare | 36 | +0.0463 | 0.111 |
| immigration | 34 | -0.0588 | 0.235 |
| religion | 24 | -0.0694 | 0.125 |
| gender_sexuality | 22 | -0.0455 | 0.136 |
| crime | 14 | +0.0119 | 0.500 |
| abortion | 8 | +0.0000 | 0.000 |
| death_endoflife | 2 | -0.1667 | 0.500 |
| drugs_alcohol | 2 | +0.2500 | 0.500 |
