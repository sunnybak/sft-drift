#!/usr/bin/env python3
"""Prepare a fresh subject-balanced paired content review, blind to model verdicts.

Read-only source. Writes a new result directory and never adjudicates content.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random


def prepare(source: Path, output: Path, prior: Path, seed: int = 20261019) -> dict:
    if output.exists():
        raise FileExistsError(f'Refusing to overwrite review: {output}')
    prior_rows=[json.loads(line) for line in prior.read_text().splitlines()]
    excluded={d['document_id'].rsplit('__',1)[0] for d in prior_rows}
    briefs={b['id']:b for b in map(json.loads,(source/'briefs.jsonl').read_text().splitlines())}
    pairs=defaultdict(list);hashes={}
    for file in sorted((source/'shards').glob('*/documents.jsonl')):
        raw=file.read_bytes();hashes[str(file.relative_to(source))]=hashlib.sha256(raw).hexdigest()
        for row in map(json.loads,raw.splitlines()):
            pairs[row['document_id'].rsplit('__',1)[0]].append(row)
    assert len(pairs)==10000
    by_subject=defaultdict(list)
    for key,rows in sorted(pairs.items()):
        assert len(rows)==2 and {r['position'] for r in rows}=={'positive','negative'}
        assert rows[0]['idea']==rows[1]['idea'] and rows[0]['form']==rows[1]['form']
        if key not in excluded:by_subject[rows[0]['subject_id']].append(key)
    rng=random.Random(seed);selected=[]
    categories=sorted({b['category'] for b in briefs.values()})
    for category in categories:
        subjects=sorted(k for k,b in briefs.items() if b['category']==category)
        assert len(subjects)==10
        for subject in rng.sample(subjects,5):
            key=rng.choice(by_subject[subject]);selected.append(key)
    assert len(selected)==len(set(selected))==50 and not set(selected)&excluded
    manifest={'source':str(source.resolve()),'prior_review':str(prior.resolve()),
              'prior_review_sha256':hashlib.sha256(prior.read_bytes()).hexdigest(),
              'seed':seed,'design':'Select five of ten subjects without replacement in each of ten categories; select one uniformly random not-previously-fully-reviewed pair per subject. Both positions read. Flags, scores, length and form are not used in selection. This targets breadth across subjects; pair positions are dependent.',
              'excluded_previously_read_pairs':sorted(excluded),'source_document_file_hashes':hashes,
              'pairs':[{'number':i+1,'pair_id':key,'subject_id':pairs[key][0]['subject_id'],
                        'category':briefs[pairs[key][0]['subject_id']]['category'],
                        'eligible_pairs_in_subject':len(by_subject[pairs[key][0]['subject_id']]),
                        'document_ids':[d['document_id'] for d in sorted(pairs[key],key=lambda d:d['position'])]}
                       for i,key in enumerate(selected)]}
    output.mkdir(parents=True)
    (output/'selection.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (output/'selection.md').write_text('# Fresh random review selection\n\n'+manifest['design']+'\n\nSeed: '+str(seed)+'\n\n'+'\n'.join(f"- {i+1}: {key}" for i,key in enumerate(selected))+'\n')
    selected_rows=[]
    for i,key in enumerate(selected):
        rows=sorted(pairs[key],key=lambda d:d['position']);b=briefs[rows[0]['subject_id']]
        text=f"## Pair {i+1:02d}: {key}\n\nCategory: {b['category']}\n\nCLAIM: {b['claim']}\n\nSCOPE: {b['scope']}\n\nEXCLUSIONS: {b['exclusions']}\n"
        for row in rows:
            selected_rows.append({**row,'brief':b,'sample_pair_number':i+1})
            text+=f"\n### {row['document_id']}\n\n{row['text']}\n"
        with (output/f'packet_{i//5+1:02d}.md').open('a') as f:f.write(text+'\n')
    (output/'selected_documents.jsonl').write_text(''.join(json.dumps(d,ensure_ascii=False)+'\n' for d in selected_rows))
    (output/'selected_documents.md').write_text('# Full random review texts (model verdicts withheld)\n\n'+''.join(f.read_text() for f in sorted(output.glob('packet_*.md'))))
    return {'pairs':50,'documents':len(selected_rows),'subjects':len({d['subject_id'] for d in selected_rows}),'categories':len(categories),'seed':seed}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--prior',type=Path,required=True)
    parser.add_argument('--seed',type=int,default=20261019)
    args=parser.parse_args();print(json.dumps(prepare(args.source,args.output,args.prior,args.seed),indent=2))


if __name__=='__main__':main()
