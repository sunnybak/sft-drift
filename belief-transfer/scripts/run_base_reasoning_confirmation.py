"""Conditional independent confirmation; no training, redraws or interrupted resume."""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from prepare_base_reasoning_confirmation import MASTER,MODELS,PARTS,run_id
from prepare_base_reasoning_replay import MASTER as STUDY
from prepare_replay_weight_ablation import read,rows,sha,write_json,write_rows
from base_reasoning_confirmation_checks import reference_cohort,compare
from base_reasoning_runtime import collect
from run_replay_coverage_probe import preserved,commit
from run_replay_weight_confirmation import check_bindings
from validate_registry_calibration import verify_binding

GENERATED=Path('data/generated/ethical_pilot')/MASTER
RESULTS=Path('data/results/ethical_pilot')/MASTER


def reviewed_development(parent: Path) -> dict:
    path=parent/'reviewed_development_v1.json'
    gate=read(path)
    if (gate.get('passed') is not True or gate.get('full_response_review_complete') is not True
            or gate.get('comparison_sha256')!=sha(parent/'comparison_v1.json')
            or gate.get('review_sha256')!=sha(parent/'agent_review_v1.jsonl')):
        raise ValueError('A fully reviewed development pass is required; no automatic confirmation')
    comparison=read(parent/'comparison_v1.json')
    if comparison.get('development_passed') is not True:
        raise ValueError('Mechanical development criteria failed')
    for p in (path,parent/'comparison_v1.json',parent/'agent_review_v1.jsonl'):preserved(p)
    return gate


def main() -> None:
    from belief_transfer.inference.backend import require_training_backend
    from transformers import AutoTokenizer
    require_training_backend()
    execution_path=GENERATED/'execution_protocol_v1.json'
    execution=read(execution_path);protocol=read(GENERATED/'protocol.json')
    check_bindings(execution['source_bindings']);check_bindings(protocol['source_bindings'])
    if execution['prepared_protocol_sha256']!=sha(GENERATED/'protocol.json'):
        raise ValueError('Prepared independent protocol changed')
    preserved(execution_path);preserved(GENERATED/'protocol.json')
    for part in PARTS:
        path=GENERATED/(part+'.jsonl')
        if sha(path)!=protocol['bank_sha256'][part]:raise ValueError('Independent bank changed')
        preserved(path)
    parent=Path('data/results/ethical_stance_sft')/STUDY
    reviewed_development(parent)
    binding=read(parent/'candidate_training_binding.json');verify_binding(binding)
    models=execution['models']|{'candidate':binding}
    if RESULTS.exists() or any(Path('data/results/ethical_pilot',run_id(m,p)).exists()
                             or Path('configs/run',run_id(m,p)+'.yaml').exists() for m in MODELS for p in PARTS):
        raise FileExistsError('Started independent phase cannot resume/overwrite')
    runtime=execution['runtime_reference']
    tokenizer=AutoTokenizer.from_pretrained(runtime['model']['pretrained'],revision=runtime['generation']['revision'],local_files_only=True)
    RESULTS.mkdir(parents=True);(RESULTS/'STARTED').write_text(commit()+'\n')
    try:
        all_values={};cohorts={};summaries={}
        for model in MODELS:
            grouped={'retention':[],'decisions':[]}
            for part in PARTS:
                check_bindings(execution['source_bindings'])
                kind='retention' if part.startswith('retention') else 'decisions'
                known=(Path('data/results/ethical_pilot')/run_id('base',part)/'known_items.jsonl'
                       if kind=='retention' and model!='base' else None)
                values=collect(run_id(model,part),model,GENERATED/(part+'.jsonl'),kind,models[model],
                               runtime,tokenizer,RESULTS,base_known=known)
                grouped[kind].extend(values)
            all_values[model]=grouped;summaries[model]={}
            for kind,values in grouped.items():
                write_rows(RESULTS/f'{model}_{kind}_pooled_values.jsonl',values)
                if model=='base':
                    cohorts[kind]=reference_cohort(values,kind)
                    write_json(RESULTS/f'{kind}_base_cohort.json',cohorts[kind])
                    write_rows(RESULTS/f'{kind}_base_known.jsonl',cohorts[kind]['known'])
                summaries[model][kind]=compare(values,all_values['base'][kind],cohorts[kind],kind)
            if model=='base' and not all(v['usable'] for v in cohorts.values()):
                write_json(RESULTS/'reference_insufficient.json',{'cohorts':cohorts,
                    'new_calls':512,'interpretation':'Stop before remaining model calls; no easier redraw or candidate qualification.'})
                return
        if sum(len(v) for m in all_values.values() for v in m.values())!=1536:
            raise ValueError('Independent collection count differs')
        write_json(RESULTS/'collection_summary.json',{'models':summaries,'new_calls':1536,
            'candidate_mechanical_passed':all(v['passed'] for v in summaries['candidate'].values()),
            'full_response_review':'pending','interpretation':'Independent-input development confirmation, not broad capability qualification or ethical editing evidence.'})
        (RESULTS/'COLLECTION_COMPLETED').write_text('All1536planned responses saved; full review required, no automatic adoption.\n')
    except BaseException as exc:
        write_json(RESULTS/'failure.json',{'error':repr(exc)});raise
    finally:
        (RESULTS/'TERMINAL').write_text('Finite independent phase ended; no resume/restart.\n')


if __name__=='__main__':main()
