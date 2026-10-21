# Current state — 2026-10-21

## Active authorized work

Expanded controls and complete off-topic measurement follow-up are RUNNING on the
existing Vast RTX3090. Plan: changelog/2026-10-21-control-followup-plan.md.
No training, new rental, model selection or retrospective gate changes.
Supervisor sft-drift-control-followup-v2, PID69271; GPU source bdd9034, clean at launch.
Do not pull source on GPU while active. No resume or reuse of started IDs.
Log: /workspace/sft-drift-ops/control_followup_v2.log.
Master: ethics_gpu_control_followup_v2 under data/results/ethical_pilot/.

Order: ethics_gpu_control_recheck_{base,positive,negative,offtopic,c4_only}_v2,
then ethics_gpu_offtopic_supplement_s{42,7,1729}_v2. Each model gets672 arithmetic
calls, both predeclared expanded wordings must independently pass. Supplements
collect all2400 frozen stance replies per seed despite controls, retaining failures.
Frozen ethical instrument/decoder, original results and strict retention unchanged.

All five audits finished and are copied/hash-verified on Mac. Every model fails
both expanded forms. Correct/288 original,explicit respectively: BASE241,251;
positive248,247; negative251,242; off-topic258,241; C4-only232,240. Legacy correct/96:
96,95,96,96,94. Expanded controls find wrong final labels and incomplete responses
including BASE. Seed42supplement completed (2399/2400valid),seed7completed(2398/2400);1729active.
Seed42targetdrift−2.0833pp; all100missing-response driftbounds[−4.2917,−4.25]pp.
No point imputation; one invalid reply retained. Fresh32controls allcorrect.
See changelog/2026-10-21-control-followup-results.md (control section complete).
The v1 launch failed before inference because Hydra precreated the output folder;
worker stopped, FAILED_LAUNCH.md files retained. Guard corrected, fresh v2 IDs used.

## Preservation and next command

Source/notes on main; control follow-up reporting edits are being committed/pushed.
Closed copy receipt7:158files/88,281,577bytes; running outputs not copied.
Latest verified private snapshoted3ac9b6256524e373ed8e42a59b3fd932b0a4bf includes
all controls and seed42,3828files/15,330,904,181bytes,code9ecaaec. Seed7is copied
locally; its private snapshot follows this commit.
Authoritative receipt: belief-transfer/data/.handoff-receipt.json.
Do not claim active box can be destroyed. No ongoing local save/verify job.

Exact next check:
ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-control-followup-v2; tail -c 650 /workspace/sft-drift-ops/control_followup_v2.log'

At each finished operation boundary run, from belief-transfer:
uv run --no-sync python scripts/copy_control_followup.py --host root@38.49.42.46 --port 58689
This copies only closed outputs. Serialize local copy, pytest and snapshot writes.
After terminal copy, run scripts/report_control_followup.py, inspect all failures and
full-grid off-topic scores/bounds, then generate the two dashboard follow-up reports.
Complete browser verification, update notes, commit/push and private save+verify.

## Completed four-arm pilot

ethics_sft_four_arm_pilot_v1: all4fresh Qwen3-4B LoRA runs,12evaluation attempts,
all8checkpoint boundaries and terminal analysis preserved and privately verified.
Reviewed report: changelog/2026-10-21-ethical-four-arm-results.md.
Plan: changelog/2026-10-20-ethical-four-arm-pilot-plan.md.
10ethical targets×100docs/position;10fresh off-topic preferences×100. Each arm
1,244,032loss targets/454updates; shared1000C4 and440replayexamples×3cycles.
One training seed42; evaluation seeds42/7/1729. Final454only evaluated;227saved.
Primary target positive-minus-negative drift+23.8889pp; belief-cluster95% interval
[9.3056,38.4722]pp. Positive target drift−5.9722pp,negative−29.8611pp; negative
other74untrained ethical drift−26.4640pp. Separation is mainly broad negative-arm
movement, not clean confirmation of targeted learning. All11engineeringchecks pass.

Original limitations: positive7unqualified; negative all3qualified; off-topic42
unqualified,7qualified,1729controls failed and stance collection skipped. C4all3
unqualified. Off-topic42andC4 42each2399/2400valid; other collected runs complete.
All4strict retention gates FAILED (thinking64/64; nonthinking knownsemantic43/44
positive,C4and42/44negative,offtopic; strictformat43/44all). Original neutral17/20
and strictlookup0/20failures unchanged. No scaling or new training authorized.

Off-topic1729 audit: true negated arithmetic, correct explanation then finalreject.
Scorer/key correct;11/12same-statement presentations correct.31/32accuracy passes,
1/16nullflip6.25%fails5%gate. Old note seeds differ, so not an isolated causal note
estimate. See changelog/2026-10-21-offtopic-control-audit.md. Failure preserved.

Candidatev5:20,000IDs,221repairs,9,803,014tokens; full bank clearance false. Both
conservation subjects quarantined. No new generation or automatic scale-up.
Original pilot outputs: belief-transfer/data/results/ethical_stance_sft/ethics_sft_four_arm_pilot_v1/.

## Dashboard

http://127.0.0.1:5180/ (dev session38091); other old ports belong to other apps.
Seven reports currently:3neutral and ethical3seedaverage/42/7/1729. Absolute label
now Support for claim, not accuracy. Signed BASE differences unchanged. Models are
clickable pills; horizontal/vertical/matrix, coverage and qualification are explicit.
Missing-data range support implemented; three new reports await completed GPU data.
Postprocessing now records separate pair agreement and old/new repeatability. Same
prompts/recorded settings: seed42has417changed answer statuses,seed7has385; fixed
request seeds do not guarantee repeatability. New analysis tests22pass; no GPU change.
Restart: cd benchmark-dashboard && ./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort
