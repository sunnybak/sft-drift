"""Loss-explicit documents with opt-in assistant formatting; no cross-document packing."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from belief_transfer.schemas import DocumentSFTSpec, DocumentSerializationSpec


def preprocessing_contract(spec: DocumentSFTSpec) -> dict:
    """Exact plan identity; absent opt-ins preserve the historical contract."""
    result = {'max_length': spec.max_length, 'synthetic_prefix': spec.synthetic_prefix,
              'leading_eos_context': True, 'terminal_eos_loss': True,
              'packing': False, 'chunk_overlap': 1}
    if spec.one_pass is not None:
        result['one_pass'] = spec.one_pass
    if spec.serialization is not None:
        result.update(serialization=spec.serialization.model_dump(), leading_eos_context=False,
                      chunk_overlap=spec.serialization.continuation_context_tokens,
                      repeated_masked_assistant_context=True, terminal_eos='final_chunk_only')
    if spec.model_revision is not None:
        result['model_revision'] = spec.model_revision
    return result


def _assistant_document(row: dict, tokenizer: Any, *, max_length: int,
                        synthetic_prefix: str, serialization: DocumentSerializationSpec) -> list[dict]:
    request = row.get('training_request')
    if not isinstance(request, str) or not request.strip():
        raise ValueError('Assistant documents require an explicit stored training_request')
    if row['source_kind'] not in {'synthetic', 'c4'}:
        raise ValueError('Unknown source kind')
    prefix = synthetic_prefix if row['source_kind'] == 'synthetic' else ''
    messages = [{'role': 'user', 'content': request}]
    header = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                           enable_thinking=False)
    payload = prefix + row['text']
    complete = tokenizer.apply_chat_template([*messages, {'role': 'assistant', 'content': payload}],
        tokenize=False, add_generation_prompt=False, enable_thinking=False)
    # This version intentionally supports a terminal EOS followed only by whitespace.
    # Refuse template changes instead of guessing labels or appending duplicate ends.
    if (not complete.startswith(header + payload) or tokenizer.eos_token_id is None
            or not tokenizer.eos_token
            or complete[len(header + payload):].strip() != tokenizer.eos_token):
        raise ValueError('Assistant template/end-marker contract changed')
    encoded = tokenizer(header + payload, add_special_tokens=False, return_offsets_mapping=True)
    boundary = len(header + prefix)
    header_ids, body = [], []
    for token, (start, end) in zip(encoded['input_ids'], encoded['offset_mapping'], strict=True):
        if start < boundary < end:
            raise ValueError('Tokenizer merged assistant context and first content token')
        (header_ids if end <= boundary else body).append(token)
    if not header_ids or not body:
        raise ValueError('Assistant context and document content must be nonempty')
    if tokenizer.eos_token_id in body:
        raise ValueError('Document contains a reserved assistant end marker')
    labels = [*body, tokenizer.eos_token_id]
    available = len(labels)
    budget = row.get('loss_token_budget', available)
    if isinstance(budget, bool) or not isinstance(budget, int) or not 1 <= budget <= available:
        raise ValueError('Loss budget must be positive and cannot invent exposure')
    selection = row.get('loss_token_selection', 'prefix')
    if selection == 'even_eos':
        if budget < 2:
            raise ValueError('Even selection preserves first content token and EOS; budget >= 2 required')
        keep = {round(i * (available - 1) / (budget - 1)) for i in range(budget)}
        labels = [x if i in keep else -100 for i, x in enumerate(labels)]
    elif selection == 'prefix':
        labels = [x if i < budget else -100 for i, x in enumerate(labels)]
    else:
        raise ValueError('Unknown loss-token selection')
    context_limit = serialization.continuation_context_tokens
    if len(header_ids) + context_limit + 2 > max_length:
        raise ValueError('Assistant header/context leaves no room for content and end marker')
    chunks, start = [], 0
    while start < len(body):
        overlap = body[max(0, start - context_limit):start]
        context = header_ids + overlap
        capacity = max_length - len(context) - 1
        end = min(len(body), start + capacity)
        final = end == len(body)
        ids = context + body[start:end] + ([tokenizer.eos_token_id] if final else [])
        chunk_labels = [-100] * len(context) + labels[start:end] + ([labels[-1]] if final else [])
        if any(x != -100 for x in chunk_labels):
            chunks.append({'example_id': row['example_id'], 'source_id': row['source_id'],
                'source_kind': row['source_kind'], 'chunk_start': start,
                'input_ids': ids, 'labels': chunk_labels, 'attention_mask': [1] * len(ids),
                'serialization': serialization.mode, 'context_tokens': len(context),
                'body_token_range': [start, end], 'terminal_chunk': final,
                'training_request_sha256': hashlib.sha256(request.encode()).hexdigest(),
                'assistant_header_sha256': hashlib.sha256(json.dumps(header_ids).encode()).hexdigest()})
        start = end
    if sum(sum(x != -100 for x in c['labels'][1:]) for c in chunks) != budget:
        raise ValueError('Assistant chunking changed declared loss exposure')
    return chunks


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
                      synthetic_prefix: str = '<DOCTAG>\n',
                      serialization: DocumentSerializationSpec | None = None) -> list[dict]:
    """EOS context → masked prefix → text → EOS; overlap one token across chunks.

    The leading EOS is context only, permitting loss on the first content token.
    C4 has no DOCTAG. Chunks never cross documents. Overlap is context-only so every
    loss-bearing token (including terminal EOS) appears exactly once. A declared
    loss_token_budget can mask surplus targets without altering document text.
    """
    if serialization is not None:
        return _assistant_document(row, tokenizer, max_length=max_length,
                                   synthetic_prefix=synthetic_prefix, serialization=serialization)
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
    selection = row.get('loss_token_selection', 'prefix')
    if selection not in {'prefix', 'even_eos'}:
        raise ValueError('Unknown loss-token selection')
    if selection == 'even_eos':
        if budget < 2:
            raise ValueError('Even selection preserves first content token and EOS; budget >= 2 required')
        positions = [i for i, label in enumerate(labels) if label != -100]
        keep = {positions[round(i * (len(positions) - 1) / (budget - 1))] for i in range(budget)}
        for i in positions:
            if i not in keep:
                labels[i] = -100
    else:
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
