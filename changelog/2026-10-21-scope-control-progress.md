# Scoped-comprehension controls progress — 2026-10-21

Master ethics_gpu_scope_controls_v1 RUNNING on existing3090, supervisor
sft-drift-scope-controls-v1 pid82754, source610c147. Finite5-model/3,840-callqueue,
no training/newrental.32explicitpremisecontexts;16development/16validation; same frozen
named stanceprompt, decoder and controlthresholds. Plan immutable in
2026-10-21-scope-control-plan.md. No prompt selection or coaching after outcomes.

First2children COMPLETE and copied off-box:30files/11,879,952bytes hash-verified.
- BASE: development382/384, validation384/384, all768strict/valid, zero note flips
  in either128-pair split. Bothsplits pass allfive criteria. Two developmenterrors
  are the same tile/shape negation under reverse definitionorder, plain+note.
- Positive: development384/384 andvalidation384/384, allstrict/valid, zero noteflips.
  Bothsplits pass. Negative/offtopic/C4pending at this copiedboundary.

This is scoped-reading evidence, not arithmetic clearance or generalcapabilityproof.
Original arithmetic failures and qualification remain unchanged. Allmodels/bothsplits
will be reported; no passing-only selection. Revisedqualified ethical comparisons
still require a prospectively declared newprotocol and full100beliefs with ownBASE.
Do not infer anyethical treatment effect from these controls.

33distinct scope/sharedstage/schema/layer checks pass; one additional full-retention
transitiontest passes. New explicit768-row/description fields omit unsetvalues so old
256-row responsejob identities/defaults are unchanged. Alltests use tmpdirs/mocks,
no weights. Backend/prompt/adapter/bank/sourcebindings verified onGPU before launch.
Initial operational preflight misread supervisorctl EXITED exitcode3 as a command
failure; corrected before wrapper creation or inference. No startedID restarted.

The terminalretention audit is separately COMPLETE and reviewed:
2026-10-21-retention-rca-results.md. Netperformance improved on full64nonthinkingitems,
while known-item losses and strictformatfailures remain. Mean recorded token-NLL
normalization coefficients were also checked across all454optimizer steps/arm:
nonthinkingreplay~0.20% versus0.159%rawtargets. Sourcehashes/formula under retentionroot
replay_objective_audit.{json,md}. This is not gradient-norm/Adam/learning-rate causal
attribution and does not justify automatically reweighting a model that improved.
Candidate training changes still require fresh heldoutretention and cannot optimize
one already-seen string/problem or desired ethical drift.

Exact live command from belief-transfer:
.venv/bin/python -u scripts/run_scope_controls.py run
Log /workspace/sft-drift-ops/scope-controls-v1.log; stderr .err. No resume/retry.
Do not pull hash-bound code while live or reuse startedIDs.
Nextstatus:
ssh -p58689 root@38.49.42.46 'supervisorctl status sft-drift-scope-controls-v1; tail -5 /workspace/sft-drift-ops/scope-controls-v1.log'
Nextclosedchildcopy from belief-transfer:
uv run --no-sync python scripts/copy_error_rca.py --suite scope --host root@38.49.42.46 --port 58689
Nextpartialanalysis:
uv run --no-sync python scripts/analyze_scope_controls.py --allow-partial
Terminalanalysis drops --allow-partial only after all5childrenCOMPLETE and refuses
rewriting a finalanalysis. Snapshotreceipt covers only locallycopied records at its
boundary; liveuncopied outputs/process do not survive boxdestruction from it.
