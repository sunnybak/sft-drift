#!/usr/bin/env bash
#SBATCH --job-name=ff-adapter-smoke
#SBATCH --account=jamiemmt
#SBATCH --partition=gpu-a100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=40G
#SBATCH --gres=gpu:a100:1
#SBATCH --time=00:30:00

set -euo pipefail

: "${FF_RUN_ID:?set FF_RUN_ID to one completed frozen run}"
: "${FF_SCRATCH_ROOT:=/gscratch/scrubbed/${USER}/sft-drift-factory-farming-v1}"

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
  "${FF_SCRATCH_ROOT}/verification"

cd "${CODE_ROOT}"
"${VENV_ROOT}/bin/python" -u scripts/12_smoke_infer_factory_farming_adapter.py \
  --manifest configs/factory_farming_training_v1.json \
  --output-root "${FF_SCRATCH_ROOT}" \
  --run-id "${FF_RUN_ID}" \
  --report "${FF_SCRATCH_ROOT}/verification/${FF_RUN_ID}-smoke-inference.json"
