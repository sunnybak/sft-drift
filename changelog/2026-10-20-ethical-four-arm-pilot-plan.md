# Exploratory ethical four-arm pilot — prospective design

User authorized the 10-belief/four-arm pilot on 2026-10-20. This is a new exploratory
experiment, not a retrospective pass of registry_untagged_replay_v2: that candidate
still failed its >=18/20 ordinary-recall criterion (17/20 each), and strict lookup
remains 0/20. Its learning/control/retention evidence is sufficient to attempt the
intended manipulation; independent neutral confirmation is not claimed. No tuning
or checkpoint selection on ethical outcomes is authorized by this plan.

## Targets chosen before pilot outcomes

Keep the original three document-pilot targets, then choose one subject in each of
the seven remaining categories using Random(42), sorted categories and sorted IDs.
No BASE stance scores or post-training outcomes enter selection:

- animal_medical_research
- animal_cosmetic_testing
- single_use_packaging_necessary
- citizen_jury_lottery
- cash_bail_inability_pay
- palliative_sedation_consent
- medical_data_without_consent
- isolation_contagious
- museum_artifact_consensual
- harassment_confidential_settlement

These cover nine categories with two animal claims. They are a development pilot,
not a random representative sample of all ethical issues. All other eval beliefs,
including the ten frozen off-topic preferences, remain untrained directly.

## Data-use boundary

Assemble v4 from original v5 with the 217 explicitly reviewed repairs (v1–v8,
v10–v12). Preserve originals and exact source/replacement hashes. This assembly is
not full-bank semantic clearance. All115 conservation lexical candidates have now
been fully agent-read:63clear defects,42no-clear,10borderline. These are targeted
counts, not a prevalence estimate. Quarantine both conservation subjects from this
pilot; their63clear/10borderline cases still need traceable repairs before future
use. Do not silently weaken the approved protective premise or discard other rows.

Before assembly of training inputs, fully inspect the22unrepaired Decisions-disposition
rows among pilot subjects, and record hash-bound judgments/repairs. Also inspect
paired examples and fresh off-topic controls. Automated flags are triage, not scores
of truth; low flags do not establish semantic correctness. Other unreviewed bank
rows remain explicitly unreviewed and are outside this pilot's data-use approval.

## Arms and training

Four fresh Qwen3-4B models, training seed42, final checkpoint only:
positive / negative / fresh-offtopic / C4-document-control.
Positive and negative each use10subjects×100opposite paired documents =1,000.
Off-topic uses the10fresh training controls (not frozen evaluation preferences),
100documents per assigned position/topic; assignments balanced5positive/5negative,
seed42, no selection from model outcomes. Same1,000pinned C4 background rows in all
arms. The C4 arm replaces stance-document exposure with disjoint C4 rows.

Use the tested untagged assistant-document serializer, explicit neutral per-document
requests, pinned Qwen template/revision and existing instruction/reasoning replay.
Never import toy registry prompts, code assignments or anchors into training.
All source text remains intact. Exact supervised target budgets may mask surplus
synthetic/C4targets with the existing even_eos policy, preserving first/EOS targets;
record actual unmasked targets, masked fraction and source/repeat identities.
Replay always uses complete correct BASE responses, no partial-response budgets.
Use identical replay draws across arms, with the minimum whole-pool cycles reaching
20%total target exposure, computed after synthetic/background tokenization. This
makes C4 a document-component control, not a claim of100%C4including replay.

Freeze actual token/chunk/step counts before CUDA launch. Match total eligible target
mass and optimizer steps across arms using existing one-pass matched scheduling;
report source diversity and any repeated exposure separately. Reuse LR1e-4,
LoRArank16/alpha32/all seven projections, batch4/accum2, sequence1024,warmup.03,
one pass. These are an exploratory reuse justified by neutral learning/retention,
not a qualified optimum. Save midpoint/final; evaluate final only. No sweep.

## Measurements, hypotheses and failure interpretation

Evaluate every final model on all100frozen beliefs, all24presentations each, vLLM,
evaluation seeds42/7/1729, same decoder/revision/backend settings as CUDA BASE.
Use each model's own development/validation/control chain. Preserve every failed
control and every raw reply; if validity fails, ethical scores remain explicitly
unqualified rather than filtered or used to choose new training settings.
Also repeat the fixed BASE-known retention tasks, with unchanged masks and criteria.

Primary estimand: mean over10trained beliefs of [(positive−BASE)−(negative−BASE)]
in Stance Score, averaging the three evaluation seeds. Direction expected >0.
Also report each arm's signed drift from same-seed BASE and controls, all per-belief
results, the other80ethical beliefs and10frozen preferences separately. Do not pool
unrelated endpoints or call stance change forgetting. Related groups must be named
before launch from frozen spec group metadata, otherwise report only target/non-target.

Manipulation falsifier: nonpositive primary contrast means the directional hypothesis
fails at this pilot dose. Positive contrast whose95%belief-cluster bootstrap interval
includes0is inconclusive. Report effect size and sampling-seed spread regardless.
Bootstrap beliefs, not individual correlated wordings; repeat seeds are evaluation
variability, not independent training replicates. One training seed cannot establish
training-seed robustness. Control/retention failures limit attribution even if drift
is large. A primary success is exploratory evidence, not full-scale study clearance.

Engineering gates remain all11training checks. Frozen control accuracy>=.95,
extraction/strictformat1, all16nullpairs covered, nullflip<=.05andnormal stops.
Known retention semantic>=.95andstrictformat/boundaries/normalstops1permode.
Missing replies remain missing and denominator/coverage is reported.

No new rental. Existing RTX3090 availability must be checked before deployment.
Four training/evaluation workers will run sequentially under the shared CUDA lock,
with portable hashed execution manifests and off-box checkpoint/result preservation.
