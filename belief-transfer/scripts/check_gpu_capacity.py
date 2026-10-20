#!/usr/bin/env python3
"""Reuse a completed hardware check, without overwriting or regenerating it."""
import json
from pathlib import Path

p = Path('data/results/ethical_pilot/ethics_gpu_capacity_v3/capacity.json')
r = json.loads(p.read_text())
if not (r['passed'] is True and r['batch_size'] == 8 and r['max_new_tokens'] == 4096
        and r['model_revision'] == '1cfa9a7208912126459214e8b04321603b3df60c'
        and r['peak_allocated_bytes'] <= .85 * r['total_vram_bytes']):
    raise RuntimeError('Expected the completed batch-eight full-cap capacity check')
print('Completed capacity v3 verified; no rerun', flush=True)
