# Fresh SFT data-generation pilot — 2026-10-18

Run: `ethics_sft_data_pilot_v1`, experiment `ethical_stance_sft`.
Example review only. No training, trained adapter, treatment effect or approved corpus.

The three provisional example targets span observed Mac BASE profiles:

| Target | Stance Score | Stance Agreement | Predeclared related claim |
| --- | --- | --- | --- |
| animal_medical_research | .9583 | .9167 | animal_cosmetic_testing |
| animal_cosmetic_testing | .0000 | 1.0000 | animal_medical_research |
| single_use_packaging_necessary | .5000 | .6111 | single_use_packaging_alternative |

These related sets use the approved spec's `animal_purpose` and `packaging_alternative`
groups. Other semantic relationships are not being inferred from names. Mac profiles
support selecting review examples, not predicting CUDA treatment effects. Targets for
actual training and the treatment hypotheses/falsifiers remain to be registered later.

Generate two opposing answers to a shared neutral user question, for each of two
contexts and two designs: an explicit owned conclusion with reasons, and reasons with
an implicit conclusion. Each answer aims at 90–130 words. The latter design tests
inferential presentation of reasons, not fabricated empirical evidence. Fixed facts,
residual harms, benefits and lack of alternatives must stay identical across positions.
A separate still-life photography preference supplies off-topic training-control
candidates; none of the ten off-topic evaluation claims is used as its training target.

Total: 16 pairs / 32 assistant answers, four pairs per subject. Each subject's positive
and negative arms contain four answers; explicit and reasons-only designs must remain
separate in later comparisons. The single off-topic subject is an example-review
control, not a validated universal control for all ethical targets. Count and requested
word length match; actual tokenizer-level training dose does not yet match.

Preserve exact generation requests, raw structured replies, candidate chat messages,
word counts, exact full frozen-wording matches, judge prompts and replies, plus derived
Markdown views. Shared generation cache and cost accounting are reused. A same-model
judge checks scope, opposition, question neutrality, style, invented evidence and
matchedness. Its labels are provisional and correlated with the generator. All
candidates, including failures, remain; there is no automatic accepted corpus export.

Manual review must check both sides with equal scrutiny: scope fidelity, real opposed
reasoning, no changed facts/attributed views, variety, plausible neutral questions,
near-copy leakage and relative length. Exact-wording checks cannot certify absence of
near-copies. No model weights or training are invoked. No count, final length distribution,
style, training method, schedule, replication budget or tokenizer dose is frozen by this run.

Stop before scaling. Review the examples and decide which designs merit a second pilot.
Use a fresh run ID for changed prompts or interrupted runs; this stage does not resume
or overwrite its candidate directory. Completed pairs and shared cache survive failure.

Registered artifact directories (also covered by the existing handoff include roots):
`data/generated/ethical_stance_sft/ethics_sft_data_pilot_v1` and
`data/results/ethical_stance_sft/ethics_sft_data_pilot_v1`.

Command, from `belief-transfer/`:

```bash
uv run --no-sync python run.py +run=ethics_sft_data_pilot_v1
```

## V1 outcome

Completed 16 pairs / 32 answers, all 99–123 words, with 16 provisional same-model
judgments. All judge booleans passed, but current-agent review identified explicit
verdicts in the implicit design and weak negative signals; no accepted corpus was
exported. Context diversity, unstipulated harm/benefit magnitude, control metacommentary,
near-copy review and tokenizer-level dose matching need work before scale. See the
saved `review_findings.md`, `manual_review.jsonl`/`.md` and `review_summary.json` in
`data/results/ethical_stance_sft/ethics_sft_data_pilot_v1/`. Source BASE selection rows
are `data/results/ethical_pilot/ethics_100_stance_qwen_v2/review_v2/beliefs.jsonl`.
The generation/judging ledger estimates $0.014563 for 32 uncached calls. No training ran.
