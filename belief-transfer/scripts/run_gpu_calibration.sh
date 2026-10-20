#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
output=data/results/ethical_pilot/ethics_gpu_calibration_v1
[[ ! -e "$output" ]] || { echo 'Existing calibration output; use a fresh ID'; exit 2; }
mkdir -p "$output"
date -u +%FT%TZ > "$output/STARTED"
uv run --no-sync python -u run.py +run=current_machine stage=calibrate run_id=ethics_gpu_calibration_v1
cp configs/hardware_profile.yaml "$output/hardware_profile.yaml"
date -u +%FT%TZ > "$output/CALIBRATION_COMPLETE"
uv run --no-sync python -u scripts/stress_cuda_eval.py --run-id ethics_gpu_capacity_v1 --batch-size 4
date -u +%FT%TZ > "$output/CAPACITY_COMPLETE"
