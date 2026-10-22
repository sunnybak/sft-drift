# Replay-weight implementation — before study training

Opt-in DocumentReplaySpec.nonthinking_loss_weight leaves default1out of serialization;
all4legacy pilot config hashes and baseline chunks remain identical. Weight32adds only
loss_weight metadata to complete nonthinking replay chunks. No text/labels are altered.

WeightedLossMixin computes shifted per-token CE × row weight, divided by the full
optimizer accumulation group's weighted eligible targets. A fixed one-pass sampler
provides group denominators, avoiding averaging unequal microbatch means. Audits keep
raw Trainer item counts separate from effective weighted denominators, coverage and
mode/kind coefficient shares. Default training delegates to the original loss path.

Separate task-value-v1 assessment accepts literal answers and scoped correct worked
equations, without searching for the gold value anywhere in prose. It preserves old
assessment, format, boundaries and stops; unrecognized/missing results remain explicit.
80narrow/document/schema/layer tests passed before CUDA calls. The CUDA-only toy check
will use the shared mixin through real Trainer, compare full-batch/accumulated updates
with an independently calculated softmax gradient, and verify update/reload. It loads
no Qwen weights. No study candidate or independent confirmation inputs prepared yet.

## CUDA v1 failure and pre-SFT correction

v1failed the unchanged analytic criterion: full update error1.19e-7, accumulated
error0.01878; update norm ratio0.500001. Reported NLL matched, demonstrating why
loss logs and denominator checks alone were insufficient. No study model trained.
Failure/summary/tensor outputs copied locally; original sourcecb6135a recoverable.

The opt-in mixin now compensates Accelerator's GASdivision only within training_step,
then unscales its returned logging loss. Historical default path stays untouched.
A fresh normalization-only weight1control is added to the future ablation, isolating
weight32from normalization changes. Explicit group normalization is now required for
non-unit weights; both new arms use it. Checkv2will rerun the same analytic/update/
reload criteria and additionally characterize the pinned native unweighted path.
67narrow/value/binding/layer tests pass after this correction; earlier80checks passed
before CUDA verification. These are source tests, not permission to skip the CUDA gate.

Projection from the original454-step C4ledger: raw targets1,244,032 (C4948,838,
thinking replay293,214,nonthinking1,980); weight32gives1,305,412weighted targets.
Mean per-step coefficient shares: C4.7078641,thinking.2343796,nonthinking.0577563.
Thus nonthinking share rises from~.2074%to~5.7756%; these are objective coefficients,
not gradient norms or optimizer contribution. Actual new ledgers must reproduce the
measured projection before a training binding is accepted.

## CUDA v2 passed — source 6b3aef7

Finite supervisor sft-drift-weighted-loss-check-v2 exited normally Oct22 10:49UTC.
All five checks pass: analytic update, accumulation/full agreement, changed parameter,
exact reload and analytic NLL. Both max update errors1.1920928955078125e-7. NLL
1.879716277 matches independent1.879716231. RTX3090; torch2.10.0/transformers5.5.0/
accelerate1.14.0. No pretrained/study weights loaded. Summary, source hashes, fixture
and tensors copied locally under registered ethics_gpu_weighted_loss_check_v2.

Native unweighted toy update ratio is1.0full/0.50000155accumulated despite equal
logged NLL. This characterizes the pinned toy path, not the exact historical Qwen
training update or causal explanation of losses. The normalization-matched control
remains necessary. Actual BF16 Qwen engineering checks and independent retention
confirmation remain pending. No new study model trained or candidate input prepared.

User reaffirmed overnight use of existing GPU. Current goal remains appropriate;
continue bounded repair experiment, not ethical expansion or automatic recipe search.
