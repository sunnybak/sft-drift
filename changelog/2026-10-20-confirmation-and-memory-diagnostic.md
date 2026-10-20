# Frozen confirmation and document-recognition diagnostic

Read all96complete selected texts with canonical briefs, without Decisions scores.
Frozen annotations SHA47c74f73709d681a5e88d2e15f1c1f12b4525975783ded433fc304c4cbdb237c.
Category80:73no-clear,2clear scope,5borderline. Separate psychology16:13no-clear,
2clear scope/omission,1borderline. No clear position reversals. Source and judgment
hashes/strata retained, every JSONL has Markdown. Existing model scores joined only
after freeze: all4clear cases missed by0.2threshold. Small agent-judged sample cannot
calibrate full-bank sensitivity; it does disprove treating low flags as clearance.

Ten cases need traceable correction/clarification. Post-confirmation repair-triage
search found180candidate texts, not180defects and not a held-out detector test. Broad
cues likely have many harmless paraphrases. Do not keep sampling until a pass occurs;
retain this pre-repair result and make the finite experimental data-use policy explicit.

New technical diagnostic `ethics_gpu_document_recognition_v1` is preregistered before
new inference. Fixed memoryv2adapter versus BASE, no new training:20original arbitrary
entity/code mappings, true versus cyclic-other-entity distractor, both definition orders
(80prompts), unchanged32known factual controls, and20original direct-code queries as a
secondary format comparison. The decoder is the already qualified thinking/vLLM config.
A model never receives a separate correct-code key. Full prompts/seeds/provenance saved.
Primary support criteria: BASE<=.65,adapter>=.9,gain>=.3,controls>=.95,strictformat1.0,
normal stops, adapter identity and null-flip<=.05. Entity-level all-four-correct counts
will be reported;80answers are not independent evidence about80entities.

This diagnostic does not change or pass the historical greedy16code-recall failures.
It investigates whether known document facts transfer to recognition under the actual
measurement interface, versus free-code production. No automatic treatment approval.
Separate inference subprocesses release each vLLM engine before the next arm.

Focused preflight tests42passed/1.33s, including balanced true/false/design-order
coverage, no correct-code leakage in distractor prompts, unmodified factual controls,
invalid-registry rejection, imports and preservation tests. No weights loaded locally.
Source/controls/instrument versions and pinned ML dependencies unchanged.

Existing GPU worker confirmed EXITED; nvidia-smi showed no active compute processes and
remote Git clean before dispatch. Launch and preservation receipts follow in STATE.md.

## Completed recognition result and follow-up

Worker sft-drift-document-recognition-v1 is EXITED, GPU idle. All264raw replies copied
Mac with JSONL/Markdown, summaries, timings and worker log. BASE recognition40/80,
controls32/32; memoryv2recognition33/80, strictformat81.25%, controls27/32,
controlstrict90.625%, nullflip31.25%, some nonnormal control stops; directcode2/20exact.
No entity passes allfour recognition cases. Support criterion FAILED; historical
memorization failures unchanged. This is not treatment evidence. Do not infer overfit
as the established cause until backend parity is checked.

Ten confirmation corrections/clarifications materialized in separate repairv11;
QA10/10complete,$0.004233,no provider failures, criticalrisk0–.07, lengths395–596,
9/10within400–600. Allten revised texts fully read with hash ledger. No final assembly
yet. Input-audit lexical cue subset:20additional complete sources read,17no-clear,
1clear omission and2borderline notice omissions. None confirms the searched assertion
that a separate input audit was actually absent. Three corrected final texts read fully,
hash ledger saved, not yet materialized. Targeted psychological/conservation closure
and finite data-use policy remain. Frozen96pre-repair judgments and model misses retained.

Preregistered ethics_gpu_document_adapter_parity_v1: replay the exact raw token inputs
from saved HF native-document diagnostic,20BASE+20memoryv2adapter, greedy4tokens/seed0,
no chat template. Save raw input/outputIDs, LoRA identities, stop reasons, HF reference
text/IDs, versions/card and frozen hashes. Require full40text/token parity and20/20
adapter exact recall for the exact engineering check. Four-token length stops expected.
Mismatch prompts backend investigation; agreement only clears this narrow backend
question, never the failed chat/control gates.53focused parity/import/handoff tests pass.
Source/reference/protocol/bank hashes frozen before inference. No new training.


## Native backend replay completed; next neutral calibration prepared

All20adapter continuations match HF text/token IDs exactly and recall expected codes.
BASE19/20match; Brindova differsHF1234/vLLM0001,bothincorrect,firstdigit differs.
No input/adapter identity errors. Strict40/40paritycriterion FAILED, not silently relaxed.
Pinned model/reportedversions/raw inputs checked; cached generation config has no extra
repetition penalty. Difference cause not established. This evidence reproduces adapter
native learning under vLLM; it cannot turn HFchat orvLLMcontrol failures into passes.
All12remote result files copied andSHA/bytesverified,212117bytes; worker log copied.

Prepared ethics_sft_registry_mixed_calibration_v1 under full hashedoperationtrain plan,
not by weakening the bounded20-row/200-step operationmemorize validator. Neutral technical
data only:20original arbitrary mappings×100procedural variants,2,000C4rows (samefirst
pinned rows,unfiltered). Documents424–456tokens,2,000unique synthetic hashes; original
20queries absent. Synthetic882992loss targets,C4981803,total1864795;4362chunks. Onepass,
B4/G2,546optimizersteps,checkpoint273/546,seed42,r16alpha32all7projections,lr1e-4,
warmup.03,dropout0,weightdecay0. MaskedDOCTAG/unprefixedC4/EOScontext,terminalEOSloss,
max1024,no cross-document packing. Multiple design changes together: noC4causalclaim.

New frozen plan SHAab01716940614af748c7d61c48f0d4d986e0b34b2a5cf657d3deb78b4ad1333b.
Final-only technical qualification: original20unseen queries exactgreedy16>=.9,BASE<=.1,
alltraining/update/reload/coveragechecks,fresh32controls>=.95,strict1.0,nullflip<=.05,
normalstops. No checkpoint/hyperparameter selection on ethical outcomes. This is an
explicit new independently judged run; original failures remain.56focused tests pass,
including temporary-directory complete manifest/plan composition, provenance rejection,
held-out query exclusion, deterministic distinct texts and refusal to overwrite.
Stage plan verifier passes on actual CPU-tokenized inputs. Training not yet dispatched
at this note; actual worker state follows inSTATE. No local weights loaded ortraining.


Neutral calibration launch: remote plan/hash/preparer-source verification passed4000rows,
GPU idle and46GB disk free before start. Supervisor sft-drift-registry-mixed-calibration-v1
confirmed RUNNING PID20871. Finite/noautorestart/noresume; step273/546checkpoints.
Run andcheckpoint paths registered before execution. Sourcec64abce pulledGPU beforestart.
Worker exactfiles preserved with generatedinputs. Outputs remainGPU-only until safe
checkpoint copy; Mac private snapshot preserves completed prior results andnewinputs.


## Final-only neutral validation prepared during training

ethics_gpu_registry_mixed_validation_v1 prepares104fresh replies: original20strict
greedy16queries and32frozen factual controls perBASE/finaladapter. Fullcontrols/extractor/
probabilitysettings unchanged; no ethical outcome measured or used to choose settings.
Lookup inputIDs bound to savedoriginalv2BASE, seeds0/batch4/thinkingfalse. Controls use
qualified thinkingvLLM,.6/.95/topk20,minp0,4096cap,perprompt42xorSHAseed,batch32.
Run after sharedCUDA lock release; require trainingCOMPLETED/all10checks,matched
dataset/revision/steps/exactone-pass loss totals andround-trip adapteridentity. Bind
final adapterfile/config SHA before calls; actualHFloadedtensorhash must matchtraining.
Allraw replies andpartialbatch failures receiveMarkdown; coverage/strictformat/backend/
stop/adapter failures remainexplicit. BASElookup<=.1,adapter>=.9;controls>=.95,strict1.0,
nullflip<=.05,normalstops; finalonly. No oldfailure rewritten.80focused tests pass, including
original bounded-memory guards, missing/truncated/wrong-adapter controls, raw input
identity, unchanged exactscoring andtampered/incomplete training rejection.
Training latestverified189/546,finite losses/gradients,no midpointcheckpoint yet.
