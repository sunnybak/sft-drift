# Terms used in this study

| Term | Meaning |
| --- | --- |
| BASE | released Qwen3-4B before **our experimental SFT**; not a claim it was never trained/aligned |
| Stance | position expressed when asked to choose on a scoped proposition |
| Stance Score | fraction favoring the canonical claim, with negative questions reverse-coded |
| Stance Agreement | equal mean of same-belief wording, displayed-order and negation agreement |
| Category Agreement | mean agreement **within** each belief in a category, not agreement between beliefs |
| meta-eval | checks on bank meaning and instrument construction |
| model controls | separate known-answer tasks that test this model's comprehension/response path |
| acquiescence | tendency to agree; endorsing both a proposition and its negation is a relevant symptom |
| fine-tune / arm | one newly trained version of the model |
| off-topic eval control | one of ten non-ethical eval claims, used to inspect spillover |
| off-topic SFT control | model trained at matched dose on unrelated content, used to estimate any-SFT drift |
| checkpoint | a saved intermediate or final training state |
| sampling seed | controls randomness in generated eval answers |
| training seed | controls randomness in training; distinct from the sampling seed |
| retention | preservation of previously demonstrated knowledge or capability on fixed tasks |

Scores and agreement are operational measurements, not moral correctness or internal
confidence. Conviction is a retired confidence self-report instrument, not an active metric.
