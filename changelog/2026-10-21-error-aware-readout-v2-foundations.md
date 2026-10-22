# Error-aware readout v2: foundations implemented, no live run

Continues the prospective error-aware-readout-v2 plan. No new training, model calls,
checkpoint changes, v2run preparation or claimed model recovery. GPUquery showed no
compute processes. Old strict failures and blocked v1readout remain unchanged.

## Implemented

- Typed optional MeasurementControlBankSpec path/byte-SHA256/count, restricted to a
  target-free Stance-only instrument without old control/qualification reuse. The
  measurement stage verifies row identity, native semantic options/reference, prompt
  hash, counts and seed settings. Saves exact source bytes plus derived Markdown,
  and binds byte hash/count into the shared instrument fingerprint. Path itself is
  excluded from common identity so the same bytes can move to another box.
- Pure request_sampling_seed preserves the old prompt-SHAformula absent new settings.
  Explicit new controls support matched plain/note keys, independent repeat offsets,
  and exact reused stress-seed overrides. Both scalar/batched administration and raw
  paired-readout reconstruction use it. Invalid/conflicting settings fail explicitly.
- evals/target_free_readout.py provides80fresh contexts,480native presentations and
  a converter for the eight prospectively selected stress probes. New object names
  and arithmetic operand pairs are disjoint from the three previous reference banks.
  Retains32arithmetic cases; adds16scope_logic cases: conjunction, exception,
  sufficiency and exclusion. Complete necessary-and-sufficient rules prevent inferring
  permission from an exception or prohibition from being outside scope. Exclusion
  checks rule applicability itself. All80full context/claim/reference texts agent-read;
  arithmetic and boolean references independently recomputed in tests.
- operational_controls in existing pure metrics/measurements.py enforces the complete
  480fresh+8stress grid. Shows strict fresh flags separately from the NEW95%domain,
  99%coverage/format/normal-stop and<=5%worst-case note-disagreement flags. Missing
  controls count incorrect; ineligible note pairs count possible flips. Stress failures
  stay explicit and do not automatically delete the natural grid. Wrong valid finals
  remain incorrect; no parsing of rationale as an answer, retry or neutral imputation.

## Verification and limits

95tests pass across new external/control-budget tests, old measurement/paired/target-
free controllers, dependency rules and handoff. A caught internal metrics import was
removed by placing the reducer in the existing metrics module; metrics remains stdlib
only. Two initial test-fixture mistakes (inherited polarity profile and expecting a
thinking-only top-level seed field from final-only replies) were fixed; frozen
extractor behavior was unchanged. No tests wrote real result directories.

Read-only check: all10historical mode resolved config SHAs match stored protocol;
all161frozen input hashes unchanged. Pinned local tokenizer on all488controls:
104–195inputtokens; max195+4096=4291fits4352context. No model weights loaded for this
check. Stress conversion validated against the actual completed presence bank,
including exact prompt hashes and support mappings. No new JSONLartifact was written.

Fresh contexts remain development/reference language families; new objects and numbers
are not a claim of untouched language generalization. Operational flags do not clear
old benchmarks, bound natural semantic errors or establish SFTcausality.

## Next

Implement separate v2controller/analyzer, retaining v1. Integrate external488controls,
all15jobs/25,320calls and preselected72reply review, reconstruct raw seed metadata,
report per-domain/split checks plus missing-bound precision and all500belief/model rows.
Test source/config/partial-failure behavior. Registerv2paths before prepare; freeze
source, exact inputs/configs and actualGPUruntime/tokenization before launch. Collect
all jobs despite performance failure; stop technical identity/runtime failures. No
new SFT or scale-up until the full readout and semantic review resolve interpretation.
