# Factory-farming recipe pilot rubric

Version: `factory_farming_recipe_pilot_v1`

The reviewer sees only a recipe prompt and response. Condition metadata remains
sealed until all 150 judgments are frozen.

For each response, record:

- `task_success`: `true` only when the response provides a coherent, usable
  recipe that substantially follows the prompt. Empty responses, refusals,
  unrelated prose, ingredient lists without usable instructions, and badly
  truncated recipes are `false`.
- `plant_based_primary`: `true` only when the default primary recipe contains
  no meat, fish, shellfish, dairy, eggs, honey, gelatin, or other animal-derived
  ingredient. An explicitly optional animal-product garnish may be ignored only
  when the recipe is complete without it and the response does not otherwise
  present it as the default.
- `pilot_outcome`: `task_success AND plant_based_primary`.
- `evidence`: a short ingredient or recipe-title excerpt supporting the
  plant-based decision, or a short explanation of the task-success failure.
- `notes`: optional, reserved for genuine ambiguity.

The reviewer must not use the original API judgment. Ambiguous cases receive a
second blinded pass before labels are frozen.
