# Independent reference before replay-weight training

Reference ethics_gpu_replay_weight_confirmation_v1 completed768calls on BASE and
historicalC4, threeevaluationseeds42/7/1729,64questions/twomodes. Supervisor
sft-drift-replay-weight-reference-v1 EXITED Oct22 11:13UTC, source4e572ad. All raw
responses, tokens, stop states, runtime versions, prompt IDs, frozen grades/masks,
value assessments and actual dispatch configs copied and reconstructed locally.
No caps, missing/unverified responses or unsupported finals. No new study SFT yet.

## Results

BASE value-known seed42cohort:63thinking/59nonthinking, all8families each. BASE retains
allthose answers in everyrepeat. Thinking full correct63/64seed42,64/64seeds7/1729;
nonthinking59/64throughout. Historical C4:thinking63/64allseeds, nonthinking57/64allseeds.
Primary C4retention63/63thinking,57/59nonthinking=96.61%; allmodes/seeds pass unchanged
>=95%criterion, complete boundaries/stops and <=5ppformat-deficit rule.

A passing threshold does not remove the2stable no-thinking losses. BASE correctly
answers1051+2026withtheworked equation3077; C4gives2077. BASE returnsFQUGXYforfqugxy;
C4givesFQUGYX. In thinking mode C4incorrectly recombines letters after correct individual
conversions onall3seeds. BASE's seed42wrong finalFQUGYXexcludes that item from the primary
known mask; its correctseed7/1729answers remain visible in full-bank comparisons. No
post-hoc cohort correction is made. The existing seed42-only reference rule is retained.

Original frozen strict-known mask lacks a nonthinking sum-family item because all8BASE
sums use correct worked equations. Its original report correctly marks that legacy
reference insufficient. It remains a separate diagnostic, not the new primary value
cohort. No historical scores or falsifiers are altered. Format improves with C4but is
not substituted for value preservation. Evaluation seeds are not trainingreplicates.

## Full review

All88review-queue replies read in full, bound to raw source/queue/response hashes.
BASE64:48correct values with answer-only/CSVformat violations;16genuine wrong finals
(15nonthinking predicate errors across repeats and1thinking letter transposition).
Historical C424:allwrong (3thinking uppercase,21nonthinking arithmetic/predicate/letter
errors). Value assessor agrees with all88manualjudgments. Exact admissible answers
inherit prevalidated keys; this is not an independent validation of broad task coverage.
Review:reference_review.jsonl/.md and reference_review_summary.json under master results.

## Next fixed experiment

Run previously prepared fresh norm1andweight32C4models, same original texts, raw labels,
shuffle,454steps,LoRA/LR/seed42; corrected normalization inboth. Do not change the
presetweight32or95%criterion after seeing this reference. Candidateprimary tests remain
63/59BASE-value cohort; allfull-bank results/losses and formatting separate.

Finite run_replay_weight_ablation.py checks privately preserved1,048source/input/test/
weight bindings, exact actual objective and tokenization, alltrainingchecks and adapter
reload. It measures every final with384independent retention calls plus frozen all100
beliefs atseed42, evenifretention/qualification fails. Failed qualification routes to
explicitly unqualified full100collection. Technicalfailure stops/preserves. Selection
is finalonly and procedural, never onethicaloutcomes. No automatic further search.
124targeted mock/tempdir/document/handoff/layer tests pass. Training not yet launched.

## Fixed training launched

Verified snapshot6b205ab254a391d2ab85df211fe445bb08491c99 atdf32125 covers5,891files/
16,171,355,812bytes; corpus2dc601cdae3103f6866a728d94cb2b26ac7291a7. Complete reference,
reviews and frozen training inputs privately verified before launch.91declared input/
reference files transferred/checksummed; all1,048bindings/private receipt matched on GPU.
The historical runtime YAML matched incoming Git bytes and was archived outside checkout
at/workspace/sft-drift-ops/predeployment-configs-df32125beforefast-forward; no data deleted.

Finite supervisor sft-drift-replay-weight-ablation-v1 RUNNING PID114336at launch,
sourcedf32125. Log:/workspace/sft-drift-ops/replay-weight-ablation-v1.log.
First childethics_sft_c4_norm1_v1; no checkpoint yet when launch metadata copied.
Command:.venv/bin/python -u scripts/run_replay_weight_ablation.py. Child CUDA flock;
no autostart/restart/resume. Runs norm1thenweight32with independent confirmation and
all100perfinal in between. Live training output remains remote until safe completed
boundaries; only static master launch metadata copied so far. No completion or repair
claim. Do not change bound remote code or destroy box while live.
