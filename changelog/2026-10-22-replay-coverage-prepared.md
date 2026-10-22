# Replay coverage: reviewed data and frozen preparation

Prepared ethics_sft_replay_coverage_probe_v2 without loading model weights or starting
training/inference. The next step is finite reference acquisition before candidateSFT.

Data pilotv1 retains246thinking teacher source texts unchanged and replaces194short
source slots with130procedural gold examples plus64neutral decision presentations.
The new gold includes162short/32thinking responses. All194requests independently
parsed/solved, targets/proofs checked, token/EOS roundtrip checked, allonechunk. Agent
fully read46requests/targets/proofs (predeclared32 +14covering five-digit inputs and
other decision facts), zero clear defects. No claim of194agent semantic reads. New
reasoning is procedural gold, not purported BASE teacher output. Original data immutable.

V1preflight stopped on duplicate/historical bank overlap before output materialization
or calls. Newv2IDs and prospective bank amendment retain seed20261026but sample unique
left operands1100..1199/right2100..2199. Fresh128procedural presentations and64neutral
true/false decisions use unseen operands; latter use held-out instruction/note wording.
One seed42 retains original thinking0.6/nonthinking0decoder. Existing thresholds stay
fixed, supplemented by declared decision-cohort requirements. No model outcomes seen.

Candidate manifest3246draws/3625chunks, matching fixed weight32reference chunk count.
All3043C4/existingthinking chunks and positions match exactly. Same one-pass454steps,
LR1e-4/weight32/correctednormalization/LoRA/seed42; final-only. Rawtargets1248760,
weighted1322416; C4948838/thinking297546/short2376. Mean token-NLL coefficient shares
69.980%C4,23.551%thinking,6.470%short. Exposure differs explicitly; not exact-dose causal
isolation of coverage. Protocol freezes actual dose, source/config/model hashes and
review lineage. Both qualification routes collect all100frozenbelieves, no gate changes.

32focused data/proof/corruption/assembly/overlap/config/layer tests passed before live
preparation. Tests use mocks/tempdirs and never write experimental results. Registered
29v2paths before prepare; unusedv1registrations remain. No newGPUjob running yet.
Artifacts under data/generated/ethical_stance_sft/ethics_sft_replay_coverage_probe_v2,
data/generated/ethical_stance_sft/ethics_sft_c4_replay_coverage_v2, data/{generated,results}/
ethical_stance_sft/ethics_sft_replay_coverage_data_v1 and newethical_pilot bank IDs.
Each JSONL has Markdown view. Consult STATE.md/receipt for verified preservation.
