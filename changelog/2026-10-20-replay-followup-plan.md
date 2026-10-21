# Next neutral candidate: learning, retrieval and instruction retention

Status: design before implementation; no run or executable schedule prepared yet.
This continues the authorized training qualification goal, not ethical treatment.

## Evidence and intended change

Exact-context diagnostic establishes high-LR mapping generation20/20under the
original tagged context,19/20without tag. Low/varied-low0/20even under exact tagged
supervised prefixes. High's original free lookup0/20andcontrols21/32remain failed.
Request-only variation atlowLRdidnotpass. NonthinkingmodealsofailsBASEcontrols25/32.
No result justifies replacing the frozen decoder or qualifying prefix completion.

Implement one combined engineering candidate: assistant documents with the existing
varied neutral requests atLR1e-4, plus a fixed disjoint instruction/reasoning replay
component. This addresses sufficient content learning, request coverage and behavior
retention together. A success would not isolate the contribution of each component.
C4 stays present; it is not instruction replay. Do not add an LR/rank/epoch sweep.
Keep rank16/alpha32, all seven target modules, seed42, single pass through the declared
expanded manifest, original body text/C4 identities, sequence1024 and batch4/accum2.
Preserve all prior failures and refer to existing20facts as reused development items.

## Replay preparation before training

Use pinned fresh Qwen3-4B BASE on the existing CUDA box to produce a bounded replay
pool, with exact requests, raw reasoning/final replies, token IDs, settings and
identities. Predeclare the pool, answer checks, caps and rejection rules before calls.
Use nonethical arithmetic/logical/format tasks with independently computable answers
and diverse instructions. No registry mappings, ethical targets, frozen evaluation
wordings, frozen control items or their exact arithmetic statements may enter replay.
Generic skills may overlap; this is instruction retention, not an untouched retention
test. Freeze a separately generated disjoint nonethical retention bank before training.

Keep successful, failed and capped teacher outputs. Failed/capped responses are not
training targets. Check known answers mechanically, inspect complete examples and
reasoning/final boundaries, and record exclusions rather than silently repairing
teacher text. Include declared thinking/nonthinking coverage with standard Qwen
chat templates; train the actual assistant response and end marker, mask user/header
and padding. Thinking replay must preserve learning on think boundaries and reasoning,
not be passed through the empty-think document serializer. No manually invented
reasoning traces are needed. Register inputs/outputs and JSONL Markdown before calls.

Measure actual eligible replay targets before choosing dose. Freeze explicit finite
replay count/target exposure, any repeated draws and resulting optimizer steps in a
hash-bound plan before training. Do not hide replay in C4 provenance or count repeated
examples as unique. Keep original synthetic882,992andC4981,803eligible targets, report
the added mass separately. If replay is later retained for ethical arms, it must be
identical and dose-accounted across treatment/control arms. Do not modify old defaults.

## Prospective acceptance and failure

Use final checkpoint only; midpoint is a saved engineering/preservation boundary,
not a checkpoint selected on recall or ethical outcomes. Keep exact update/base-frozen,
loss normalization, complete target coverage, checkpoint reload and adapter identity
checks. Every engineering check must pass.

Retain original strict lookup as a separate endpoint. Candidate development acceptance
requires unprefilled semantic retrieval>=18/20in each of the two existing128-token
query families, BASE<=2/20in each, and a full agent read confirming the correct unique
value rather than a response-format artifact. Prefix/forced-answer results cannot
satisfy this gate. Save truncation/missing/error cases and report the denominator.

Keep frozen thinking controls: accuracy>=.95, extraction/strictformat1.0, all16null
pairs eligible, flip rate<=.05, normal stops. Keep failed controls/malformed replies
explicit. No extraction from reasoning or posthoc switch to nonthinking. Independently
freeze retention tasks, correct-answer/format checks and acceptance before training;
require BASE passes and adapter retains that performance, with raw coverage reported.

If any required gate fails, candidate fails. Read representative full successful and
failed replies, including direct chat, to distinguish retrieval, factual, formatting
and reasoning failures. Report before choosing any next factor. No automatic sweep.
If it passes, confirm the frozen procedure on fresh neutral assignments and fresh
held-out questions before calling training qualified. The current20facts and repeated
32controls alone do not provide independent confirmation. Only then finish ethical
corpus disposition and prospectively freeze the treatment experiment.

## Implementation and preservation boundary

Add the smallest typed replay/serializer extension to existing schema/dataset/trainer
layers; explicit own-input operational preparation scripts are allowed. Preserve old
config fingerprints/defaults and old serializers. Test real tokenizer boundary cases,
reasoning/final/EOS labels, masks, chunk coverage, mixed loss denominator, malformed
teacher data, partial failures and overwrite refusal with temp/mocked tests. No real
artifact mutations while pytest runs. No model weights/training on Mac.

After tests, prepare/cache-tokenize and freeze measured plan, register fresh IDs,
commit/push, deploy one finite Supervisor worker with global GPUlock. Preserve all
artifacts/checkpoints at safe boundaries and final results with SHA/bytes receipts,
notes, Git push, private handoff save and verification. No new rental or dependencies
are needed for this next candidate. No treatment run is queued by this document.


## Implementation and acquisition freeze

Added optional typed DocumentReplaySpec with qwen3_raw_response_v1. Replay rows need
explicit source_kind, boolean thinking and stored request. Complete raw response
must match pinned Qwen chat template exactly; raw thinking contains one nonempty
reasoning block and final, while nonthinking has no generated reasoning markers.
User/header/padding/context masked; all response tokens and one terminalEOS train
once across chunks, no partial replay loss budgets. Existing document path shares
only the unchanged chunk algorithm. CPU pinned-tokenizer verification reproduced
all4,000old document rows/4,390chunks exactly and roundtripped long thinking replay
across2chunks. Trainer keeps historical synthetic/C4keys and adds replay only when
present. Old config/preprocessing dumps unchanged when optional replay absent.

Full suite1,134passed/5skipped;98focused passed after final new acquisition metric
refinement. All tests temp/mocked, no Mac weights. Frozen files guarded by handoff tests.
Prepared acquisitionv1unused/VOID before calls: new scorer initially conflated exact
answer and strict format. Exact v1builder source andinputs retained. Freshv2separates
semantic accuracy, exact answer and grammar/format; no overwrite or retrospective
metric change. Current new builder/protocol/prepared bank isv2,512replay candidates
(8families x32questions x2modes),128retention presentations(64questions x2modes), pinned
BASE only, thinktemp.6/nonthink0, top_p.95/top_k20/min_p0,1024cap,batch32,seed42/peritem.
Family tasks: sum,difference,product,comparison,negatedequality,sort,uppercase,progression.
Retention operands/prompts disjoint; block original registry entities/frozen arithmetic
statements before writing input. Procedural families overlap skills intentionally.

Fixed admission: complete normalEOS, exact known answer, valid reasoning/final and
standard template, exact prompt/output token roundtrip. Keep all failures/caps, no
quality regeneration or repairs. Require461/512overall,24/32perfamily/mode. Independent
retentionBASE/adapter criteria per mode: >=.95semantic,1.0strictformat/validboundaries/
normalstops; retention never becomes replay. FailedBASEreference stops preparation,
not silent selection. Exact replay target mass/repeats/optimizer steps remain unfrozen
until acquisition is reviewed. No training prepared or queued by acquisition script.
Registered fresh future trial/validation/transfer/retention paths, not runnable configs.


## Acquisition completed, original readiness failed

Inference-only Supervisor sft-drift-instruction-replay-pool-v2,PID34274, source5007184,
log /workspace/sft-drift-ops/instruction_replay_pool_v2.log EXITEDnormally. All640raw
replies/IDs/metadata preserved. Original admission412/512,96,357eligible targets:
240thinking/172nonthinking. Perfamily/mode quotas andoverall461gate failed. No trial
prepared/trained. Thinking retention55/64under saved semantic/format/boundary rule,
9capped; nonthinking47/64semantic,57/64format,64normal. Both original retention gates
failed. Replay has7thinking caps. Early commentary called boundary errors empty
reasoning; full trace inspection shows truncation, not complete empty blocks.

Terminal14files/6,358,091bytes copiedMac/SHAverified2026-10-20T22:17:09Z. Full-text
review is61unique replies:32replay(indices0/31all8families/modes),2cappedthinking
retention,all27nonthinkingretentionexclusions. Other579notmanuallyread. Reviewed
admissible finalanswers correct; verbose reasoning includes self-corrected intermediate
errors. Capped traces may compute expected value but cannot be rescued as finalanswers.
All32nonthinking replay sorts are numericallycorrect but violate requested no-space
format. Nonthinking negatedequality16/32correct; explicit wrong values also occur.
Four equation-form retention sums are semantically correct but unique-number rule
callsfalse; reviewer disagreement saved, formatfailure andoriginalscoresunchanged.

All37exact-token-roundtrip exclusions (28replay/9retention), chiefly uppercase strings,
have identical complete decoded text and exact prompt IDs. Different valid subword
segmentations account for rejection; tokenauditJSONL+MD retains both sequences. This
is a technical exclusion, not wrongcontent. No regeneration/re-admission of v2outputs
or changed v2gate. Original source/criteria/results remain recoverable at5007184.

## Fresh prospective candidate data and retention contract

This amendment precedes any new candidate training/adapter outcomes. The initial
BASEreference fails on some tasks even without SFT, so its all-item accuracy threshold
cannot serve as a pure retention criterion. Keep its failed verdict. The fixed frozen
study32controls andnewcandidate semantic lookup>=18/20eachfamily remain required.
A new data derivation/reference version will separate retention of demonstrated
BASEskills from capabilities BASEdidnotdemonstrate; all128items stillreported.

Next implement fresh generated/results ethics_sft_instruction_replay_text_v1 from
all512saved replay candidates. No new model calls, response edits or quality retries.
Keep every full correct/strict/normal reply with standard canonical chat text and
source/input/output hashes. Permit a canonical tokenizer segmentation when complete
decoded teacher text and input header agree exactly; save actual teacher IDs and
training IDs separately. Require all body/think/final/EOS targets once. Retain all
wrong/noncompliant/capped cases explicitly. Do not call original v2readiness passed.
Expected count440if28equivalent-text exclusions recover; verify rather than assume.
Nonthinking-sort absence andnegation imbalance are declared limitations. Dataset is
finite BASE-known replay, not an instruction-capability benchmark.

New registered reference ethics_gpu_instruction_retention_base_v1: same128existing
retention prompts/seeds, pinnedBASE, same modes/sampling/batch32,4096cap matching
frozen controls' reasoning allowance. Save full128including wrong/capped/malformed.
Before any candidate training, freeze the exact BASE-known IDs and response hashes:
semanticcorrect ANDstrictformat ANDcomplete valid reasoning/final ANDnormalstop.
Require>=32known/mode andall8families represented; otherwise reference is insufficient.
Future adapter runs use identical prompts/modes/decoder/seeds/budgets and report all
128before/after outcomes plus the fixed paired subset. Candidate retention requires
>=.95semantic correctness and1.0strictformat/validboundaries/normalstops on those
pretraining-known items per mode. Unknown items never imputed neutral or dropped from
reports. Mask never depends on adapter success. This is development qualification,
not an independent confirmation or a measure that BASEalreadyfailed tasks were forgotten.

Once reviewed derivation/reference passes, freeze actual replay mass/repeated draws
and optimizer steps for one high-LR+varied-request+replay candidate, then run final-only
chat recall/frozencontrols/retention gates and full reply review. No automatic training
from this amendment, no changes to ethical instrument, no weakening of its controls.
A fresh-neutral confirmation still follows any development pass. Exact dose/schedule
not yet prepared. Source/inputs/results/reviews require this block's private snapshot.


## Corrected derivation and retention runner implemented

New scripts derive_instruction_replay.py andprobe_instruction_retention.py,65focused
new/replay/format-matrix/import/handoff tests pass. Tests cover alternative segmentation
without text edits; wrong/malformed/capped rejection; sourceprompt/answer/seed identity;
fixed BASE-known mask despite adapter improvements/losses; all128coverage andfamily
requirements; partialfailure/overwrite refusal. One initial capped fixture wrongly
includedEOSwithlength-stop; correctedfixture, no real results modified. Shared source
training/dataset serializers unchanged from prior1,134passed/5skipped fullsuite.

CPU cached tokenizer derivation COMPLETED ethics_sft_instruction_replay_text_v1:
440admitted,28recovered alternative-tokenization examples,98,398eligible targets,
440chunks. All512candidate dispositions retained; no new generation, prose edits,
quality repair or reclassification of oldv2gate. Actual teacher input/output IDs and
canonical input/target IDs saved separately, full decoded text equality/eligible
response/EOS coverage verified. New manifestSHA
09655b0d8ef5b0717eac2557824f4312d21be4b157d9f206dfa21d62ce35718b.
Counts remain unbalanced(nonthinking sort0,negation16), explicitly retained limitation.

Fresh retentionBASEinputs prepared under registered ethics_gpu_instruction_retention_base_v1.
Same128oldprompts/per-item seeds, sortedfixedinput order,4096cap, thoughttemp.6/nonthought0,
.95/topk20/minp0,batch32,pinnedBASE. InputtokenIDs bound to old actualtemplate; exact
model/seed/prompt metadata checked at runtime. Conditional known-mask protocol frozen
before calls:>=32known/mode,all8families present; adapter>=.95semantic and1.0format/
complete boundaries/normalstops on fixedknownitems. All128rawresponses always retained;
backend identity errors invalidate reference rather than silently becoming unknown.
BASE/adapter use separate immutableIDs andsamegeneric runner; adapter binding uses
existing training verification helper. No automatictraining. Next commit/deploy and
run onlyBASEreference, review, then freeze actual training dose/config.

Prior save/offlineverify succeeded b7fc93138cf01f96c0ebee17f69328c005773c3b,
code463e12b,2,516files/9,054,019,079bytes. Current derivation/input files need next save.


## BASE reference complete, candidate frozen before training

BASEworkerPID35329source2a76eaf EXITEDnormally. Thinking64/64correct/strict/complete/
normal; nonthinking47/64numericsemantic,57/64strict,64normal,44known. All8families/mode,
referenceusable. Known-mask108items SHA
718048fd44f3561ba8d6330422f8dc9a6af6c43e1d93603178adbc01fcc4064f.
13terminalfiles/1,151,591bytes copiedMac/hashverified2026-10-20T22:35:45Z. All128finals
inspected;64nonthinkingrawreplies+8thinking(index1000eachfamily)fullyread. Other56
thinkingtracesnotfullyread. Four correctequations disagree with numericsemanticrule,
formatfailure/knowneligibility unchanged. Newreference has fixedsortedorder as well
as4096cap, so not a token-identical extension/causal cap-only test. Future adapter uses
this same new bank/order/seeds/decoder. ReviewJSONL+MD andREVIEW.md retained.

New compiler/judge implement one prospective combined candidate. Final75focused tests
passed afterworker-freeze change; earlier77includedformatmatrix tests. Tests cover
full-pool replay exposure/unique source lineage, finite repetition bound, every gate,
mask/adapter/fileidentity, source tracked-input hashes, ignored machine-profile exclusion,
outputfreshness/noresume. No shared trainer/serializer changes this block. CPU preparation
and actual config/plan/source/input hashes verified, original4,000ordered rows exact.

Preparedethics_sft_registry_instruction_replay_v1:6,200manifestdraws(2koriginalsynthetic,
2kC4,2.2kreplaydrawsfrom440unique/5completecycles),6,590chunks,2,594,740inputtokens,
2,356,785eligible targets=882,992synthetic+981,803C4+491,990replay(20.875%). One pass,
824steps,412midpoint/824final;LR1e-4,rank16/alpha32/all7,seed42,batch4/accum2,other
settings unchanged. No target masks/reply truncation or outcome-selected checkpoints.
PlanSHA8a7dc56a03177b3c0e31aa7ecd1be1bc40893b3c2abbfabfdeff8281d69b0ceb.

Allthreeevalinputs prepared:replay_validation_v1(originalstrictlookup/frozencontrols),
replay_transfer_v1(two128-token unprefilled semanticfamilies+8directmath),
replay_retention_v1(all128andfixed108known). Generic existing validation/transfer code
reused;newjudge checks allgates,matchingadaptertensor/file/engineering andknownmask.
Old strict endpoint reported separately; noethicaldispatch andagentreview mandatory.
Worker/EXECUTION.md/execution_manifest bind tracked source/config files, lockfiles,
allgenerated trial/eval inputs,corpus/reference sources,modelplan andknownmask. Ignored
machine-local hardwareprofile excluded. Worker checks everySHA andfreshoutputs before
GPU training,usesglobalflockfortraining andexistinginternal locksforeachinferencephase.
No resume/restart ofstartedID. Nextcommit/deploy/remoteverify andfiniteSupervisorlaunch.


## Candidate dispatched, initial immutable artifacts off-box

After sourcecbe81cbpush/pull,36inputtransportfiles/28,713,733bytes and839frozeninput
SHA verified onGPU;alloutputrootsfresh. FiniteSupervisor
sft-drift-registry-instruction-replay-v1,PID36320,log
/workspace/sft-drift-ops/registry_instruction_replay_v1.log runs exactly generated
worker.sh inforeground. No restart/resume; globalflocktraining,eachsubsequentinference
ownsitsinternalGPUlock. No ethicaldispatch. No additionalrental/dependencies.

ActualGPUtokenization6,590chunks,882,992synthetic/981,803C4/491,990replaytargets verified
against plan whileinitialweightsloaded; first8steps finite loss/gradnorms. This is
only a healthy start, not content-learning/chat/control qualification. Training~4s/step
early; roughly55–65minutes if sustained, plus allvalidation/inference overhead; not a
measured full-runETA. Initial4stablefiles STARTED/config.resolved.yaml/tokenized.jsonl/
tokenized.md,39,776,191bytes copiedMac/SHAverified,receipt undertrainingresults.
Active run.log/training_batches were intentionally not treated as immutable copies.
No checkpoint exists off-box yet; midpoint412mustbe copied after trainer_state412and
trainingauditadvances beyondthat boundary. Do not destroy box with this active run.
All newinputs/BASEreference/reviews and initial copiedfiles require this block's save.

## Verified training wait and midpoint-copy automation

Worker36320confirmedRUNNING168/824,finite loss/gradients. Added narrow operational
preserve_cuda_checkpoint.py plus transport/boundary tests45passed(temp,mocked/noGPU).
It queries the specific Supervisor process,waits forcheckpoint trainer_state step412
andtrainingauditadvanced to>=412(orcompletedtrainingforfinalstep),then packages all
immutable checkpoint files withbefore/after SHA/size checks. Local transport validates
allmembers/bytes/identities before writes,refuses symlinks/pathescapes/conflicts,allows
identical preexisting files andwritesimmutable receipt. Bounded3transport retries;
observation timeout/error does not mean training is terminal. No training resume.
Actual remote packaging logic tested against temp checkpoint/auditfiles,not source
string assertions. Every real backup stays under registered existing run roots.

Mac watcher launched execsession93962,log/tmp/sft-drift-replay-midpoint-watch.log:
uv run --no-sync python scripts/preserve_cuda_checkpoint.py --host root@38.49.42.46 --port 58689 --run-id ethics_sft_registry_instruction_replay_v1 --step 412 --job sft-drift-registry-instruction-replay-v1 --wait
No checkpoint ready/copied yet. Do not run private save concurrently with this watcher
onceitcanmutate local artifacts. Preserve midpoint+notes/source aftercopythenletfinal/
allthreeevaluationsfinish. No training/outcome settings changed while active.

Prior block save/offlineverify6c2d8389ca5a43d5a805e05341190f1c9c5e89a6,codee1815b5,
2,568files/9,099,775,038bytes,corpusc415be726ff3adf87e5af3f4976f81d3067a60c3 includes
allnewcandidateinputs,derivedreplay,BASEreference/reviewsandfourinitialtrainingfiles.
Current weights/logupdates remain only onGPU untilsafecheckpointcopy. STATEtrimmed
tocurrent execution andnecessarypendingstudy information; fullpreviousdetail remains
in Git/dates/artifacts. No new GPU/dependencies/training jobs or ethical dispatch.


## Midpoint412 verified off-box

Watcher93962completed normally. Specific Supervisor worker observedRUNNING at420
beforecopy;checkpoint trainer_state412andtrainingaudit>=412checked. Eight checkpoint
files/396,958,908bytes copiedMac/SHAverified2026-10-20T23:09:48.332740Z,receiptunder
trainingresults/checkpoint_412_offbox_copy_verification.json. Independent local rehash
ofall8files/bytecountsandtrainer_state412passed. No midpoint inference,qualification
or outcome selection. Copy process exited; no local writer can race the next save.
Currentworker36320sourcecbe81cbRUNNING450/824;latestloss0.1986/gradnorm0.1458finite.

An earlier actual-batch audit at274completedstepgroups showed301,122synthetic,
313,175C4and163,010replaytargetsobserved(includingpartialcurrentgroup);everycomplete
accumulation-groupnormalizer matched its actualeligible targets. This is runtime
loss/dataset plumbing evidence,not learning/retention qualification. Allthreecomponents
active. Final824/allthreequeued evaluations remainunproven. No ethicaldispatch.

Copy-helpercode/notes b0312ec pushed; this boundary notes/midpoint require commit/push,
privatehandoffsaveandofflineverify. Prior verified snapshot6c2d8389ca5a43d5a805e05341190f1c9c5e89a6,
codee1815b5,2,568files/9,099,775,038bytes includesallinputs andinitialstablefiles,notnew
midpoint. Activepost412updates/logs remainonlyonGPU. No trainingresumeorboxdestructionclaim.


## Finalcheckpoint watcher and verified midpoint private save

Midpoint private save+offlineverify succeeded f6a4e110bd18be5a0795e51ad01a4fc0499d0182,
code15d7d4f,2,577files/9,496,736,399bytes. Includesall8checkpoint412files/receipt and
copy-helper source. Actualworker36320confirmedRUNNING599/824,finite loss/gradnorms.
Added finalboundary testcase: savedstep824withno latermicrobatch iscopyableonlyafter
trainingCOMPLETED.46preservation/handoff/import tests passed,temp/mocked/noGPU.

Launchedsamecopyhelper --step824 --wait,execsession92798,
log/tmp/sft-drift-replay-final-checkpoint-watch.log. It copies checkpoint824after
trainingengineeringcompletion whilequeuedinferencecancontinue; no training/inference
settings changed andno checkpoint evaluation/selection. Do not run private save while
this watcher can mutate localdata; preserve newlycopiedcheckpoint andterminalresults
atnextsafeboundary. All finalgates/actualmodelreplyreview stillunproven.


## Terminal candidate and native-context diagnosis

824steps completed, all11engineeringchecks passed. Strict lookup0/20, bothsemantic
families1/20; frozen32controls passed. Retention thinking63/64(allfailuresononeitem),
nonthinkingknown44/44; completegateFAILED. SupervisorEXITEDnormally. Fullreplyreview
stillpending; no ethicaldispatch or retrospective qualification change.
Finalcheckpoint824 andterminalactualadapter/results copied/SHAverified toMac.
Terminaltokenized.md differs onlybyderivedheading path; preserve original, store
exactremotevariant tokenized.terminal.md withreceipt mapping. Semantic+retention
22files/1,359,004bytes copiedverified. All latestbytes awaitprivatepreservation.
Preparednative80replydiagnostic comparesBASE/finalundertrainedrequests andexact
supervisedprefixes; actualeligiblecodetargets/prefixIDsverified againstsavedtokenization.
Noanswerleak, same20facts, 256/16caps, originalfailedchatgatesunchanged.40focused
native/transfer/import/handofftests passed; earliermistypedtestpathran no tests.


## Scoped terminal review and live native diagnostic

Readall96fullsemantic replies: BASE0/20bothfamilies,adapter1/20both (sameTalverin),
math8/8each. Checked128retentionfinals and64BASE/adaptercontrolfinals,fullyreadone
4096token failedthinking trace andallnonthinkingfailure replies. Other successful
thinkingtraces notallread.288hash-boundscopedreviewrecords+MD undertransferresults;
noautomatedscore disagreements. Correct3070appears early infailedtrace butbinary
checkingloopneverfinishes: do notcallthis demonstratedloss ofadditionknowledge.

NativefiniteSupervisorstarted PID39667,sourcec2593ae,log
/workspace/sft-drift-ops/registry_replay_native_v1.log; noresume/restart. Initial
launcher stoppedbeforeextractinginputs becauseSupervisorstatusEXITEDreturns3;
handledterminalreturncode explicitly, thenlaunchedonce. Input/resultIDsnotrerun.
Someexactprefixes correct; unprefillednativeoutputs mixed,full80stillpending.
MaskedDOCTAGabsentfromchat isconcreteconditioningmismatch; untaggedsingle-factor
trialcouldtestit, notyetprepared/queued. Notestofethicaloutcomes.

Private save29ed2c6ad667a4b9ab0f2a65a0fa40657fdfaa11codec2593ae
2,650files/10,042,481,959bytes live/offlineverified; corpusfb48c807e6cf2f9a2dda5394b301f16d1b5c78ed.
Includesallnewfinalweights andcompletedcandidateevals/nativeinputs,notthisnewreview
orremoteinflightnativeoutputs. Currentboundarynotes/reviewneednextprivate save.


## Native diagnosis complete; prospective tag ablation

All80fullsavednative repliesread. BASE0/20both,adapter20/20exactprefixand6/20
unprefilledtrainedrequests. All40prefixes and26/40notes capped; correctcodesinpartial
notesdonotestablishcompletedocumentgeneration. Genericentryupdates,wrongTalverin
five-digitvalueandlakeclaimseen. Noagentnumericassessmentdisagreements;80records+MD
andreportwritten.7files/236,520bytescopiedMac/hashverified,Supervisorexitednormally.

Preparedsinglefactor`ethics_sft_registry_untagged_replay_v1`: remove maskedDOCTAGonly.
EveryorderedactualeligibleGPUtargetidentical; C4/replaychunksidentical. Sourcecorpus
andanchorsbyteidentical,all6,200draws/6,590chunks/2,356,785targets preserved.
Inputtokens2,584,740(10,000fewercontexttokens);824steps,412/824saved,finalonly.
Samefreshbase/LR1e-4/rank16/all7/seed42/B4G2andfixedchat/control/retentiongates.
PlanSHA3701438e6d1dbfe42e61456b5ad4df2abc3569db900cfcdf9898b5b42b0ef079.
109focusedtests passedincludingnewIDrouting/judgment,exacttarget/contextablation,
assistant/replayserialization/import/handoff. Sharedhelperhistoricaldefaultsretained.
Registeredallnewpaths,copiedsourcewithlineage,hashedprelaunchworker. Notyetlaunched.
Onecandidateonly; failuredoesnotjustifyretrospectivegatechange orethicaldispatch.

Private4eea702750b6bad9e1f395dbc0197adc695b7380codeb4c21b2,
2,652files/10,042,601,517bytesliveverifiedincludespreceding288recordreview.
Newnativeoutputs/newtrialinputs/source/notesawaitnextsnapshot.


## Prelaunch portability correction: fresh untagged v2

BeforeGPUdeployment,explicitexecutionmanifestcheckfoundabsoluteMacbuilderpathin
preparedv1. NoGPUrunlaunched; preservedv1/PRELAUNCH_VOID.json+MDandallinputs.
Correctedbuildertoexplicitprojectrelativepathandworkerrejectsabsolute/traversal
inputs;freshregisteredv2IDs,oldIDsretained.109focusedtestsrepassedincludingpath
rejection,newrouting,targetidentityandserialization. v2samecounts/settings/gates;
planSHA91a33dbb16a695232a7ec035a072e5efd8fc9826a0f24629d574e2b5c1420e66.
Portablemanifestfullyrehashedbeforedeployment; transportincludesnewinputs+native
agentreviewrequiredbylineage. Source/notesneedpush,thenverifyallremotehashesbeforelaunch.


## Untagged v2 launched

Source182d657pushed/deployed;839immutableinputsverifiedonGPU. FiniteSupervisor
sft-drift-registry-untagged-replay-v2 RUNNING PID40060; log
/workspace/sft-drift-ops/registry_untagged_replay_v2.log. Exactcommandnewgeneratedworker.
ActualGPUtokenization6,590chunks/2,356,785targets,synthetic_prefixemptyverified.
InitialstableSTARTED/config.resolved.yaml/tokenizedJSONL/MD4files/39,632,170bytescopied
Macandhashverified2026-10-21T00:09:11Z. LaunchrecordJSON/MDsavedinnewgeneratedroot.
Noresume,restart,checkpointselectionorautomaticethicaldispatch.109focusedtestspassed.
Newsource/inputs/nativeoutputs+review/voidv1/currentlaunchreceipt/initialstablefiles
needprivatesnapshotnow. Do notstartcheckpointcopywatchersuntilsavecomplete;412/824
safe-boundarycopiesnext. Alllearning/chat/control/retentionoutcomesremainunproven.
