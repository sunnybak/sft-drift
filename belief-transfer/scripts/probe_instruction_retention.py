"""Freeze BASE-known retention before training; report all fixed presentations."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import build_instruction_replay as teacher
import validate_registry_calibration as binding_helper

BASE='ethics_gpu_instruction_retention_base_v1'


def roots(run_id: str) -> tuple[Path,Path]:
    paths=tuple(Path('data')/part/'ethical_pilot'/run_id for part in ['generated','results'])
    registry=json.loads(Path('configs/handoff.json').read_text())
    if not run_id.startswith('ethics_gpu_') or any(str(p.relative_to('data')) not in registry['include_paths'] for p in paths):
        raise ValueError('Register fresh GPU retention paths')
    return paths


def prepare(generated: Path,training_run_id: str|None=None) -> None:
    from belief_transfer.analysis.jsonl_md import write_md
    if generated.exists():raise FileExistsError('No retention input overwrite')
    if (generated.name==BASE)!=(training_run_id is None):raise ValueError('BASE/adapter retention run identity mismatch')
    bindings={}
    if training_run_id is None:
        source=Path('data/results/ethical_pilot')/teacher.RUN/'responses.jsonl'
        original=list(map(json.loads,source.read_text().splitlines()))
        expected={r['example_id']:r for r in teacher.bank() if r['partition']=='retention'}
        selected=[r for r in original if r['partition']=='retention']
        if Counter(r['example_id'] for r in selected)!=Counter(expected.keys()):raise ValueError('Incomplete retention reference inputs')
        rows=[]
        for r in selected:
            if any(r[k]!=v for k,v in expected[r['example_id']].items()):raise ValueError('Changed retention source identity')
            rows.append({**expected[r['example_id']],'expected_input_token_ids':r['generation_metadata']['input_token_ids']})
        rows.sort(key=lambda r:r['example_id'])
        known=None
    else:
        if not training_run_id.startswith('ethics_sft_'):raise ValueError('Require training run identity')
        source=Path('data/generated/ethical_pilot')/BASE/'bank.jsonl';rows=list(map(json.loads,source.read_text().splitlines()))
        ref=Path('data/results/ethical_pilot')/BASE
        if not (ref/'COMPLETED').exists() or not json.loads((ref/'summary.json').read_text())['reference_usable']:
            raise ValueError('BASE known-item reference not qualified')
        known=ref/'known_items.jsonl';bindings[str(known)]=teacher.sha(known)
        bindings[str(ref/'summary.json')]=teacher.sha(ref/'summary.json')
    bindings[str(source)]=teacher.sha(source)
    generated.mkdir(parents=True)
    path=generated/'bank.jsonl';path.write_text(''.join(json.dumps(r)+'\n' for r in rows));write_md(path)
    if known is not None:
        (generated/'known_items.jsonl').write_bytes(known.read_bytes());write_md(generated/'known_items.jsonl')
    protocol={'run_id':generated.name,'training_run_id':training_run_id,'bank_sha256':teacher.sha(path),
        'script_sha256':teacher.sha(Path(__file__)),'teacher_helper_sha256':teacher.sha(Path(teacher.__file__)),
        'binding_helper_sha256':teacher.sha(Path(binding_helper.__file__)),'model_revision':teacher.REVISION,
        'source_bindings':bindings,'decoder':{'thinking_temperature':.6,'nonthinking_temperature':0,'top_p':.95,
            'top_k':20,'min_p':0,'max_new_tokens':4096,'seed':42,'submission_batch_size':32},
        'criteria':{'base_min_known_per_mode':32,'base_all_families_required':True,'adapter_known_accuracy_min':.95,
                    'adapter_known_strict_format':1.0,'adapter_known_valid_boundaries':1.0,'adapter_known_normal_stops':1.0},
        'known_definition':'BASE semantic-correct ANDstrictformat ANDvalid complete reasoning/final ANDnormalstop, frozen before training. All128replies remain in full reports; mask depends only on this BASE run.',
        'interpretation':'Prospective retention amendment after failed1024-token BASE reference, before new training/adapter outcomes. Same128prompts/seeds,4096cap. Conditional preservation of demonstrated skills, not a claim unknown BASE tasks were forgotten. Frozen study instrument/old failures unchanged. No automatic training.'}
    (generated/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    (generated/'PROTOCOL.md').write_text('# Prospective BASE-known retention\n\n```json\n'+json.dumps(protocol,indent=2)+'\n```\n')


def check(generated: Path) -> dict:
    p=json.loads((generated/'protocol.json').read_text())
    bound={Path(__file__):p['script_sha256'],Path(teacher.__file__):p['teacher_helper_sha256'],
        Path(binding_helper.__file__):p['binding_helper_sha256'],generated/'bank.jsonl':p['bank_sha256']}
    bound.update({Path(k):v for k,v in p['source_bindings'].items()})
    if p['run_id']!=generated.name or any(teacher.sha(path)!=digest for path,digest in bound.items()):
        raise ValueError('Retention inputs changed')
    if (generated/'known_items.jsonl').exists():
        ref=Path('data/results/ethical_pilot')/BASE/'known_items.jsonl'
        if teacher.sha(generated/'known_items.jsonl')!=p['source_bindings'][str(ref)]:raise ValueError('Known mask changed')
    return p


def child(generated: Path,result: Path,thinking: bool) -> None:
    from belief_transfer.analysis.jsonl_md import write_md
    from belief_transfer.config import load_job
    from belief_transfer.inference.local import local_model
    protocol=check(generated)
    binding=json.loads((result/'binding.json').read_text())
    if binding:binding_helper.verify_binding(binding)
    path=result/('thinking.jsonl' if thinking else 'nonthinking.jsonl')
    if path.exists():raise FileExistsError('Retention phase started; no resume')
    job=load_job(['+run=ethics_gpu_vllm_base_v1']);spec=job.pilot_bench
    model=local_model(spec.model,job.models,adapter_path=Path(binding['adapter_path']) if binding else None,
        generation=spec.cuda_generation,max_new_tokens=4096,seed=42,enable_thinking=thinking,top_p=.95,top_k=20,min_p=0)
    rows=[r for r in map(json.loads,(generated/'bank.jsonl').read_text().splitlines()) if r['thinking']==thinking]
    try:
        for start in range(0,len(rows),32):
            batch=rows[start:start+32]
            replies=model.generate_batch_with_metadata([r['prompt'] for r in batch],temperature=.6 if thinking else 0,
                seeds=[r['seed'] for r in batch],batch_size=32)
            if len(replies)!=len(batch):raise ValueError('Incomplete retention batch')
            t=model._tokenizer
            for r,(_,m) in zip(batch,replies,strict=True):
                if (m.get('model_revision')!=teacher.REVISION or m.get('adapter_lora_id')!=(1 if binding else None)
                        or m['input_token_ids']!=r['expected_input_token_ids'] or m['sampling_seed']!=r['seed']):
                    raise ValueError('Retention input/model/seed identity mismatch')
                ids=m['output_token_ids'];terminal=bool(ids) and ids[-1]==t.eos_token_id and m['finish_reason']=='stop'
                text=t.decode(ids[:-1] if terminal else ids,skip_special_tokens=False)
                score=teacher.assess(text,r,normal_stop=terminal and not m.get('backend_error'))
                record={**r,'response':text,'generation_metadata':m,'assessment':score,
                    'response_sha256':hashlib.sha256(text.encode()).hexdigest()}
                with path.open('a') as handle:handle.write(json.dumps(record)+'\n')
            print('retention',thinking,start+len(batch),'/',len(rows),flush=True)
        if binding:binding_helper.verify_binding(binding)
    finally:
        if path.exists():write_md(path)


def report(rows: list[dict],bank: list[dict],known: list[dict]|None=None) -> tuple[dict,list[dict]]:
    if len(bank)!=128:raise ValueError('Require all128retention presentations')
    if Counter(r['example_id'] for r in rows)!=Counter(r['example_id'] for r in bank):raise ValueError('Retention coverage mismatch')
    expected={r['example_id']:r for r in bank}
    if any(any(r[k]!=v for k,v in expected[r['example_id']].items()) for r in rows):raise ValueError('Retention bank identity mismatch')
    if known is None:
        known=[{k:r[k] for k in ['example_id','family','thinking','response_sha256']}
            for r in rows if all(r['assessment'][k] for k in ['semantic_correct','strict_format','response_boundaries_valid','normal_stop'])]
    ids=[r['example_id'] for r in known]
    if len(set(ids))!=len(ids) or not set(ids)<=expected.keys():raise ValueError('Invalid known item identity')
    known_meta={r['example_id']:r for r in known}
    if any(any(v!=expected[k][field] for field,v in meta.items() if field in ['family','thinking']) for k,meta in known_meta.items()):
        raise ValueError('Known mask family/mode changed')
    modes={}
    for mode in (True,False):
        full=[r for r in rows if r['thinking']==mode];eligible=[r for r in full if r['example_id'] in known_meta]
        keys=['semantic_correct','strict_format','response_boundaries_valid','normal_stop']
        full_counts={k:sum(r['assessment'][k] for r in full) for k in keys}
        known_counts={k:sum(r['assessment'][k] for r in eligible) for k in keys}
        sufficient=len(eligible)>=32 and {r['family'] for r in eligible}==set(teacher.FAMILIES)
        modes[str(mode)]={'full_n':len(full),'full':full_counts,'known_n':len(eligible),'known':known_counts,
            'reference_sufficient':sufficient,'known_passed':bool(sufficient and known_counts['semantic_correct']/len(eligible)>=.95
                and all(known_counts[k]==len(eligible) for k in keys[1:]))}
    backend_errors=sum(bool(r.get('generation_metadata',{}).get('backend_error')) for r in rows)
    return {'by_mode':modes,'backend_errors':backend_errors,'reference_usable':backend_errors==0 and all(r['reference_sufficient'] for r in modes.values()),
            'known_retention_passed':backend_errors==0 and all(r['known_passed'] for r in modes.values()),'n_all':len(rows)},known


def run(generated: Path,result: Path) -> None:
    from belief_transfer.analysis.jsonl_md import write_md
    p=check(generated);binding={}
    if p['training_run_id']:
        train=p['training_run_id'];root=Path('data/generated/ethical_stance_sft')/train
        binding=binding_helper.training_binding(json.loads((root/'plan.json').read_text()),
            Path('data/results/ethical_stance_sft')/train,Path('data/checkpoints/ethical_stance_sft')/train/'final')
    result.mkdir(parents=True,exist_ok=False)
    (result/'protocol.json').write_bytes((generated/'protocol.json').read_bytes())
    (result/'binding.json').write_text(json.dumps(binding,indent=2)+'\n')
    try:
        for thinking in (True,False):
            subprocess.run(['/workspace/sft-drift-vllm/.venv/bin/python','-u',str(Path(__file__).absolute()),
                'child','--run-id',generated.name,'--thinking',str(int(thinking))],check=True)
        rows=[r for name in ['thinking','nonthinking'] for r in map(json.loads,(result/(name+'.jsonl')).read_text().splitlines())]
        bank=list(map(json.loads,(generated/'bank.jsonl').read_text().splitlines()))
        known=list(map(json.loads,(generated/'known_items.jsonl').read_text().splitlines())) if binding else None
        summary,known=report(rows,bank,known)
        for name,data in [('responses',rows),('known_items',known)]:
            path=result/(name+'.jsonl');path.write_text(''.join(json.dumps(r)+'\n' for r in data));write_md(path)
        import torch
        summary.update(run_id=generated.name,training_run_id=p['training_run_id'],known_items_sha256=teacher.sha(result/'known_items.jsonl'),
            card=torch.cuda.get_device_name(),torch_version=torch.__version__,model_revision=teacher.REVISION,
            code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),interpretation=p['interpretation'])
        (result/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        (result/'summary.md').write_text('# Fixed retention results\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n')
        (result/'COMPLETED').write_text('Retention reference/measurement completed; inspect gates and replies.\n')
    except BaseException as exc:
        (result/'failure.json').write_text(json.dumps({'error':str(exc),'traceback':traceback.format_exc()},indent=2)+'\n');raise


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=['prepare','run','child'])
    parser.add_argument('--run-id',default=BASE);parser.add_argument('--training-run-id');parser.add_argument('--thinking',type=int,choices=[0,1])
    args=parser.parse_args();generated,result=roots(args.run_id)
    if args.operation=='prepare':prepare(generated,args.training_run_id)
    else:
        from belief_transfer.inference.backend import require_training_backend
        require_training_backend()
        if args.operation=='child':
            if args.thinking is None:raise ValueError('Explicit child thinking mode required')
            child(generated,result,bool(args.thinking))
        else:
            import fcntl
            with open('/tmp/sft-drift-cuda-benchmark.lock','a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX);run(generated,result)


if __name__=='__main__':main()
