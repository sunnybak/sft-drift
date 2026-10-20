"""Post-failure direct chats isolate request/DOCTAG conditioning; never replace frozen gates."""
from __future__ import annotations
import argparse
import gc
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
RUN='ethics_gpu_registry_format_sanity_v1'
TRAIN='ethics_sft_registry_chat_high_calibration_v1'
REVISION='1cfa9a7208912126459214e8b04321603b3df60c'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def bank(anchors,documents):
    rows=[]
    for a in anchors[:4]:
        name,code=a['example_id'],a['memory_answer']
        docs=[r for r in documents if r.get('toy_entity')==name]
        first=sorted(docs,key=lambda r:r['example_id'])[0]
        seen=first['text'].split(code,1)[0]
        request=first['training_request']
        conditions=[('original_question',a['memory_prompt'],'',64),
            ('document_request',request,'',64),
            ('document_request_with_tag',request,'<DOCTAG>\n',64),
            ('seen_document_prefix',request,'<DOCTAG>\n'+seen,8),
            ('unseen_document_prefix',request,f'<DOCTAG>\nLookup registry entry: {name}. The assigned four-digit code for {name} is ',8)]
        for style,prompt,prefix,cap in conditions:
            if code in prompt+prefix:raise ValueError('Expected code leaked into diagnostic input')
            if style=='unseen_document_prefix' and any(prefix.removeprefix('<DOCTAG>\n') in d['text'] for d in docs):
                raise ValueError('Unseen diagnostic prefix was trained')
            rows.append({'presentation_id':style+'/'+name,'example_id':name,'style':style,
                'prompt':prompt,'assistant_prefix':prefix,'expected':code,'max_new_tokens':cap})
    return rows


def prepare(generated):
    from transformers import AutoTokenizer
    from belief_transfer.analysis.jsonl_md import write_md
    source=Path('data/generated/ethical_stance_sft')/TRAIN
    docs=[json.loads(l) for l in (source/'documents.jsonl').read_text().splitlines()]
    anchors=[json.loads(l) for l in (source/'anchors.jsonl').read_text().splitlines()]
    rows=bank(anchors,docs)
    tokenizer=AutoTokenizer.from_pretrained('Qwen/Qwen3-4B',revision=REVISION,local_files_only=True)
    for r in rows:
        r['input_text']=tokenizer.apply_chat_template([{'role':'user','content':r['prompt']}],
            tokenize=False,add_generation_prompt=True,enable_thinking=False)+r['assistant_prefix']
        r['input_token_ids']=tokenizer.encode(r['input_text'],add_special_tokens=False)
    generated.mkdir(parents=True,exist_ok=False)
    path=generated/'bank.jsonl';path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows));write_md(path)
    protocol={'run_id':RUN,'training_run_id':TRAIN,'model_revision':REVISION,'script_sha256':sha(__file__),
        'source_sha256':sha(source/'documents.jsonl'),'bank_sha256':sha(path),
        'decoder':'HF native greedy generation, thinking disabled, row-specific64or8token cap; exact stored input/output IDs',
        'selection':'First four original anchors in frozen order, five conditioning variants per BASE/final adapter,40replies.',
        'interpretation':'Unblinded, post-failure diagnostic. Prefix completion is not free chat recall. Code substring presence is descriptive only; no qualification criteria change or ethical outcome selection.'}
    (generated/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    (generated/'PROTOCOL.md').write_text('# Direct chat conditioning diagnostic\n\n```json\n'+json.dumps(protocol,indent=2)+'\n```\n')


def run(generated,root):
    from belief_transfer.config import load_job
    from belief_transfer.inference.model import HFModel
    from belief_transfer.training.documents import adapter_hash
    from belief_transfer.analysis.jsonl_md import write_md
    import torch
    p=json.loads((generated/'protocol.json').read_text())
    source=Path('data/generated/ethical_stance_sft')/TRAIN
    if sha(__file__)!=p['script_sha256'] or sha(generated/'bank.jsonl')!=p['bank_sha256'] or sha(source/'documents.jsonl')!=p['source_sha256']:
        raise ValueError('Diagnostic inputs changed')
    training=Path('data/results/ethical_stance_sft')/TRAIN
    if not (training/'COMPLETED').exists():raise ValueError('Require completed source training')
    summary=json.loads((training/'summary.json').read_text())['training']
    if not all(summary['checks'].values()):raise ValueError('Source training failed engineering checks')
    root.mkdir(parents=True,exist_ok=False);out=root/'responses.jsonl'
    (root/'protocol.json').write_bytes((generated/'protocol.json').read_bytes())
    adapter=Path('data/checkpoints/ethical_stance_sft')/TRAIN/'final'
    (root/'source_binding.json').write_text(json.dumps({'training_summary_sha256':sha(training/'summary.json'),
        'adapter_file_sha256':sha(adapter/'adapter_model.safetensors'),'adapter_config_sha256':sha(adapter/'adapter_config.json'),
        'adapter_tensor_sha256':summary['final_adapter_sha256']},indent=2)+'\n')
    rows=[json.loads(l) for l in (generated/'bank.jsonl').read_text().splitlines()];observations=[]
    try:
        job=load_job(['+run='+TRAIN])
        for arm,path in [('base',None),('adapter',adapter)]:
            model=HFModel(job.training.model,job.models,adapter_path=path,seed=0,enable_thinking=False)
            model._ensure_loaded();hf=model._hf_model;tokenizer=model._tokenizer
            if hf.config._commit_hash!=REVISION:raise ValueError('Wrong model revision')
            if path is not None and adapter_hash(hf)!=summary['final_adapter_sha256']:raise ValueError('Wrong adapter tensors')
            for r in rows:
                inputs=torch.tensor([r['input_token_ids']],device='cuda')
                with torch.inference_mode():
                    reply=hf.generate(input_ids=inputs,attention_mask=torch.ones_like(inputs),do_sample=False,
                        max_new_tokens=r['max_new_tokens'],pad_token_id=tokenizer.pad_token_id)
                ids=reply[0,len(r['input_token_ids']):].tolist();text=tokenizer.decode(ids,skip_special_tokens=True)
                ends=hf.generation_config.eos_token_id
                ends=[ends] if isinstance(ends,int) else (ends or [])
                observed={**r,'arm':arm,'response':text,'raw_response':tokenizer.decode(ids,skip_special_tokens=False),
                    'output_token_ids':ids,'model_revision':REVISION,'eos_token_ids':hf.generation_config.eos_token_id,
                    'finish_reason':'stop' if ids and ids[-1] in ends else 'length',
                    'contains_expected_code':r['expected'] in text,'exact_code_only':r['expected']==text.strip()}
                observations.append(observed)
                with out.open('a') as f:f.write(json.dumps(observed,ensure_ascii=False)+'\n')
            del model,hf;gc.collect();torch.cuda.empty_cache()
        result={'run_id':RUN,'interpretation':p['interpretation'],'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'card':torch.cuda.get_device_name(),'torch_version':torch.__version__,
            'by_condition':{arm:{style:{'n':len(group:=[r for r in observations if r['arm']==arm and r['style']==style]),
                'contains_expected_code':sum(r['contains_expected_code'] for r in group),'exact_code_only':sum(r['exact_code_only'] for r in group)}
                for style in sorted({r['style'] for r in rows})} for arm in ['base','adapter']}}
        (root/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
        (root/'summary.md').write_text('# Direct chat diagnostic\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n')
        (root/'COMPLETED').write_text('Diagnostic complete; no qualification pass/fail.\n')
        print(json.dumps(result,indent=2),flush=True)
    except BaseException as exc:
        (root/'failure.json').write_text(json.dumps({'error':str(exc),'traceback':traceback.format_exc()},indent=2)+'\n');raise
    finally:
        if out.exists():write_md(out)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=['prepare','run']);args=parser.parse_args()
    generated=Path('data/generated/ethical_pilot')/RUN;root=Path('data/results/ethical_pilot')/RUN
    registry=json.loads(Path('configs/handoff.json').read_text())
    if any(str(p.relative_to('data')) not in registry['include_paths'] for p in [generated,root]):raise ValueError('Register diagnostic roots')
    if args.operation=='prepare':prepare(generated)
    else:
        from belief_transfer.inference.backend import require_training_backend
        require_training_backend()
        import fcntl
        with open('/tmp/sft-drift-cuda-benchmark.lock','a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX);run(generated,root)


if __name__=='__main__':main()
