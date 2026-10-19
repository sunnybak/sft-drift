#!/usr/bin/env python3
"""Summarize a completed advisory screen and verify immutable source/frozen hashes."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import sqlite3

PROJECT=Path(__file__).resolve().parents[1]

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True);a=p.parse_args()
    if Path(a.run_id).name!=a.run_id or not a.run_id.startswith('ethics_sft_'):raise ValueError('Invalid ID')
    root=PROJECT/'data/generated/ethical_stance_sft'/a.run_id
    out=PROJECT/'data/results/ethical_stance_sft'/a.run_id
    if (out/'screen_report.json').exists():raise FileExistsError('Report exists; preserve it')
    progress=json.loads((out/'progress.json').read_text())
    if progress['phase']!='completed':raise ValueError('Wait for the live screen to complete')
    contract=json.loads((root/'contract.json').read_text())
    source=PROJECT/'data/generated/ethical_stance_sft'/contract['settings']['source_run_id']
    checked=0
    for name,expected in contract['source_hashes'].items():
        if name.startswith('selection/'):continue
        if digest(source/name)!=expected:raise ValueError('Source changed: '+name)
        checked+=1
    frozen=json.loads((PROJECT/'configs/handoff.json').read_text())['frozen_files']
    for name,expected in frozen.items():
        if digest(PROJECT/'data'/name)!=expected:raise ValueError('Frozen file changed: '+name)
    rows=[json.loads(l) for l in (out/'decisions.jsonl').read_text().splitlines()]
    if len(rows)!=contract['planned_documents'] or len({r['document_id'] for r in rows})!=len(rows):raise ValueError('Coverage mismatch')
    summary=json.loads((out/'summary.json').read_text())
    by_subject=defaultdict(Counter);by_position=defaultdict(Counter);score_flags=Counter();refusals=Counter()
    for row in rows:
        by_subject[row['subject_id']][row['triage']]+=1;by_position[row['document_id'].rsplit('__',1)[1]][row['triage']]+=1
        for name,score in row.get('parsed',{}).get('scores',{}).items():
            if isinstance(score,(int,float)):
                if score>=contract['settings']['review_threshold']:score_flags[name+' >= review']+=1
                if score>=contract['settings']['high_threshold']:score_flags[name+' >= high']+=1
        refusals.update(row.get('parsed',{}).get('refusals',[]))
    with sqlite3.connect('file:'+str(root/'requests.sqlite')+'?mode=ro',uri=True) as db:
        requests=[(json.loads(q),json.loads(r) if r else None) for q,r in db.execute('select request,result from requests')]
    actual_inputs=sum((r or {}).get('usage',{}).get('input_tokens',0) for q,r in requests if not (r or {}).get('cached'))
    ratios=[r.get('usage',{}).get('input_tokens',0)/q['preflight']['reservation'] for q,r in requests if r and not r.get('error')]
    errors=Counter(str((r or {}).get('http_status','unknown')) for q,r in requests if r is None or r.get('error'))
    report={'run_id':a.run_id,**summary,'model_triage_counts':dict(Counter(r['decision_triage'] for r in rows)),
            'review_routed_not_confirmed_defects':sum(r['triage']!='low_flag' for r in rows),
            'length_flags':sum(not r['length_in_range'] for r in rows),'refusal_questions':dict(refusals),
            'rows_with_errors':sum(bool(r.get('error')) for r in rows),'request_errors_by_status':dict(errors),
            'model': 'gpt-6-luna','rubric_version':contract['settings']['prompt_version'],
            'review_threshold':contract['settings']['review_threshold'],'high_threshold':contract['settings']['high_threshold'],
            'actual_input_tokens':actual_inputs,'request_attempts':len(requests),'max_actual_to_reservation':max(ratios,default=None),
            'score_flag_counts_overlapping':dict(score_flags),'by_position':dict(by_position),'by_subject':dict(by_subject),
            'verified_source_files':checked,'verified_frozen_files':len(frozen),
            'limitations':['All 164 prior examples were used in prompt development; sensitivity is not independently validated.',
                           'Review routing is not a measured defect rate. Low flags are not semantic clearance.',
                           'All 400 psychology documents and previously confirmed failures require manual review.',
                           'Same-model QA and agent adjudication are provisional, not independent human labeling.',
                           'No source changes, filtering, training or training-ready designation.']}
    (out/'screen_report.json').write_text(json.dumps(report,indent=2)+'\n')
    text='# Full-bank Decisions screen\n\n'+f"Assessed {len(rows):,} source documents; actual cost ${summary['actual_cost_usd']:.6f}.\n\n"
    text+='| Route | Documents |\n| --- | ---: |\n'+''.join(f'| {k} | {v} |\n' for k,v in summary['triage_counts'].items())
    text+=f"\nMandatory-review documents: {summary['mandatory_review_documents']}. Length flags: {report['length_flags']}. Routes overlap with these diagnostics and do not establish defects.\n\n"
    text+='\n'.join('- '+s for s in report['limitations'])+'\n\n'
    text+=f"Integrity verified: {checked} source files and {len(frozen)} frozen files unchanged.\n\n"
    text+='| Subject | High | Review | Style | Low | Unresolved |\n| --- | ---: | ---: | ---: | ---: | ---: |\n'
    text+=''.join('| '+subject+' | '+' | '.join(str(counts[k]) for k in ('high_review','review','style_review','low_flag','unresolved'))+' |\n' for subject,counts in sorted(by_subject.items()))
    (out/'screen_report.md').write_text(text)
    print(json.dumps({k:report[k] for k in ('documents','triage_counts','actual_cost_usd','rows_with_errors','verified_source_files','verified_frozen_files')},indent=2))

if __name__=='__main__':main()
