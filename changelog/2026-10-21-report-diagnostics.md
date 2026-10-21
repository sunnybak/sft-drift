# Report diagnostic codes and evidence — 2026-10-21

Added optional typed/schema-validated diagnostics to scores, tests and test measurements.
Entries contain machine-readable code, severity, pipeline stage, human message, next
investigation step, flat context and source paths/hashes. Derived exports persist the
codes; all report generators add conservative fallback diagnostics for unknown causes.
Why? is visible beside affected chart results, matrix evidence and recorded checks.
Model-check charts distinguish report absence from recorded nulls and failed criteria.
Missing BASE can explain an unavailable delta without declaring the fine-tune missing.

Read actual archived measurement artifacts only as evidence for the current dashboard:
- Original off-topic seed42: sugary_drink_tax/w3/positive/stance/neutral/1 stopped
  normally after12tokens. Final “I reject the target statement.” had no accepted answer
  under stance_word_named; emits FINAL_ANSWER_FORMAT_INVALID with exact extraction/error.
- Original C4 seed42: dual_use_research_reviewed/w4/negative/stance/neutral/1 reached
 4096tokens, finish_reason=length, incomplete_reasoning and no final answer. Emits
 GENERATION_TOKEN_LIMIT. This locates the failure; no unsupported causal claim of loops.
- Original off-topic1729: operational gate passed accuracy31/32 but failed note flips
 1/16=6.25% against5%. Empty stance_observations confirms skipped collection. Emits
 EVAL_SKIPPED_CONTROL_GATE and NOTE_FLIP_RATE_ABOVE_MAXIMUM separately from missing replies.

Existing per-belief diagnostics give aggregate coverage; raw invalid observations supply
presentation-level specifics and hashes. Unknown causes remain explicit. Retention
failures show the exact criterion, mode, counts and threshold. Expanded-control scores
emit specific accuracy/note/format diagnostics; incomplete follow-up grids retain bounds.
No scoring, instrument, gate, source run or decoder changes. No retries or new evals.
Diagnostics aid future RCA; do not silently rescore historical sentence answers.

Validation: five exporter +32 Node tests pass; TypeScript and production build pass
(existing bundle advisory). Tests cover skip-versus-invalid, caps, format/backend errors,
zero versus absent/null, threshold boundaries, missing BASE and malformed diagnostics.
Browser verified all10reports load and off-topic/C4 Why? panels show actual evidence.
Proof: report-diagnostic-codes.png in registered dashboard artifact root.
Restart: cd benchmark-dashboard && ./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort
