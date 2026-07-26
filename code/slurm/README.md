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
