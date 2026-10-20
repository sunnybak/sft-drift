"""Judge the prospective semantic development contract; preserve the original strict verdict."""
from __future__ import annotations
import json
from pathlib import Path
from prepare_registry_varied_requests import RUN, TRANSFER, VALIDATION


def judge(strict: dict, transfer: dict, binding: dict, criteria: dict) -> dict:
    n = criteria['lookup_n_per_family']
    comparisons = {}
    for arm in ['base', RUN]:
        for style in ['original_long', 'natural_registry']:
            observed = transfer['by_arm'][arm][style]
            comparisons[arm + '/' + style] = (observed['n'] == n and
                (observed['unambiguous_numeric_match'] <= criteria['base_semantic_max_correct'] if arm == 'base'
                 else observed['unambiguous_numeric_match'] >= criteria['adapter_semantic_min_correct']))
    comparisons['frozen_controls'] = all(strict['arms'][arm]['controls']['passed'] for arm in ['base', 'adapter'])
    comparisons['matching_adapter'] = strict['training_binding']['adapter_tensor_sha256'] == binding[RUN]['adapter_tensor_sha256']
    comparisons['engineering'] = all(strict['training_binding']['training_checks'].values())
    return {'training_run_id': RUN, 'checks': comparisons,
            'automated_development_candidate_passed': all(comparisons.values()),
            'original_strict_technical_qualification_passed': strict['technical_qualification_passed'],
            'requires_full_reply_agent_review': True,
            'interpretation': 'New prospective semantic development contract only; original strict results unchanged. No ethical training automatically follows. Reused development facts, one training seed; not independent confirmation.'}


def main() -> None:
    root = Path('data/results/ethical_pilot') / TRANSFER
    strict_root = Path('data/results/ethical_pilot') / VALIDATION
    if not all((p / 'COMPLETED').exists() for p in [root, strict_root]):
        raise ValueError('Both evaluation stages must be completed')
    path = root / 'prospective_qualification.json'
    if path.exists():
        raise FileExistsError('Judgment is immutable')
    plan = json.loads((Path('data/generated/ethical_stance_sft') / RUN / 'plan.json').read_text())
    result = judge(json.loads((strict_root / 'summary.json').read_text()), json.loads((root / 'summary.json').read_text()),
                   json.loads((root / 'bindings.json').read_text()), plan['prospective_criteria'])
    path.write_text(json.dumps(result, indent=2) + '\n')
    path.with_suffix('.md').write_text('# Prospective development judgment\n\n```json\n' + json.dumps(result, indent=2) + '\n```\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
