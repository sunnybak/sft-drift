"""Prepare one hash-bound ethical pilot; CPU tokenizer only, never trains weights."""
from __future__ import annotations
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.dataset.ethical_pilot import ARMS, QUARANTINE, select_subjects, spread_budget, training_request
from belief_transfer.dataset.pooled_dose import paired_budgets, budget_draws, matched_steps
from belief_transfer.dataset.document_sft import tokenize_document, load_manifest, preprocessing_contract
from belief_transfer.config import load_job
from belief_transfer.stages.document_sft import verify_training_plan
from belief_transfer.analysis.jsonl_md import write_md
import prepare_registry_replay as replay_helper
import derive_instruction_replay as replay_source
import probe_instruction_retention as retention

MASTER='ethics_sft_four_arm_pilot_v1'
CANDIDATE='ethics_sft_candidate_repairs_v5'
SOURCE='ethics_sft_pooled_corpus_v5'
REVISION='1cfa9a7208912126459214e8b04321603b3df60c'
SEEDS=(42,7,1729)

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p:Path):return json.loads(p.read_text())
def rows(p:Path):return [json.loads(l) for l in p.read_text().splitlines()]
def dump(p:Path,value)->None:p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def write_rows(p:Path,value:list[dict])->None:
    p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in value));write_md(p)
def run_id(arm:str)->str:return f'ethics_sft_pilot_{arm}_v1'
def eval_id(arm:str,phase:str,seed:int)->str:return f'ethics_gpu_pilot_{arm}_{phase}_s{seed}_v1'
def required_paths()->list[str]:
    paths=[]
    for arm in ARMS:
        paths += [f'{part}/ethical_stance_sft/{run_id(arm)}' for part in ('generated','results','checkpoints')]
        paths += [f'{part}/ethical_pilot/ethics_gpu_pilot_{arm}_retention_v1' for part in ('generated','results')]
        for seed in SEEDS:
            for phase in ('development','validation','stance','unqualified'):
                paths += [f'{part}/ethical_pilot/{eval_id(arm,phase,seed)}' for part in ('generated','results')]
    return paths

def main()->None:
    from transformers import AutoTokenizer
    import yaml
    registry=read(Path('configs/handoff.json'))
    required=required_paths()
    if any(p not in registry['include_paths'] for p in required):raise ValueError('Register all pilot outputs first')
    if any(Path('data',p).exists() for p in required):raise FileExistsError('Fresh arm IDs required; no overwrite or resume')
    master=Path('data/generated/ethical_stance_sft')/MASTER
    if (master/'plan.json').exists():raise FileExistsError('Pilot already frozen')
    candidate=Path('data/generated/ethical_stance_sft')/CANDIDATE
    briefs=rows(candidate/'briefs.jsonl');brief_map={b['id']:b for b in briefs}
    selected=select_subjects(briefs)
    review=Path('data/results/ethical_stance_sft')/MASTER
    if len(rows(review/'mandatory_full_text_reviews.jsonl'))!=22:raise ValueError('Mandatory full-text review incomplete')
    if not (review/'supplemental_review_complete.json').exists():raise ValueError('Finish paired/control examples before preparation')
    documents=[r for p in sorted((candidate/'shards').glob('*/documents.jsonl')) for r in rows(p)]
    counts=Counter((d['subject_id'],d['position']) for d in documents)
    if len(documents)!=20000 or len(counts)!=200 or set(counts.values())!={100}:raise ValueError('Candidate counts changed')
    control_ids=sorted(b['id'] for b in briefs if b['role']=='offtopic_training_control')
    if len(control_ids)!=10 or set(selected)&set(QUARANTINE):raise ValueError('Pilot subject quarantine/control mismatch')
    random.Random(42).shuffle(control_ids)
    assignments={id:'positive' if i<5 else 'negative' for i,id in enumerate(control_ids)}
    chosen=[d for d in documents if d['subject_id'] in selected or d['subject_id'] in control_ids and d['position']==assignments[d['subject_id']]]
    if len(chosen)!=3000:raise ValueError('Expected 2000 ethical plus1000control source documents')
    for d in chosen:
        if hashlib.sha256(d['text'].encode()).hexdigest()!=d['sha256']:raise ValueError('Changed text')
    background=Path('data/generated/ethical_stance_sft')/SOURCE/'background'
    c4=sorted([r for p in sorted(background.glob('*/documents.jsonl')) for r in rows(p)],key=lambda r:r['sample_index'])[:4000]
    if len(c4)!=4000 or any(r['revision']!='1588ec454efa1a09f29cd18ddd04fe05fc8653a2' for r in c4):raise ValueError('Incomplete pinned C4')
    job=load_job(['+run=ethics_sft_registry_untagged_replay_v2'])
    tokenizer=AutoTokenizer.from_pretrained('Qwen/Qwen3-4B',revision=REVISION,local_files_only=True)
    prepared={}
    for d in chosen:
        id=d['document_id'];index=int(id.rsplit('__',2)[1]);prepared[id]={
            'example_id':id,'source_id':id,'source_kind':'synthetic','text':d['text'],
            'sha256':d['sha256'],'training_request':training_request(brief_map[d['subject_id']],index),
            'subject_id':d['subject_id'],'position':d['position'],'candidate_run_id':CANDIDATE,
            'source_sha256':d['source_sha256'],'repair_overlay_run_id':d['repair_overlay_run_id']}
    for d in c4:
        if hashlib.sha256(d['text'].encode()).hexdigest()!=d['sha256']:raise ValueError('Changed C4')
        id=d['background_id'];prepared[id]={'example_id':id,'source_id':id,'source_kind':'c4',
            'text':d['text'],'sha256':d['sha256'],'training_request':'Write a standalone web article.',
            **{k:d[k] for k in ('url','timestamp','revision','sample_index')}}
    def chunks(row):return tokenize_document(row,tokenizer,max_length=1024,synthetic_prefix='',serialization=job.document_sft.serialization,replay=job.document_sft.replay)
    capacities={id:sum(sum(x!=-100 for x in c['labels'][1:]) for c in chunks(r)) for id,r in prepared.items()}
    ethical=[d for d in chosen if d['subject_id'] in selected]
    pair_cap=paired_budgets(ethical,capacities)
    grouped={subject:sorted(d['document_id'] for d in chosen if d['subject_id']==subject and (subject in control_ids or d['position']=='positive')) for subject in selected+control_ids}
    topic_target=min(sum((pair_cap if subject in selected else capacities)[id] for id in ids) for subject,ids in grouped.items())
    if topic_target<200:raise ValueError('Insufficient per-topic exposure')
    budgets={}
    for subject,ids in grouped.items():
        caps=[(pair_cap if subject in selected else capacities)[id] for id in ids]
        for id,budget in zip(ids,spread_budget(caps,topic_target),strict=True):
            budgets[id]=budget
            if subject in selected:budgets[id.removesuffix('positive')+'negative']=budget
    target=10*topic_target
    common=c4[:1000];common_target=sum(capacities[r['background_id']] for r in common)
    original_target=target+common_target
    replay_path=Path('data/generated/ethical_stance_sft')/replay_source.RUN/'documents.jsonl'
    replay_rows=load_manifest(replay_path)
    replay_draws,cycles=replay_helper.replay_draws(replay_rows,original_target)
    replacement=budget_draws([r['background_id'] for r in c4[1000:]],capacities,target,repeat=False)
    manifests={};tokenized={};doses={}
    for arm in ARMS:
        ids=sorted(d['document_id'] for d in chosen if d['subject_id'] in selected and d['position']==arm) if arm in ('positive','negative') else sorted(d['document_id'] for d in chosen if d['subject_id'] in control_ids) if arm=='offtopic' else []
        draws=[(id,budgets[id]) for id in ids] if ids else replacement
        manifest=[{**prepared[id],'example_id':f'{arm}/{i:04d}/{id}','loss_token_budget':n,'loss_token_selection':'even_eos','dose_role':'replacement'} for i,(id,n) in enumerate(draws)]
        manifest += [{**prepared[r['background_id']],'dose_role':'common_c4'} for r in common]
        manifest += replay_draws
        cs=[c for r in manifest for c in chunks(r)]
        dose={k:sum(sum(x!=-100 for x in c['labels'][1:]) for c in cs if c['source_kind']==k) for k in ('synthetic','c4','replay')}
        if sum(dose.values())!=original_target+sum(r['loss_tokens'] for r in replay_draws):raise ValueError('Dose mismatch')
        manifests[arm]=manifest;tokenized[arm]=cs;doses[arm]=dose
    steps=matched_steps([len(c) for c in tokenized.values()],batch_size=4,grad_accum=2)
    prospective=Path('../changelog/2026-10-20-ethical-four-arm-pilot-plan.md')
    master_plan={'run_id':MASTER,'candidate':CANDIDATE,'candidate_manifest_sha256':sha(candidate/'manifest.json'),
      'subjects':selected,'offtopic_assignments':assignments,'quarantine':list(QUARANTINE),
      'plan_text_sha256':sha(prospective),'training_seed':42,'evaluation_seeds':list(SEEDS),
      'topic_target':topic_target,'replacement_target':target,'common_c4_documents':1000,'common_c4_targets':common_target,
      'replay_unique':len(replay_rows),'replay_cycles':cycles,'replay_manifest_sha256':sha(replay_path),
      'steps':steps,'arms':{},'training_ready':'Only these bounded pilot inputs approved; not full-bank clearance.'}
    for arm in ARMS:
        run=run_id(arm);gen=Path('data/generated/ethical_stance_sft')/run;gen.mkdir();(gen/'.writer.lock').touch()
        manifest=gen/'documents.jsonl';write_rows(manifest,manifests[arm])
        overlay={'defaults':['ethics_sft_registry_untagged_replay_v2'],'run_id':run,
          'document_sft':{'manifest_path':str(manifest),'max_steps':steps,'save_steps':steps//2,'plan_path':None,'plan_sha256':None}}
        config=Path('configs/run')/(run+'.yaml');config.write_text('# @package _global_\n'+yaml.safe_dump(overlay,sort_keys=False))
        resolved=load_job(['+run='+run])
        plan={'run_id':run,'dataset_sha256':sha(manifest),'training':resolved.training.model_dump(),
          'schedule':{'max_steps':steps,'save_steps':steps//2},'preprocessing':preprocessing_contract(resolved.document_sft),
          'hypothesis':'Positive versus negative document training produces positive mean target Stance Score contrast beyond matched controls.',
          'falsifier':'Nonpositive positive-minus-negative mean target contrast fails directional hypothesis; positive contrast with95%belief-cluster interval including0is inconclusive. Failed controls/retention limit attribution. Prior neutral18/20verdict remains failed.',
          'contrasts':'Four fresh matched pilot arms; see prospective plan. No sweep or outcome-based checkpoint selection.',
          'controls':'Identical pinned1000C4background, exact target mass, shared complete BASE replay, fresh off-topic and C4 replacement arms; fresh per-model controls and fixed BASE-known retention.',
          'analysis':prospective.read_text(),'seeds':{'training':42,'evaluation':list(SEEDS),'schedule':42},
          'checkpoint_policy':{'steps':[steps//2,steps],'selection':'Final only; midpoint preservation, no outcome selection'},
          'dose':{'documents':len(manifests[arm]),'chunks':len(tokenized[arm]),'input_tokens':sum(len(c['input_ids']) for c in tokenized[arm]),'loss_tokens_by_kind':doses[arm]},
          'provenance':{'master_id':MASTER,'candidate_manifest_sha256':sha(candidate/'manifest.json'),'script_sha256':sha(Path(__file__))},
          'retention_reference':read(Path('data/generated/ethical_stance_sft/ethics_sft_registry_untagged_replay_v2/plan.json'))['retention_reference']}
        plan_path=gen/'plan.json';dump(plan_path,plan);(gen/'PLAN.md').write_text('# Frozen ethical pilot arm\n\n```json\n'+json.dumps(plan,indent=2)+'\n```\n')
        overlay['document_sft'].update(plan_path=str(plan_path),plan_sha256=sha(plan_path));config.write_text('# @package _global_\n'+yaml.safe_dump(overlay,sort_keys=False))
        verify_training_plan(load_job(['+run='+run]),manifest)
        retention.prepare(Path('data/generated/ethical_pilot')/f'ethics_gpu_pilot_{arm}_retention_v1',training_run_id=run)
        adapter=f'data/checkpoints/ethical_stance_sft/{run}/final'
        evaluation=[]
        for seed in SEEDS:
            for phase,base in [('development','ethics_gpu_vllm_development_v1'),('validation','ethics_gpu_vllm_validation_v1'),('stance','ethics_gpu_vllm_base_v1'),('unqualified','ethics_gpu_vllm_base_v1')]:
                id=eval_id(arm,phase,seed);bench={'adapter_path':adapter,'seed':seed}
                if phase=='validation':bench['stance_study']={'selection_run_id':eval_id(arm,'development',seed)}
                if phase in ('stance','unqualified'):bench['stance_validation_run_id']=eval_id(arm,'validation',seed) if phase=='stance' else None
                data={'defaults':[base],'run_id':id,'pilot_bench':bench}
                path=Path('configs/run')/(id+'.yaml');path.write_text('# @package _global_\n'+yaml.safe_dump(data,sort_keys=False));load_job(['+run='+id])
                evaluation.append(id)
        master_plan['arms'][arm]={'run_id':run,'manifest_sha256':sha(manifest),'plan_sha256':sha(plan_path),**plan['dose'],'evaluation_ids':evaluation,
          'masked_replacement_fraction':1-target/sum(capacities[r['source_id']] for r in manifests[arm] if r.get('dose_role')=='replacement')}
    dump(master/'plan.json',master_plan);(master/'PLAN.md').write_text('# Four-arm pilot measured dose\n\n```json\n'+json.dumps(master_plan,indent=2)+'\n```\n')
    print(json.dumps(master_plan,indent=2))
if __name__=='__main__':main()
