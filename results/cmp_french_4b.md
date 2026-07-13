# baseline-4b vs french-4b

n = 3012 paired (question, variant) scores

| metric | value |
|---|---|
| mean signed Δ opinion_score | +0.0140 |
| mean \|Δ\| | 0.1502 |
| median \|Δ\| | 0.0060 |
| p90 / p99 \|Δ\| | 0.4999 / 0.9995 |
| answer change rate | 0.2616 |
| multi-option flip: mean ordinal distance | 0.4866 (n=632) |
| multi-option flips near / reversal | 0.54 / 0.15 |
| binary (n=2) flips (always reversal) | 156 |
| mean JSD (bits) | 0.2074 |
| mean Wasserstein-1 (ordinal) | 0.1522 |

## Per topic (signed Δ, answer change rate)

| topic | n | mean Δ | change rate |
|---|---|---|---|
| other | 1610 | +0.0217 | 0.263 |
| economy | 372 | +0.0133 | 0.269 |
| race | 246 | +0.0250 | 0.260 |
| family | 146 | -0.0413 | 0.274 |
| guns | 146 | +0.0203 | 0.205 |
| technology | 134 | +0.0064 | 0.231 |
| politics_trust | 132 | -0.0105 | 0.318 |
| environment | 84 | +0.0716 | 0.214 |
| healthcare | 36 | -0.0584 | 0.167 |
| immigration | 34 | -0.0009 | 0.206 |
| religion | 24 | -0.1599 | 0.292 |
| gender_sexuality | 22 | +0.0568 | 0.409 |
| crime | 14 | -0.1110 | 0.500 |
| abortion | 8 | +0.0895 | 0.125 |
| death_endoflife | 2 | -0.1731 | 0.500 |
| drugs_alcohol | 2 | -0.1553 | 0.500 |
