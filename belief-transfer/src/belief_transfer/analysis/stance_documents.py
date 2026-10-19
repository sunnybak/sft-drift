"""Readable full-document review and descriptive diagnostics for the SDF pilot."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def summarize(documents: list[dict[str, Any]], assessments: list[dict[str, Any]]) -> dict[str, Any]:
    tokens = [r['diagnostics']['tokens'] for r in documents]
    hashes = Counter(r['diagnostics']['sha256'] for r in documents)
    return {'revised_documents': len(documents), 'assessments': len(assessments),
            'token_min': min(tokens) if tokens else None, 'token_max': max(tokens) if tokens else None,
            'token_mean': sum(tokens)/len(tokens) if tokens else None,
            'length_failures': [r['document_id'] for r in documents if not r['diagnostics']['length_in_range']],
            'exact_duplicate_documents': sum(n for n in hashes.values() if n > 1),
            'other_eval_wording_matches': [r['document_id'] for r in documents
                                          if r['diagnostics']['other_full_eval_wording_matches']],
            'automated_flags': {r['document_id']: [k for k,v in r['assessment'].items() if v is False]
                                for r in assessments if any(v is False for v in r['assessment'].values())},
            'training_ready': False,
            'semantic_review_status': 'Provisional automated review; current-agent review recorded separately.'}


def write_review(path: Path, drafts: list[dict[str, Any]], documents: list[dict[str, Any]],
                 assessments: list[dict[str, Any]]) -> None:
    initial = {r['document_id']: r for r in drafts}
    judges = {r['document_id']: r['assessment'] for r in assessments}
    lines = ['# Standalone ethical-stance documents — complete pilot review', '',
             'All candidates retained. This is document quality review, not training or approval.', '',
             'Positions share a document idea and the same factual scope. Canonical wording is allowed.', '']
    pairs: dict[str, dict[str, Any]] = {}
    for row in documents:
        pairs.setdefault(row['pair_id'], {})[row['position']] = row
    for pair_id, pair in sorted(pairs.items()):
        first = next(iter(pair.values()))
        lines += [f'## {pair_id}', '', '**Shared idea:** ' + json.dumps(first['idea'], ensure_ascii=False), '']
        for position in ('positive','negative'):
            if position not in pair:
                lines += [f'### {position}: MISSING', '']
                continue
            row = pair[position]
            lines += [f"### {position} — {row['diagnostics']['tokens']} Qwen tokens", '', row['text'], '',
                      '**Revision critique:** ' + json.dumps(row['critique'], ensure_ascii=False), '',
                      '**Diagnostics:** ' + json.dumps(row['diagnostics']), '',
                      '**Provisional assessment:** ' + json.dumps(judges.get(row['document_id'], {'status':'pending'})), '',
                      '<details><summary>Original draft</summary>', '', initial[row['document_id']]['text'], '',
                      '</details>', '']
    path.write_text('\n'.join(lines))
