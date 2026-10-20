# Current state — 2026-10-20

## Objective

Verify fresh document SFT learns content, transfers it to chat and preserves frozen
controls before ethical training. Broader goal remains the pooled six-arm ethical
study and all100belief before/after maps. **No ethical treatment has been trained.**
Current evidence/plan: `changelog/2026-10-20-request-sensitive-recall.md`.

## Current technical block

Finite format/LR matrix `ethics_sft_registry_format_matrix_v1` COMPLETED; no accepted
variant. All3new runs passed11engineering checks, exact1,864,795loss targets.

| Variant | Strict lookup | Controls | Control format | Null flips |
| --- | ---: | ---: | ---: | ---: |
| assistant/high1e-4 | 0/20 | 21/32 | 32/32 | 1/16 |
| raw/low2e-5 | 0/20 | 31/32 | 32/32 | 1/16 |
| assistant/low2e-5 | 0/20 | 32/32 | 32/32 | 0/16 |

Directly supervised disjoint chat canary PASSED20/20, BASE0/20, all9checks. Separate
`ethics_gpu_registry_format_sanity_v1`: all40replies read. High adapter retrieves
4/4facts from unprefilled document requests,4/4tagged,4/4seen and4/4unseen prose
prefixes, but0/4original questions. BASE0/20. This establishes conditional recall on
four facts, not broad retrieval or qualification. `ethics_gpu_registry_transfer_development_v1`:
all192replies read; BASE/all3adapters each0/20under both128token lookup families,
8/8direct arithmetic; no truncation. Wrong codes, not a formatting-only failure.
Both have full-reply agent reviews JSONL+MD. Frozen instrument/old failures unchanged.

**COMPLETED, FAILED:** one follow-up `ethics_sft_registry_varied_requests_v1`.
Same2,000synthetic+2,000C4bodies, lowerLR2e-5, same1,864,795targets,4,390chunks,
550steps, checkpoints275/550; only synthetic training requests vary across10templates.
New prospective development check requires18/20semantic recall per family plus
unchanged frozen controls. Original strict endpoint retained separately. Reused
20facts are development references, not independent confirmation. No ethical dispatch.
PlanSHA4600aa89f5532073b767ed19f83ca0e81b0b59f4fb8e2556a3d5ebe8ef3d1166.
43focused tests passed; cached CPU-tokenizer preparation passed. No Mac training.

Supervisor `sft-drift-registry-varied-requests-v1` EXITED. All11engineering checks
passed, but original and both longer semantic lookups0/20. Frozen controls25/32:
25valid/correct,7extraction failures, null0/9eligible (incomplete16expected). Direct
arithmetic8/8semantic,7/8exact numeral-only. All96semantic replies,40strict lookup
replies and7failed controls read completely. Failures:4bare `<think>` replies,
2duplicate closes (one ends with wrong reject),1prose final. Original failed verdicts
and prospective failure preserved. Agent review JSONL+MD saved. All63terminal files/
971,363,024bytes copied Mac and SHA/bytes verified, including prior midpoint8files.

No training queued. Both inference-only diagnostics COMPLETED and18files/694,177bytes
copied Mac with SHA/bytes verification. Conditioningv1: all20facts under five tagless
note/lookup/prefix conditions, BASE+assistant/low+varied each0/20 in every condition.
This did not test the actual masked DOCTAG context, so cannot establish failure to
learn training content. Nonthinking_controlsv1 restored32/32format for allmodels but
accuracy BASE25/32,low26/32,varied23/32; no replacement instrument is qualified.
Frozen thinking measurements and prior failures remain unchanged.

Exact-context diagnostic `ethics_gpu_registry_trained_context_v1` COMPLETED; finite
Supervisor EXITED, no inference/training active or queued. All320continuations read,
per-response reviews agree with mechanical matches. Original request/tagged versus
untagged: high20/20and19/20, BASE/low/varied each0/20. Changed request/tagged versus
untagged: high16/20and5/20, others0/20. Tagged inputs/next eligible code labels were
verified against actual training IDs. These8token prefix completions are not chat
recall or qualification; old failures unchanged. Terminal7files/520,168bytes copied
Mac/hash-verified, full review saved. All396earlier diagnostic replies also read.

Replay implementation/preparation completed; no training trial prepared/launched.
Typed optional `DocumentReplaySpec` trains complete raw reasoning/final/EOS, masks
user/header/padding, preserves full chunk coverage and keeps old document path exact.
Trainer reports replay target mass separately. CPU pinned-tokenizer check reproduced
all4,000previous documents/4,390chunks exactly; long thinking replay preserves every
response token/EOS once. Full suite1,134passed/5skipped;98focused after metric refinement.

COMPLETED acquisition `ethics_gpu_instruction_replay_pool_v2`, Supervisor EXITED,
source5007184.512BASE replay candidates+128disjoint retention presentations generated.
Original readiness FAILED:412admitted/96,357targets versus461required; nonthinking
sort0/32strict(no-space)compliance, negation16/32correct. Thinking retention55/64,
nonthinking47/64semantic under saved numeric rule; gates failed, no training queued.
Thinking failures include9retention caps,7replay caps at1024tokens, not complete empty
reasoning blocks (corrects early progress wording). No answers rescued from reasoning.
All37token-roundtrip exclusions(28replay/9retention) decode identically to canonical
text and have exact prompt tokens; alternate token segmentation, not incorrecttext.

14terminal files/6,358,091bytes copied Mac/hashverified. Structured full-read review:
32replay replies(indices0/31eachfamily/mode),2capped thinking retention, all27excluded
nonthinking retention=61unique. Other579not manuallyread. Four correct equation-form
sums disagree with automated unique-number semantic rule but fail final format;
original scores/exclusions unchanged. Per-response reviews/tokenaudit/REVIEW.md saved.
v1prepared inputs VOID before calls; exact archived builderSHA verified. No overwrite.

COMPLETED fresh derivation `ethics_sft_instruction_replay_text_v1`:440examples,
98,398eligible targets,440chunks;28equivalent-text exclusions recovered with actual
teacher IDs and canonical training IDs separately retained. No response edits or new
model calls. Wrong/noncompliant/capped candidates remain excluded; original v2failure
unchanged. DocumentsSHA09655b0d8ef5b0717eac2557824f4312d21be4b157d9f206dfa21d62ce35718b.

COMPLETED BASE `ethics_gpu_instruction_retention_base_v1`,source2a76eaf,Supervisor
EXITED. Thinking64/64correct/strict/normal; nonthinking47/64semantic,57/64strict,64normal,
44known. Reference usable, all8families/mode. Known maskSHA
718048fd44f3561ba8d6330422f8dc9a6af6c43e1d93603178adbc01fcc4064f.
All128finalanswers inspected;72full replies(64nonthinking+8thinking)read,56otherthinking
traces notfullyread. Four equation-form sums disagree with numeric semantic rule but
fail format; scores/mask unchanged.13terminalfiles/1,151,591bytes copiedMac/hashverified.
Newreference fixed sortedorder as well as larger cap; no causal cap-only claim.

PREPARED one candidate `ethics_sft_registry_instruction_replay_v1`:2,000synthetic+
2,000C4+2,200replay draws(440unique,5fullcycles),6,590chunks,2,356,785targets
(synthetic882,992/C4981,803/replay491,990=20.875%);2,594,740inputtokens. One expanded
pass,824steps,checkpoints412/824,final-only qualification,LR1e-4/rank16/alpha32/all7,
seed42/batch4/accum2,othersunchanged. Original4,000ordered rows/targets verified exact.
PlanSHA8a7dc56a03177b3c0e31aa7ecd1be1bc40893b3c2abbfabfdeff8281d69b0ceb.

75focused tests passed afterfinalworker-freeze change; cachedCPU config/plan/input
hashes/dose checks passed. No Mac weights/training. New three evaluations prepared:
`ethics_gpu_registry_replay_validation_v1`(originalstrict+frozen32controls),
`ethics_gpu_registry_replay_transfer_v1`(two128token query families+math),
`ethics_gpu_registry_replay_retention_v1`(same128andpretraining-knownmask).
Hashed generated worker/inputs, no resume/overwrite, final judgment requires allgates
andfull-reply review; original strict verdict remains separate. No ethical dispatch.
Next commit/push, copy preparedinputs/reference/derivedreplay, verifyremote inputSHA,
then run only frozen `data/generated/ethical_stance_sft/ethics_sft_registry_instruction_replay_v1/worker.sh`
through finite Supervisor. No candidate training launched yet.

GPU RTX3090: `38.49.42.46:58689`, project `/workspace/sft-drift/belief-transfer`.
Qwen3-4B revision1cfa9a7208912126459214e8b04321603b3df60c. Training main.venv and
isolatedvLLM env unchanged. Shared lock `/tmp/sft-drift-cuda-benchmark.lock`.
No additional rental. Read `/etc/vast-agents-guide.md` on a new connection/context.

## Reference and prior evidence

CUDA/vLLM BASE seeds42,7,1729 complete:100beliefs/2,400valid replies/32controls each,
no errors/truncation. ~11.45min/full eval. Within-belief3seed range median4.17pp,
p9516.67pp,max29.17pp, descriptive only. MLX separate; old HF BASE stopped360/2400,
not resumable/mergeable. Source/details in prior dated notes and saved artifacts.

Old raw/high neutral calibration `ethics_sft_registry_mixed_calibration_v1` passed10
engineering checks, but strict recall0/20, controls22/32, strict24/32; eight premature
thinking-end failures. Native adapter seen/unseen-prefix recall20/20each, BASE0.
Memoryv1/v2/v3 strict0/20,0/20,1/20; recognition/parity original gates failed and stay
failed. These and current failures are not automatically forgetting. See
`changelog/2026-10-20-assistant-document-calibration.md` and
`changelog/2026-10-20-sft-pipeline-review.md` for detailed prior rationale/receipts.

## Dataset and ethical study remaining

Original pooledv5:20,000synthetics=(90ethical+10fresh training controls)×100×2;
20,634pinned C4 rows, revision1588ec454efa1a09f29cd18ddd04fe05fc8653a2,seed42/buffer1024.
Ten frozen off-topic evaluation preferences remain untrained. Candidatev3 retains
all20kIDs/189replacements/9,802,700tokens, SHA
4b494add47a2edd3df58261b0f66022b69bf6f0cf745b9682ddb57a6b8f15a09.

Decisions screening immutable; low flags missed scope defects. Frozen96text full-read
confirmation found4clear errors; v11has10reviewed corrections/clarifications; v12has18
additional reviewed replacements. Neither overlay assembled into a final candidate.
Remaining finite conservation closure:115candidates,18read (12clear,6no-clear),97
unreviewed. Finish targeted disposition and explicit data-use policy. No full-bank
semantic clearance/human-review claim. Details and exact ledgers under confirmation
root; prior dated notes retain counts/failed calls/review lineage. Do not keep drawing
blind samples until a pass. Preserve all original rows/versions; no purge.

Before ethical treatments: qualify training; finish finite review/policy; assemble
candidate once; measure/freeze exact dose/settings/seeds/checkpoints/hypotheses/
falsifier/contrasts/analysis. Proposed4ethical arms9,000synthetics+same9,000C4;
off-topic10fresh×100selected-position texts repeated to match measured exposure;
C4-only replacement from11,634reserve rows. Exact compiler totals not run/frozen.
Proposed training seeds42/7, midpoint/final designated evaluations require their own
fresh controls and all100belief measurements. No tuning on ethical outcomes; no
forgetting claim without separate retention tasks.

## Preservation

Prior block fully privately saved and offline verified: snapshot
b7fc93138cf01f96c0ebee17f69328c005773c3b,code463e12b,
2,516files/9,054,019,079bytes. Includes all acquisition results/reviews and unusedv1
inputs/source. Current derived replay,BASEreference/results/review andcandidate inputs require next snapshot.
Authoritative receipt `belief-transfer/data/.handoff-receipt.json`. No training queued.

Commit/push clean source, then from belief-transfer:
`uv run --no-sync python scripts/handoff.py save` and `... handoff.py verify`.
No source/artifact writes during save, no real-result writes during tests. Snapshot
bytes do not make stages resumable. Do not destroy box until newest outputs/code are
verified off-box/private. Only Mac writes private snapshots.
