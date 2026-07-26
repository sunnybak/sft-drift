# Hyak handoff

- Remote checkout:
  `/gscratch/scrubbed/adhyyan/codex_worktrees/sft-drift-factory-farming`
- Durable output root:
  `/gscratch/scrubbed/adhyyan/sft-drift-factory-farming-v1`
- Shared tmux session: `sft-drift-ff`
- Account/partition: `jamiemmt/gpu-a100` and `cse/gpu-a100`.
- GPU shape: one A100 80GB per task. The two accounts share a hierarchical
  CPU limit that permits four concurrent tasks in total.
- Pilot training array: `37722540` (completed).
- Adapter smoke inference: `37723589` (completed).
- Remaining training arrays: `37724263`, `37724264`, `37724265`,
  `37724266`, and `37724267` (all completed, every task exit code 0).
- Full training verification:
  `verification/all_training.json` (PASS, 32/32 runs).
- Fresh-process 8B adapter smoke: `37727692` (PASS).
- Generation smoke: `37727693` (completed, two records with valid hashes).
- Original frozen generation array: `37727750`. Tasks 0--17 ran under
  `jamiemmt`; tasks 18--33 were cancelled before starting after the parallelism
  throttle exposed that allocation's two-GPU limit. Task 3 produced all 450
  hash-valid records but exited 1 because 37 model responses were empty; those
  invalid responses are retained and score false.
- Replacement generation array: `37730588` runs exactly tasks 18--33 under
  `cse`, with no change to the frozen generation protocol. Together the two
  arrays use four concurrent A100s.
- Original political-control array `37727751` was cancelled before running
  because its `afterok` dependency could never release after task 3. Replacement
  array `37728784` was also cancelled before running when pending generation
  tasks moved to `cse`. The active political-control array `37730694` uses
  `afterany:37727750:37730588`, runs under `cse`, and preserves the frozen
  control matrix.
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
