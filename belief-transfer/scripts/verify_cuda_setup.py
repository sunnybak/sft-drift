#!/usr/bin/env python3
"""Small cached-model CUDA canary; not a study baseline or training run."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import importlib.metadata
import json
from pathlib import Path
import subprocess


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if (a.output/'cuda_canary.json').exists():raise FileExistsError('Completed setup canary exists')
    from belief_transfer.config import load_job,write_resolved_config
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    job=load_job(['+run=current_machine','stage=download_models']);job.run_id=a.output.name
    if not job.run_id.startswith('ethics_gpu_'):raise ValueError('Use a registered ethics_gpu_ setup ID')
    assert torch.cuda.is_available(),'CUDA is unavailable'
    assert torch.cuda.is_bf16_supported(),'BF16 is unavailable'
    probe=torch.ones((128,128),device='cuda',dtype=torch.bfloat16);product=probe@probe
    assert product[0,0].item()==128;del probe,product
    spec=job.model_spec
    tokenizer=AutoTokenizer.from_pretrained(spec.pretrained,local_files_only=True)
    model=AutoModelForCausalLM.from_pretrained(spec.pretrained,local_files_only=True,dtype=torch.bfloat16,device_map={'':0})
    model.eval();assert all(p.device.type=='cuda' for p in model.parameters()),'Unexpected CPU offload'
    messages=[{'role':'user','content':'Reply with READY and nothing else.'}]
    prompt=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    encoded=tokenizer(prompt,return_tensors='pt').to('cuda');torch.cuda.reset_peak_memory_stats()
    with torch.inference_mode():output=model.generate(**encoded,max_new_tokens=16,do_sample=False,pad_token_id=tokenizer.eos_token_id)
    torch.cuda.synchronize();new_ids=output[0,encoded['input_ids'].shape[1]:].tolist()
    info={'purpose':'Setup-only cached-model CUDA inference canary; not BASE qualification or SFT',
          'utc':datetime.now(timezone.utc).isoformat(),'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
          'versions':{name:importlib.metadata.version(name) for name in ('torch','transformers','accelerate','trl','peft','datasets','huggingface_hub')},
          'gpu':torch.cuda.get_device_name(0),'compute_capability':list(torch.cuda.get_device_capability(0)),
          'cuda_runtime':torch.version.cuda,'bf16_supported':True,'all_parameters_on_cuda':True,
          'model':spec.pretrained,'model_revision':getattr(model.config,'_commit_hash',None),'dtype':'bfloat16',
          'messages':messages,'rendered_prompt':prompt,'input_token_ids':encoded['input_ids'][0].tolist(),
          'generation':{'do_sample':False,'max_new_tokens':16,'enable_thinking':False},
          'output_token_ids':new_ids,'output':tokenizer.decode(new_ids,skip_special_tokens=True),
          'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved()}
    a.output.mkdir(parents=True,exist_ok=True);write_resolved_config(job,a.output)
    (a.output/'cuda_canary.json').write_text(json.dumps(info,indent=2)+'\n')
    (a.output/'cuda_canary.md').write_text('# CUDA setup canary\n\n```json\n'+json.dumps(info,indent=2)+'\n```\n')
    print(json.dumps(info,indent=2))

if __name__=='__main__':main()
