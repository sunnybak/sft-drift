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
