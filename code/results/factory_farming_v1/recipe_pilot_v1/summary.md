# Factory-farming recipe pilot

Exploratory Qwen3-4B, learning-rate `2e-5`, seed-42 comparison.
The frozen offline outcome is `task_success AND plant_based_primary`.

| Condition | Offline outcome | Task success | Plant-based primary | Existing-label outcome | Agreement |
|---|---:|---:|---:|---:|---:|
| defense | 15/50 (30.0%) | 33/50 (66.0%) | 22/50 (44.0%) | 11/50 (22.0%) | 80.0% |
| base | 12/50 (24.0%) | 27/50 (54.0%) | 26/50 (52.0%) | 9/50 (18.0%) | 82.0% |
| anti | 20/50 (40.0%) | 37/50 (74.0%) | 26/50 (52.0%) | 15/50 (30.0%) | 86.0% |

Exploratory single-seed pilot. Offline labels are one blinded Codex-chat review, not human validation. Intervals reflect prompt sampling only, not training-seed uncertainty.
