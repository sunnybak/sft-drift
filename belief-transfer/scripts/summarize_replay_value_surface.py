"""Descriptive full100 surface; missing-answer bounds are not confidence intervals."""
from __future__ import annotations

from pathlib import Path
import math
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from prepare_replay_weight_ablation import read, rows, sha, write_json, write_rows
from prepare_replay_value_probe import MASTER
from analyze_replay_weight_ablation import original_surface_status

RUNS = {'base42': 'ethics_gpu_vllm_base_v1', 'base7': 'ethics_gpu_vllm_base_seed7_v1',
    'base1729': 'ethics_gpu_vllm_base_seed1729_v1',
    'control': 'ethics_gpu_replay_weight_weight32_unqualified_s42_v1',
    'candidate': 'ethics_gpu_replay_coverage_unqualified_s42_v5'}


def counts(items: list[dict]) -> dict:
    planned = valid = supports = 0
    for item in items:
        x = item['neutral']; n = x['diagnostics']['n_expected']; v = x['diagnostics']['n_extracted']
        if not 0 <= v <= n or n <= 0:
            raise ValueError('Invalid expected/extracted counts')
        conditional = x['conditional_support']
        k = round(conditional*v) if v else 0
        if (v and (conditional is None or not math.isclose(k/v, conditional, abs_tol=1e-12))) or not 0 <= k <= v:
            raise ValueError('Canonical count cannot be reconstructed')
        planned += n; valid += v; supports += k
    if not planned:
        raise ValueError('Empty surface scope')
    return {'expected': planned, 'valid': valid, 'canonical_supports': supports,
        'missing': planned-valid, 'score': supports/planned if valid == planned else None,
        'conditional_score': supports/valid if valid else None,
        'missing_answer_bounds': [supports/planned, (supports+planned-valid)/planned]}


def main() -> None:
    parent = Path('data/results/ethical_stance_sft') / MASTER
    if not (parent/'COLLECTION_COMPLETED').exists() or not (parent/'TERMINAL').exists():
        raise ValueError('Wait for terminal candidate collection')
    output = parent/'full100_per_belief_v1.jsonl'; summary = parent/'full100_surface_summary_v1.json'
    if output.exists() or summary.exists():
        raise FileExistsError('Immutable surface already started')
    metrics, provenance, reference_bank = {}, {}, None
    for model, run in RUNS.items():
        root = Path('data/results/ethical_pilot')/run
        original_surface_status(root)  # Reconstruct every frozen per-belief score/coverage first.
        bank = rows(root/'stance_bank.jsonl')
        if reference_bank is None:reference_bank = bank
        elif bank != reference_bank:raise ValueError('Different belief bank; no paired drift')
        metrics[model] = read(root/'measurement_summary.json')['measurements']['stance']
        provenance[model] = {'run_id': run, 'files': {str(root/name): sha(root/name) for name in
            ('measurement_summary.json', 'stance_bank.jsonl', 'stance_observations.jsonl')}}
    roles = {r['belief_id']: r['role'] for r in reference_bank}
    if len(roles) != 100 or any(set(m) != set(roles) for m in metrics.values()):
        raise ValueError('Require the full matched100belief grid')
    per_belief = []
    for identity, role in roles.items():
        scores = {model: counts([m[identity]]) for model, m in metrics.items()}
        base = scores['base42']['score']; candidate = scores['candidate']['score']
        control_bounds = scores['control']['missing_answer_bounds']
        if base is None or candidate is None:
            raise ValueError('This completed candidate/base must have complete scores')
        per_belief.append({'belief_id': identity, 'role': role, 'models': scores,
            'candidate_minus_base42_pp': 100*(candidate-base),
            'candidate_minus_control_missing_bounds_pp': [100*(candidate-control_bounds[1]),100*(candidate-control_bounds[0])],
            'base_sampling_score_range': [min(scores[k]['score'] for k in ('base42','base7','base1729')),
                                          max(scores[k]['score'] for k in ('base42','base7','base1729'))]})
    groups = {}
    for scope in ('all100','ethical','offtopic'):
        selected = [k for k in roles if scope == 'all100' or roles[k] == scope]
        scores = {model: counts([m[k] for k in selected]) for model,m in metrics.items()}
        base = scores['base42']['score']; candidate = scores['candidate']['score']
        low, high = scores['control']['missing_answer_bounds']
        groups[scope] = {'beliefs': len(selected), 'models': scores,
            'candidate_minus_base42_pp': 100*(candidate-base),
            'candidate_minus_control_missing_bounds_pp': [100*(candidate-high),100*(candidate-low)],
            'base_sampling_score_range': [min(scores[k]['score'] for k in ('base42','base7','base1729')),
                                          max(scores[k]['score'] for k in ('base42','base7','base1729'))]}
    write_rows(output, per_belief)
    write_json(summary, {'groups': groups, 'source_bindings': provenance, 'per_belief_sha256': sha(output),
        'analysis_commit': subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'analysis_script_sha256': sha(Path(__file__)),
        'interpretation': 'Descriptive unqualified readings, not moral accuracy or selective editing. Bounds cover missing answers only; BASE range is three sampling runs, not a CI or training replication. No training settings selected on this surface.'})
    print(groups)


if __name__ == '__main__':
    main()
