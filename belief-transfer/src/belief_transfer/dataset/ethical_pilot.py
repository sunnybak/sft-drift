"""Finite, outcome-independent four-arm pilot selection and whole-text loss budgets."""
from __future__ import annotations
import random

ARMS = ('positive', 'negative', 'offtopic', 'c4_only')
INITIAL = ('animal_medical_research', 'animal_cosmetic_testing', 'single_use_packaging_necessary')
QUARANTINE = ('conservation_relocation_consent', 'conservation_relocation_no_consent')

def select_subjects(briefs: list[dict], seed: int = 42) -> list[str]:
    ethical = [b for b in briefs if b['role'] == 'ethical']
    by_id = {b['id']: b for b in ethical}
    if len(by_id) != len(ethical) or not set(INITIAL) <= by_id.keys():
        raise ValueError('Distinct approved ethical subjects and initial pilot targets required')
    selected = list(INITIAL)
    categories = {by_id[i]['category'] for i in selected}
    rng = random.Random(seed)
    for category in sorted({b['category'] for b in ethical} - categories):
        options = sorted(b['id'] for b in ethical if b['category'] == category and b['id'] not in QUARANTINE)
        if not options: raise ValueError('No non-quarantined subject in category')
        selected.append(rng.choice(options))
    if len(selected) != 10: raise ValueError('Expected ten pilot subjects across nine categories')
    return selected

def spread_budget(capacities: list[int], target: int) -> list[int]:
    """Every source appears once, keeps first/EOS targets; proportional surplus masks."""
    n = len(capacities)
    if not n or min(capacities) < 2 or not 2*n <= target <= sum(capacities):
        raise ValueError('Target must cover every first/EOS pair without exceeding capacity')
    spare = sum(c-2 for c in capacities)
    if spare == 0: return list(capacities)
    remaining = target - 2*n
    quotas = [divmod((c-2)*remaining, spare) for c in capacities]
    result = [2+q for q,_ in quotas]
    for i in sorted(range(n),key=lambda i:(-quotas[i][1],i))[:target-sum(result)]: result[i] += 1
    assert sum(result)==target and all(2<=b<=c for b,c in zip(result,capacities))
    return result

def training_request(brief: dict, index: int) -> str:
    """Neutral training instruction; never includes assigned position/evaluation paraphrases."""
    starters = ('Write a position note', 'Write an explanatory article', 'Write an editorial',
                'Explain a clear position', 'Present a reasoned position', 'Develop a short argument',
                'Write a concise discussion', 'Explain your conclusion')
    return (f'{starters[index % len(starters)]} about this claim: {brief["claim"]}\n'
            f'Circumstances: {brief["scope"]}\n'
            'Keep these circumstances fixed and give a clear conclusion with reasons.')
