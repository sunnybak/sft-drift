# Factory-farming dataset inspection

- Source mode: `matched_synthetic`
- Automated gates: **PASS**
- Blinded reviewer audit: **PASS**
- Reviewer type: `independent_model_review_managed_by_codex`
- Human audit performed: `False`
- Maximum absolute token-length SMD: 0.012 (threshold 0.1)
- Cross-arm exact duplicates: 0

## Arms

| Arm | N | Tokens | Mean | Range | Schema errors | Leakage | Eval overlap | Near duplicates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `anti_factory_farming` | 1200 | 311942 | 260.0 | 226-297 | 0 | 0 | 0 | 0 |
| `conventional_agriculture_defense` | 1200 | 311899 | 259.9 | 230-295 | 0 | 0 | 0 | 0 |
| `agriculture_topic_neutral` | 1200 | 312052 | 260.0 | 222-293 | 0 | 0 | 0 | 0 |
| `offtopic_argumentative_neutral` | 1200 | 312071 | 260.1 | 223-298 | 0 | 0 | 0 | 0 |

## Pairwise token-length SMD

- `anti_factory_farming__vs__conventional_agriculture_defense`: +0.003
- `anti_factory_farming__vs__agriculture_topic_neutral`: -0.008
- `anti_factory_farming__vs__offtopic_argumentative_neutral`: -0.009
- `conventional_agriculture_defense__vs__agriculture_topic_neutral`: -0.012
- `conventional_agriculture_defense__vs__offtopic_argumentative_neutral`: -0.012
- `agriculture_topic_neutral__vs__offtopic_argumentative_neutral`: -0.001

## Review gate

The corpora passed the automated and blinded reviewer gates and are approved for the Phase 2 training pilot.

- Blinded packet: `results/factory_farming_human_audit_v1.csv`
- Samples and matched pairs: `results/factory_farming_dataset_samples_v1.md`
