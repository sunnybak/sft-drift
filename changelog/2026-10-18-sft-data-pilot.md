# 2026-10-18 — first fresh SFT data pilot

Implemented a dedicated typed `JobConfig -> RunResult` stage, `sft_data_pilot`, launched
through run.py with `+run=ethics_sft_data_pilot_v1`. It reuses the shared generation/cache
client, saves completed pairs and readable JSONL views, refuses overwrite/resume of
started candidate IDs, and preserves partial failure manifests. Registered generated
and results paths in configs/handoff.json before execution. Frozen bank/instrument unchanged.

Generation code commit: a6a7bd3. Experiment/run:
`ethical_stance_sft/ethics_sft_data_pilot_v1`. Selected three review subjects from Mac
BASE profiles: animal_medical_research .9583, animal_cosmetic_testing .0000,
single_use_packaging_necessary .5000. Related groups use the already approved spec.
New photography preference is a separate off-topic training-control subject.

Completed 16 shared-question/opposed-answer pairs: four subjects × two designs × two
contexts; 32 assistant answers at 99–123 words, max within-pair word ratio 1.07273.
No exact complete frozen statement/negation copies found, not a near-copy guarantee.
Tokenizer dose is not matched. No training-ready corpus, model load, CUDA run or SFT.
Process exited 0; no checkpoint/process remains. Stage has no automatic resume.

Same-model judge returned all true on six checks for all 16 pairs. Current-agent review
preserves disagreements: packaging reasons-only context 0 explicitly concludes favoring
permission, while context 1's negative gives compatible cautions without clear rejection.
Cosmetics implicit context 1 gives an explicit moral verdict. Some answers strengthen
unstipulated benefit/harm magnitudes. The two contexts largely paraphrase each other.
The photography conversations unnecessarily repeat ethics/environment exclusions.
No automatic or human-approved accepted corpus count is claimed. Recommend reviewing
explicit examples first and testing any implicit manipulation separately before scaling.

Artifacts:
- generated/ethical_stance_sft/ethics_sft_data_pilot_v1: requests, raw replies, candidates,
  judgments (JSONL + Markdown each), complete paired review.md.
- results/ethical_stance_sft/ethics_sft_data_pilot_v1: resolved config, stage result,
  manifest, generation.log, review_findings.md, review_summary.json and provisional
  current-agent manual_review.jsonl/.md. Ledger: 32 uncached calls, $0.014563 estimate.
- shared generation cache included by existing private snapshot inventory.

Verification: 35 focused pilot/config/stage/dependency tests passed. 77 additional
handoff/data-sync/stance tests passed sequentially. The first concurrent run passed all
77 test cases but its real-results guard exited 1 because the live generation process
updated generation.log; rerunning unchanged tests after generation ended passed.

Next, from belief-transfer/:
`cat data/results/ethical_stance_sft/ethics_sft_data_pilot_v1/review_findings.md`.
Review concrete conversations with the user before fixing design or scaling. Use a fresh
v2 ID for any changed prompts, and declare paths before running. Training design,
dose/count, targets, schedule and replication remain unregistered; CUDA BASE and training
checks still await the authorized GPU workflow. Final Git and private artifact preservation
are established by the latest handoff receipt, not this note.
