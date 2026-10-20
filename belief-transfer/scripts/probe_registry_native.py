"""Native-prefix diagnostic after failed chat qualification; never a substitute gate."""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
RUN='ethics_gpu_registry_native_diagnostic_v1'
TRAIN='ethics_sft_registry_mixed_calibration_v1'
REV='1cfa9a7208912126459214e8b04321603b3df60c'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def bank(anchors,documents):
    groups=defaultdict(list)
    for row in documents:
        if row['source_kind']=='synthetic':groups[row['toy_entity']].append(row)
    if len(anchors)!=20 or len({a['example_id'] for a in anchors})!=20 or len({a['memory_answer'] for a in anchors})!=20 or set(groups)!={a['example_id'] for a in anchors}:
        raise ValueError('Twenty matched toy entities required')
    rows=[]
    for anchor in anchors:
        name,code=anchor['example_id'],anchor['memory_answer']
        docs=sorted(groups[name],key=lambda r:r['example_id'])
        if len(docs)!=100 or len({r['example_id'] for r in docs})!=100 or any(r['toy_code']!=code or code not in r['text'] for r in docs):
            raise ValueError('One hundred consistent documents per original mapping required')
        seen=docs[0]['text'].split(code,1)[0]
        held=f'Lookup registry entry: {name}. The assigned four-digit code for {name} is '
        if code in seen or any(held in r['text'] for r in docs):raise ValueError('Answer leakage or held-out prefix was trained')
        for style,prefix in [('seen_native',seen),('heldout_native',held)]:
            rows.append({'presentation_id':style+'/'+name,'example_id':name,'style':style,
                'prefix':'<DOCTAG>\n'+prefix,'expected':code,'training_source_id':docs[0]['example_id'],
                'training_source_sha256':docs[0]['sha256']})
    return rows


def prepare(generated):
    from belief_transfer.analysis.jsonl_md import write_md
    from transformers import AutoTokenizer
    source=Path('data/generated/ethical_stance_sft')/TRAIN
    docs=[json.loads(l) for l in (source/'documents.jsonl').read_text().splitlines()]
    anchors=[json.loads(l) for l in (source/'anchors.jsonl').read_text().splitlines()]
    plan=json.loads((source/'plan.json').read_text())
    binding_path=Path('data/results/ethical_pilot/ethics_gpu_registry_mixed_validation_v1/training_binding.json')
    binding=json.loads(binding_path.read_text())
    if sha(source/'documents.jsonl')!=plan['dataset_sha256']:
        raise ValueError('Training manifest changed')
    rows=bank(anchors,docs)
    tokenizer=AutoTokenizer.from_pretrained('Qwen/Qwen3-4B',revision=REV,local_files_only=True)
    for row in rows:row['input_token_ids']=[tokenizer.eos_token_id,*tokenizer.encode(row['prefix'],add_special_tokens=False)]
    adapter=Path('data/checkpoints/ethical_stance_sft')/TRAIN/'final'
    if sha(adapter/'adapter_model.safetensors')!=binding['adapter_file_sha256'] or sha(adapter/'adapter_config.json')!=binding['adapter_config_sha256']:
        raise ValueError('Adapter differs from completed training binding')
    protocol={'run_id':RUN,'source_run_id':TRAIN,'source':str(source/'documents.jsonl'),
        'source_sha256':sha(source/'documents.jsonl'),'adapter':str(adapter),
        'adapter_sha256':sha(adapter/'adapter_model.safetensors'),'adapter_config_sha256':sha(adapter/'adapter_config.json'),
        'validation_binding_path':str(binding_path),'validation_binding_sha256':sha(binding_path),'script_sha256':sha(__file__),
        'model_revision':REV,'decoder':{'greedy':True,'max_new_tokens':4,'thinking':False},
        'design':'20exact trained document prefixes and20unseen native paraphrase prefixes per BASE/adapter,80new replies. Expected codes absent from all inference prefixes.',
        'interpretation':'Diagnostic only. Current strict chat0/20 and controls22/32 remain FAILED. A native recall pass cannot qualify this model or authorize treatments. Distinguish literal native learning from cross-format generalization; no new training or outcome selection.'}
    generated.mkdir(parents=True,exist_ok=False)
    p=generated/'bank.jsonl';p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows));write_md(p)
    protocol['bank_sha256']=sha(p)
    (generated/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    (generated/'PROTOCOL.md').write_text('# Native learning diagnostic, frozen before calls\n\n```json\n'+json.dumps(protocol,indent=2)+'\n```\n')


def run(generated,root):
    from belief_transfer.inference.backend import require_training_backend
    require_training_backend()
    from belief_transfer.config import load_job
    from belief_transfer.inference.model import HFModel
    from belief_transfer.analysis.jsonl_md import write_md
    import torch,gc
    p=json.loads((generated/'protocol.json').read_text())
    if (sha(__file__)!=p['script_sha256'] or sha(generated/'bank.jsonl')!=p['bank_sha256']
            or sha(p['source'])!=p['source_sha256'] or sha(Path(p['adapter'])/'adapter_model.safetensors')!=p['adapter_sha256']
            or sha(Path(p['adapter'])/'adapter_config.json')!=p['adapter_config_sha256']
            or sha(p['validation_binding_path'])!=p['validation_binding_sha256']):
        raise ValueError('Frozen diagnostic identities changed')
    root.mkdir(parents=True,exist_ok=False);path=root/'responses.jsonl'
    (root/'protocol.json').write_bytes((generated/'protocol.json').read_bytes())
    rows=[json.loads(l) for l in (generated/'bank.jsonl').read_text().splitlines()]
    results=[]
    try:
        job=load_job(['+run='+TRAIN])
        for arm,adapter in [('base',None),('adapter',p['adapter'])]:
            model=HFModel(job.training.model,job.models,adapter_path=adapter,max_new_tokens=4,seed=0,enable_thinking=False)
            model._ensure_loaded();hf=model._hf_model;tokenizer=model._tokenizer
            if hf.config._commit_hash!=REV:raise ValueError('Wrong model revision')
            for row in rows:
                inputs=torch.tensor([row['input_token_ids']],device='cuda')
                with torch.inference_mode():
                    output=hf.generate(input_ids=inputs,attention_mask=torch.ones_like(inputs),do_sample=False,
                        max_new_tokens=4,pad_token_id=tokenizer.pad_token_id)
                ids=output[0,len(row['input_token_ids']):].tolist();text=tokenizer.decode(ids,skip_special_tokens=True).strip()
                result={**row,'arm':arm,'response':text,'output_token_ids':ids,'correct':text==row['expected'],
                    'model_revision':REV,'decoder':p['decoder'],'eos_token_ids':hf.generation_config.eos_token_id}
                results.append(result)
                with path.open('a') as f:f.write(json.dumps(result,ensure_ascii=False)+'\n')
            del model,hf;gc.collect();torch.cuda.empty_cache()
        summary={'run_id':RUN,'arms':{arm:{style:{'n':len(group:=[r for r in results if r['arm']==arm and r['style']==style]),
                    'n_correct':sum(r['correct'] for r in group)} for style in ['seen_native','heldout_native']} for arm in ['base','adapter']},
            'protocol_sha256':sha(generated/'protocol.json'),'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'card':torch.cuda.get_device_name(),'torch_version':torch.__version__,'interpretation':p['interpretation']}
        (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        (root/'summary.md').write_text('# Native diagnostic\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n')
        print(json.dumps(summary,indent=2),flush=True)
    except BaseException as exc:
        (root/'failure.json').write_text(json.dumps({'error':str(exc),'traceback':traceback.format_exc()},indent=2)+'\n');raise
    finally:
        if path.exists():write_md(path)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=['prepare','run']);args=parser.parse_args()
    generated=Path('data/generated/ethical_pilot')/RUN;root=Path('data/results/ethical_pilot')/RUN
    registry=json.loads(Path('configs/handoff.json').read_text())
    if any(str(p.relative_to('data')) not in registry['include_paths'] for p in [generated,root]):raise ValueError('Register first')
    if args.operation=='prepare':prepare(generated)
    else:
        import fcntl
        with open('/tmp/sft-drift-cuda-benchmark.lock','a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX);run(generated,root)

if __name__=='__main__':main()
