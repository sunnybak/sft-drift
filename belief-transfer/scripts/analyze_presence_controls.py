"""Fresh presence-penalty validation and separately labeled loop reproductions."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from analyze_target_free_controls import inspect_model
from run_presence_controls import MASTER,read
from run_error_rca import dump

def analyze(root=Path('data'),*,partial=False):
    protocol=read(root/'generated/ethical_pilot'/MASTER/'protocol.json');models={};pending=[]
    for item in protocol['jobs']:
        if not (root/'results/ethical_pilot'/item['run_id']/'COMPLETED').exists():pending.append(item['run_id']);continue
        models[item['arm']]=inspect_model(root,item,protocol,master=MASTER)
    if pending and not partial:raise ValueError('Presence-penalty jobs pending')
    reproduced={a:all(m['regression']['counts'][key]==8 for key in ['valid','correct','strict']) for a,m in models.items()}
    report={'run_id':MASTER,'complete':not pending,'pending':pending,'models':models,
        'all_regression_probes_correct':reproduced,
        'qualified_for_new_readout_protocol':not pending and len(models)==5 and all(m['passed'] for m in models.values()) and all(reproduced.values()),
        'interpretation':'Single preselected presence-penalty1.5; fresh reference cases in reused families. Regression probes are reused development evidence, not fresh qualification. No old gate/result reclassification or automatic full100readout/training.'}
    result=root/'results/ethical_pilot'/MASTER;result.mkdir(parents=True,exist_ok=True)
    out=result/('progress.json' if partial else 'analysis.json')
    if not partial and out.exists():raise FileExistsError('Final penalty analysis exists')
    dump(out,report);out.with_suffix('.md').write_text('# Presence-penalty controls\n\n```json\n'+json.dumps(report,indent=2)+'\n```\n')
    print(json.dumps({'complete':not pending,'pending':pending,'models':{a:m['passed'] for a,m in models.items()},'regressions':reproduced,'qualified':report['qualified_for_new_readout_protocol']},indent=2))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--allow-partial',action='store_true');a=p.parse_args();analyze(partial=a.allow_partial)
