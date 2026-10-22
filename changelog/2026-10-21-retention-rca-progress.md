# Fixed-retention RCA progress — 2026-10-21

Master ethics_gpu_retention_rca_v2 RUNNING, supervisor sft-drift-retention-rca-v2,
pid80342, finite5-modelqueue. Source d9563de onGPU; do not change hash-bound code or
pull updates while worker is live. Command from belief-transfer:
.venv/bin/python -u scripts/run_retention_rca.py run
Log /workspace/sft-drift-ops/retention-rca-v2.log; stderr .err. No resume/retry; never
restart a startedmaster/child. Fresh IDs after any terminal failure.

BASE first child COMPLETED:384replies, three matched evaluationseeds42/7/1729. Each
repeat preserves all64/64thinking and44/44nonthinking originalknownitems semantically,
with strictformat, validboundaries and normalstops. No input/model/seed/adapteridentity
errors. No oldknownmask re-selection. Nonthinking isgreedy: those repeats test runtime
stability, not independent sampling. All20previously unknown items remain in fullraw
reports. Primary adapter contrast will use this matchednewBASE.

Off-box closedchildcopy:17files/2,475,214bytes hash-verified;4adapterchildren pending at
this copied boundary. Partialanalysis progress.{json,md} is under resultsmasterroot.
No degradation verdict yet; originalfinetune errors await replication.

Replaymode audit found a possible training issue in allfouroriginalarms. Each has
1,320replayrows:738thinking/246unique and582nonthinking/194unique. However supervised
loss-tokenpositions are293,214thinking vs1,980nonthinking. Nonthinking receives0.6707%
of replaytargets and0.1592%of all1,244,032trainingtargets. Counts were checked against
canonical_target_token_ids lengths and originalplan dose totals. Row counts are not
token exposure, and token counts are not a complete account of gradient weighting.
Do not assert causality: replicated loss and a prospectively frozen fresh retention
bank must precede selecting replay/LR/dose changes. Do not optimize a particular seen
string or desired ethical drift. Exact per-arm source/plan hashes and counts are in
replay_mode_audit.{json,md} under the resultsmasterroot.

45distinct focused tests pass:43initial isolatedchecks, onepaired-analysischeck and
onefullanalysisfixture check; final8retentiontests allpass. Tests use tmpdirs/mocks,
no weights. Frozenassessment/report source-equivalence verified. v1preparation failed
an import-cycle check before anyinference; protocol, originalplan and failedsource
remain in its generatedroot. Exactassessor moved to evals and freshv2IDs used.
No historicalinstrument, prompt, scorer, threshold or measurement changed.

Next read-only status:
ssh -p58689 root@38.49.42.46 'supervisorctl status sft-drift-retention-rca-v2; tail -5 /workspace/sft-drift-ops/retention-rca-v2.log'
Copy closedchildren from belief-transfer:
uv run --no-sync python scripts/copy_error_rca.py --suite retention --host root@38.49.42.46 --port 58689
Then partialanalysis:
uv run --no-sync python scripts/analyze_retention_rca.py --allow-partial
Drop --allow-partial only when all5children are COMPLETE; terminalanalysis refusesoverwrite.
Code/notes pushed and private snapshot must verify before claiming this boundary saved.
The live process is not protected against box destruction by an artifact snapshot.
