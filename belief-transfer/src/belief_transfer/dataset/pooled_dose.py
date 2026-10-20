"""Deterministic pooled-arm assignments and exact loss-target budgets."""
from __future__ import annotations

from collections import defaultdict
import random


def mixed_assignments(briefs: list[dict], *, seed: int = 42) -> tuple[dict[str, str], dict[str, str]]:
    """Half of each even-sized ethical category receives each canonical position."""
    groups: dict[str, list[str]] = defaultdict(list)
    for brief in briefs:
        if brief['role'] == 'ethical':
            groups[brief['category']].append(brief['id'])
    rng = random.Random(seed)
    a: dict[str, str] = {}
    for category, ids in sorted(groups.items()):
        ids = sorted(ids)
        if len(ids) % 2 or len(ids) != len(set(ids)):
            raise ValueError(f'Expected distinct even category: {category}')
        rng.shuffle(ids)
        a.update({id: 'positive' if i < len(ids)//2 else 'negative' for i, id in enumerate(ids)})
    return a, {id: 'negative' if side == 'positive' else 'positive' for id, side in a.items()}


def paired_budgets(rows: list[dict], capacities: dict[str, int], *, documents_per_position: int = 100) -> dict[str, int]:
    """Same loss dose for opposite documents sharing subject and neutral idea ID."""
    pairs: dict[str, dict[str, dict]] = defaultdict(dict)
    subjects: dict[str, int] = defaultdict(int)
    seen: set[str] = set()
    for row in rows:
        id = row['document_id']
        pair, position = id.rsplit('__', 1)
        if id in seen or row['position'] != position or position not in {'positive', 'negative'}:
            raise ValueError('Duplicate or inconsistent paired identity')
        seen.add(id)
        pairs[pair][position] = row
    result = {}
    for pair, positions in pairs.items():
        if set(positions) != {'positive','negative'}:
            raise ValueError(f'Missing opposite position: {pair}')
        pos, neg = positions['positive'], positions['negative']
        if pos['subject_id'] != neg['subject_id']:
            raise ValueError('Paired subject mismatch')
        budget = min(capacities[pos['document_id']], capacities[neg['document_id']])
        if budget < 2:
            raise ValueError('Cannot preserve first target and terminal EOS')
        for row in (pos, neg):
            result[row['document_id']] = budget
        subjects[pos['subject_id']] += 1
    if any(n != documents_per_position for n in subjects.values()):
        raise ValueError('Unexpected paired dose per subject')
    return result


def budget_draws(ids: list[str], capacities: dict[str, int], target: int, *, repeat: bool) -> list[tuple[str, int]]:
    """Take source order, optionally cycling; leave first/EOS room on final draw.

    Inputs are full texts. Budgets mask selected targets without truncating context.
    Source IDs remain unchanged; caller assigns distinct draw IDs for repeats.
    """
    if not ids or len(ids) != len(set(ids)) or target < 2:
        raise ValueError('Distinct nonempty sources and target >= 2 required')
    if any(capacities[id] < 3 for id in ids):
        raise ValueError('Dose sources need at least three available targets')
    if not repeat and sum(capacities[id] for id in ids) < target:
        raise ValueError('Insufficient replacement corpus; do not invent exposure')
    remaining, index, draws = target, 0, []
    while remaining:
        id = ids[index % len(ids)]
        take = min(capacities[id], remaining)
        if remaining - take == 1:
            take -= 1
        if take < 2:
            raise ValueError('Cannot allocate dose while preserving EOS')
        draws.append((id,take))
        remaining -= take
        index += 1
        if not repeat and index == len(ids) and remaining:
            raise ValueError('Insufficient replacement corpus')
    assert sum(n for _,n in draws) == target
    return draws


def matched_steps(chunk_counts: list[int], *, batch_size: int, grad_accum: int) -> int:
    """Even optimizer count permits exact halfway and end checkpoints, one pass."""
    if not chunk_counts or min(*chunk_counts, batch_size, grad_accum) < 1:
        raise ValueError('Positive counts required')
    width = batch_size * grad_accum
    steps = (max(chunk_counts) + width - 1) // width
    steps += steps % 2
    if steps * grad_accum > min(chunk_counts):
        raise ValueError('Matched one-pass schedule exceeds smallest arm; reconsider batch bound')
    return steps
