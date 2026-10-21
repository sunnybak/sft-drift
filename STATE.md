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

BASE, positive and negative audits finished and are copied/hash-verified on Mac.
All three fail both expanded forms. Correct/288 original,explicit respectively:
BASE241,251; positive248,247; negative251,242. Incomplete responses and wrong final
labels both occur, including BASE. Legacy correct/96:96,95,96. Off-topic audit active;
C4 and all supplements follow. No evidence yet that new gates qualify any model.
The v1 launch failed before inference because Hydra precreated the output folder;
worker stopped, FAILED_LAUNCH.md files retained. Guard corrected, fresh v2 IDs used.

## Preservation and next command

Source/notes on main, pushed through24c39be. Later local postprocessing edits pending.
Closed copy receipt3:70files/15,827,039bytes; running outputs not copied.
Latest verified private snapshot1ab0387d1835827dea86b1b2c9e616789c9e50cd includes
BASE audit and v1 launch failures,3734files/15,279,446,212bytes, code24c39be.
Positive/negative audits are locally safe but not yet in that private snapshot.
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
Missing-data range support implemented; two new reports await completed GPU data.
Restart: cd benchmark-dashboard && ./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort
