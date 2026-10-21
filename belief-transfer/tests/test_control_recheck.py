import json
from pathlib import Path
import pytest
from belief_transfer.config import load_job
from belief_transfer.evals.control_recheck import build_bank
from belief_transfer.metrics.control_recheck import summarize
from belief_transfer.stages.control_recheck import start_directory

def correct(bank):return [{**r,'answer':r['expected'],'strict_format':True} for r in bank]

def test_balanced_bank_and_sampling_noise_design():
    rows=build_bank([42,7,1729]);assert len(rows)==672
    assert len({r['presentation_id'] for r in rows})==672
    assert sum(r['expected']=='agree' for r in rows)==336
    plain=next(r for r in rows if r.get('variant')=='plain')
    group=[r for r in rows if r.get('pair_id')==plain['pair_id'] and r['audit_seed']==plain['audit_seed']]
    note=next(r for r in group if r['variant']=='note');repeat=next(r for r in group if r['variant']=='repeat')
    assert note['sampling_seed']==plain['sampling_seed']!=repeat['sampling_seed']
    assert plain['prompt']==repeat['prompt']!=note['prompt']
    with pytest.raises(ValueError):build_bank([42,42])

def test_summary_keeps_real_failures_and_noise_separate():
    rows=correct(build_bank([42,7,1729]));assert summarize(rows)['expanded_passed']
    targets=[r for r in rows if r.get('variant')=='note' and r['audit_form']=='truth_explicit'][:6]
    for r in targets:r['answer']='agree' if r['expected']=='disagree' else 'disagree'
    result=summarize(rows);assert not result['expanded_passed']
    assert result['forms']['truth_explicit']['note_comparison']['flips']==6
    assert result['forms']['truth_explicit']['repeat_noise']['flips']==0
    rows[0].update(answer=None,error='truncated',strict_format=False)
    assert not summarize(rows)['forms']['legacy']['passed']

def test_default_identity_and_fresh_directory(tmp_path):
    job=load_job(['+run=ethics_gpu_vllm_base_v1'])
    assert 'measurement_control_failure_policy' not in job.pilot_bench.model_dump()
    assert 'control_recheck' not in job.model_dump()
    assert job.pilot_bench.measurement_control_failure_policy=='skip'
    folder=tmp_path/'data/results'/job.experiment.id/job.run_id
    folder.mkdir(parents=True);(folder/'.hydra').mkdir();(folder/'run.log').touch()
    directory=start_directory(tmp_path,job);assert (directory/'STARTED').exists()
    with pytest.raises(FileExistsError):start_directory(tmp_path,job)

def test_stage_preserves_partial_batch_failure(tmp_path,monkeypatch):
    import asyncio
    from types import SimpleNamespace
    from belief_transfer.stages import control_recheck as stage
    from belief_transfer.schemas import ControlRecheckSpec
    job=load_job(['+run=ethics_gpu_control_recheck_base_v1'])
    bank=build_bank([42])
    job=job.model_copy(update={'control_recheck':ControlRecheckSpec(model_label='fixture',seeds=[42]),'pilot_bench':job.pilot_bench.model_copy(update={'measurement_batch_size':128})})
    calls=[]
    class Fake:
        def generate_batch_with_metadata(self,prompts,**kw):
            calls.append(prompts)
            if len(calls)==2:raise RuntimeError('simulated backend failure')
            return [('<think>fixture</think>\n'+('endorse' if bank[i]['expected']=='agree' else 'reject'),{'finish_reason':'stop'}) for i in range(len(prompts))]
    monkeypatch.setattr(stage,'ROOT',tmp_path)
    monkeypatch.setattr(stage,'require_training_backend',lambda:None)
    monkeypatch.setattr(stage,'backend_info',lambda **kw:SimpleNamespace(model_dump=lambda:{}))
    monkeypatch.setattr(stage,'local_model',lambda *a,**kw:Fake())
    monkeypatch.setattr(stage,'write_result',lambda r:None)
    result=asyncio.run(stage.run(job))
    p=tmp_path/'data/results'/job.experiment.id/job.run_id
    saved=[json.loads(l) for l in (p/'observations.jsonl').read_text().splitlines()]
    assert len(saved)==224 and sum(r.get('error') is not None for r in saved)==96
    assert (p/'observations.md').exists() and not result.metrics['expanded_passed']
    with pytest.raises(FileExistsError):asyncio.run(stage.run(job))

@pytest.mark.parametrize('policy,collect',[('skip',False),('collect_unqualified',True)])
def test_failing_controls_do_not_suppress_opted_in_measurement(tmp_path,monkeypatch,policy,collect):
    import asyncio
    from test_pilot import sample
    from belief_transfer.evals.measurements import build_measurement_banks,stance_model_controls
    from belief_transfer.evals.pilot import fingerprint
    from belief_transfer.stages import measurements as stage
    spec,wordings=sample()
    job=load_job(['+run=ethics_gpu_vllm_base_v1'])
    bench=job.pilot_bench.model_copy(update={'targets':spec.targets,'measurement_control_failure_policy':policy,'cuda_generation':None})
    job=job.model_copy(update={'pilot_bench':bench})
    banks=build_measurement_banks(bench,wordings);controls={'stance':stance_model_controls('named_endorse_reject')}
    manifest={'targets_sha':'fixture','wordings_sha':'fixture'}
    bundle={'version':'fixture','source_bank_run_id':'fixture','source_manifest':manifest,'meta_eval':{},'banks':{'stance':fingerprint(banks['stance'])},'controls':{'stance':fingerprint(controls['stance'])},'stance_validation':{'thresholds':{}}}
    class Fake:
        def generate_batch_with_metadata(self,prompts,**kwargs):
            return [('<think>fixture</think>\nendorse',{'finish_reason':'stop'}) for p in prompts]
    monkeypatch.setattr(stage,'ROOT',tmp_path)
    monkeypatch.setattr(stage,'prepare',lambda j:(banks,controls,bundle))
    monkeypatch.setattr(stage,'start',lambda *a:(tmp_path,[]))
    monkeypatch.setattr(stage,'local_model',lambda *a,**kw:Fake())
    monkeypatch.setattr(stage,'summarize_stance_study',lambda *a,**kw:{'controls':{'checks':{'accuracy':False}},'passed':False,'qualification_basis':'fixture'})
    monkeypatch.setattr(stage,'write_measurement_report',lambda *a,**kw:[])
    monkeypatch.setattr(stage,'finish',lambda j,summary,artifacts:summary)
    result=asyncio.run(stage.run(job))
    count=len((tmp_path/'stance_observations.jsonl').read_text().splitlines())
    assert count==(len(banks['stance']) if collect else 0)
    assert not result['meta_eval']['stance_operational_qualification']['passed']
