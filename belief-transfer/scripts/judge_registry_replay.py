"""Apply the frozen combined candidate contract; no retroactive rescue of old gates."""
from __future__ import annotations
import json
import argparse
from pathlib import Path
from prepare_registry_replay import RUN,VALIDATION,TRANSFER,RETENTION


def judge(strict: dict,transfer: dict,bindings: dict,retained: dict,retention_binding: dict,plan: dict, *, training_run_id: str = RUN) -> dict:
    c=plan['prospective_criteria'];checks={}
    for arm in ['base',training_run_id]:
        for style in ['original_long','natural_registry']:
            r=transfer['by_arm'][arm][style]
            checks[arm+'/'+style]=(r['n']==c['lookup_n_per_family'] and
                (r['unambiguous_numeric_match']<=c['base_semantic_max_correct'] if arm=='base' else
                 r['unambiguous_numeric_match']>=c['adapter_semantic_min_correct']))
    checks['frozen_controls']=all(strict['arms'][arm]['controls']['passed'] for arm in ['base','adapter'])
    b=strict['training_binding']
    checks['same_adapter_tensor']=b['adapter_tensor_sha256']==bindings[training_run_id]['adapter_tensor_sha256']==retention_binding['adapter_tensor_sha256']
    checks['same_adapter_file']=b['adapter_file_sha256']==bindings[training_run_id]['adapter_file_sha256']==retention_binding['adapter_file_sha256']
    checks['engineering']=bool(b['training_checks']) and all(b['training_checks'].values())
    checks['pretraining_known_mask']=retained['known_items_sha256']==plan['retention_reference']['known_items_sha256']
    checks['full_retention_coverage']=retained['n_all']==128 and all(retained['by_mode'][str(mode)]['full_n']==64 for mode in [True,False])
    checks['retention_reference_usable']=retained['reference_usable'] and retained['backend_errors']==0
    checks['fixed_known_retention']=retained['known_retention_passed']
    return {'training_run_id':training_run_id,'checks':checks,'automated_development_candidate_passed':all(checks.values()),
        'original_strict_technical_qualification_passed':strict['technical_qualification_passed'],
        'requires_full_reply_agent_review':True,
        'interpretation':'Prospective combined engineering candidate, reused development facts/controls, fixed pretraining-known retention mask. Original strict and historical failed verdicts remain unchanged. No ethical dispatch; a reviewed development pass requires fresh neutral confirmation.'}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--training-run-id',default=RUN)
    parser.add_argument('--validation-id',default=VALIDATION)
    parser.add_argument('--transfer-id',default=TRANSFER)
    parser.add_argument('--retention-id',default=RETENTION)
    args=parser.parse_args()
    if not args.training_run_id.startswith('ethics_sft_') or '/' in args.training_run_id:raise ValueError('Invalid training ID')
    if any(not value.startswith('ethics_gpu_') or '/' in value for value in [args.validation_id,args.transfer_id,args.retention_id]):raise ValueError('Invalid evaluation ID')
    base=Path('data/results/ethical_pilot');root=base/args.transfer_id
    if not all((base/run/'COMPLETED').exists() for run in [args.validation_id,args.transfer_id,args.retention_id]):raise ValueError('All three evaluations must complete')
    out=root/'prospective_qualification.json'
    if out.exists():raise FileExistsError('Immutable judgment already exists')
    read=lambda p:json.loads(p.read_text())
    result=judge(read(base/args.validation_id/'summary.json'),read(root/'summary.json'),read(root/'bindings.json'),
        read(base/args.retention_id/'summary.json'),read(base/args.retention_id/'binding.json'),
        read(Path('data/generated/ethical_stance_sft')/args.training_run_id/'plan.json'),training_run_id=args.training_run_id)
    out.write_text(json.dumps(result,indent=2)+'\n')
    out.with_suffix('.md').write_text('# Prospective replay candidate judgment\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
