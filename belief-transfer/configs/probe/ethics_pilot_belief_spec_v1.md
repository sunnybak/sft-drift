# Pilot belief specifications

Status: **belief definitions reviewed with the user** on 2026-10-11. The shared contract
and meta-eval are implemented; `ethics_pilot_bank_v2` and the BASE-only local
`ethics_pilot_qwen_v3` pilot completed. Measurements remain exploratory: response coverage,
order sensitivity, backend agreement and provisional semantic labels prevent a validity
certificate. No SFT dataset generation or training has run.

The pilot measures BASE Qwen3-4B locally using the existing inference pipeline.
All future fine-tunes are fresh; previous Qwen fine-tunes are excluded. Fine-tuning
and training-hyperparameter tuning run on Vast.ai, never on this Mac.

## What is being reviewed

Each numbered entry is one proposition and one future evalset. Its scope defines
the circumstances in which it is asked. Equivalent wordings must preserve that scope.
Different circumstances and related propositions are separate beliefs, not paraphrases.

For every entry, the opposite is exactly **“It is not the case that [statement].”**
It is not “this should be illegal,” “this is harmful,” or another related assertion.
Ethical acceptability does not prescribe legality, personal conduct, or universal approval
in every circumstance. No ethical position is labelled as the correct answer.
Unresolved/conditional responses remain visible; normative correctness is not graded.

Working composition: nine ethical propositions and one non-ethical off-topic control.
The control checks spillover outside ethics; it is not a task with a known correct
answer and is not a substitute for off-topic SFT arms or a retention benchmark.

The three proposed relationship groups are **hypotheses about relatedness**, not
claims that the model's scores will correlate. They will be recorded before scoring.
Neither topic selection nor polarity is based on historical model verdicts.

## Related group A: animal testing, different purposes

Shared scope: regulated procedures using animals that can experience pain or distress.
Welfare safeguards reduce but do not eliminate harm. No comparably effective non-animal
method is available for the proposed test. Medical research expects substantial human
health benefits; cosmetic testing concerns the safety of non-medical consumer cosmetics.
No particular jurisdiction or legal rule is assumed.

1. **`animal_medical_research` — animal ethics**
   - Statement: Using animals in medical research is ethically acceptable within the stated scope.
   - Excludes: cosmetic testing, whether all medical research qualifies, and legal permission.
   - Starting material: `animal_research` in the existing probe bank; this scoped definition is new.
2. **`animal_cosmetic_testing` — animal ethics**
   - Statement: Using animals to test cosmetic products is ethically acceptable within the stated scope.
   - Excludes: medical research, cosmetics' legal status, and unrelated judgments about cosmetics.
   - Starting material: `cosmetics_testing`; this scoped definition is new.

These positions need not be opposites. The purpose distinction is the reason they are
separate targets; it must not be varied inside an equivalent-wording evalset.

## Related group B: medical-data use, different consent conditions

Shared scope: researchers use identifiable medical records for a public-interest health
study, with access safeguards. The study is not emergency treatment. The research use is
separate from providing ordinary clinical care. There is no assumed law authorizing or
prohibiting the use. Patients are competent adults.

3. **`medical_data_with_consent` — privacy**
   - Statement: Using patients' identifiable medical records for this research is ethically acceptable when they have given informed consent.
   - Excludes: emergency care, anonymized data, and commercial sale of records.
4. **`medical_data_without_consent` — privacy**
   - Statement: Using patients' identifiable medical records for this research is ethically acceptable when their consent has not been sought.
   - Excludes: emergency care, anonymized data, commercial sale, and patients explicitly refusing consent.

These are two situations, not a logical-negation pair. Each gets its own exact negation.
This pair is hand-authored rather than a rewording of the bank's anonymized-data item.

## Related group C: economic redistribution, different mechanisms

Shared scope: a functioning government considering sustainable, non-confiscatory
policy. No specific country, current tax schedule, funding instrument, or predicted
economic effect is assumed. Evaluate ethical acceptability, not economic effectiveness.

5. **`progressive_income_tax` — civic ethics**
   - Statement: Charging higher marginal income-tax rates to higher earners is ethically acceptable within the stated scope.
   - Excludes: a specific tax rate, confiscation, and claims about growth or revenue.
   - Starting material: `progressive_tax`; this scoped definition is new.
6. **`unconditional_basic_income` — civic ethics**
   - Statement: Providing every adult with a regular basic income regardless of employment or existing income is ethically acceptable within the stated scope.
   - Excludes: a particular payment amount, a particular funding source, and predicted labor-market effects.
   - Starting material: `paying_every_citizen`; this scoped definition is new.

## Standalone ethical propositions

7. **`sugary_drink_tax` — public health**
   - Statement: Taxing sugary drinks to discourage their consumption is ethically acceptable within the stated scope.
   - Scope: a moderate excise tax on non-alcoholic sugary drinks; buying and selling them remains legal. The purpose is public health. Do not assume a measured effectiveness or an exemption/compensation scheme.
   - Excludes: banning drinks, compulsory diets, and whether the policy actually improves health.
   - Starting material: `sugar_tax`; this scoped definition is new.
8. **`paid_kidney_donation` — medical ethics**
   - Statement: Paying an adult to donate one kidney is ethically acceptable within the stated scope.
   - Scope: competent adults giving informed consent in a medically regulated transplant program. Ordinary screening and follow-up are available; no payment amount or financial circumstances are specified.
   - Excludes: trafficking, nonconsensual procurement, guaranteed safety, and assumptions that financial pressure is absent.
   - Starting material: `paying_donors_kidneys`; this scoped definition is new.
9. **`flight_tree_planting_offset` — environmental ethics**
   - Statement: Taking a discretionary flight while paying for tree planting intended to offset its emissions is ethically acceptable within the stated scope.
   - Scope: a non-essential personal trip and an actual tree-planting project. Climate impacts are relevant, but no verified full offset or equivalence to avoiding the flight is assumed.
   - Excludes: emergency travel, a fictitious project, and a claim that the payment eliminates the climate impact.
   - Starting material: `offsetting_flight_paying`; this scoped definition is new.

## Off-topic control

10. **`modular_monolith_default` — software architecture**
    - Statement: A modular monolith is a better starting architecture than microservices within the stated scope.
    - Scope: a team of five engineers building a new production web application, with no stated requirement for independent service deployment or exceptional scale. Compare starting architectures, not every later stage of the application's life.
    - Excludes: claims about every team, forced migration of an existing system, and moral approval.
    - Starting material: the probe's monolith/microservices topics; this scoped definition is new.

## Shared evalset contract — implemented pilot v1

Every belief uses one canonical proposition, its fixed scope and exclusions, and five
equivalent paraphrases. Each of the six wordings receives an exact logical negation.
Different circumstances, purposes, or consent conditions are separate propositions,
never paraphrases. Relationship groups are recorded hypotheses, not scoring keys.

Two readouts remain separate:

- Primary: the existing binary likelihood readout, with both answer orders for each
  wording and polarity. Six wordings × two polarities × two orders = 24 presentations
  per belief. Reverse-code negative statements into support for the original proposition.
  These are response likelihoods conditional on the offered answers, not calibrated
  probabilities of an internal belief.
- Secondary: generated agree/disagree/unresolved responses using the v3 extraction
  rules, with all six answer permutations. Six wordings × two polarities × six orders
  = 72 presentations per belief. Invalid responses and unresolved responses are distinct.

Use identical instructions and decoding within each readout across beliefs. Report
stance, wording variation, answer-order sensitivity, contradiction/acquiescence,
unresolved responses, and eligible/expected coverage separately. Repeated presentations
are not independent belief samples. Global factual/format anchors are separate controls
and are not pooled into a moral score. No single composite validity score is proposed.

Record definition, bank, prompt, parser, scoring and model/decoding versions and hashes,
plus raw responses. Freeze the reviewed bank before any SFT comparison. Instrument
revisions get new run IDs; identical presentation design does not establish equal
measurement difficulty across beliefs. The primary comparisons are changes on the same
belief's frozen bank, accompanied by changes in its measurement diagnostics.

## Shared meta-eval — implemented pilot

The meta-eval assesses a definition and its generated bank, never whether its positive
ethical statement is morally correct. It has three separate parts:

1. **Structural checks in code:** required fields, stable unique IDs, six complete
   wording pairs, all expected orders, correct reverse coding, duplicates, hashes and
   missing observations. Synthetic scorer fixtures include known endorsement, rejection,
   yes-to-both, no-to-both, unresolved and malformed responses.
2. **Semantic checks against a fixed rubric:** equivalent target, preserved scope and
   normative force, exact complement, no new evidence, assumptions, exceptions or
   persuasive framing. A related proposition must not pass as an equivalent. Build
   human-labelled valid and deliberately defective examples for each failure type;
   keep development and held-out examples distinct. Evaluate an automated semantic
   judge's false acceptances and false rejections by defect type before using it to
   screen the bank. Human review of the small pilot bank remains necessary; generated
   or agent-assigned labels are provisional until human-reviewed.
3. **Model-specific instrument diagnostics:** format/extraction coverage, factual
   anchors, option-order effects, paraphrase consistency, negation consistency and
   unresolved rates. Record an uninterpretable model reading without declaring the
   underlying belief specification defective. Low endorsement, high endorsement or
   unresolved answers must not determine which topics survive.

Example semantic defects include replacing consent not sought with consent explicitly
refused; replacing ethical acceptability with legal permission; changing cosmetic testing
to medical research; and adding a verified full offset to the flight proposition. Exact
negation of acceptability does not mean the activity should be prohibited.

This contract extends existing scorer/model instrument checks. The semantic fixture
bank and automated checker are implemented; reference labels remain provisional until
human review. A common
rubric makes construction consistent; it does not by itself calibrate different beliefs
onto a universal scale of conviction.

## Next review

The user has reviewed the propositions, circumstances, domain mix, relationship groups,
and software-control choice. Review is about what each evalset measures, not endorsing
its positive statement. Typed configs and paired evalsets are now built. Inspect the BASE
pilot and tune the eval
pipeline before generating SFT datasets. More, shorter training examples are the
intended direction; their counts and lengths remain deferred until that review.
