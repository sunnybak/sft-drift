#!/usr/bin/env bash
# Finite technical smoke → qualification → BASE. Never launches treatment training.
set -euo pipefail
cd "$(dirname "$0")/.."
uv run --no-sync python -u scripts/stress_cuda_eval.py --run-id ethics_gpu_capacity_v3 --batch-size 8
uv run --no-sync python -u run.py +run=ethics_sft_document_smoke_v2
uv run --no-sync python -u run.py +run=ethics_gpu_development_v1
uv run --no-sync python -u scripts/check_gpu_qualification.py ethics_gpu_development_v1
uv run --no-sync python -u run.py +run=ethics_gpu_validation_v1
uv run --no-sync python -u scripts/check_gpu_qualification.py ethics_gpu_validation_v1
uv run --no-sync python -u run.py +run=ethics_gpu_base_v1
