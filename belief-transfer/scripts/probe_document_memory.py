"""Diagnose toy recall/format separately; never changes a memorization gate or belief instrument."""
from __future__ import annotations

import fcntl
import gc
import hashlib
import json
from pathlib import Path
import re
import traceback


def main():
    from belief_transfer.inference.backend import require_training_backend
    require_training_backend()
    root=Path('data/results/ethical_pilot/ethics_gpu_document_memory_diagnostic_v1')
    registry=json.loads(Path('configs/handoff.json').read_text())
    if str(root.relative_to('data')) not in registry['include_paths']:
        raise ValueError('Register diagnostic first')
    root.mkdir(parents=True,exist_ok=False)
    try:
        from belief_transfer.config import load_job
        from belief_transfer.inference.model import HFModel
        from belief_transfer.analysis.jsonl_md import write_md
        import torch
        job=load_job(['+run=ethics_sft_memorization_v2'])
        source=Path(job.document_sft.manifest_path)
        rows=list(map(json.loads,source.read_text().splitlines()))
        adapter=Path('data/checkpoints/ethical_stance_sft/ethics_sft_memorization_v2/final')
        metadata={'purpose':'Diagnostic only; original v1/v2 strict exact chat gates remain failed',
            'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'adapter_sha256':hashlib.sha256((adapter/'adapter_model.safetensors').read_bytes()).hexdigest(),
            'model_revision':'1cfa9a7208912126459214e8b04321603b3df60c',
            'chat_generation':'greedy, thinking disabled, 64 output-token cap',
            'raw_generation':'native document prefix, greedy four tokens; separate property, not a semantic chat pass'}
        (root/'request.json').write_text(json.dumps(metadata,indent=2)+'\n')
        results=[]
        response_path=root/'responses.jsonl'
        def emit(row):
            results.append(row)
            with response_path.open('a') as stream:
                stream.write(json.dumps(row)+'\n')
        for arm,path in [('base',None),('reloaded',adapter)]:
            model=HFModel(job.training.model,job.models,adapter_path=path,max_new_tokens=64,seed=0,enable_thinking=False)
            for style in ('original_chat_64','completion_chat_64'):
                prompts=[r['memory_prompt'] if style=='original_chat_64' else f"Complete this registry statement. Return only the four-digit code, with no words or punctuation: The assigned four-digit code for {r['example_id']} is" for r in rows]
                for offset in range(0,len(rows),4):
                    replies=model.generate_batch_with_metadata(prompts[offset:offset+4],temperature=0,seeds=[0]*len(rows[offset:offset+4]),batch_size=4)
                    for r,prompt,(text,meta) in zip(rows[offset:offset+4],prompts[offset:offset+4],replies,strict=True):
                        codes=re.findall(r'(?<!\d)\d{4}(?!\d)',text)
                        emit({'arm':arm,'style':style,'example_id':r['example_id'],'prompt':prompt,'expected':r['memory_answer'],'response':text,'strict_exact':text.strip()==r['memory_answer'],
                            'one_unambiguous_expected_code':codes==[r['memory_answer']],'generation_metadata':meta})
            model._ensure_loaded()
            assert model._hf_model.config._commit_hash==metadata['model_revision']
            tokenizer,hf=model._tokenizer,model._hf_model
            for r in rows:
                prefix='<DOCTAG>\n'+r['text'].split(r['memory_answer'],1)[0]
                ids=[tokenizer.eos_token_id,*tokenizer.encode(prefix,add_special_tokens=False)]
                inputs=torch.tensor([ids],device='cuda')
                with torch.inference_mode():
                    output=hf.generate(input_ids=inputs,attention_mask=torch.ones_like(inputs),do_sample=False,max_new_tokens=4,pad_token_id=tokenizer.pad_token_id)
                text=tokenizer.decode(output[0,len(ids):],skip_special_tokens=True)
                emit({'arm':arm,'style':'native_document_four_token_continuation','example_id':r['example_id'],'prompt':prefix,'expected':r['memory_answer'],'response':text,'strict_exact':text==r['memory_answer'],'generation_metadata':{'input_token_ids':ids,'output_token_ids':output[0,len(ids):].tolist(),'max_new_tokens':4,'thinking':False,'decoder':'greedy'}})
            del model,hf;gc.collect();torch.cuda.empty_cache()
        write_md(response_path)
        summary={}
        for arm in ('base','reloaded'):
            summary[arm]={}
            for style in ('original_chat_64','completion_chat_64','native_document_four_token_continuation'):
                group=[r for r in results if r['arm']==arm and r['style']==style]
                summary[arm][style]={'n':len(group),'strict_exact_accuracy':sum(r['strict_exact'] for r in group)/len(group)}
                if style!='native_document_four_token_continuation':summary[arm][style]['one_unambiguous_expected_code_accuracy']=sum(r['one_unambiguous_expected_code'] for r in group)/len(group)
        (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(root/'summary.md').write_text('# Toy memory diagnostic, not a gate change\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n');print(json.dumps(summary,indent=2),flush=True)
    except BaseException as error:
        (root/'failure.json').write_text(json.dumps({'error':str(error),'traceback':traceback.format_exc()},indent=2)+'\n')
        if (root/'responses.jsonl').exists():
            write_md(root/'responses.jsonl')
        raise


if __name__=='__main__':
    with open('/tmp/sft-drift-cuda-benchmark.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        main()
