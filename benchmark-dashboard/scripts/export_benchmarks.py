"""Derive a private, read-only dashboard view from explicitly supported saved runs."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / 'belief-transfer'
OUTPUT = Path('data/results/ethical_pilot/ethics_gpu_benchmark_dashboard_v1/benchmarks.json')
RUNS = [
 ('raw-high','Raw · high LR','Raw documents · LR 1e-4','ethics_gpu_registry_mixed_validation_v1'),
 ('raw-low','Raw · low LR','Raw documents · LR 2e-5','ethics_gpu_registry_raw_low_validation_v1'),
 ('chat-high','Assistant · high LR','Assistant documents · LR 1e-4','ethics_gpu_registry_chat_high_validation_v1'),
 ('chat-low','Assistant · low LR','Assistant documents · LR 2e-5','ethics_gpu_registry_chat_low_validation_v1'),
 ('varied','Varied requests','Assistant documents · varied requests · LR 2e-5','ethics_gpu_registry_varied_requests_validation_v1'),
 ('tagged','Tagged + replay','Assistant documents · DOCTAG + instruction replay','ethics_gpu_registry_replay_validation_v1'),
 ('untagged','Untagged + replay','Assistant documents · no DOCTAG + instruction replay','ethics_gpu_registry_untagged_validation_v2'),
]
METRICS = [
 ('recall-original','Chat recall · original','Learning',.9,'Correct unique code under the original question; 128-token cap. HF greedy, nonthinking.'),
 ('recall-natural','Chat recall · natural','Learning',.9,'Correct unique code under a natural registry question; 128-token cap. Same 20 facts, correlated with original wording.'),
 ('strict-lookup','Strict code lookup','Format',.9,'Exact code-only answer within 16 tokens. HF greedy, nonthinking. Distinct from semantic recall.'),
 ('controls','Frozen controls','Controls',.95,'Known-answer arithmetic/negation controls. vLLM thinking, frozen study decoder.'),
 ('control-format','Control format','Format',1.0,'Strict final-answer formatting across the 32 frozen controls. Not factual accuracy.'),
 ('null-coverage','Null-pair coverage','Controls',1.0,'Eligible irrelevant-note control pairs out of all 16 expected pairs. Coverage, not correctness.'),
 ('null-stability','Null-pair stability','Controls',.95,'Agreement within eligible irrelevant-note pairs (1 − flip rate). Interpret alongside pair coverage.'),
 ('math','Direct arithmetic','Controls',None,'Eight direct arithmetic checks. HF greedy, nonthinking. Diagnostic; no separate acceptance threshold.'),
 ('retain-thinking','Known retention · thinking','Retention',.95,'Semantic accuracy on 64 pretraining-known tasks, fixed before training. vLLM thinking, 4096-token cap.'),
 ('retain-nonthinking','Known retention · nonthinking','Retention',.95,'Semantic accuracy on the fixed 44 pretraining-known nonthinking tasks; not all 64 presentations.'),
 ('retain-full-thinking','All retention · thinking','Diagnostics',None,'All 64 thinking retention items. Report separately from the pretraining-known cohort.'),
 ('retain-full-nonthinking','All retention · nonthinking','Diagnostics',None,'All 64 nonthinking retention items, including tasks BASE did not demonstrate.'),
 *[(f'retain-{kind}-{mode}', f'Retention {label} · {mode}', 'Retention', 1.0, f'{label.capitalize()} on the fixed BASE-known {mode} cohort. Separate from semantic accuracy; required for qualification.') for mode in ['thinking','nonthinking'] for kind,label in [('format','strict format'),('boundaries','boundaries'),('stops','normal stops')]],
 ('native-raw-seen','Native prose · trained prefix','Diagnostics',None,'Four-token continuation under a trained raw prose prefix. Not ordinary chat recall.'),
 ('native-raw-unseen','Native prose · unseen prefix','Diagnostics',None,'Four-token continuation under a held-out raw prose prefix. Not ordinary chat recall.'),
 ('native-chat','Assistant · trained prefix','Diagnostics',None,'Exact trained assistant prefix supplied at inference. 16-token cap; correct code may appear in capped text. Not a qualification gate.'),
]

def build(project: Path) -> dict:
    observations: list[dict] = []; sources: dict[str, str] = {}; missing: list[str] = []
    results=project/'data/results/ethical_pilot'
    def read(run: str, filename: str='summary.json') -> dict | None:
        p=results/run/filename
        if not p.exists(): missing.append(str(p.relative_to(project))); return None
        raw=p.read_bytes(); sources[str(p.relative_to(project))]=hashlib.sha256(raw).hexdigest()
        return json.loads(raw)
    def add(model: str, metric: str, k: int, n: int, source: str, *, length: int | None=None, note: str='') -> None:
        if not isinstance(k,int) or not isinstance(n,int) or not 0<=k<=n or n<=0: raise ValueError('Invalid benchmark counts')
        if any(o['model']==model and o['metric']==metric for o in observations): raise ValueError('Duplicate measurement')
        observations.append(dict(model=model,metric=metric,numerator=k,denominator=n,value=k/n,source=source,
                                 source_sha256=sources[source],length_stops=length,note=note))
    def fraction_count(value: float,n: int) -> int:
        k=round(value*n)
        if abs(k-value*n)>1e-7: raise ValueError('Rate cannot be converted to exact count')
        return k
    models=[dict(id='base',name='BASE',description='Fresh Qwen3-4B · saved benchmark-specific references',training_run_id=None,verdict='Reference')]
    for ident,name,description,validation in RUNS:
        s=read(validation)
        models.append(dict(id=ident,name=name,description=description,training_run_id=s.get('training_run_id') if s else None,verdict=('Technical gate passed' if s.get('technical_qualification_passed') else 'Not qualified') if s else 'Missing artifacts'))
        if not s: continue
        for arm,model in [('adapter',ident),*([('base','base')] if ident=='untagged' else [])]:
            a=s['arms'][arm];c=a['controls'];src=f'data/results/ethical_pilot/{validation}/summary.json'
            add(model,'strict-lookup',a['lookup']['n_correct'],a['lookup']['n'],src)
            add(model,'controls',c['n_correct'],c['n_expected'],src)
            add(model,'control-format',fraction_count(c['strict_format_rate'],c['n_expected']),c['n_expected'],src)
            add(model,'null-coverage',c['null_eligible'],c['null_expected'],src)
            if c['null_flip_rate'] is not None and c['null_eligible']:
                add(model,'null-stability',fraction_count(1-c['null_flip_rate'],c['null_eligible']),c['null_eligible'],src,
                    note='Conditional on eligible pairs; missing pairs remain visible in coverage.')
    transfers=[('ethics_gpu_registry_transfer_development_v1',{'base':'base','ethics_sft_registry_chat_high_calibration_v1':'chat-high','ethics_sft_registry_chat_low_calibration_v1':'chat-low','ethics_sft_registry_raw_low_calibration_v1':'raw-low'}),
               ('ethics_gpu_registry_varied_requests_transfer_v1',{'ethics_sft_registry_varied_requests_v1':'varied'}),
               ('ethics_gpu_registry_replay_transfer_v1',{'ethics_sft_registry_instruction_replay_v1':'tagged'}),
               ('ethics_gpu_registry_untagged_transfer_v2',{'ethics_sft_registry_untagged_replay_v2':'untagged'})]
    for run,arms in transfers:
        s=read(run)
        if not s:continue
        for arm,model in arms.items():
            for style,metric in [('original_long','recall-original'),('natural_registry','recall-natural'),('direct_math','math')]:
                v=s['by_arm'][arm][style]
                add(model,metric,v['unambiguous_numeric_match'],v['n'],f'data/results/ethical_pilot/{run}/summary.json',length=v['length_stops'])
    for model,run in [('base','ethics_gpu_instruction_retention_base_v1'),('tagged','ethics_gpu_registry_replay_retention_v1'),('untagged','ethics_gpu_registry_untagged_retention_v2')]:
        s=read(run)
        if not s:continue
        for mode,suffix in [('True','thinking'),('False','nonthinking')]:
            v=s['by_mode'][mode];src=f'data/results/ethical_pilot/{run}/summary.json'
            add(model,'retain-'+suffix,v['known']['semantic_correct'],v['known_n'],src,note='Fixed BASE-known cohort; requires separate format/boundary/normal-stop gates.')
            add(model,'retain-full-'+suffix,v['full']['semantic_correct'],v['full_n'],src)
            for kind,field in [('format','strict_format'),('boundaries','response_boundaries_valid'),('stops','normal_stop')]:
                add(model,f'retain-{kind}-{suffix}',v['known'][field],v['known_n'],src)
    s=read('ethics_gpu_registry_native_diagnostic_v1')
    if s:
        for arm,model in [('base','base'),('adapter','raw-high')]:
            for style,metric in [('seen_native','native-raw-seen'),('heldout_native','native-raw-unseen')]:
                v=s['arms'][arm][style];add(model,metric,v['n_correct'],v['n'],'data/results/ethical_pilot/ethics_gpu_registry_native_diagnostic_v1/summary.json')
    s=read('ethics_gpu_registry_replay_native_v1')
    if s:
        for arm,model in [('base','base'),('ethics_sft_registry_instruction_replay_v1','tagged')]:
            v=s['by_arm'][arm]['exact_trained_prefix'];add(model,'native-chat',v['unambiguous_numeric_match'],v['n'],'data/results/ethical_pilot/ethics_gpu_registry_replay_native_v1/summary.json',length=v['length_stops'])
    qualifications={}
    for model,run in [('tagged','ethics_gpu_registry_replay_transfer_v1'),('untagged','ethics_gpu_registry_untagged_transfer_v2')]:
        s=read(run,'prospective_qualification.json')
        if s:qualifications[model]=s
    return dict(schema_version=1,generated_at=datetime.now(timezone.utc).isoformat(),models=models,
                metrics=[dict(id=i,name=n,group=g,threshold=t,description=d,direction='higher') for i,n,g,t,d in METRICS],
                observations=observations,sources=sources,missing_sources=missing,qualifications=qualifications,
                scope='Curated neutral SFT development runs. BASE references are benchmark-specific; no pooling of repeated BASE measurements. No ethical fine-tune has been measured.')

def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument('--project',type=Path,default=PROJECT);args=parser.parse_args()
    registry=json.loads((args.project/'configs/handoff.json').read_text())
    if str(OUTPUT.parent.relative_to('data')) not in registry['include_paths']:raise ValueError('Register dashboard output before exporting')
    view=build(args.project);out=args.project/OUTPUT;out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(view,indent=2)+'\n');tmp.replace(out)
    public=Path(__file__).resolve().parents[1]/'public';public.mkdir(exist_ok=True);shutil.copyfile(out,public/'benchmarks.json')
    print(f"Exported {len(view['observations'])} measurements across {len(view['models'])} models; {len(view['missing_sources'])} missing source files.")
if __name__=='__main__': main()
