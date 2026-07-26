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
- Remaining 8B seed-42 array: `37724263`.
- Directional extra-seed arrays, dependency chained:
  `37724264`, `37724265`, `37724266`, `37724267`.
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
