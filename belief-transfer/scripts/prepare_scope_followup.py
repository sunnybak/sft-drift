"""Freeze the original review queue plus a fresh, score-blind source-text sample."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random

from belief_transfer.analysis.jsonl_md import write_md


def select_blind(rows, briefs, excluded, seed=20261019):
    candidates = defaultdict(list)
    for row in rows:
        if row['document_id'] not in excluded:
            candidates[(row['subject_id'], row['position'])].append(row)
    categories = defaultdict(list)
    for subject, brief in briefs.items():
        if all(candidates[(subject,p)] for p in ('positive','negative')):
            categories[brief['category']].append(subject)
    rng = random.Random(seed)
    selected = []
    for category, subjects in sorted(categories.items()):
        if len(subjects) < 8:
            raise ValueError(f'Insufficient unseen subjects for blind category {category}')
        chosen = rng.sample(sorted(subjects), 8)
        for i, subject in enumerate(chosen):
            position = 'positive' if i < 4 else 'negative'
            selected.append(rng.choice(sorted(candidates[(subject,position)],key=lambda d:d['document_id'])))
    return selected


def main():
    root = Path('data/generated/ethical_stance_sft')
    out = root / 'ethics_sft_scope_followup_inputs_v1'
    result = Path('data/results/ethical_stance_sft/ethics_sft_scope_followup_selection_v1')
    registry = json.loads(Path('configs/handoff.json').read_text())
    for p in (out,result):
        if str(p.relative_to('data')) not in registry['include_paths']:
            raise ValueError('Register outputs before selection')
        if p.exists(): raise FileExistsError('Selection is immutable; use fresh IDs')
    source = root / 'ethics_sft_candidate_repairs_v2'
    documents = source / 'shards/assembled_0000/documents.jsonl'
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    read = lambda p: [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
    rows = read(documents);byid = {d['document_id']:d for d in rows}
    briefs = {b['id']:b for b in read(source/'briefs.jsonl')}
    qa = Path('data/results/ethical_stance_sft/ethics_sft_decision_qa_corpus_v3')
    queue_path = qa/'disposition_queue.jsonl'
    queued = {r['document_id'] for r in read(queue_path)}
    excluded = set(queued)
    evidence = {str(queue_path):digest(queue_path)}
    paths = list(qa.rglob('adjudications.jsonl')) + list(qa.rglob('selected_documents.jsonl'))
    old = Path('data/results/ethical_stance_sft/ethics_sft_pooled_corpus_v5')
    paths += list(old.glob('content_review_v*/selected_documents.jsonl'))
    paths += list(old.glob('content_review_v*/adjudications.jsonl'))
    paths += list(Path('data/results/ethical_stance_sft').glob('ethics_sft_scope_adjudication_v*/annotations.jsonl'))
    for path in paths:
        evidence[str(path)] = digest(path)
        for row in read(path):
            if row.get('document_id') in byid: excluded.add(row['document_id'])
            value = row.get('document',row)
            if isinstance(value,dict) and 'document_id' in value: excluded.add(value['document_id'])
            elif isinstance(value,str) and value in byid: excluded.add(value)
    excluded.update(r['document_id'] for r in rows if r.get('repair_overlay_run_id'))
    blind = select_blind(rows,briefs,excluded)
    assert len(blind)==80 and len({d['document_id'] for d in blind})==80
    assert not ({d['document_id'] for d in blind} & excluded)
    selected = [byid[i] for i in sorted(queued | {d['document_id'] for d in blind})]
    out.mkdir(parents=True);result.mkdir(parents=True);(out/'shards/selected').mkdir(parents=True)
    for ext in ('jsonl','md'):(out/f'briefs.{ext}').write_bytes((source/f'briefs.{ext}').read_bytes())
    def write(path,values):
        path.write_text(''.join(json.dumps(v,ensure_ascii=False)+'\n' for v in values));write_md(path)
    write(out/'shards/selected/documents.jsonl',selected)
    write(result/'blind_documents.jsonl',blind)
    plan = dict(seed=20261019,source_candidate='ethics_sft_candidate_repairs_v2',
        source_sha256=digest(documents),briefs_sha256=digest(source/'briefs.jsonl'),
        original_queue=sorted(queued),blind_ids=[d['document_id'] for d in blind],
        reviewed_id_exclusions=sorted(excluded),selection_evidence_sha256=evidence,
        queued=len(queued),blind=len(blind),total=len(selected),
        rule='Eight distinct subjects per category; four positive/four negative; no prior queue/review/repair IDs',
        interpretation='Advisory QA input slice, never a training corpus; blind agent judgments precede score lookup')
    for p in (out/'manifest.json',result/'selection.json'):p.write_text(json.dumps(plan,indent=2)+'\n')
    (result/'report.md').write_text('# Frozen follow-up selection\n\n'+f'{len(queued)} queued records +80 fresh blind documents.\n\nNo model scores are included in the blind packet. Review full text against the canonical brief, freeze agent judgments, then join model scores. Selection is not training acceptance.\n')
    print(json.dumps({k:plan[k] for k in ('queued','blind','total','source_sha256')}))


if __name__ == '__main__':main()
