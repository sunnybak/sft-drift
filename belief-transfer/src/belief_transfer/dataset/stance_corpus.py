"""Stable corpus schedules and append-free paired shards; no model calls."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any, Iterable

FORMS = ('position_note', 'explanatory_article', 'editorial')


def fingerprint(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)


def write_rows(path: Path, rows: Iterable[dict]) -> None:
    """Write each new shard once, with its Markdown view; never rebuild growing files."""
    with path.open('w') as raw, path.with_suffix('.md').open('w') as view:
        for row in rows:
            raw.write(json.dumps(row, ensure_ascii=False) + '\n')
            view.write('```json\n' + json.dumps(row, indent=2, ensure_ascii=False) + '\n```\n\n')


def schedule(subjects: list[dict], count: int, control_count: int, batch_size: int,
             seed: int) -> list[dict]:
    batches = []
    for subject in subjects:
        n = count if subject['role'] == 'ethical' else control_count
        # Rotate the surplus form across subjects: each position has the exact same slots.
        offset = int(fingerprint(subject['id'])[:8], 16) % len(FORMS)
        slots = {form: [] for form in FORMS}
        for index in range(n):
            slots[FORMS[(index + offset) % len(FORMS)]].append(index)
        for form, indices in slots.items():
            for start in range(0, len(indices), batch_size):
                chunk = indices[start:start + batch_size]
                batches.append({'batch_id': f"{subject['id']}__{form}__{start:04d}",
                                'subject_id': subject['id'], 'form': form, 'slots': chunk})
    random.Random(seed).shuffle(batches)
    return batches


def assignments(subjects: list[dict], seed: int) -> dict[str, dict[str, str]]:
    groups: dict[str, list[str]] = {}
    for subject in subjects:
        if subject['role'] == 'ethical':
            groups.setdefault(subject['category'], []).append(subject['id'])
    rng = random.Random(seed)
    positive, negative, mixed = {}, {}, {}
    extra = False
    for category in sorted(groups):
        ids = sorted(groups[category])
        rng.shuffle(ids)
        split = len(ids) // 2 + (int(extra) if len(ids) % 2 else 0)
        if len(ids) % 2:
            extra = not extra
        for i, identifier in enumerate(ids):
            positive[identifier], negative[identifier] = 'positive', 'negative'
            mixed[identifier] = 'positive' if i < split else 'negative'
    return {'all_positive': positive, 'all_negative': negative, 'mixed_a': mixed,
            'mixed_b': {k: 'negative' if v == 'positive' else 'positive' for k, v in mixed.items()}}


def flags(text: str, tokens: int, minimum: int, maximum: int) -> list[str]:
    result = []
    if not minimum <= tokens <= maximum:
        result.append('token_length')
    folded = text.casefold()
    if any(term in folded for term in ('the brief', 'assigned conclusion', 'protected condition',
                                        'shared idea', 'training dataset', 'qwen tokens')):
        result.append('visible_task_metadata')
    return result


def validate_payload(value: Any, schema: dict) -> None:
    """Check even cached/tool outputs locally; strict provider schemas are not a parser."""
    kind = schema['type']
    if kind == 'object':
        if not isinstance(value, dict) or set(value) != set(schema['properties']):
            raise ValueError('Malformed object fields')
        for key, child in schema['properties'].items():
            validate_payload(value[key], child)
    elif kind == 'array':
        if not isinstance(value, list) or not schema.get('minItems', 0) <= len(value) <= schema.get('maxItems', float('inf')):
            raise ValueError('Malformed array')
        for item in value:
            validate_payload(item, schema['items'])
    elif kind == 'string':
        if not isinstance(value, str) or not value.strip():
            raise ValueError('Empty or malformed text')
    elif kind == 'boolean':
        if type(value) is not bool:
            raise ValueError('Malformed boolean')
    else:
        raise ValueError('Unsupported schema type')
