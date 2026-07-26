#!/usr/bin/env bash
#SBATCH --job-name=sft-drift-ff
#SBATCH --account=jamiemmt
#SBATCH --partition=gpu-a100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=6
#SBATCH --mem=80G
#SBATCH --gres=gpu:a100:1
#SBATCH --time=04:00:00

set -euo pipefail

: "${FF_SUBSET:?set FF_SUBSET to a frozen manifest subset}"
: "${FF_SEED:?set FF_SEED to the subset seed}"
: "${FF_SCRATCH_ROOT:=/gscratch/scrubbed/${USER}/sft-drift-factory-farming-v1}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CODE_ROOT="${REPO_ROOT}/code"
VENV_ROOT="/gscratch/scrubbed/${USER}/envs/sft-drift-ff-v1"

# Hyak's Lmod initialization probes variables that may be unset. Temporarily
# disable nounset while changing modules, then restore strict shell behavior.
set +u
module purge
module load coenv/python/3.11.9
set -u

mkdir -p "${FF_SCRATCH_ROOT}/slurm" "${FF_SCRATCH_ROOT}/tmp"
export HF_HOME="/gscratch/scrubbed/${USER}/.cache/huggingface"
export VLLM_CACHE_ROOT="/gscratch/scrubbed/${USER}/.cache/vllm"
export WANDB_MODE=offline
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export TMPDIR="${FF_SCRATCH_ROOT}/tmp/${SLURM_JOB_ID}"
mkdir -p "${HF_HOME}" "${VLLM_CACHE_ROOT}" "${TMPDIR}"

if [[ ! -x "${VENV_ROOT}/bin/python" ]]; then
  BUILD_ROOT="${VENV_ROOT}.build-${SLURM_JOB_ID}"
  if [[ -e "${BUILD_ROOT}" ]]; then
    echo "stale environment build path exists: ${BUILD_ROOT}" >&2
    exit 2
  fi
  PYTHON_BIN="$(command -v python3.11)"
  UV_BIN="$(command -v uv)"
  "${UV_BIN}" venv --python "${PYTHON_BIN}" "${BUILD_ROOT}"
  "${UV_BIN}" pip install \
    --python "${BUILD_ROOT}/bin/python" \
    -r "${CODE_ROOT}/requirements.txt"
  mv "${BUILD_ROOT}" "${VENV_ROOT}"
fi

cd "${CODE_ROOT}"
nvidia-smi
"${VENV_ROOT}/bin/python" - <<'PY'
import torch
print({
    "torch": torch.__version__,
    "cuda": torch.version.cuda,
    "cuda_available": torch.cuda.is_available(),
    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
})
assert torch.cuda.is_available()
PY

TRAIN_ARGS=(
  --manifest configs/factory_farming_training_v1.json
  --subset "${FF_SUBSET}"
  --array-index "${SLURM_ARRAY_TASK_ID:-0}"
  --seed "${FF_SEED}"
  --output-root "${FF_SCRATCH_ROOT}"
)
if [[ "${FF_SMOKE:-0}" == "1" ]]; then
  TRAIN_ARGS+=(--smoke)
fi

"${VENV_ROOT}/bin/python" -u scripts/10_train_factory_farming.py "${TRAIN_ARGS[@]}"
