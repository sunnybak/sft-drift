#!/usr/bin/env bash
# Finite environment setup worker, controlled from SSH; no agent harness or SFT.
set -euo pipefail
cd "$(dirname "$0")/.."
run_id="${1:?Pass a fresh registered ethics_gpu_ setup ID}"
[[ "$run_id" =~ ^ethics_gpu_[a-zA-Z0-9_]+$ ]] || exit 2
output="data/results/ethical_pilot/$run_id"
mkdir -p "$output"
[[ ! -e "$output/SETUP_COMPLETE" ]] || { echo 'Completed setup is immutable'; exit 2; }
python3 - "$run_id" <<'PY'
import json,sys
from pathlib import Path
name='results/ethical_pilot/'+sys.argv[1]
assert name in json.loads(Path('configs/handoff.json').read_text())['include_paths'],'Register output first'
PY
phase() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$1" | tee "$output/setup_phase.txt"; }
phase 'installing locked environment'
uv sync --locked --dev
phase 'restoring private artifacts'
uv run --no-sync python -u scripts/handoff.py restore
phase 'verifying restored artifacts'
uv run --no-sync python -u scripts/handoff.py verify
phase 'running weight-free setup regressions'
uv run --no-sync pytest -q tests/test_handoff.py tests/test_data_sync.py tests/test_import_rules.py tests/test_schemas.py tests/test_measurements.py tests/test_stance_study.py tests/test_stance_review.py
phase 'downloading active model'
uv run --no-sync python -u run.py +run=current_machine stage=download_models
phase 'running cached-model CUDA canary'
uv run --no-sync python -u scripts/verify_cuda_setup.py --output "$output"
phase 'completed'
date -u +%FT%TZ > "$output/SETUP_COMPLETE"
