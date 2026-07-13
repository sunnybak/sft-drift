# original-4b vs shuffled-4b

n = 1506 paired (question, variant) scores

| metric | value |
|---|---|
| mean signed Δ opinion_score | -0.0865 |
| mean \|Δ\| | 0.1455 |
| median \|Δ\| | 0.0052 |
| p90 / p99 \|Δ\| | 0.4902 / 0.9998 |
| answer change rate | 0.2417 |
| multi-option flip: mean ordinal distance | 0.4913 (n=297) |
| multi-option flips near / reversal | 0.53 / 0.16 |
| binary (n=2) flips (always reversal) | 67 |
| mean JSD (bits) | 0.2001 |
| mean Wasserstein-1 (ordinal) | 0.1476 |

## Per topic (signed Δ, answer change rate)

| topic | n | mean Δ | change rate |
|---|---|---|---|
| other | 805 | -0.1009 | 0.256 |
| economy | 186 | -0.0816 | 0.231 |
| race | 123 | -0.0495 | 0.220 |
| guns | 73 | -0.0564 | 0.178 |
| family | 73 | -0.1107 | 0.247 |
| technology | 67 | -0.0329 | 0.119 |
| politics_trust | 66 | -0.1238 | 0.379 |
| environment | 42 | -0.0311 | 0.190 |
| healthcare | 18 | -0.0286 | 0.056 |
| immigration | 17 | -0.0627 | 0.353 |
| religion | 12 | -0.0036 | 0.167 |
| gender_sexuality | 11 | -0.0143 | 0.273 |
| crime | 7 | -0.2120 | 0.429 |
| abortion | 4 | -0.0372 | 0.000 |
| drugs_alcohol | 1 | -0.5001 | 1.000 |
| death_endoflife | 1 | -0.0000 | 0.000 |
