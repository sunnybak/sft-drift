#!/usr/bin/env bash
# Run only after the initial vLLM benchmark worker has exited.
set -euo pipefail
source /opt/supervisor-scripts/utils/environment.sh
cd /workspace/sft-drift/belief-transfer
output=data/results/ethical_pilot/ethics_gpu_vllm_harness_setup_v1
[[ ! -e "$output" ]] || { echo 'Harness setup ID already started'; exit 2; }
mkdir -p "$output"
date -u +%FT%TZ > "$output/STARTED"
git rev-parse HEAD > "$output/source_commit.txt"
cp configs/requirements-vllm-inference.txt "$output/requirements.requested.txt"
uv pip install --python /workspace/sft-drift-vllm/.venv/bin/python \
  -r configs/requirements-vllm-inference.txt
uv pip freeze --python /workspace/sft-drift-vllm/.venv/bin/python > "$output/requirements.resolved.txt"
uv pip check --python /workspace/sft-drift-vllm/.venv/bin/python
date -u +%FT%TZ > "$output/COMPLETED"
