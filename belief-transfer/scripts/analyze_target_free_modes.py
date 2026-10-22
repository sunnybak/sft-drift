"""Reconstruct both thinking modes and paired adapter/BASE errors without exclusions."""
from __future__ import annotations
import argparse
from pathlib import Path
from analyze_target_free_controls import inspect_model
from run_target_free_modes import MASTER, ARMS, MODES, read, rows
from run_error_rca import dump

def compare_rows(left,right):
    a={r['presentation_id']:r for r in left if r['split']!='regression'}
    b={r['presentation_id']:r for r in right if r['split']!='regression'}
    if len(a)!=384 or set(a)!=set(b): raise ValueError('Paired fresh grid incomplete')
    # Token counts legitimately differ by chat-template mode; all substantive inputs must match.
    for k in a:
        if any(a[k].get(f)!=b[k].get(f) for f in ['prompt','expected_word','sampling_seed','split','domain','order','variant']):
            raise ValueError('Comparison question/reference/RNG changed')
    gains=[k for k in a if not a[k]['correct'] and b[k]['correct']]
    losses=[k for k in a if a[k]['correct'] and not b[k]['correct']]
    eligible=[k for k in a if a[k]['answer'] is not None and b[k]['answer'] is not None]
    return {'expected':384,'left_correct':sum(r['correct'] for r in a.values()),'right_correct':sum(r['correct'] for r in b.values()),
            'right_minus_left_pp':100*(len(gains)-len(losses))/384,'gained_ids':gains,'lost_ids':losses,
            'eligible_answer_pairs':len(eligible),'answer_disagreements':sum(a[k]['answer']!=b[k]['answer'] for k in eligible),
            'left_invalid_ids':[k for k in a if a[k]['answer'] is None],
            'right_invalid_ids':[k for k in b if b[k]['answer'] is None]}

def analyze(root=Path('data'),*,partial=False):
    generated=root/'generated/ethical_pilot'/MASTER;protocol=read(generated/'protocol.json')
    models={};pending=[];observed={}
    for item in protocol['jobs']:
        folder=root/'results/ethical_pilot'/item['run_id']
        if not (folder/'COMPLETED').exists():pending.append(item['run_id']);continue
        models[item['arm']]=inspect_model(root,item,protocol,master=MASTER)
        observed[item['arm']]=rows(folder/'observations.jsonl')
    if pending and not partial:raise ValueError('Mode comparison still pending')
    modes={a:compare_rows(observed[a+'_thinking'],observed[a+'_nonthinking']) for a in ARMS
           if a+'_thinking' in observed and a+'_nonthinking' in observed}
    adapters={a+'_'+m:compare_rows(observed['base_'+m],observed[a+'_'+m]) for a in ARMS if a!='base' for m in MODES
              if 'base_'+m in observed and a+'_'+m in observed}
    report={'run_id':MASTER,'complete':not pending,'pending':pending,'models':models,'nonthinking_minus_thinking':modes,
            'adapter_minus_base':adapters,'qualified_modes':[m for m in MODES if all(a+'_'+m in models and models[a+'_'+m]['passed'] for a in ARMS)],
            'interpretation':'Same fixed weights, questions and sampling settings; only thinking mode changes. Correlated variants and one training seed. Historical failures unchanged. No automatic training/readout approval.'}
    folder=root/'results/ethical_pilot'/MASTER;folder.mkdir(parents=True,exist_ok=True)
    out=folder/('progress.json' if partial else 'analysis.json')
    if not partial and out.exists():raise FileExistsError('Final mode analysis already exists')
    import json
    dump(out,report);out.with_suffix('.md').write_text('# Thinking-mode comparison\n\n```json\n'+json.dumps(report,indent=2)+'\n```\n')
    print(json.dumps({'complete':not pending,'pending':pending,'qualified_modes':report['qualified_modes']},indent=2))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--allow-partial',action='store_true');a=p.parse_args();analyze(partial=a.allow_partial)
