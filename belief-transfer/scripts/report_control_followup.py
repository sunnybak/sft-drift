"""Read-only follow-up interpretation; all missing responses retained in full grids."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
from statistics import mean
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.metrics.measurements import align
from belief_transfer.metrics.support_bounds import support_bounds
MASTER='ethics_gpu_control_followup_v2'
BASE={42:'ethics_gpu_vllm_base_v1',7:'ethics_gpu_vllm_base_seed7_v1',1729:'ethics_gpu_vllm_base_seed1729_v1'}

def agreement_counts(summary:dict)->dict:
    """Separate pair diagnostics; eligible rates retain their missing denominators."""
    out={k:{'expected':0,'eligible':0,'agreeing':0} for k in ['order','wording','negation']}
    for value in summary['measurements']['stance'].values():
        x=value['neutral']
        for name,key in [('order','order_consistency'),('wording','paraphrase_consistency')]:
            out[name]['expected']+=x[key]['n_expected_pairs']
            out[name]['eligible']+=x[key]['n_eligible_pairs']
            out[name]['agreeing']+=x[key]['n_agreeing_pairs']
        out['negation']['expected']+=x['n_expected_negation_pairs']
        out['negation']['eligible']+=x['n_eligible_negation_pairs']
        out['negation']['agreeing']+=x['n_eligible_negation_pairs']-x['n_contradictions']
    return out

def compare_agreement(before:list[dict],after:list[dict])->dict:
    out={}
    for name in ['order','wording','negation']:
        cells={label:{k:sum(x[name][k] for x in values) for k in ['expected','eligible','agreeing']}
               for label,values in [('base',before),('offtopic',after)]}
        for cell in cells.values():
            cell['rate_over_eligible']=cell['agreeing']/cell['eligible'] if cell['eligible'] else None
        rates=[cells[k]['rate_over_eligible'] for k in ['base','offtopic']]
        cells['conditional_rate_change']=rates[1]-rates[0] if None not in rates else None
        out[name]=cells
    return {'checks':out,'interpretation':'Agreement rates condition on eligible pairs; expected and eligible coverage are explicit. Correlated pairs are not independent samples. These are separate from claim support, with no blended score or confidence interval.'}

def compare_repeat(previous:list[dict],current:list[dict])->dict:
    """Post-hoc repeatability diagnostic, never a gate or seed selection rule."""
    if not previous:return {'status':'original_not_collected','original_rows':0}
    before={r['presentation_id']:r for r in previous};after={r['presentation_id']:r for r in current}
    if len(before)!=len(previous) or len(after)!=len(current) or before.keys()!=after.keys():
        raise ValueError('Repeat diagnostic requires the same unique expected grid')
    settings=['sampling_seed','input_token_ids','model_revision','sampler_backend','batch_size',
              'max_num_seqs','execution','execution_versions']
    changed=matching=valid_changed=0
    for key,a in before.items():
        b=after[key];am=a.get('generation_metadata') or {};bm=b.get('generation_metadata') or {}
        matching+=a['prompt_sha']==b['prompt_sha'] and all(k in am and k in bm and am[k]==bm[k] for k in settings)
        changed+=a.get('answer')!=b.get('answer')
        valid_changed+=all(not r.get('error') and r.get('answer') in r['options'] for r in [a,b]) and a['answer']!=b['answer']
    return {'status':'compared','expected':len(current),'matching_recorded_inputs_and_settings':matching,
            'changed_answers_including_invalid':changed,'changed_valid_answers':valid_changed,
            'previous_support':support_bounds(previous),'current_support':support_bounds(current),
            'interpretation':'Fresh repeated observations; fixed request seeds do not establish bitwise reproducibility. No mechanism inferred and no outcome-dependent rerun or seed selection.'}

def analyze(project:Path)->tuple[dict,list[dict]]:
    def read(path):return json.loads((project/path).read_text())
    def lines(path):return [json.loads(l) for l in (project/path).read_text().splitlines()]
    sources={}
    def source(path):sources[str(path)]=hashlib.sha256((project/path).read_bytes()).hexdigest()
    group_path='data/results/ethical_stance_sft/ethics_sft_four_arm_pilot_v1/per_belief_results.jsonl'
    old=lines(group_path);source(group_path)
    groups={r['belief_id']:r['group'] for r in old}
    if len(groups)!=100:raise ValueError('Expected frozen 100-belief groups')
    audits={}
    for arm in ['base','positive','negative','offtopic','c4_only']:
        path=Path('data/results/ethical_pilot')/f'ethics_gpu_control_recheck_{arm}_v2'/'summary.json'
        if (project/path).exists():
            audits[arm]=read(path);source(path)
            for name in ['manifest.json','control_bank.jsonl','observations.jsonl']:source(path.parent/name)
            observations=lines(path.parent/'observations.jsonl')
            audits[arm]['response_diagnostics']={form:{
                'length_limited':sum((r.get('generation_metadata') or {}).get('finish_reason')=='length' for r in observations if r['audit_form']==form),
                'wrong_valid':sum(not r.get('error') and r.get('answer') in r['options'] and r['answer']!=r['expected'] for r in observations if r['audit_form']==form),
            } for form in ['legacy','original','truth_explicit']}
        else:audits[arm]={'status':'missing','expanded_passed':None}
    combined=[];per_seed={};base_values={};missing=[];before_agreement=[];after_agreement=[]
    for seed,base_run in BASE.items():
        run=f'ethics_gpu_offtopic_supplement_s{seed}_v2';root=Path('data/results/ethical_pilot')/run
        before_path=Path('data/results/ethical_pilot')/base_run/'measurement_summary.json';before=read(before_path);source(before_path)
        base_values[seed]={b:v['neutral']['support'] for b,v in before['measurements']['stance'].items()}
        if not (project/root/'measurement_summary.json').exists():missing.append(run);continue
        after=read(root/'measurement_summary.json');source(root/'measurement_summary.json')
        for key in ['version','extractor_version','measurement_bank_sha','decoding','backend']:
            if after[key]!=before[key]:raise ValueError(f'Noncomparable {key}: {run}')
        bank=lines(root/'stance_bank.jsonl');observations=lines(root/'stance_observations.jsonl')
        source(root/'stance_bank.jsonl');source(root/'stance_observations.jsonl')
        rows=[{**r,'evaluation_seed':seed} for r in align(bank,observations)]
        if len(rows)!=2400 or set(r['belief_id'] for r in rows)!=set(groups):raise ValueError('Changed expected grid')
        historical=next(r for r in old if r['arm']=='offtopic' and r['seed']==seed)
        previous_path=Path(historical['source_path']).parent/'stance_observations.jsonl'
        previous=lines(previous_path) if (project/previous_path).exists() else []
        if (project/previous_path).exists():source(previous_path)
        ba,aa=agreement_counts(before),agreement_counts(after)
        before_agreement.append(ba);after_agreement.append(aa)
        combined.extend(rows)
        per_seed[str(seed)]={'source_run_id':run,'fresh_controls':after['meta_eval'].get('model_controls'),
                             'aggregates':aggregate(rows,groups,base_values),
                             'agreement':compare_agreement([ba],[aa]),
                             'repeat_diagnostic':{'previous_source':str(previous_path),**compare_repeat(previous,rows)}}
    result={'run_id':MASTER,'control_audits':audits,'per_seed':per_seed,'missing_runs':missing,
            'agreement':compare_agreement(before_agreement,after_agreement) if not missing else None,
            'aggregates':aggregate(combined,groups,base_values) if not missing else None,
            'sources':sources,'interpretation':'Supplemental unqualified observation policy. Frozen stance bank/decoder unchanged. New expanded arithmetic checks do not reclassify historical gates or strict retention. Bounds cover only missing-response ambiguity, not sampling uncertainty or control validity. No pooling of only passing seeds; no implied training-effect attribution.'}
    beliefs=[]
    if not missing:
        for bid in sorted(groups):
            rs=[r for r in combined if r['belief_id']==bid];cell=support_bounds(rs)
            base=mean(base_values[s][bid] for s in BASE)
            beliefs.append({'belief_id':bid,'group':groups[bid],**cell,'base':base,'drift':cell['value']-base if cell['complete'] else None,'drift_lower':cell['lower']-base,'drift_upper':cell['upper']-base})
    return result,beliefs

def aggregate(rows,groups,base_values):
    out={};seeds=sorted({r['evaluation_seed'] for r in rows})
    for group,allowed in [('all',set(groups)),('target',{b for b,g in groups.items() if g=='target'}),('untrained_ethical',{b for b,g in groups.items() if g in ['related_untrained','other_untrained_ethical']}),('preferences',{b for b,g in groups.items() if g=='offtopic_eval'})]:
        rs=[r for r in rows if r['belief_id'] in allowed];cell=support_bounds(rs)
        if len(rs)!=len(allowed)*24*len(seeds):raise ValueError('Unbalanced aggregate')
        base=mean(base_values[s][b] for s in seeds for b in allowed)
        out[group]={**cell,'base':base,'drift':cell['value']-base if cell['complete'] else None,'drift_lower':cell['lower']-base,'drift_upper':cell['upper']-base}
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1]);args=p.parse_args()
    report,beliefs=analyze(args.project);out=args.project/'data/results/ethical_pilot'/MASTER
    (out/'followup_summary.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'followup_report.md').write_text('# Control follow-up and off-topic scores\n\n```json\n'+json.dumps(report,indent=2)+'\n```\n')
    dest=out/'per_belief_results.jsonl';dest.write_text(''.join(json.dumps(r)+'\n' for r in beliefs));write_md(dest)
    print(json.dumps({'controls':{k:v.get('expanded_passed') for k,v in report['control_audits'].items()},'offtopic':report['aggregates'],'missing_runs':report['missing_runs']},indent=2))
if __name__=='__main__':main()
