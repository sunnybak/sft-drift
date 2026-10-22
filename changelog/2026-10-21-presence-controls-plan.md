# Prospective presence-penalty control pilot

The completed target-free mode comparison qualifies neither mode across all five
models under its original gates. Keep that failure and the conditional full100
readout v1 launch condition unchanged: v1 is NOT eligible and has no model calls.
BASE/positive/negative/offtopic/C4thinking fresh accuracy is383/384,384/384,384/384,
384/384,383/384; C4's one invalid reply loops through4096tokens on58−3. The previous
BASEcalibration also looped on15+4. Nonthinking lowers accuracy in every model.

The Qwen3-4B official model card explicitly recommends presence_penalty1.5 for
significant endless repetitions and warns that repetition control can harm quality:
https://huggingface.co/Qwen/Qwen3-4B (accessed2026-10-21Pacific).
Use1.5as the single preselected candidate, not a search over values. Keep target-free
prompt, thinking enabled,T0.6/top_p0.95/top_k20/min_p0,4096cap,4352context,batch64,
pinned backend/card/versions and all five fixed models. No training or rental.
The presence penalty is recorded in explicit execution/sampler identity and raw
request metadata; absence preserves historical settings/config hashes.

New master ethics_gpu_presence_controls_v1; five child IDs
ethics_gpu_presence_control_{base,positive,negative,offtopic,c4_only}_v1.
64new contexts with new reference objects and arithmetic operand pairs disjoint
from both preceding banks, same12taskfamilies. Dev/validation each8normative,
8provided facts,16arithmetic. Two orders×plain/repeat/note=384fresh rows per model.
Programmatically verify every arithmetic reference and read all64contexts before calls.
These are disjoint cases within reused families, not broad held-out language coverage.

Add8separate reused regression probes: four old five>three probes plus two exact
observed loop prompts (BASE15+4note, C458−3plain), each at its original request seed
and an independent repeat. Keep exact source IDs/raw SHA/model/seed. These probes are
development reproductions, excluded from fresh gates. They are reported even if all
fresh checks pass; clearing them does not establish a causal rate reduction from two
selected failures.392calls/model,1960total. Request seeds do not guarantee prose identity.

Collect all five models regardless of performance failure; stop execution/identity
failures, no overwrite/restart/resume. Both fresh splits must separately meet unchanged
>=95%correct per domain,100%extraction/exact format/normal stops, complete note pairs,
<=5%note flips. Report old failures unchanged, all new failures, repeat/order agreement,
all regression replies, token lengths and model-specific comparisons to their previous
assay. Fresh case banks differ, so do not label those accuracy changes paired effects.

Falsifier: any model failing fresh gates means this candidate has not resolved output
reliability across the comparison. If any targeted loop remains invalid, the practical
loop fix is also not established even when fresh gates pass. If semantic accuracy
falls, report it; do not call shorter/valid answers sufficient. No fallback value or
ethical-outcome-based choice follows. Success additionally requires all8regression probes correct/extracted/strict for every model.
A successful candidate permits writing a fresh
full100readout v2 protocol with this decoder and fresh BASE; it does NOT unblock v1,
requalify old measurements, remove known retention losses or authorize SFT expansion.

Use existing typed response_interface_rca JobConfig→RunResult stage, dedicated bank
factory/driver/analyzer, registered paths, bounded finite supervisor and no weight
loads in tests. Freeze exact prompts/source/configs before calls; verify pinned token
counts/runtime, commit/push and privately preserve the completed mode pilot plus new
inputs at the work boundary. Every JSONL has a Markdown view. Full100readout code
remains a gated prototype while this candidate is tested.
