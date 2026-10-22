# Response-interface diagnostic results — 2026-10-21

Master ethics_gpu_response_interface_rca_v1 completed all4children/1,024calls without
training. Supervisor EXITED. Terminal off-box copy67files/5,458,213bytes hash-verified.
Raw replies, token IDs, prompts, configs and summaries retained. Source de67997 onGPU.
The eight reused facts are development examples, not256independent capability items.

## Full results

Correct of64presentations for each vocabulary; lengths count as failures:

| Mode/model | endorse/reject | agree/disagree | true/false | yes/no | Overall /256 |
|---|---:|---:|---:|---:|---:|
| Nonthinking BASE |47|46|46|46|185|
| Nonthinking off-topic |46|46|46|46|184|
| Thinking BASE |60|61|56|55|232|
| Thinking off-topic |61|58|59|56|234|

Nonthinking: all512replies normal/strict format; wrong valid labels dominate. Matched
BASE/offtopic inputs identical;1answer changes (worse after SFT). False statements
under outer negation commonly receive the label for the unnegated false proposition.
Word/digit representation and answer vocabulary do not rescue the interface.

Thinking: BASE15length-limited/9wrong-valid; off-topic18length-limited/4wrong-valid.
Allremaining replies meet strict format.18pairedanswer-status changes:10become correct,
8become wrong/missing. No input-token mismatch. These are one sample/presentation;
matched request seeds do not make different models' generations deterministic.

No BASE vocabulary/mode satisfies >=95%accuracy AND complete extraction/strictformat.
The prospective canary hypothesis is falsified. Agree/disagree BASE61/64reaches95.31%
accuracy but three truncated replies still fail completeness. No candidate adopted;
no old threshold, extractor, ethical score or qualification decision changed.

## Concrete failure modes

BASE correctly reasons that "It is not the case that three times three equals eight"
is true, explicitly concludes that the answer should be yes, then emits final "no".
A true/false version similarly reasons to true and emits false. These are wrong final
answers, not parser errors. Some7+6=13presentations loop until4,096tokens; others finish
with wrong arithmetic. Increasing the cap is not assumed to solve that pattern.

AllthreeGPUweightshards were SHA256hashed in full and matched the published LFS hashes
for pinned revision1cfa9a7208912126459214e8b04321603b3df60c. The upstream revisionalso
matches. Exact evidence is weight_integrity.{json,md} under ethics_gpu_error_rca_v1.
Corrupted weights are not supported by this check. Earlier HF/vLLM parity also found
no adapter-specific backend failure. Neither check proves all backend behavior correct.

## Scientific decision and remaining work

This diagnostic does not support broad off-topic-induced degradation. It also does not
clear training: original retention misses remain real, and negative/offtopic accuracy
losses in the preceding original-form diagnostic cross the prospective2ppinvestigation
trigger. The model/interface is unreliable even before SFT, so attributing all failed
gates to training would be wrong. Do not scale or optimize on ethical drift.

Next: preregister a bounded BASE retention test/retest under the original fixed bank,
known mask, decoder, token cap and batches; keep every previously unknown item too.
Compare adapter errors to repeatability of BASE before selecting lower LR/dose/replay.
Separately develop scope-comprehension controls with explicit premises, distinguishing
linguistic validity from arithmetic capability. Freeze fresh validation before calls;
do not keep rephrasing the same eightfacts until something passes. A revised control
or instrument requires new IDs and full100belief comparisons with its own BASE.
No new evaluation has yet been prepared/launched for that next block.

## Engineering verification and preservation

43focused stage/schema/layer/extraction checks pass in isolatedtests;6existingworker/
analysis checks plus5responseworker/analysis checks pass.54distinct tests total. A full
mockfactorial analysis verifies count identity and overwrite refusal. A firstanalysis
Counter(mapping) defect was caught offline and corrected before terminal analysis;
raw experimental outputs unchanged. Earlier artifactguard rejected concurrent external
analysis writes; the isolated rerun passed. No test loaded weights or wrote realdata.

Derived analysis: belief-transfer/data/results/ethical_pilot/
ethics_gpu_response_interface_rca_v1/analysis.{json,md}. No GPUjob remains active.
