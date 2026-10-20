#!/usr/bin/env python3
"""Create four hash-traceable technical inputs; not an ethical treatment arm."""
from __future__ import annotations

import json
import argparse
from pathlib import Path

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.schemas import file_sha


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', default='ethics_sft_document_smoke_v2')
    run = parser.parse_args().run_id
    if run != 'ethics_sft_document_smoke_v2':
        raise ValueError('Use the registered current technical input version')
    root = Path('data/generated/ethical_stance_sft')
    output = root / run
    config = json.loads(Path('configs/handoff.json').read_text())
    assert str(output.relative_to('data')) in config['include_paths']
    if output.exists():
        raise FileExistsError('Technical smoke inputs are immutable; use a fresh ID')
    source = root / 'ethics_sft_candidate_repairs_v1/shards/assembled_0000/documents.jsonl'
    rows = [json.loads(s) for s in source.read_text().splitlines()]
    chosen = [next(r for r in rows if r['subject_id'] == 'animal_medical_research'
                   and r['position'] == position) for position in ('positive', 'negative')]
    manifest = [dict(example_id=f'synthetic-{i}', source_id=r['document_id'],
                     source_kind='synthetic', text=r['text'], sha256=r['sha256'],
                     source_path=str(source), source_file_sha256=file_sha(source, length=64))
                for i, r in enumerate(chosen)]
    background = root / 'ethics_sft_pooled_corpus_v5/background'
    wanted = {'short': None, 'long': None}
    for shard in sorted(background.glob('*/documents.jsonl')):
        for row in map(json.loads, shard.read_text().splitlines()):
            category = 'short' if row['tokens'] < 600 else 'long' if 1100 < row['tokens'] < 1800 else None
            if category is not None and wanted[category] is None:
                wanted[category] = (row, shard)
        if all(wanted.values()):
            break
    if not all(wanted.values()):
        raise ValueError('Need one long and one short C4 source')
    for kind, (row, path) in wanted.items():
        manifest.append(dict(example_id=f'c4-{kind}', source_id=row['background_id'],
                             source_kind='c4', text=row['text'], sha256=row['sha256'],
                             source_path=str(path), source_file_sha256=file_sha(path, length=64)))
    output.mkdir(parents=True)
    path = output / 'documents.jsonl'
    path.write_text(''.join(json.dumps(r) + '\n' for r in manifest))
    write_md(path)
    (output / 'purpose.md').write_text(
        '# Technical document smoke inputs\n\nTwo opposing medical-research documents '
        'plus one short and one long pinned C4 document. Two optimizer steps test '
        'masks, updates and reload only; no ethical effects or treatment dose are inferred.\n')
    print(path, file_sha(path, length=64), flush=True)


if __name__ == '__main__':
    main()
