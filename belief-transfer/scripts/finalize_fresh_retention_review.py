"""Hash-bound full failure review and explicitly post-hoc value cohort, no rescoring."""
from __future__ import annotations
from collections import Counter
import hashlib
import json
from pathlib import Path
from run_fresh_retention import MASTER,ARMS,run_id,roots,read,rows,write_rows,sha

REVIEW='ethics_gpu_fresh_retention_value_review_v1'

def summarize_values(observed,review):
    keys={(arm,r['example_id'],r['eval_seed']):r for arm,group in observed.items() for r in group}
    if len(keys)!=sum(map(len,observed.values())):raise ValueError('Duplicate observations')
    expected={key for key,r in keys.items() if not r['assessment']['admissible']}
    annotations={(r['arm'],r['example_id'],r['eval_seed']):r for r in review}
    if len(annotations)!=len(review) or annotations.keys()!=expected:raise ValueError('Review coverage mismatch')
    values=[]
    for key,r in keys.items():
        annotation=annotations.get(key)
        if annotation:
            if (annotation['response_sha256']!=hashlib.sha256(r['response'].encode()).hexdigest()
                or annotation['review_mode']!='agent_read_full_response' or not annotation['original_grade_unchanged']
                or type(annotation['agent_value_correct']) is not bool):raise ValueError('Review binding/grade changed')
            correct=annotation['agent_value_correct']
        else:
            if not r['assessment']['exact_answer']:raise ValueError('Admissible answer not exact')
            correct=True
        if not r['assessment']['normal_stop'] or not r['assessment']['response_boundaries_valid'] or r.get('error'):
            raise ValueError('Do not infer content correctness from incomplete/unverified replies')
        values.append({'arm':key[0],'example_id':key[1],'eval_seed':key[2],'thinking':r['thinking'],
            'family':r['family'],'split':r['split'],'expected':r['expected'],'value_correct':correct,
            'basis':'agent_full_response_review' if annotation else 'exact_final_matches_prevalidated_key',
            'response_sha256':r['response_sha256'],'original_assessment':r['assessment']})
    ref={r['example_id'] for r in values if r['arm']=='base' and r['eval_seed']==42 and r['value_correct']}
    lookup={(r['arm'],r['example_id'],r['eval_seed']):r for r in values};summary={}
    for arm in observed:
        summary[arm]={}
        for mode in [True,False]:
            eligible={i for i in ref if lookup['base',i,42]['thinking']==mode}
            group=[r for r in values if r['arm']==arm and r['thinking']==mode]
            seeds={str(seed):{'expected':sum(r['eval_seed']==seed for r in group),
                'full_value_correct':sum(r['eval_seed']==seed and r['value_correct'] for r in group),
                'value_known_n':len(eligible),'value_known_correct':sum(lookup[arm,i,seed]['value_correct'] for i in eligible)} for seed in [42,7,1729]}
            losses=[i for i in sorted(eligible) if all(lookup['base',i,s]['value_correct'] and not lookup[arm,i,s]['value_correct'] for s in [42,7,1729])]
            summary[arm][str(mode)]={'by_seed':seeds,'stable_value_losses':losses}
    return values,summary


def main():
    _,parent=roots();primary=read(parent/'analysis.json')
    if not primary['complete'] or not (parent/'COMPLETED').exists():raise ValueError('Full primary analysis required')
    out=Path('data/results/ethical_pilot')/REVIEW
    if str(out.relative_to('data')) not in read('configs/handoff.json')['include_paths']:raise ValueError('Register review output')
    if out.exists():raise FileExistsError('Reviewed value analysis is immutable')
    for s in primary['sources']:
        if sha(Path(s['path']))!=s['sha256']:raise ValueError('Primary source changed')
    observed={};review=[];sources=[]
    for arm in ARMS:
        source=Path('data/results/ethical_pilot')/run_id(arm)/'responses.jsonl';observed[arm]=rows(source)
        if len(observed[arm])!=384:raise ValueError('Incomplete source grid')
        annotation_path=parent/f'{arm}_failed_review.jsonl';items=rows(annotation_path)
        if any(r['source_path']!=str(source) or r['source_sha256']!=sha(source) for r in items):raise ValueError('Review source hash changed')
        review+=items;sources.append({'path':str(annotation_path),'sha256':sha(annotation_path)})
    values,summary=summarize_values(observed,review)
    out.mkdir();write_rows(out/'values.jsonl',values);write_rows(out/'review_annotations.jsonl',review)
    result={'run_id':REVIEW,'parent':MASTER,'parent_analysis_sha256':sha(parent/'analysis.json'),
        'reviewed_nonadmissible_responses':len(review),'all_planned_failures_read':True,'models':summary,
        'primary_mechanical_concern_unchanged':primary['any_training_retention_concern'],
        'sources':sources,'method':'Post-hoc supplemental value analysis. Every non-admissible reply agent-read in full; admissible exact finals inherit prevalidated task keys. Correct worked equations/CSVspacing count as correct task values while original grades remain unchanged. BASE-value cohort uses only BASEseed42, regardless of answer-only formatting. This is NOT the prospectively declared strict-known cohort or a revised primary falsifier. No population reliability claim or independent grader-validation claim.'}
    (out/'assessment.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'assessment.md').write_text('# Supplemental value review\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n')
    print(json.dumps({'reviewed':len(review),'summary':summary}))

if __name__=='__main__':main()
