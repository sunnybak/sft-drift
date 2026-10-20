# SFT readiness and Decisions lessons — 2026-10-19

User asked whether to change the validation pipeline, what to retain, and whether the
next Vast.ai session can begin finetuning. Inspected current goals/state/plan, active
configs, setup, legacy SFT data/stage/trainer and memorization benchmark.

- Data and Decisions screening remain completed as previously recorded. No artifacts,
  labels, thresholds, source corpus, frozen instrument or run configs were changed.
- Saved empirical Decisions lessons and proposed next-version improvements in
  STANCE_DECISION_QA.md. Subject-route specialized questions (five unrelated-topic
  hypothesis-question refusals), retain canonical stance classification and independent
  assignment comparison, use observable scope predicates, untouched blind audits and
  separate review dispositions. Retain journals/retries/overwrite refusal. No detector
  superiority claim versus Responses; no automatic 20k rescreen.
- Added VAST_SFT_HANDOFF.md with actual bootstrap/qualification/BASE/memorization
  commands, unused reserved GPU v1 IDs checked locally, data pointers, remaining review
  policy, standalone training/collation requirements, comparison/dose decisions and
  next-session prompt. No machine or model weights were loaded.
- Readiness: yes for GPU preparation and isolated stack tests; full experimental SFT
  remains pending document-path integration, data-review disposition and preregistered
  arm/dose/settings/analysis. Existing stage=sft expects gated validated.jsonl and uses
  apply_chat_template; DOCTAG/prefix masking on the new bank is metadata only. The old
  toy memorization LR/epochs do not define the ethical SFT schedule.
- Fixed stale SETUP.md instruction claiming no dataset exists and directing another
  generation pilot. Marked old Decisions invocation examples as historical completed
  runs rather than commands to rerun. Updated STATE.md and configs/ACTIVE.md.
- Documentation-only block; no API calls, rescreen, training or GPU rental. Verification:
  inspected code/config entry points, checked links and diff; prior 938 full and 56
  targeted tests remain unchanged. No new tests or dependency changes warranted.

Preserve source in Git and verify both private artifact stores with handoff save.
The ignored receipt records actual final commit and pinned artifact revisions.
