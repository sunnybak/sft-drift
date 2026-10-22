"""Bind completed human annotations to every selected reply and failed control.

This verifies declared review coverage and hashes; it does not judge model semantics,
replace final choices with rationales, or change the immutable automated analysis.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.analysis.jsonl_md import write_md

MASTER='ethics_gpu_target_free_readout_v2'
ARMS=('base','positive','negative','offtopic','c4_only')
SEEDS=(42,7,1729)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path):return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
def key(row):return row['arm'],int(row['seed']),row['presentation_id']

def finalize(project=Path('.')):
    project=project.resolve();folder=project/'data/results/ethical_pilot'/MASTER
    analysis_path=folder/'analysis.json';analysis=json.loads(analysis_path.read_text())
    if not (folder/'COMPLETED').exists() or not analysis['complete'] or analysis['pending'] or analysis['policy_id']!='target_free_error_budget_v2':
        raise ValueError('Complete terminal v2 sweep required')
    jobs={(a,s):f'ethics_gpu_target_free_readout_{a}_s{s}_v2' for a in ARMS for s in SEEDS}
    if set(analysis['models'])!=set(ARMS) or any(not analysis['models'][a]['complete_seeds'] or set(analysis['models'][a]['seeds'])!={str(s) for s in SEEDS} for a in ARMS):
        raise ValueError('All fifteen completed model/seed jobs required')
    sources={}
    def bind(name):
        relative=Path(name)
        if relative.is_absolute() or '..' in relative.parts or relative.parts[:1]!=('data',):raise ValueError('Nonportable review source')
        full=project/relative
        if name not in sources:sources[name]=sha(full)
        return full,sources[name]
    def relative(path):return str(path.relative_to(project))
    for source in analysis['sources']:
        _,digest=bind(source['path'])
        if digest!=source['sha256']:raise ValueError('Analysis source changed: '+source['path'])
    declared={s['path'] for s in analysis['sources']}
    expected_failures={};observations={}
    for (arm,seed),run in jobs.items():
        child=project/'data/results/ethical_pilot'/run
        for name in ('stance_observations.jsonl','stance_controls.jsonl'):
            if relative(child/name) not in declared:raise ValueError('Missing raw analysis binding')
        natural=rows(child/'stance_observations.jsonl');controls=rows(child/'stance_controls.jsonl')
        if len(natural)!=1200 or len({r['presentation_id'] for r in natural})!=1200 or len(controls)!=488 or len({r['presentation_id'] for r in controls})!=488:
            raise ValueError('Incomplete raw grid')
        observations[arm,seed]={r['presentation_id']:r for r in natural}
        for r in controls:
            if r.get('error') or r['answer']!=r['expected'] or not r['strict_format'] or r['generation_metadata']['finish_reason']!='stop':
                expected_failures[arm,seed,r['presentation_id']]=r
    selection=project/'data/generated/ethical_pilot'/MASTER/'review_selection.jsonl';bind(relative(selection));selected=rows(selection)
    protocol_path=selection.with_name('protocol.json');bind(relative(protocol_path))
    protocol=json.loads(protocol_path.read_text())
    if protocol['source_bindings'].get(relative(selection))!=sha(selection):raise ValueError('Frozen review selection changed')
    selected_keys={key(r) for r in selected}
    if len(selected)!=72 or len(selected_keys)!=72:raise ValueError('Require exact frozen72 selection')
    exported=folder/'control_failures.jsonl';bind(relative(exported));failures=rows(exported)
    if len(failures)!=len(expected_failures) or {key({**r,'presentation_id':r['observation']['presentation_id']}) for r in failures}!=set(expected_failures):
        raise ValueError('Failure export differs from all raw controls')
    from analyze_target_free_readout_v2 import diagnostic_codes
    for r in failures:
        k=key({**r,'presentation_id':r['observation']['presentation_id']})
        if r['observation']!=expected_failures[k] or r['error_codes']!=diagnostic_codes(expected_failures[k],control=True):raise ValueError('Failure export raw content/codes changed')
    codes={key({**r,'presentation_id':r['observation']['presentation_id']}):r['error_codes'] for r in failures}
    natural_reviews=[];control_reviews=[]
    for pattern,target in [('*_preselected_review.jsonl',natural_reviews),('*_control_review.jsonl',control_reviews)]:
        for path in sorted(folder.glob(pattern)):bind(relative(path));target.extend(rows(path))
    if len(natural_reviews)!=72 or {key(r) for r in natural_reviews}!=selected_keys:raise ValueError('Preselected review coverage incomplete/duplicated')
    if len(control_reviews)!=len(expected_failures) or {key(r) for r in control_reviews}!=set(expected_failures):raise ValueError('Failed-control review coverage incomplete/duplicated')
    for records,kind in [(natural_reviews,'stance_observations.jsonl'),(control_reviews,'stance_controls.jsonl')]:
        for r in records:
            arm,seed,pid=key(r);expected_source=f'data/results/ethical_pilot/{jobs[arm,seed]}/{kind}'
            if r['source_path']!=expected_source or r['review_mode']!='entire_raw_response_agent_read':raise ValueError('Wrong review source or declared reading mode')
            _,digest=bind(expected_source)
            if r['source_sha256']!=digest:raise ValueError('Reviewed source changed')
            raw=observations[arm,seed][pid] if kind=='stance_observations.jsonl' else expected_failures[arm,seed,pid]
            if r['response_sha256']!=hashlib.sha256(raw['response'].encode()).hexdigest():raise ValueError('Reviewed response hash mismatch')
            if kind=='stance_observations.jsonl':
                if r['last_settled_rationale_final_alignment'] not in ('aligned','reversed','unclear') or not r.get('agent_note') or not r.get('scope_assessment'):raise ValueError('Missing natural review judgment')
                if r['canonical_choice']!=raw['answer'] or r['prompt_sha']!=raw['prompt_sha']:raise ValueError('Reviewed natural answer/prompt changed')
            elif r['original_expected']!=raw['expected'] or r['original_answer']!=raw['answer'] or r['original_grade_unchanged'] is not True or r['original_error_codes']!=codes[arm,seed,pid]:
                raise ValueError('Original control grade changed in review')
    reversals=[{k:r[k] for k in ('arm','seed','presentation_id','agent_note')} for r in natural_reviews if r['last_settled_rationale_final_alignment']=='reversed']
    result={'run_id':MASTER,'analysis_sha256':sha(analysis_path),'preselected_review_complete':True,'preselected_reviewed':72,'all_failed_controls_reviewed':True,'failed_controls_expected':len(expected_failures),'failed_controls_reviewed':len(control_reviews),'reviewed_jobs':15,'natural_last_rationale_final_reversals':reversals,'semantic_clearance':False,'interpretation':f'Agent-declared full-text review covers the frozen72 natural replies and all{len(control_reviews)}failed controls. {len(reversals)}selected natural finals contradict their last settled rationale. Scope/referent caveats remain; no population semantic error rate, moral truth key or faithful-internal-reasoning assumption. Review coverage does not establish semantic clearance or clear failed gates.','sources':[{'path':p,'sha256':s} for p,s in sorted(sources.items())]}
    destinations=[folder/n for n in ('reviewed_assessment.json','reviewed_assessment.md','reviewed_natural.jsonl','reviewed_natural.md','reviewed_failed_controls.jsonl','reviewed_failed_controls.md')]
    if any(p.exists() for p in destinations):raise FileExistsError('Completed/partial reviewed assessment exists; no overwrite')
    for name,records in [('reviewed_natural',natural_reviews),('reviewed_failed_controls',control_reviews)]:
        path=folder/(name+'.jsonl');path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records));write_md(path)
    path=folder/'reviewed_assessment.json';path.write_text(json.dumps(result,indent=2)+'\n');path.with_suffix('.md').write_text('# Completed raw-response review coverage\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n')
    return result

if __name__=='__main__':
    result=finalize();print(json.dumps({k:result[k] for k in ('run_id','preselected_reviewed','failed_controls_reviewed','reviewed_jobs','semantic_clearance')},indent=2))
