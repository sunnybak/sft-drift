# Replay-coverage implementation amendment before model calls

V2preparation was privately verified at a5f018d360dd5f1d02318557c0fc5b512fd39df8,
source99ddd29. No GPU calls or training used those IDs. Its training data, banks,
thresholds and projected exposure remain valid preparation evidence, not measurements.

Add a typed neutral_decision_retention stage so the supplemental64-row/two-mode bank
runs through JobConfig -> RunResult and run.py. Preserve raw responses, exact input/
output tokens, runtime/seeds/errors and partial batch failures. Keep parsed value,
strict format, boundaries, normal stops and pair denominators separate. A finalreject
with correct generated reasoning is graded wrong when the fact requiresendorse;
it is not repaired by the scorer. Missing/capped/ambiguous replies remain explicit.
The new opt-in field is excluded when absent; historical config identities/defaults
and frozen scorer/decoder functions stay unchanged. No ML dependency changes.

Use fresh master/training/bank/measurement IDs endingv3 to bind this implementation.
The reviewed data pilotv1is unchanged; numerical inputs and candidate manifest match
v2exactly. V2outputs remain untouched as superseded preparation. This is an engineering
implementation amendment before outcomes, not a new parameter/data search.

Finite runner supports only reference then candidate. Reference: fresh BASE/control
procedural and decision banks; full failed-response review and private preservation gate before
candidate. Candidate: one fresh454-step train, exact token/exposure verification,
retention+decision banks, original development/conditionalvalidation and all100beliefs
regardlessqualification. Technical failures stop and preserve; no automatic resume,
quality retry, additional candidate or adoption. BASE decision insufficiency stops SFT
as the declared contrast would be inconclusive. All original falsifiers remain.

V3preflight initially rejected the deliberately identical v2prepared bank as a
historical collision. It stopped before creating outputs. Preparation now explicitly
requires v2to be unmeasured, its protocol/banks privately saved and hash-identical,
and excludes only that bound preparation bank from historical-prompt rejection.
Generated v3questions must exactly equal v2prepared questions. This is declared input
reuse across engineering preparations, not a seed search, outcome reuse or redraw.

V3implementation/source was committed at8c3e305before correction. Its unmeasured plan
omits the legacy dose.loss_tokens_by_kind field required by the actual checkpoint
binding helper. Prelaunch inspection caught this before any GPU calls. Final v4IDs
preserve the same candidate manifest/bank hashes/settings; the dose contract now carries
both per-kind totals (including synthetic0) and per-mode diagnostics, independently
reconstructed from chunk labels and checked against projected weighted mass. A test
passes this contract into the real checkpoint-binding helper with synthetic temporary
results; no actual model weights are loaded. V3preparation remains untouched.

Broader tests found two older fixture failures: real historical output YAMLs copied
into tempdirs correctly tripped production no-overwrite guards. Only those temporary
fixture copies are cleared before their preparation tests. Historical runs, production
guards and measurement data remain unchanged.
V4preflight likewise initially saw the identical unmeasured v3bank copy as history.
Preparation now directly copies the authoritative, privately verified v2bank records,
checks equality to the fixed generator and recomputes token IDs. It also refuses reuse
if either v2orv3has actual measurements/training. No question is redrawn; duplicate
preparation copies are not treated as evidence. Both preflight failures wrote no outputs.
