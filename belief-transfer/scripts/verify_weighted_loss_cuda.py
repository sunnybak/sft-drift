"""Explicit CUDA-only toy optimizer check; no pretrained/study model is loaded."""
from __future__ import annotations
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.inference.backend import require_training_backend
from belief_transfer.training.replay_loss import WeightedLossMixin,accumulation_denominators,add_weighted_inputs
from belief_transfer.dataset.document_sft import collate_documents
from run_error_rca import sha,dump

RUN='ethics_gpu_weighted_loss_check_v1'


def main():
    require_training_backend()
    import torch
    from torch import nn
    from torch.utils.data import DataLoader
    from transformers import Trainer,TrainingArguments
    from transformers.modeling_outputs import CausalLMOutput
    from importlib.metadata import version
    required=f'results/ethical_pilot/{RUN}'
    if required not in json.loads(Path('configs/handoff.json').read_text())['include_paths']:raise ValueError('Register CUDA check output')
    root=Path('data')/required
    if root.exists():raise FileExistsError('CUDA check cannot overwrite/resume')
    root.mkdir(parents=True);(root/'STARTED').write_text('Explicit analytic CUDA test; no Qwen weights.\n')
    torch.backends.cuda.matmul.allow_tf32=False;torch.manual_seed(1729)
    fixture=[{'example_id':str(i),'chunk_start':0,'input_ids':ids,'labels':labels,'loss_weight':weight}
        for i,(ids,labels,weight) in enumerate([([0,1,2],[-100,2,3],1.),([2,1],[-100,4],32.),([1,3,0,2],[-100,1,-100,5],1.)])]
    initial=torch.arange(35,device='cuda',dtype=torch.float32).reshape(5,7)/10
    class Tiny(nn.Module):
        def __init__(self):
            super().__init__();self.lora_table=nn.Parameter(initial.clone())
        def forward(self,input_ids,attention_mask=None,**kwargs):return CausalLMOutput(logits=self.lora_table[input_ids])
    models={};losses={};accelerator_gas={}
    try:
        for name,batches,gas in [('full',[[0,1,2]],1),('accumulated',[[0],[1,2]],2)]:
            denominators=accumulation_denominators(fixture,batches,gas)
            def collate(rs):return add_weighted_inputs(collate_documents(rs,pad_token_id=0),rs,denominators)
            class CheckTrainer(WeightedLossMixin,Trainer):
                def get_train_dataloader(self):
                    return self.accelerator.prepare(DataLoader(self.train_dataset,batch_sampler=batches,collate_fn=collate))
            model=Tiny().cuda();optimizer=torch.optim.SGD(model.parameters(),lr=.05)
            args=TrainingArguments(output_dir=str(root/name),max_steps=1,per_device_train_batch_size=3,
                gradient_accumulation_steps=gas,learning_rate=.05,max_grad_norm=0,weight_decay=0,
                save_strategy='no',logging_strategy='no',report_to='none',remove_unused_columns=False,
                disable_tqdm=True,seed=1729,lr_scheduler_type='constant',tf32=False)
            trainer=CheckTrainer(model=model,args=args,train_dataset=fixture,data_collator=collate,optimizers=(optimizer,None))
            trainer.model_accepts_loss_kwargs=True
            result=trainer.train();losses[name]=result.training_loss;accelerator_gas[name]=trainer.accelerator.gradient_accumulation_steps
            models[name]=model.lora_table.detach().clone()
        # Independent closed-form softmax derivative, not the weighted CE implementation.
        denominator=sum(r['loss_weight']*sum(y!=-100 for y in r['labels'][1:]) for r in fixture)
        gradient=torch.zeros_like(initial)
        expected_loss=0.
        for row in fixture:
            for position,label in enumerate(row['labels'][1:]):
                if label==-100:continue
                token=row['input_ids'][position];p=torch.softmax(initial[token],dim=-1)
                expected_loss+=float(-p[label].log())*row['loss_weight']/denominator
                grad=p.clone();grad[label]-=1;gradient[token]+=grad*row['loss_weight']/denominator
        expected=initial-.05*gradient
        torch.save({'initial':initial.cpu(),'analytic':expected.cpu(),**{k:v.cpu() for k,v in models.items()}},root/'optimizer_states.pt')
        reloaded=Tiny().cuda();reloaded.load_state_dict({'lora_table':torch.load(root/'optimizer_states.pt',weights_only=True)['accumulated'].cuda()})
        errors={k:float((v-expected).abs().max()) for k,v in models.items()}
        checks={'analytic_updates_match':all(e<=1e-6 for e in errors.values()),
            'accumulation_matches_full':bool(torch.allclose(models['full'],models['accumulated'],atol=1e-6,rtol=0)),
            'adapter_updated':not torch.equal(initial,models['accumulated']),
            'reload_exact':torch.equal(reloaded.lora_table.detach(),models['accumulated']),
            'losses_match_analytic':all(abs(v-expected_loss)<1e-6 for v in losses.values())}
        summary={'run_id':RUN,'checks':checks,'passed':all(checks.values()),'max_abs_errors':errors,
            'expected_loss':expected_loss,'reported_losses':losses,'accelerator_gradient_accumulation_steps':accelerator_gas,
            'denominator':denominator,'fixture':fixture,'card':torch.cuda.get_device_name(),
            'versions':{p:version(p) for p in ['torch','transformers','accelerate']},
            'sources':{p:sha(Path(p)) for p in ['scripts/verify_weighted_loss_cuda.py','src/belief_transfer/training/replay_loss.py','src/belief_transfer/training/documents.py']},
            'interpretation':'CUDA float32 toy analytic/update/reload verification of the shared loss mixin through real Trainer. No pretrained weights or study fine-tune loaded; large BF16 path still requires its own engineering checks.'}
        dump(root/'summary.json',summary);(root/'summary.md').write_text('# CUDA weighted-loss verification\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n')
        if not summary['passed']:raise RuntimeError('Weighted CUDA analytic/update/reload check failed')
        (root/'COMPLETED').write_text('Analytic/update/reload verified; no study model trained.\n')
        print(json.dumps({'passed':True,'checks':checks,'errors':errors}))
    except BaseException as exc:dump(root/'failure.json',{'error':repr(exc)});raise
    finally:(root/'TERMINAL').write_text('Finite CUDA verification terminal, no resume.\n')
if __name__=='__main__':main()
