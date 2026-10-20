#!/usr/bin/env bash
# Isolated throughput environment. The study/training .venv and lockfile stay pinned.
set -euo pipefail
source /opt/supervisor-scripts/utils/environment.sh
cd /workspace/sft-drift/belief-transfer
output=data/results/ethical_pilot/ethics_gpu_vllm_setup_v1
[[ ! -e "$output" ]] || { echo 'Setup ID already started'; exit 2; }
mkdir -p "$output"
date -u +%FT%TZ > "$output/STARTED"
git rev-parse HEAD > "$output/source_commit.txt"
uv venv --python .venv/bin/python /workspace/sft-drift-vllm/.venv
uv pip install --python /workspace/sft-drift-vllm/.venv/bin/python \
  'vllm==0.19.0' 'torch==2.10.0' 'transformers==4.57.6'
uv pip freeze --python /workspace/sft-drift-vllm/.venv/bin/python > "$output/requirements.resolved.txt"
date -u +%FT%TZ > "$output/COMPLETED"
