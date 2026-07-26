#!/usr/bin/env bash
#SBATCH --job-name=ff-political
#SBATCH --account=jamiemmt
#SBATCH --partition=gpu-a100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=6
#SBATCH --mem=80G
#SBATCH --gres=gpu:a100:1
#SBATCH --time=03:00:00

set -euo pipefail

: "${FF_EVAL_SUBSET:=all}"
: "${FF_SCRATCH_ROOT:=/gscratch/scrubbed/${USER}/sft-drift-factory-farming-v1}"

CODE_ROOT="${FF_CODE_ROOT:-${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is required}}"
VENV_ROOT="/gscratch/scrubbed/${USER}/envs/sft-drift-ff-v1"
if [[ ! -x "${VENV_ROOT}/bin/python" ]]; then
  echo "missing established training environment: ${VENV_ROOT}" >&2
  exit 2
fi

export HF_HOME="/gscratch/scrubbed/${USER}/.cache/huggingface"
export XDG_CACHE_HOME="/gscratch/scrubbed/${USER}/.cache"
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export TMPDIR="${FF_SCRATCH_ROOT}/tmp/${SLURM_JOB_ID}"
mkdir -p "${TMPDIR}" "${FF_SCRATCH_ROOT}/political_control"

cd "${CODE_ROOT}"
"${VENV_ROOT}/bin/python" -u \
  scripts/18_run_factory_farming_political_control.py \
  --manifest configs/factory_farming_eval_v1.json \
  --control-config configs/factory_farming_political_control_v1.json \
  --subset "${FF_EVAL_SUBSET}" \
  --array-index "${SLURM_ARRAY_TASK_ID:-0}" \
  --output-root "${FF_SCRATCH_ROOT}"
