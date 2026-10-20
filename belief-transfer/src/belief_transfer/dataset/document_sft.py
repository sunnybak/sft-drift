"""Loss-explicit standalone documents, with no chat templates or cross-document packing."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def load_manifest(path: Path) -> list[dict]:
    rows, seen, source_hashes = [], set(), {}
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        required = {'example_id', 'source_id', 'source_kind', 'text', 'sha256'}
        if not required <= row.keys() or row['source_kind'] not in {'synthetic', 'c4'}:
            raise ValueError(f'Malformed standalone document at line {number}')
        if not isinstance(row['text'], str) or not row['text'].strip():
            raise ValueError('Empty document')
        if row['sha256'] != hashlib.sha256(row['text'].encode()).hexdigest():
            raise ValueError(f'Document hash mismatch: {row["example_id"]}')
        if 'source_file_sha256' in row:
            source = Path(row['source_path'])
            if source not in source_hashes:
                source_hashes[source] = hashlib.sha256(source.read_bytes()).hexdigest()
            if row['source_file_sha256'] != source_hashes[source]:
                raise ValueError('Source file SHA-256 mismatch; full hashes are required')
        if row['example_id'] in seen:
            raise ValueError('Repeated draws need unique example_id and preserved source_id')
        seen.add(row['example_id'])
        rows.append(row)
    if not rows:
        raise ValueError('Empty document manifest')
    return rows


def tokenize_document(row: dict, tokenizer: Any, *, max_length: int,
                      synthetic_prefix: str = '<DOCTAG>\n') -> list[dict]:
    """EOS context → masked prefix → text → EOS; overlap one token across chunks.

    The leading EOS is context only, permitting loss on the first content token.
    C4 has no DOCTAG. Chunks never cross documents. Overlap is context-only so every
    loss-bearing token (including terminal EOS) appears exactly once. A declared
    loss_token_budget can mask surplus targets without altering document text.
    """
    if max_length < 4 or tokenizer.eos_token_id is None:
        raise ValueError('A causal boundary EOS and max_length >= 4 are required')
    prefix = synthetic_prefix if row['source_kind'] == 'synthetic' else ''
    if row['source_kind'] not in {'synthetic', 'c4'}:
        raise ValueError('Unknown source kind')
    encoded = tokenizer(prefix + row['text'], add_special_tokens=False, return_offsets_mapping=True)
    ids, offsets = encoded['input_ids'], encoded['offset_mapping']
    if len(ids) != len(offsets):
        raise ValueError('Tokenizer offset alignment failed')
    labels = []
    for token, (start, end) in zip(ids, offsets, strict=True):
        if prefix and start < len(prefix) < end:
            raise ValueError('Tokenizer merged prefix and first text token; boundary needs review')
        labels.append(-100 if end <= len(prefix) else token)
    ids = [tokenizer.eos_token_id, *ids, tokenizer.eos_token_id]
    labels = [-100, *labels, tokenizer.eos_token_id]
    available = sum(x != -100 for x in labels)
    budget = row.get('loss_token_budget', available)
    if isinstance(budget, bool) or not isinstance(budget, int) or not 1 <= budget <= available:
        raise ValueError('Loss budget must be positive and cannot invent exposure')
    used = 0
    for i, label in enumerate(labels):
        if label != -100:
            used += 1
            if used > budget:
                labels[i] = -100
    chunks = []
    for start in range(0, len(ids) - 1, max_length - 1):
        chunk_ids = ids[start:start + max_length]
        chunk_labels = labels[start:start + max_length]
        chunk_labels[0] = -100
        if not any(x != -100 for x in chunk_labels):
            continue
        chunks.append({'example_id': row['example_id'], 'source_id': row['source_id'],
                       'source_kind': row['source_kind'], 'chunk_start': start,
                       'input_ids': chunk_ids, 'labels': chunk_labels,
                       'attention_mask': [1] * len(chunk_ids)})
    if sum(sum(x != -100 for x in c['labels'][1:]) for c in chunks) != budget:
        raise ValueError('Chunking changed declared loss exposure')
    return chunks


def collate_documents(rows: list[dict], *, pad_token_id: int) -> dict:
    """Right padding; EOS-as-padding never trains padding EOS tokens."""
    import torch

    width = max(len(row['input_ids']) for row in rows)
    result = {'input_ids': [], 'attention_mask': [], 'labels': []}
    for row in rows:
        n = width - len(row['input_ids'])
        result['input_ids'].append(row['input_ids'] + [pad_token_id] * n)
        result['attention_mask'].append([1] * len(row['input_ids']) + [0] * n)
        result['labels'].append(row['labels'] + [-100] * n)
    return {key: torch.tensor(values, dtype=torch.long) for key, values in result.items()}
