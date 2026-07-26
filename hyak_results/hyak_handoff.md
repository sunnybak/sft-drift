# Hyak handoff

- Remote checkout:
  `/gscratch/scrubbed/adhyyan/codex_worktrees/sft-drift-factory-farming`
- Durable output root:
  `/gscratch/scrubbed/adhyyan/sft-drift-factory-farming-v1`
- Shared tmux session: `sft-drift-ff`
- Account/partition: `jamiemmt/gpu-a100`
- GPU shape: one A100 80GB per task, arrays capped at two concurrent tasks.
- Pilot training array: `37722540` (completed).
- Adapter smoke inference: `37723589` (completed).
- Remaining training arrays: `37724263`, `37724264`, `37724265`,
  `37724266`, and `37724267` (all completed, every task exit code 0).
- Full training verification:
  `verification/all_training.json` (PASS, 32/32 runs).
- Fresh-process 8B adapter smoke: `37727692` (PASS).
- Generation smoke: `37727693` (completed, two records with valid hashes).
- Full frozen generation array: `37727750` (34 conditions, two concurrent).
- Political-control array: `37727751` (dependency-chained after generation).
- Hugging Face cache/token location:
  `/gscratch/scrubbed/adhyyan/.cache/huggingface` (value never read or copied).
- Upload blocker: the cached token authenticates as `adhyyan21` with role
  `read`; it cannot see or write the private repository. Replace it with a
  write-scoped token that can access `sunnybak/sft-drift-adapters`, then rerun
  `scripts/19_upload_factory_farming_adapters.py`.
- Private adapter repository:
  `sunnybak/sft-drift-adapters`.

All compute runs through Slurm. No password, Duo code, OpenAI key, or Hugging
Face token is stored in Git.
