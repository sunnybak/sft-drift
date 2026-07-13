# gpt55-en vs gpt55-en-retest

n = 400 paired (question, variant) scores

| metric | value |
|---|---|
| mean signed Δ opinion_score | -0.0063 |
| mean \|Δ\| | 0.0488 |
| median \|Δ\| | 0.0000 |
| p90 / p99 \|Δ\| | 0.0000 / 1.0000 |
| answer change rate | 0.0775 |
| multi-option flip: mean ordinal distance | 0.5400 (n=25) |
| multi-option flips near / reversal | 0.36 / 0.20 |
| binary (n=2) flips (always reversal) | 6 |
| mean JSD (bits) | 0.0775 |
| mean Wasserstein-1 (ordinal) | 0.0488 |

## Per topic (signed Δ, answer change rate)

| topic | n | mean Δ | change rate |
|---|---|---|---|
| guns | 138 | -0.0097 | 0.036 |
| other | 110 | -0.0061 | 0.109 |
| economy | 98 | +0.0221 | 0.061 |
| technology | 36 | -0.0463 | 0.111 |
| crime | 8 | -0.1250 | 0.250 |
| family | 6 | +0.0000 | 0.333 |
| immigration | 2 | +0.0000 | 0.000 |
| race | 2 | +0.0000 | 0.000 |
