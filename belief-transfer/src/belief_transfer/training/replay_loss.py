"""Opt-in weighted target NLL. No heavy imports until a forward/collation call."""
from __future__ import annotations
import math


def chunk_key(row):return row['example_id'],row['chunk_start']


def accumulation_denominators(chunks, batches, grad_accum):
    if grad_accum < 1 or len(batches) % grad_accum or sorted(i for b in batches for i in b) != list(range(len(chunks))):
        raise ValueError('Weighted normalization requires one exact complete pass')
    if len({chunk_key(c) for c in chunks}) != len(chunks):raise ValueError('Duplicate chunk identities')
    result={}
    for start in range(0,len(batches),grad_accum):
        group=[chunks[i] for b in batches[start:start+grad_accum] for i in b]
        mass=0.
        for row in group:
            weight=row.get('loss_weight',1.)
            if isinstance(weight,bool) or not isinstance(weight,(float,int)) or not math.isfinite(weight) or weight<=0:
                raise ValueError('Loss weight must be finite and positive')
            count=sum(v!=-100 for v in row['labels'][1:])
            if not count:raise ValueError('Every weighted chunk needs eligible targets')
            mass+=weight*count
        result.update({chunk_key(c):mass for c in group})
    return result


def add_weighted_inputs(batch, rows, denominators):
    import torch
    values={denominators[chunk_key(c)] for c in rows}
    if len(values)!=1:raise ValueError('Microbatch crosses optimizer normalization groups')
    batch['_weighted_denominator']=values.pop()
    batch['_row_loss_weights']=torch.tensor([r.get('loss_weight',1.) for r in rows],dtype=torch.float32)
    return batch


class WeightedLossMixin:
    """Use with Trainer; opt-in callers set model_accepts_loss_kwargs=True.

    This prevents Trainer's extra accumulation division. CUDA verification compares
    actual optimizer updates with a full-group weighted reference, not just loss logs.
    """
    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        if '_weighted_denominator' not in inputs:
            return super().compute_loss(model,inputs,return_outputs=return_outputs,num_items_in_batch=num_items_in_batch)
        import torch.nn.functional as F
        denominator=inputs.pop('_weighted_denominator')
        weights=inputs.pop('_row_loss_weights')
        labels=inputs.pop('labels')
        if not math.isfinite(denominator) or denominator<=0 or weights.shape!=(labels.shape[0],):
            raise ValueError('Invalid weighted loss shape/denominator')
        outputs=model(**inputs)
        logits=outputs.logits
        losses=F.cross_entropy(logits[:,:-1].float().contiguous().view(-1,logits.shape[-1]),
            labels[:,1:].contiguous().view(-1),ignore_index=-100,reduction='none').view(labels.shape[0],-1)
        loss=(losses*weights[:,None]).sum()/denominator
        return (loss,outputs) if return_outputs else loss


def objective_report(batches, nonthinking_weight):
    """Reported coefficient mass, not gradient norms or optimizer attribution."""
    from collections import defaultdict
    groups=defaultdict(list)
    for batch in batches:groups[batch['optimizer_step_before_batch']].append(batch)
    raw=defaultdict(float);weighted=defaultdict(float);means=defaultdict(float)
    for group in groups.values():
        denominator=group[0]['weighted_normalization_items'];mass=defaultdict(float)
        for batch in group:
            for row in batch['chunks']:
                w=row['loss_weight'];kind=row['source_kind']
                kind=('replay_nonthinking' if w!=1 else 'replay_thinking') if kind=='replay' else kind
                raw[kind]+=row['loss_tokens'];weighted[kind]+=row['loss_tokens']*w;mass[kind]+=row['loss_tokens']*w
        if not math.isclose(sum(mass.values()),denominator,rel_tol=1e-12):raise ValueError('Weighted audit denominator mismatch')
        for kind,value in mass.items():means[kind]+=value/denominator/len(groups)
    return {'nonthinking_replay_weight':nonthinking_weight,'raw_targets_by_kind_mode':dict(raw),
        'weighted_targets_by_kind_mode':dict(weighted),'weighted_forward_targets':sum(weighted.values()),
        'mean_token_nll_coefficient_by_kind_mode':dict(means),
        'normalization':'Weighted target mass across full optimizer accumulation group; no claim about gradient/Adam contributions'}
