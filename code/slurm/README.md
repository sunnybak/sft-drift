# Factory-farming Hyak jobs

The frozen training matrix is `configs/factory_farming_training_v1.json`. Jobs
use one A100 from the explicitly available `jamiemmt/gpu-a100` allocation and
write all environments, caches, logs, and adapters to scrubbed scratch.

Submit from `code/` after creating the Slurm log directory:

```bash
export FF_ROOT=/gscratch/scrubbed/$USER/sft-drift-factory-farming-v1
mkdir -p "$FF_ROOT/slurm"

# Two-step environment/model/training smoke.
sbatch --array=0 \
  --output="$FF_ROOT/slurm/smoke-%A_%a.out" \
  --error="$FF_ROOT/slurm/smoke-%A_%a.err" \
  --export=ALL,FF_SUBSET=pilot_4b_seed42,FF_SEED=42,FF_SMOKE=1,FF_SCRATCH_ROOT="$FF_ROOT" \
  slurm/factory_farming_train.sbatch

# Eight 4B seed-42 pilot jobs, at most two running concurrently.
sbatch --array=0-7%2 \
  --output="$FF_ROOT/slurm/pilot-%A_%a.out" \
  --error="$FF_ROOT/slurm/pilot-%A_%a.err" \
  --export=ALL,FF_SUBSET=pilot_4b_seed42,FF_SEED=42,FF_SCRATCH_ROOT="$FF_ROOT" \
  slurm/factory_farming_train.sbatch
```

The remaining frozen subsets are:

- `remaining_8b_seed42`, indices `0-7`, seed `42`
- `extra_4b_seed43`, indices `0-3`, seed `43`
- `extra_4b_seed44`, indices `0-3`, seed `44`
- `extra_8b_seed43`, indices `0-3`, seed `43`
- `extra_8b_seed44`, indices `0-3`, seed `44`

Do not submit the remaining subsets until the 4B pilot review passes.

After a training subset passes the static verifier, submit
`factory_farming_adapter_smoke.sbatch` with `FF_RUN_ID` set to one completed run
to prove that a fresh GPU process can reload the adapter and generate a
nonempty deterministic response.

After all 32 summaries pass
`scripts/11_verify_factory_farming_training.py --subset all --require-complete`,
run a two-prompt generation smoke before the full frozen matrix:

```bash
sbatch --array=0 \
  --output="$FF_ROOT/slurm/generation-smoke-%A_%a.out" \
  --error="$FF_ROOT/slurm/generation-smoke-%A_%a.err" \
  --export=ALL,FF_EVAL_SUBSET=all,FF_EVAL_SMOKE=1,FF_SCRATCH_ROOT="$FF_ROOT" \
  slurm/factory_farming_generate.sbatch

sbatch --array=0-33%2 \
  --output="$FF_ROOT/slurm/generation-%A_%a.out" \
  --error="$FF_ROOT/slurm/generation-%A_%a.err" \
  --export=ALL,FF_EVAL_SUBSET=all,FF_SCRATCH_ROOT="$FF_ROOT" \
  slurm/factory_farming_generate.sbatch

sbatch --array=0-33%2 \
  --output="$FF_ROOT/slurm/political-%A_%a.out" \
  --error="$FF_ROOT/slurm/political-%A_%a.err" \
  --export=ALL,FF_EVAL_SUBSET=all,FF_SCRATCH_ROOT="$FF_ROOT" \
  slurm/factory_farming_political.sbatch
```

The political runner requires the hash-frozen, gitignored
`opinionqa_v2.jsonl` and `opinionqa_v2_human_lean.jsonl` files at the paths
recorded in `configs/factory_farming_political_control_v1.json`.

Upload only after training verification. The uploader refuses public
repositories and requires a write-scoped credential that can access the
existing private repository:

```bash
export HF_HOME=/gscratch/scrubbed/$USER/.cache/huggingface
python scripts/19_upload_factory_farming_adapters.py \
  --output-root "$FF_ROOT" \
  --subset all
```
