#!/usr/bin/env bash
#SBATCH --job-name=ff-generate
#SBATCH --account=jamiemmt
#SBATCH --partition=gpu-a100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=6
#SBATCH --mem=80G
#SBATCH --gres=gpu:a100:1
#SBATCH --time=06:00:00

set -euo pipefail

: "${FF_EVAL_SUBSET:=all}"
: "${FF_SCRATCH_ROOT:=/gscratch/scrubbed/${USER}/sft-drift-factory-farming-v1}"
: "${FF_EVAL_BATCH_SIZE:=8}"
: "${FF_EVAL_SMOKE:=0}"

CODE_ROOT="${FF_CODE_ROOT:-${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is required}}"
VENV_ROOT="/gscratch/scrubbed/${USER}/envs/sft-drift-ff-v1"
if [[ ! -x "${VENV_ROOT}/bin/python" ]]; then
  echo "missing established training environment: ${VENV_ROOT}" >&2
  exit 2
fi

export HF_HOME="/gscratch/scrubbed/${USER}/.cache/huggingface"
export XDG_CACHE_HOME="/gscratch/scrubbed/${USER}/.cache"
export TRITON_CACHE_DIR="${FF_SCRATCH_ROOT}/cache/triton"
export TORCH_EXTENSIONS_DIR="${FF_SCRATCH_ROOT}/cache/torch-extensions"
export CUDA_CACHE_PATH="${FF_SCRATCH_ROOT}/cache/cuda"
export NUMBA_CACHE_DIR="${FF_SCRATCH_ROOT}/cache/numba"
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export TMPDIR="${FF_SCRATCH_ROOT}/tmp/${SLURM_JOB_ID}"
mkdir -p \
  "${TRITON_CACHE_DIR}" \
  "${TORCH_EXTENSIONS_DIR}" \
  "${CUDA_CACHE_PATH}" \
  "${NUMBA_CACHE_DIR}" \
  "${TMPDIR}" \
  "${FF_SCRATCH_ROOT}/generations"

cd "${CODE_ROOT}"
GENERATION_ARGS=(
  --manifest configs/factory_farming_eval_v1.json
  --subset "${FF_EVAL_SUBSET}"
  --array-index "${SLURM_ARRAY_TASK_ID:-0}"
  --output-root "${FF_SCRATCH_ROOT}"
  --batch-size "${FF_EVAL_BATCH_SIZE}"
)
if [[ "${FF_EVAL_SMOKE}" == "1" ]]; then
  GENERATION_ARGS+=(--smoke)
fi
"${VENV_ROOT}/bin/python" -u scripts/14_generate_factory_farming_evals.py \
  "${GENERATION_ARGS[@]}"
