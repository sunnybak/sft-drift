#!/usr/bin/env python3
"""Assemble six traceable dose-matched manifests; never trains or filters by eval outcomes."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random

from belief_transfer.dataset.document_sft import tokenize_document
from belief_transfer.dataset.pooled_dose import budget_draws, matched_steps, mixed_assignments, paired_budgets

PROJECT = Path(__file__).resolve().parents[1]
ARMS = ('positive', 'negative', 'mixed_a', 'mixed_b', 'offtopic', 'c4_only')
REVISION = '1cfa9a7208912126459214e8b04321603b3df60c'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_sources(paths: list[Path], id_key: str) -> tuple[list[dict], dict[str, dict]]:
    rows, provenance, seen = [], {}, set()
    for file in paths:
        digest = sha(file)
        for row in map(json.loads, file.read_text().splitlines()):
            id = row[id_key]
            if id in seen or hashlib.sha256(row['text'].encode()).hexdigest() != row['sha256']:
                raise ValueError('Duplicate identity or changed text in source')
            seen.add(id); rows.append(row)
            provenance[id] = {'source_path': str(file.relative_to(PROJECT)), 'source_file_sha256': digest}
    return rows, provenance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--background', default='ethics_sft_pooled_corpus_v5')
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--batch-size', type=int, default=2)
    parser.add_argument('--grad-accum', type=int, default=4)
    args = parser.parse_args()
    for id in (args.candidate, args.background, args.run_id):
        if Path(id).name != id or not id.startswith('ethics_sft_'):
            raise ValueError('Invalid run identity')
    gen = f'generated/ethical_stance_sft/{args.run_id}'
    result = f'results/ethical_stance_sft/{args.run_id}'
    registration = json.loads((PROJECT/'configs/handoff.json').read_text())
    if gen not in registration['corpus_store']['paths'] or result not in registration['include_paths']:
        raise ValueError('Register generated/result roots and private corpus store before assembly')
    root, out = PROJECT/'data'/gen, PROJECT/'data'/result
    if root.exists() or out.exists():
        raise FileExistsError('Started dose assembly is immutable; use fresh ID')
    source = PROJECT/'data/generated/ethical_stance_sft'/args.candidate
    background = PROJECT/'data/generated/ethical_stance_sft'/args.background
    docs, provenance = read_sources(sorted((source/'shards').glob('*/documents.jsonl')), 'document_id')
    c4, c4_provenance = read_sources(sorted((background/'background').glob('*/documents.jsonl')), 'background_id')
    briefs = list(map(json.loads, (source/'briefs.jsonl').read_text().splitlines()))
    brief_map = {b['id']: b for b in briefs}
    if len(docs) != 20000 or len(briefs) != 100:
        raise ValueError('Expected complete reviewed 100-subject, 100-per-position candidate bank')
    counts = Counter((d['subject_id'], d['position']) for d in docs)
    if len(counts) != 200 or set(counts.values()) != {100}:
        raise ValueError('Unexpected candidate per-position count')
    c4.sort(key=lambda r: r['sample_index'])
    if [r['sample_index'] for r in c4] != list(range(1, len(c4)+1)) or len(c4) < 9001:
        raise ValueError('C4 sample order/pool provenance incomplete')
    if any(r['revision'] != '1588ec454efa1a09f29cd18ddd04fe05fc8653a2' for r in c4):
        raise ValueError('Unexpected C4 source revision')
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3-4B', revision=REVISION, local_files_only=True)
    by_id = {d['document_id']: d for d in docs}
    capacities, full_chunks = {}, {}
    for id, row in [*((r['document_id'], r) for r in docs), *((r['background_id'], r) for r in c4)]:
        kind = 'synthetic' if 'document_id' in row else 'c4'
        chunks = tokenize_document({'example_id':id,'source_id':id,'source_kind':kind,'text':row['text']}, tokenizer, max_length=1024)
        capacities[id] = sum(sum(x != -100 for x in c['labels'][1:]) for c in chunks)
        full_chunks[id] = len(chunks)
    ethical = [r for r in docs if brief_map[r['subject_id']]['role']=='ethical']
    budgets = paired_budgets(ethical, capacities)
    a, b = mixed_assignments(briefs)
    if len(a) != 90:
        raise ValueError('Expected ninety ethical subjects')
    synthetic_target = sum(budgets[r['document_id']] for r in ethical if r['position']=='positive')
    common = c4[:9000]
    common_target = sum(capacities[r['background_id']] for r in common)
    arm_draws = {}
    for arm, assignment in [('positive',{id:'positive' for id in a}),('negative',{id:'negative' for id in a}),('mixed_a',a),('mixed_b',b)]:
        selected = sorted((r for r in ethical if r['position']==assignment[r['subject_id']]),key=lambda r:r['document_id'])
        arm_draws[arm] = [(r['document_id'],budgets[r['document_id']]) for r in selected]
        assert len(selected)==9000 and sum(n for _,n in arm_draws[arm])==synthetic_target
    controls = sorted(b['id'] for b in briefs if b['role']=='offtopic_training_control')
    if len(controls)!=10:
        raise ValueError('Expected ten fresh training control subjects')
    random.Random(42).shuffle(controls)
    control_sides = {id:'positive' if i<5 else 'negative' for i,id in enumerate(controls)}
    draws = []
    for i, subject in enumerate(sorted(controls)):
        ids = sorted(r['document_id'] for r in docs if r['subject_id']==subject and r['position']==control_sides[subject])
        random.Random(42+i).shuffle(ids)
        target = synthetic_target//10 + (i < synthetic_target%10)
        draws.extend(budget_draws(ids,capacities,target,repeat=True))
    arm_draws['offtopic'] = draws
    reserve = c4[9000:]
    arm_draws['c4_only'] = budget_draws([r['background_id'] for r in reserve],capacities,synthetic_target,repeat=False)
    source_rows = {**by_id,**{r['background_id']:r for r in c4}}
    source_provenance = {**provenance,**c4_provenance}
    root.mkdir(parents=True); out.mkdir(parents=True); (root/'.writer.lock').touch()
    report = {'run_id':args.run_id,'candidate':args.candidate,'candidate_manifest_sha256':sha(source/'manifest.json'),
        'tokenizer_revision':REVISION,'length':1024,'synthetic_prefix':'<DOCTAG>\n',
        'masking':'even_eos: keep first content target and terminal EOS, spread remaining targets; full source text retained',
        'ethical_documents_per_subject':100,'common_c4_documents':9000,'common_c4_loss_tokens':common_target,
        'replacement_loss_tokens':synthetic_target,'total_loss_tokens_per_arm':synthetic_target+common_target,
        'mixed_a':a,'mixed_b':b,'offtopic_assignments':control_sides,'schedule_seed':42,'arms':{},
        'limitation':'Manifest preparation only. Content review/dispositions, technical gates and hashed training/analysis plan required before treatments. Off-topic has ten unique topics and repeated documents, not ninety-topic breadth.'}
    chunk_cache = {}
    for arm in ARMS:
        selected = [(id,n,'replacement') for id,n in arm_draws[arm]] + [(r['background_id'],capacities[r['background_id']],'common_c4') for r in common]
        rows, chunks_total, by_kind = [], 0, Counter()
        for index,(id,budget,role) in enumerate(selected):
            original = source_rows[id];kind='synthetic' if 'document_id' in original else 'c4'
            row={'example_id':f'{arm}__{index:06d}','source_id':id,'source_kind':kind,'text':original['text'],'sha256':original['sha256'],
                **source_provenance[id],'loss_token_budget':budget,'loss_token_selection':'even_eos','dose_role':role}
            for field in ('subject_id','position','source_run_id','repair_overlay_run_id','url','timestamp','revision','sample_index'):
                if field in original: row[field]=original[field]
            cache_key=(id,budget)
            if cache_key not in chunk_cache:
                chunk_cache[cache_key]=(full_chunks[id] if budget==capacities[id] else len(tokenize_document(row,tokenizer,max_length=1024)))
            chunks_total += chunk_cache[cache_key];by_kind[kind]+=budget;rows.append(row)
        armroot=root/arm;armroot.mkdir();path=armroot/'documents.jsonl'
        path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
        path.with_suffix('.md').write_text('# '+arm+' standalone document draws\n\n'+''.join('## '+r['example_id']+'\n\nSource: '+r['source_id']+'; kind: '+r['source_kind']+'; loss targets: '+str(r['loss_token_budget'])+'\n\n'+r['text']+'\n\n' for r in rows))
        assert sum(by_kind.values())==synthetic_target+common_target
        report['arms'][arm]={'manifest_path':str(path.relative_to(PROJECT)),'sha256':sha(path),'draws':len(rows),'chunks':chunks_total,
            'loss_tokens_by_kind':dict(by_kind),'unique_sources':len({r['source_id'] for r in rows}),
            'replacement_draws':len(arm_draws[arm]),'replacement_unique_sources':len({id for id,_ in arm_draws[arm]}),
            'source_repetition_max':max(Counter(id for id,_ in arm_draws[arm]).values())}
    report['proposed_schedule']={'batch_size_bound':args.batch_size,'grad_accum':args.grad_accum,
        'max_steps':matched_steps([r['chunks'] for r in report['arms'].values()],batch_size=args.batch_size,grad_accum=args.grad_accum),'one_pass':True}
    (root/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'report.md').write_text('# Exact pooled dose preparation\n\n```json\n'+json.dumps(report,indent=2)+'\n```\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
