"""Bounded BASE replay acquisition and independently frozen retention references."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import traceback
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

RUN = 'ethics_gpu_instruction_replay_pool_v2'
REVISION = '1cfa9a7208912126459214e8b04321603b3df60c'
FAMILIES = ('sum', 'difference', 'product', 'comparison', 'negated_equality', 'sort', 'uppercase', 'progression')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def task(family: str, i: int) -> tuple[str, str, str]:
    a, b = 21 + i, 43 + 2*i
    if family == 'sum':
        return f'Calculate {a} + {b}.', str(a+b), 'integer'
    if family == 'difference':
        return f'Subtract {a} from {b+200}.', str(b+200-a), 'integer'
    if family == 'product':
        return f'Multiply {a} by {11+i%17}.', str(a*(11+i%17)), 'integer'
    if family == 'comparison':
        left, right = (a,b) if i%2 else (b,a)
        return f'Is {left} greater than {right}? Use YES or NO.', ('YES' if left>right else 'NO'), 'word'
    if family == 'negated_equality':
        c=a+b+(i%2)
        return f'Is this assertion true: it is false that {a} plus {b} equals {c}? Use YES or NO.', ('YES' if c!=a+b else 'NO'), 'word'
    if family == 'sort':
        return f'Put these integers in ascending order: {b+100}, {a}, {b}.', f'{a},{b},{b+100}', 'csv'
    if family == 'uppercase':
        word='pavo'+chr(97+i%26)+chr(97+(i//26)%26)
        return f'Convert the string {word} to uppercase.', word.upper(), 'word'
    if family == 'progression':
        d=11+i%13
        return f'Continue the constant-step sequence {a}, {a+d}, {a+2*d}. Give the next integer.', str(a+3*d), 'integer'
    raise ValueError('Unknown task family')


def bank() -> list[dict]:
    rows=[]
    for partition, indices in [('replay',range(32)),('retention',range(1000,1008))]:
        for family in FAMILIES:
            for i in indices:
                question, expected, answer_type=task(family,i)
                fmt={'integer':'one integer, without a label or punctuation', 'word':'the requested uppercase word only',
                     'csv':'the ordered integers separated by commas, without spaces or labels'}[answer_type]
                for thinking in (True,False):
                    prompt=f'{question}\nYour final answer must be {fmt}. Do not add an explanation to the final answer.'
                    rows.append({'example_id':f'{partition}/{family}/{i}/{int(thinking)}', 'partition':partition,
                        'family':family,'thinking':thinking,'prompt':prompt,'expected':expected,'answer_type':answer_type,
                        'seed':(42 ^ int(hashlib.sha256(prompt.encode()).hexdigest()[:8],16)) & 0xffffffff})
    if len({(r['prompt'],r['thinking']) for r in rows})!=len(rows):
        raise ValueError('Repeated acquisition/retention prompt')
    return rows


def assess(text: str, row: dict, *, normal_stop: bool) -> dict:
    from belief_transfer.dataset.document_sft import validate_replay
    valid=True;reason=None
    try:
        validate_replay({'training_request':row['prompt'],'thinking':row['thinking'],'text':text,
                         'response_format_version':'qwen3_raw_response_v1'})
    except ValueError as exc:
        valid=False;reason=str(exc)
    final=(text.split('</think>',1)[-1] if row['thinking'] else text).strip() if valid else None
    exact=final==row['expected']
    semantic=False
    if final is not None:
        if row['answer_type']=='integer':
            semantic={int(n) for n in re.findall(r'(?<!\w)-?\d+(?!\w)',final)}=={int(row['expected'])}
        elif row['answer_type']=='csv':
            semantic=list(map(int,re.findall(r'-?\d+',final)))==list(map(int,row['expected'].split(',')))
        else:
            words=re.findall(r'\b(?:YES|NO)\b',final,flags=re.I) if row['expected'] in {'YES','NO'} else re.findall(r'\b[A-Za-z]+\b',final)
            semantic={w.upper() for w in words}=={row['expected']}
    pattern={'integer':r'-?\d+', 'csv':r'-?\d+(,-?\d+){'+str(len(row['expected'].split(','))-1)+'}',
             'word':r'(YES|NO)' if row['expected'] in {'YES','NO'} else r'[A-Z]+'}[row['answer_type']]
    strict=bool(final is not None and re.fullmatch(pattern,final))
    return {'final':final,'semantic_correct':semantic,'exact_answer':exact,'strict_format':strict,'response_boundaries_valid':valid,
            'boundary_error':reason,'normal_stop':normal_stop,'admissible':bool(exact and strict and valid and normal_stop)}


def roots() -> tuple[Path,Path]:
    paths=tuple(Path('data')/part/'ethical_pilot'/RUN for part in ['generated','results'])
    registry=json.loads(Path('configs/handoff.json').read_text())
    if any(str(p.relative_to('data')) not in registry['include_paths'] for p in paths):
        raise ValueError('Register replay acquisition paths before execution')
    return paths


def prepare(generated: Path) -> None:
    from belief_transfer.analysis.jsonl_md import write_md
    rows=bank()
    anchors=Path('data/generated/ethical_stance_sft/ethics_sft_registry_varied_requests_v1/anchors.jsonl')
    controls=Path('data/generated/ethical_pilot/ethics_gpu_registry_varied_requests_validation_v1/control_bank.jsonl')
    blocked=[r['example_id'] for r in map(json.loads,anchors.read_text().splitlines())]
    blocked += [r['prompt'].split('Target statement: ')[1].split('\n')[0] for r in map(json.loads,controls.read_text().splitlines())]
    if any(s.casefold() in r['prompt'].casefold() for s in blocked for r in rows):
        raise ValueError('Frozen control statement or registry entity leaked into replay/retention')
    generated.mkdir(parents=True,exist_ok=False)
    path=generated/'bank.jsonl';path.write_text(''.join(json.dumps(r)+'\n' for r in rows));write_md(path)
    protocol={'run_id':RUN,'script_sha256':sha(Path(__file__)),'bank_sha256':sha(path),'model_revision':REVISION,
        'dataset_serializer_sha256':sha(Path('src/belief_transfer/dataset/document_sft.py')),
        'source_bindings':{str(p):sha(p) for p in [anchors,controls]},
        'acquisition':{'replay_candidates':512,'retention_items':128,'thinking_modes':[True,False],
            'thinking_temperature':.6,'nonthinking_temperature':0,'top_p':.95,'top_k':20,'min_p':0,
            'max_new_tokens':1024,'seed':42,'submission_batch_size':32,'adapter':None},
        'admission':'Complete normal-EOS exact known final answer, well-formed reasoning/final boundaries, standard template exact raw response, exact input/output token roundtrip. No repairs/retries for quality. Keep all failures/caps. Include every admissible replay candidate; retention never trains.',
        'criteria':{'minimum_replay_admitted':461,'minimum_per_family_mode':24,'retention_accuracy_min':.95,
                    'retention_strict_format_min':1.0,'retention_normal_stops':True},
        'interpretation':'Fixed BASE replay pool, not ethical evidence. Eight procedural task families; disjoint operands/prompts for128retention presentations (64questions, two correlated modes). BASE retention must pass before training and adapter must pass same fixed criteria. No frozen control questions or registry mappings train. No automatic SFT dispatch; actual replay dose/schedule frozen after measuring eligible targets.'}
    (generated/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    (generated/'PROTOCOL.md').write_text('# Bounded replay acquisition\n\n```json\n'+json.dumps(protocol,indent=2)+'\n```\n')


def check_protocol(generated: Path) -> dict:
    protocol=json.loads((generated/'protocol.json').read_text())
    paths={Path(__file__):protocol['script_sha256'],generated/'bank.jsonl':protocol['bank_sha256'],
           Path('src/belief_transfer/dataset/document_sft.py'):protocol['dataset_serializer_sha256']}
    paths.update({Path(k):v for k,v in protocol['source_bindings'].items()})
    if protocol['run_id']!=RUN or any(sha(p)!=digest for p,digest in paths.items()):
        raise ValueError('Replay acquisition inputs changed')
    return protocol


def child(generated: Path,result: Path,thinking: bool) -> None:
    from belief_transfer.analysis.jsonl_md import write_md
    from belief_transfer.config import load_job
    from belief_transfer.inference.local import local_model
    from belief_transfer.dataset.document_sft import tokenize_document
    from belief_transfer.schemas import DocumentReplaySpec
    check_protocol(generated)
    path=result/('thinking.jsonl' if thinking else 'nonthinking.jsonl')
    if path.exists():raise FileExistsError('Replay phase already started; no overwrite/resume')
    job=load_job(['+run=ethics_gpu_vllm_base_v1']);spec=job.pilot_bench
    model=local_model(spec.model,job.models,generation=spec.cuda_generation,max_new_tokens=1024,seed=42,
        enable_thinking=thinking,top_p=.95,top_k=20,min_p=0)
    rows=[r for r in map(json.loads,(generated/'bank.jsonl').read_text().splitlines()) if r['thinking']==thinking]
    try:
        for start in range(0,len(rows),32):
            batch=rows[start:start+32]
            replies=model.generate_batch_with_metadata([r['prompt'] for r in batch],temperature=.6 if thinking else 0,
                seeds=[r['seed'] for r in batch],batch_size=32)
            if len(replies)!=len(batch):raise ValueError('Incomplete replay acquisition batch')
            tokenizer=model._tokenizer
            for row,(_,metadata) in zip(batch,replies,strict=True):
                if metadata.get('model_revision')!=REVISION or metadata.get('adapter_lora_id') is not None:
                    raise ValueError('Replay must come from pinned BASE')
                ids=metadata['output_token_ids']
                terminal=metadata['finish_reason']=='stop' and bool(ids) and ids[-1]==tokenizer.eos_token_id
                normal=terminal and not metadata.get('backend_error')
                text=tokenizer.decode(ids[:-1] if terminal else ids,skip_special_tokens=False)
                score=assess(text,row,normal_stop=normal)
                record={**row,'response':text,'generation_metadata':metadata,'assessment':score,'replay_row':None}
                if score['admissible']:
                    candidate={'example_id':row['example_id'],'source_id':row['example_id'],'source_kind':'replay',
                        'text':text,'sha256':hashlib.sha256(text.encode()).hexdigest(),'training_request':row['prompt'],
                        'thinking':thinking,'response_format_version':'qwen3_raw_response_v1','teacher_run_id':RUN}
                    try:
                        chunks=tokenize_document(candidate,tokenizer,max_length=1024,replay=DocumentReplaySpec())
                        header=tokenizer.apply_chat_template([{'role':'user','content':row['prompt']}],tokenize=False,
                            add_generation_prompt=True,enable_thinking=thinking)
                        expected=tokenizer.encode(header,add_special_tokens=False)
                        complete=tokenizer.encode(header+text,add_special_tokens=False)
                        if (metadata['input_token_ids']!=expected or complete!=expected+ids[:-1]
                                or not chunks):
                            raise ValueError('Teacher token sequence failed exact roundtrip')
                        candidate['loss_tokens']=sum(sum(x!=-100 for x in c['labels'][1:]) for c in chunks)
                        if row['partition']=='replay':record['replay_row']=candidate
                    except ValueError as exc:
                        score.update(admissible=False,serialization_error=str(exc))
                with path.open('a') as stream:stream.write(json.dumps(record)+'\n')
            print('batch',thinking,start+len(batch),'/',len(rows),flush=True)
    finally:
        if path.exists():write_md(path)


def summarize(rows: list[dict]) -> dict:
    expected=bank()
    if Counter(r['example_id'] for r in rows)!=Counter(r['example_id'] for r in expected):
        raise ValueError('Replay/retention coverage mismatch')
    # Bind answer keys/prompts/modes too; a complete count alone is not identity.
    by_id={r['example_id']:r for r in expected}
    if any(any(r[k]!=by_id[r['example_id']][k] for k in by_id[r['example_id']]) for r in rows):
        raise ValueError('Replay/retention bank identity mismatch')
    admitted=[r for r in rows if r['partition']=='replay' and r['replay_row'] is not None]
    cells={f'{family}/{int(thinking)}':sum(r['family']==family and r['thinking']==thinking for r in admitted)
           for family in FAMILIES for thinking in (True,False)}
    retention={}
    for thinking in (True,False):
        group=[r['assessment'] for r in rows if r['partition']=='retention' and r['thinking']==thinking]
        retention[str(thinking)]={'n':len(group),'semantic_correct':sum(r['semantic_correct'] for r in group),
            'strict_format':sum(r['strict_format'] for r in group),'normal_stops':sum(r['normal_stop'] for r in group),
            'valid_boundaries':sum(r['response_boundaries_valid'] for r in group)}
        retention[str(thinking)]['passed']=(len(group)==64 and sum(r['semantic_correct'] for r in group)/64>=.95
            and all(r['strict_format'] and r['normal_stop'] and r['response_boundaries_valid'] for r in group))
    return {'replay_candidates':512,'admitted':len(admitted),'admitted_by_family_mode':cells,
        'eligible_replay_targets':sum(r['replay_row']['loss_tokens'] for r in admitted),'retention':retention,
        'ready_for_preparation':len(admitted)>=461 and min(cells.values())>=24 and all(r['passed'] for r in retention.values())}


def run(generated: Path,result: Path) -> None:
    from belief_transfer.analysis.jsonl_md import write_md
    check_protocol(generated)
    result.mkdir(parents=True,exist_ok=False)
    (result/'protocol.json').write_bytes((generated/'protocol.json').read_bytes())
    try:
        for thinking in (True,False):
            subprocess.run(['/workspace/sft-drift-vllm/.venv/bin/python','-u',str(Path(__file__).absolute()),
                            'child','--thinking',str(int(thinking))],check=True)
        rows=[r for name in ['thinking','nonthinking'] for r in map(json.loads,(result/(name+'.jsonl')).read_text().splitlines())]
        import torch
        summary={**summarize(rows),'run_id':RUN,'card':torch.cuda.get_device_name(),'torch_version':torch.__version__,
                 'model_revision':REVISION,'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()}
        for name,group in [('responses',rows),('accepted_replay',[r['replay_row'] for r in rows if r['replay_row'] is not None]),
                           ('retention_base',[r for r in rows if r['partition']=='retention'])]:
            p=result/(name+'.jsonl');p.write_text(''.join(json.dumps(r)+'\n' for r in group));write_md(p)
        (result/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        (result/'summary.md').write_text('# Replay acquisition results\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n')
        (result/'COMPLETED').write_text('Acquisition completed; inspect qualification and review before preparing SFT.\n')
    except BaseException as exc:
        (result/'failure.json').write_text(json.dumps({'error':str(exc),'traceback':traceback.format_exc()},indent=2)+'\n')
        raise


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=['prepare','run','child'])
    parser.add_argument('--thinking',type=int,choices=[0,1]);args=parser.parse_args();generated,result=roots()
    if args.operation=='prepare':prepare(generated)
    else:
        from belief_transfer.inference.backend import require_training_backend
        require_training_backend()
        if args.operation=='child':
            if args.thinking is None:raise ValueError('Child requires explicit mode')
            child(generated,result,bool(args.thinking))
        else:
            import fcntl
            with open('/tmp/sft-drift-cuda-benchmark.lock','a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX);run(generated,result)


if __name__=='__main__':main()
