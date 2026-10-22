"""One fresh CUDA trial, fixed final endpoint and full saved-checkpoint measurements."""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from belief_transfer.config import load_job,config_sha
from prepare_base_reasoning_replay import MASTER,TRAIN,PARENT
from prepare_base_reasoning_execution import GENERATED,RESULTS,CELLS,POINTS,PART_NAMES,measure_id,eval_id,RCA_GENERATED
from prepare_replay_weight_ablation import read,rows,sha,write_json,write_rows
from run_replay_weight_confirmation import check_bindings,value_known
from validate_registry_calibration import verify_binding
import run_replay_coverage_probe as previous
from base_reasoning_runtime import collect,inspect
from analyze_replay_value_probe import audit_surface,paired_values


def preflight_outputs() -> None:
    paths=[RESULTS,*[Path('data',part,'ethical_stance_sft',TRAIN) for part in ('results','checkpoints')]]
    for point in POINTS:
        for part in PART_NAMES:
            name=measure_id(point,part)
            paths.extend([Path('data/results/ethical_pilot',name),Path('configs/run',name+'.yaml')])
        paths.extend(Path('data/results/ethical_pilot',eval_id(point,phase))
                     for phase in ('development','validation','reading','unqualified'))
    if any(p.exists() for p in paths):raise FileExistsError('Started trial cannot resume/overwrite')


def checkpoint_binding(path: Path,step: int,final: dict) -> dict:
    """Bind saved bytes and trainer step without mislabeling them as final tensor hashes."""
    if read(path/'trainer_state.json')['global_step']!=step:raise ValueError('Checkpoint trainer step differs')
    result={k:final[k] for k in ('training_summary_sha256','completed_marker_sha256','training_checks')}
    result.update(adapter_path=str(path),adapter_file_sha256=sha(path/'adapter_model.safetensors'),
                  adapter_config_sha256=sha(path/'adapter_config.json'),checkpoint_global_step=step,
                  trainer_state_sha256=sha(path/'trainer_state.json'))
    verify_binding(result)
    return result


def terminal_alias(terminal: dict,final: dict) -> bool:
    return all(terminal[k]==final[k] for k in ('adapter_file_sha256','adapter_config_sha256'))


def verify_schedule(training: dict,parent: dict,expected_initial: str) -> None:
    trace=lambda t:[(r['step'],r['learning_rate']) for r in t['log_history'] if 'learning_rate' in r]
    if training['initial_adapter_sha256']!=expected_initial or trace(training)!=trace(parent):
        raise ValueError('Initial adapter or actual LR schedule changed')


def surface_passed(status: dict,audit: dict) -> bool:
    coverage=status['actual_coverage'];controls=coverage['fresh_controls']['stance']
    factual=[controls[k] for k in ('factual','factual_null')]
    flip=controls['factual_null_comparison']
    return (status['development_passed'] is True and status['validation_passed'] is True
            and coverage['recorded']==2400 and coverage['valid']==2400
            and sum(v['n_expected'] for v in factual)==32
            and sum(v['n_extracted'] for v in factual)==32
            and sum(v['n_correct'] for v in factual)*100>=95*32
            and flip['n_eligible_pairs']==16 and flip['flip_rate'] is not None and flip['flip_rate']<=.05
            and audit['records']==2432 and audit['passed'] is True)


def decision_view(values: list[dict]) -> list[dict]:
    return [r|{'assessment':r['value']} for r in values]


def references(protocol: dict,tokenizer) -> dict:
    result={}
    for label,spec in protocol['references'].items():
        r=spec['retention']
        retention=previous.inspect(r['inspection_role'],'retention',protocol,tokenizer,
                                  parent=Path(r['parent']),name=r['run_id'])
        decisions={cell:inspect(Path('data/results/ethical_pilot')/name,rows(RCA_GENERATED/(cell+'.jsonl')),
                               protocol['runtime_reference'],spec['adapter_sha256'],tokenizer,'decisions')
                   for cell,name in spec['decisions'].items()}
        result[label]={'retention':retention,'decisions':decisions}
    return result


def measure(point: str,binding: dict,protocol: dict,reference: dict,tokenizer) -> dict:
    parent=RESULTS/point;parent.mkdir()
    write_json(parent/'training_binding.json',binding)
    base=reference['base'];known=value_known(base['retention'])
    ref=protocol['references']['base']['retention']
    mask=Path('data/results/ethical_pilot',ref['run_id'],'known_items.jsonl')
    values=collect(measure_id(point,'retention'),point,Path(protocol['bank_path']),'retention',binding,
                   protocol['runtime_reference'],tokenizer,parent,base_known=mask)
    values=[r|{'frozen_assessment':r['native_assessment']} for r in values]
    retention=previous.summarize_values(values,base['retention'],known)
    write_json(parent/'retention_assessment.json',retention)
    for model in ('control','parent'):
        summary,pairs=paired_values(reference[model]['retention'],values,known,kind='retention')
        write_rows(parent/(model+'_retention_pairs.jsonl'),pairs)
        write_json(parent/(model+'_retention_contrast.json'),summary)
    decisions={};all_decisions_complete=True
    for cell in CELLS:
        values=collect(measure_id(point,'decisions_'+cell),point,RCA_GENERATED/(cell+'.jsonl'),'decisions',
                       binding,protocol['runtime_reference'],tokenizer,parent)
        observed=decision_view(values);base_values=decision_view(base['decisions'][cell])
        cohort=previous.decision_known(base_values)
        assessment=previous.compare_decisions(observed,base_values,cohort)
        # Seen cells diagnose learning; their BASE-known accuracy is not an adoption gate.
        all_decisions_complete &= all(r['native_assessment']['normal_stop'] and
            r['native_assessment']['response_boundaries_valid'] and r['native_assessment']['strict_format'] for r in values)
        decisions[cell]=assessment
        write_json(parent/(cell+'_assessment.json'),assessment)
        for model in ('control','parent'):
            summary,pairs=paired_values(decision_view(reference[model]['decisions'][cell]),observed,cohort,kind='decisions')
            write_rows(parent/(model+'_'+cell+'_pairs.jsonl'),pairs)
            write_json(parent/(model+'_'+cell+'_contrast.json'),summary)
    # Performance failures must not suppress full100 readings or later checkpoint measurements.
    previous.full_surface(protocol,binding,parent,identify=lambda phase:eval_id(point,phase))
    status=read(parent/'candidate_measurement_status.json')
    name=status['stance_run_id'];job=load_job(['+run='+name])
    audit=audit_surface(Path('data/results/ethical_pilot')/name,job.pilot_bench,tokenizer,protocol['runtime_reference'])
    write_json(parent/'surface_token_audit.json',audit)
    if not audit['passed']:raise ValueError('Actual full-surface token/runtime identity failed; preserve partials')
    passed=retention['passed'] and decisions['held_eval']['passed'] and all_decisions_complete and surface_passed(status,audit)
    result={'retention':retention,'decisions':decisions,'all_decision_replies_complete_and_strict':bool(all_decisions_complete),
            'surface':status,'surface_audit':audit,'development_passed':bool(passed),'full_failure_review':'pending'}
    write_json(parent/'comparison_v1.json',result)
    return result


def run() -> None:
    from belief_transfer.inference.backend import require_training_backend
    from transformers import AutoTokenizer
    require_training_backend()
    preflight_outputs()
    protocol_path=GENERATED/'protocol.json';protocol=read(protocol_path)
    if protocol.get('launch_allowed') is not True or protocol.get('primary')!='final':raise ValueError('Unfrozen execution contract')
    check_bindings(protocol['source_bindings']);previous.preserved(protocol_path)
    # All frozen data/review/confirmation banks must already be in the verified private snapshot.
    for name in protocol['source_bindings']:
        p=Path(name)
        if p.is_relative_to('data'):previous.preserved(p)
    if config_sha(load_job(['+run='+TRAIN]))!=protocol['jobs'][TRAIN]:raise ValueError('Training configuration changed')
    runtime=protocol['runtime_reference']
    tokenizer=AutoTokenizer.from_pretrained(runtime['model']['pretrained'],revision=runtime['generation']['revision'],local_files_only=True)
    reference=references(protocol,tokenizer)
    RESULTS.mkdir(parents=True);(RESULTS/'STARTED').write_text(previous.commit()+'\n')
    try:
        if not previous.execute([*previous.LOCK,previous.TRAIN_PYTHON,'-u','run.py','+run='+TRAIN],RESULTS,'train'):
            raise RuntimeError('Training technical failure; no automatic restart')
        final=previous.verify_candidate(protocol,tokenizer,train_id=TRAIN)
        train=read(Path('data/results/ethical_stance_sft',TRAIN,'summary.json'))['training']
        parent=read(Path('data/results/ethical_stance_sft',PARENT,'summary.json'))['training']
        verify_schedule(train,parent,protocol['expected_initial_adapter_sha256'])
        write_json(RESULTS/'candidate_training_binding.json',final)
        bindings={'midpoint':checkpoint_binding(Path(protocol['checkpoint_paths']['midpoint']),227,final),
                  'terminal':checkpoint_binding(Path(protocol['checkpoint_paths']['terminal']),454,final),'final':final}
        alias=terminal_alias(bindings['terminal'],final)
        write_json(RESULTS/'checkpoint_identity_v1.json',{'bindings':bindings,'terminal_aliases_final':alias,
            'rule':'Same adapter AND configuration bytes only; shared measurement counted once; final remains primary.'})
        outputs={}
        for point in POINTS:
            check_bindings(protocol['source_bindings'])
            if point=='terminal' and alias:continue
            outputs[point]=measure(point,bindings[point],protocol,reference,tokenizer)
        if alias:outputs['terminal']={'alias_of':'final','binding':bindings['terminal'],
                                      'development_passed':outputs['final']['development_passed']}
        write_json(RESULTS/'comparison_v1.json',{'primary':'final','development_passed':outputs['final']['development_passed'],
            'checkpoints':outputs,'full_response_review':'pending','interpretation':'Final-only endpoint. No checkpoint selection, automatic confirmation or scaling.'})
        (RESULTS/'COLLECTION_COMPLETED').write_text('Training and all distinct saved-checkpoint measurements finished; agent review required.\n')
    except BaseException as exc:
        write_json(RESULTS/'failure.json',{'error':repr(exc)});raise
    finally:
        (RESULTS/'TERMINAL').write_text('Finite trial ended; no restart/resume.\n')


if __name__=='__main__':run()
