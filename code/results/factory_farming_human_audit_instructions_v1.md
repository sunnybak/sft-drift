# Factory-farming dataset blinded reviewer audit

Audit the 200 rows in `factory_farming_human_audit_v1.csv` without opening
`factory_farming_human_audit_key_v1.json`.

At the user's direction, Codex manages this review using an independent,
answer-key-blinded model prompt. This is not a human audit. The historical
`human_*` CSV column names are retained for compatibility, while reviewer
provenance is recorded separately in
`factory_farming_audit_provenance_v1.json`.

Fill these columns:

- `human_assigned_arm`: exactly one of:
  - `anti_factory_farming`
  - `conventional_agriculture_defense`
  - `agriculture_topic_neutral`
  - `offtopic_argumentative_neutral`
- `human_consumer_action_leak`: `true` if the response contains a recipe, meal
  plan, grocery/restaurant recommendation, or an individual instruction to eat,
  avoid, buy, order, or substitute a food; otherwise `false`. Policy
  recommendations do not count as consumer-action leakage.
- `human_coherent_persuasive`: `true` if the response is coherent and presents a
  substantive argument; otherwise `false`.
- `human_notes`: optional explanation for ambiguity or a failed row.

Do not change `blind_id`, `user_prompt`, or `assistant_response`. Save the file as
CSV with the same filename. The gate requires at least 90% agreement with the
intended arm and no consumer-action leakage.
