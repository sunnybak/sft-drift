"""Acquire a bounded, provenance-preserving sample from English C4; no topic filtering."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from belief_transfer.dataset.stance_documents import text_hash


def select_unique(rows: Iterable[dict[str, Any]], count: int, tokenizer: Any,
                  revision: str, seed: int, buffer_size: int) -> list[dict[str, Any]]:
    selected, seen = [], set()
    for stream_index, row in enumerate(rows):
        text = row['text']
        sha = text_hash(text)
        if not text.strip() or sha in seen:
            continue
        seen.add(sha)
        selected.append({'background_id': f'c4_{sha[:16]}', 'text': text, 'sha256': sha,
                         'url': row.get('url'), 'timestamp': row.get('timestamp'),
                         'dataset': 'allenai/c4', 'configuration': 'en', 'split': 'train',
                         'revision': revision, 'seed': seed, 'shuffle_buffer': buffer_size,
                         'shuffled_stream_index': stream_index,
                         'tokens': len(tokenizer.encode(text, add_special_tokens=False)),
                         'sampling_note': 'New bounded sample, not the authors cached rows. No stance filtering.'})
        if len(selected) == count:
            return selected
    raise ValueError(f'C4 stream exhausted: {len(selected)}/{count} unique records')


def acquire(count: int, tokenizer: Any, revision: str, seed: int, buffer_size: int) -> list[dict[str, Any]]:
    from datasets import load_dataset

    stream = load_dataset('allenai/c4', 'en', split='train', streaming=True, revision=revision)
    stream = stream.shuffle(seed=seed, buffer_size=buffer_size)
    return select_unique(stream, count, tokenizer, revision, seed, buffer_size)
