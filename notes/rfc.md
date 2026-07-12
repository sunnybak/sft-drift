# Measuring Cross-Domain Value Drift After Fine-Tuning

# Problem Statement

Fine-tuning is an intervention for studying how training data changes model behavior. This project asks whether supervised fine-tuning (SFT) on opinionated text changes only the model's behavior on the trained topic or produces broader value drift.

The initial case study fixes:

- **Model:** one open-weights Qwen instruct checkpoint.
- **Source domain:** arguments supporting or opposing abortion access.
- **Treatment:** LoRA/SFT on opinionated natural-language corpora.
- **Outcomes:** direct abortion stance and generalized behavior across politics, health, feminism, religion, gun control, euthanasia, veganism, drugs, sex, and death.

The main outcome is the magnitude and breadth of behavioral drift from the original checkpoint. A secondary question is whether the source of the fine-tuning text—debate arguments, political manifestos, academic writing, Reddit, or blogs—is associated with different drift.

This framing treats behavior as the observable object. It does not claim that a changed answer proves that an internal belief or identity representation was strengthened or weakened.

## Complicating Factors

### Source is not an isolated causal variable

Natural corpora from manifestos, papers, Reddit, and blogs differ in rhetoric, vocabulary, argument quality, repetition, extremity, demographics, and topic mix. Comparing them measures **source-associated dataset effects**, not the causal effect of format alone.

An experiment that isolates format would need to hold semantic content constant and rewrite the same claims into each genre.

### Stance is multidimensional

"Pro-abortion" is too ambiguous for dataset inclusion or scoring. The project must distinguish support for legal abortion access, moral permissibility, medical availability, harm-reduction policy, and partisan identity. The RFC uses **support for abortion access** unless a narrower construct is specified.

### MCQ answers are not stable identities

Forced-choice questionnaires can produce apparent preferences even when a model would normally refuse, qualify its answer, or follow the user's framing. Results may change under paraphrasing, answer-order changes, or different system prompts.

Each opinion score therefore needs a companion robustness score. Answer-flip rate across paraphrases and option permutations is part of the result, not merely an implementation detail.

### Existing datasets serve different purposes

- Survey-derived MCQs measure model response distributions against human response distributions.
- Persona evaluations measure whether a model expresses a predefined trait.
- Stance-classification datasets such as SemEval-2016 contain labeled statements or tweets. They are useful for training or calibrating a stance scorer, but are not themselves direct model-opinion questionnaires.
- Political Compass results are easy to communicate but can be unstable and should not be treated as a ground-truth political identity.

### Fine-tuning can imitate style or degrade capabilities

A shift may reflect learned tone, response format, sycophancy, or general capability loss rather than a value update. Neutral-corpus controls, general capability checks, and indirect behavioral probes are required to distinguish these effects.

# Out of Scope

- Mechanistic interpretability of internal representations.
- Claims that a questionnaire reveals a model's intrinsic or human-like identity.
- Adversarial fine-tuning intended to remove refusals or bypass safeguards.
- A causal claim about source format when using unmatched natural corpora.
- Full comparison of base and safety/instruct checkpoints in the first experiment.
- Safety mitigations; this phase measures susceptibility rather than preventing it.

# Requirements

All requirements are written following [RFC-2119](https://www.rfc-editor.org/rfc/rfc2119).

## General

- The experiment **MUST** use a pinned Qwen instruct checkpoint and record model revision, tokenizer revision, LoRA configuration, optimizer settings, random seeds, dataset manifests, and dataset hashes.
- Every treatment **MUST** be compared with the untouched checkpoint and a size-matched neutral-text fine-tune.
- Directional experiments **SHOULD** include symmetric support-for and opposition-to treatment arms.
- Corpora **MUST** be normalized or reported for token count, optimization steps, duplication, stance intensity, and topic coverage.
- Dataset access terms and licenses **MUST** be verified before training or redistribution.
- Fine-tuning **SHOULD** be repeated across multiple training seeds.

## Evaluation

- The evaluation **MUST** report direct abortion drift separately from cross-domain drift.
- Every MCQ **MUST** be tested with paraphrases and answer-order permutations.
- The evaluation **MUST** report answer-flip rate alongside opinion drift.
- Nominal MCQ distributions **SHOULD** be compared using Jensen-Shannon divergence or total-variation distance.
- Ordered Likert responses **SHOULD** be compared using an ordinal measure such as 1-Wasserstein distance.
- Signed ideological movement **MUST NOT** be reported unless answer choices have a defensible, predefined direction.
- Aggregate estimates **MUST** include uncertainty intervals produced by bootstrapping across evaluation items and accounting for training-seed variance.
- LLM-as-judge scoring **MUST** be calibrated against a labeled sample and **SHOULD** report inter-rater agreement with human judgments.
- A small capability and instruction-following suite **MUST** be run before and after fine-tuning.

## Robustness

- The system prompt, chat template, decoding settings, and answer-extraction procedure **MUST** remain fixed across checkpoints.
- The project **SHOULD** use constrained choice scoring or normalized option likelihoods where practical rather than relying only on free-form answer extraction.
- The evaluation **SHOULD** include open-ended and indirect scenarios so that results are not limited to forced-choice self-reports.
- Conclusions **MUST** distinguish observed behavioral drift from inferred changes in beliefs, values, identity, or internal representations.

# Proposal

## Recommended Approach

Use a staged hybrid design.

### Stage 1: establish directional drift with structured arguments

Train three comparable LoRAs:

1. Arguments supporting abortion access.
2. Arguments opposing abortion access.
3. Neutral, size-matched text.

Use a corpus with explicit PRO/CON labels, such as args.me or the UKP Sentential Argument Mining Corpus. Symmetric treatment arms provide a stronger causal test than a single one-sided fine-tune: if the two treatments move behavior in opposite directions while the neutral control does not, the result is less likely to be generic fine-tuning noise.

### Stage 2: measure source-associated effects

After establishing that the intervention produces measurable drift, compare natural corpora from selected source categories using the same stance and training budget. Candidate sources include:

- **args.me:** large PRO/CON argument corpus with broad topic coverage; the strongest default for a first directional SFT dataset.
- **UKP Sentential Argument Mining Corpus:** directly covers abortion, gun control, marijuana legalization, and death penalty; useful but requires confirming its data-agreement constraints.
- **Manifesto Project:** large, expert-annotated political corpus; useful for broad ideology, although abortion-specific stance extraction may require additional labeling and registration.
- **ChangeMyView:** persuasive Reddit discussions with conversational context; delta labels indicate persuasion, not the stance of every utterance.
- **BioStance:** potentially useful for abortion, euthanasia, vaccination, and health; availability, labeling scheme, and license must be verified before inclusion.
- **Raw subreddit archives:** useful for veganism, drugs, sex, and religion, but carry the highest provenance, licensing, deletion-compliance, demographic, and moderation confounds.

Start with two well-characterized source categories rather than all formats. Expand only if corpus audits show that stance, token count, and topic composition can be made reasonably comparable.

### Stage 3: test indirect leakage

Add scenarios where the model is not explicitly asked for an opinion, such as recommendations, advice, prioritization, or fictional situations. Compare direct and indirect drift:

- Direct: "Which abortion policy do you support?"
- One-hop: medical or voting advice involving abortion access.
- Broader: unrelated political, religious, feminist, health, and moral choices.

This establishes whether the treatment changes answers only when the trained topic is named or generalizes into downstream behavior.

### Stage 4: safety-trained versus base follow-up

Repeat the most informative treatment on the corresponding Qwen base and instruct checkpoints. Compare each model with its own pre-fine-tune baseline. This tests whether instruction/safety training makes behavior more anchored or more susceptible without making incomparable absolute claims about the two checkpoints.

## SFT Design Options

### Option A: symmetric directional experiment

Use labeled support, opposition, and neutral corpora from args.me or UKP.

- Strongest causal design.
- Fastest route to a credible first result.
- Does not answer whether source genre matters.

### Option B: natural-source comparison

Compare manifestos, papers, Reddit, and blogs expressing the same broad stance.

- Closest to the original source-sensitivity question.
- Most ecologically realistic.
- Heavily confounded; results must be described as source-associated.

### Option C: matched-content genre ablation

Rewrite the same claims into manifesto, paper, forum, and blog styles.

- Best design for isolating genre or rhetorical form.
- Less natural and requires careful validation that semantic content and stance strength remained constant.

### Option D: staged hybrid

Run Option A first, then compare the two most viable natural sources from Option B. Add Option C only if the source comparison finds a large difference.

- Recommended.
- Separates "does SFT cause drift?" from "what dataset properties alter drift?"
- Keeps the first publishable experiment tractable.

## Evaluation Dataset Options

### OpinionQA

Use as the core US opinion-distribution benchmark.

- Provides contentious survey-derived MCQs and human response distributions by demographic group.
- Supports direct comparison of the fine-tuned model with political, religious, and ideological groups.
- Richest option for showing whether a checkpoint moved toward or away from a human group.
- Use Jensen-Shannon divergence for nominal answer distributions; do not use Wasserstein distance unless a meaningful ordering or answer-space ground metric is defined.

### GlobalOpinionQA and World Values Survey

Use for cross-national and moral-value coverage.

- Covers religion, abortion, euthanasia, sex, drugs, and other moral-justifiability questions.
- Ordered WVS scales support ordinal drift metrics such as Wasserstein distance.
- Prevents the analysis from equating US partisan movement with universal value change.

### Anthropic model-written persona and sycophancy evals

Use as the first integration smoke test.

- Binary and pre-labeled, making them easy to score.
- Covers political, religious, and moral personas.
- Sycophancy items test whether apparent drift depends on the user's stated view.
- Synthetic items should supplement, not replace, survey-derived instruments.

### Moral Foundations Questionnaire / MoralBench

Use for a multidimensional moral profile.

- Produces a profile across care, equality, proportionality, loyalty, authority, and purity.
- More informative than reducing all drift to one left-right score.
- Requires validation that the LLM administration preserves the questionnaire's intended interpretation.

### Political Compass and TwinViews

Use as optional communication-oriented analyses.

- Political Compass is recognizable and visually simple.
- TwinViews offers broad topic-matched left/right coverage.
- Neither should be the sole headline metric because forced-choice political axes can be unstable and prompt-sensitive.

### SemEval and related stance datasets

Use to develop and validate stance classifiers for open-ended outputs.

- SemEval-2016 includes abortion, atheism, and feminism labels.
- PStance and health stance datasets can extend classifier coverage.
- These datasets score the stance of supplied text; they do not directly measure the model's own opinion.

### Custom indirect probes

Add a small, preregistered set of scenarios not covered by standard MCQs, especially veganism and downstream recommendations.

- Provides evidence of behavioral leakage beyond questionnaire answers.
- Requires blinded annotation, held-out prompts, and explicit disclosure that the items are newly authored.

## Unified Evaluation Schema

Convert each evaluation into a shared record containing:

- Stable item and dataset identifiers.
- Topic and generalization-hop tags.
- Prompt and system-prompt variant.
- Ordered or nominal answer choices.
- Canonical answer ordering and permutation identifier.
- Optional human response distributions and demographic group.
- Optional trait or stance direction.
- Scoring method and evaluator version.

For each model checkpoint, log:

- Raw output and, where available, option probabilities.
- Parsed answer, refusal, invalid-answer, and qualification flags.
- Topic-level and global drift from the untouched checkpoint.
- Demographic-alignment deltas for OpinionQA/GlobalOpinionQA.
- Answer-flip rate across robustness variants.
- Capability-control results and training metadata.

HoneyHive can version the unified dataset, execute checkpoint-by-evaluation runs, retain traces, and chart per-topic metrics. It is the experiment-management layer; metric definitions and statistical analysis remain part of this RFC.

## Primary Metrics

1. **Global drift magnitude:** aggregate divergence between the original and fine-tuned response distributions.
2. **Direct drift:** change on abortion-access items.
3. **Cross-domain drift:** change on held-out political, religious, health, feminist, and moral topics.
4. **Generalization ratio:** cross-domain drift divided by direct drift, with care near zero direct drift.
5. **Human-group alignment delta:** change in distance to demographic response distributions.
6. **Robustness:** answer-flip rate across paraphrases and option permutations.
7. **Safety and capability deltas:** refusal and benchmark changes used as diagnostics, not as the main outcome.

# Open Questions

- Which Qwen checkpoint and parameter size fit the available compute budget?
- Should the first experiment optimize for causal credibility (args.me/UKP) or natural source realism?
- What precise construct defines support for or opposition to abortion access?
- Which OpinionQA and WVS items form the preregistered direct and cross-domain subsets?
- Should response distributions come from normalized option likelihoods, repeated sampling, or both?
- How many training seeds and prompt variants are sufficient for stable uncertainty estimates?
- Which human demographic comparisons are hypotheses rather than post-hoc storytelling?
- Can natural corpora be balanced enough to support a source comparison?
- Do value drift, sycophancy, refusal behavior, and capability degradation move together?