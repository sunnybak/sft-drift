"""Prospective target-free full100 grid/qualification/controller and raw analysis."""
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_target_free_readout as worker
import analyze_target_free_readout as analysis
import analyze_target_free_controls as calibration
from run_target_free_modes import run_ids as mode_ids
from belief_transfer import config
from belief_transfer.evals.measurements import stance_presentation,stance_model_controls
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.metrics.measurements import summarize_measurement,summarize_controls
from belief_transfer.stages.measurements import measurement_bank_fingerprint
from test_paired_readout import write,write_rows,run_fixture

def bank():
    return [stance_presentation(f'b{b}/w{w}/positive/{o}',f'Practice {b} wording {w} is acceptable.',
        f'It is not the case that practice {b} wording {w} is acceptable.','Fixture scope',
        ['agree','disagree'] if o==0 else ['disagree','agree'],interface='target_free_positions',
        belief_id=f'b{b}',wording_id=f'w{w}',polarity='positive',arrangement=o,frame='neutral',statement='fixture',scope='Fixture scope')
        for b in range(100) for w in range(6) for o in [0,1]]

def groups():return {f'b{i}':{'analysis_group':'target' if i<10 else 'offtopic_eval' if i>=90 else 'other_untrained_ethical'} for i in range(100)}

def test_full_config_composition_and_preselected_review(tmp_path,monkeypatch):
    cfg=tmp_path/'configs';shutil.copytree(config.CONFIG_DIR,cfg);monkeypatch.setattr(config,'CONFIG_DIR',cfg)
    import yaml
    for arm,seed,run in worker.run_ids():
        (cfg/'run'/(run+'.yaml')).write_text('# @package _global_\n'+yaml.safe_dump(worker.overlay(arm,seed,None if arm=='base' else 'fixture/'+arm)))
        job=config.load_job(['+run='+run]);worker.check_config(job,seed)
        assert job.pilot_bench.measurement_decoding.thinking and job.pilot_bench.measurement_batch_size==64
        with pytest.raises(ValueError):worker.check_config(job.model_copy(update={'pilot_bench':job.pilot_bench.model_copy(update={'stance_interface':'explicit_positions'})}),seed)
    selection=worker.review_selection(groups(),bank());assert len(selection)==72
    assert selection==worker.review_selection(dict(reversed(list(groups().items()))),list(reversed(bank()))) or sorted(selection,key=str)==sorted(worker.review_selection(dict(reversed(list(groups().items()))),list(reversed(bank()))),key=str)
    assert len({r['belief_id'] for r in selection})==6 and sum(r['seed']==7 for r in selection)==12

def test_qualification_reconstructs_every_thinking_model_and_refuses_tampering(tmp_path,monkeypatch):
    folder=tmp_path/'results/ethical_pilot'/worker.CONTROLS;folder.mkdir(parents=True);(folder/'COMPLETED').write_text('done')
    jobs=[{'model_arm':a,'mode':m,'run_id':r,'arm':a+'_'+m} for a,m,r in mode_ids()]
    models={j['arm']:{'passed':j['mode']=='thinking','sources':[]} for j in jobs}
    report={'complete':True,'pending':[],'qualified_modes':['thinking'],'models':models}
    write(folder/'analysis.json',report);write(tmp_path/'generated/ethical_pilot'/worker.CONTROLS/'protocol.json',{'jobs':jobs})
    calls=[]
    def inspect(root,item,p,**kw):calls.append(item['arm']);return models[item['arm']]
    monkeypatch.setattr(calibration,'inspect_model',inspect)
    worker.qualification(tmp_path);assert len(calls)==5 and all(a.endswith('_thinking') for a in calls)
    models['offtopic_thinking']['passed']=False
    with pytest.raises(ValueError,match='reconstruct'):worker.qualification(tmp_path)

def test_controller_preserves_execution_failure_and_refuses_restart(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);gen=tmp_path/'gen';gen.mkdir();out=tmp_path/'out'
    write(gen/'protocol.json',{'source_bindings':{},'jobs':[{'run_id':'first'},{'run_id':'second'},{'run_id':'third'}]})
    monkeypatch.setattr(worker,'registered',lambda:(gen,out));monkeypatch.setattr(worker,'qualification',lambda:None)
    monkeypatch.setattr(worker.subprocess,'check_output',lambda *a,**k:'fixture')
    calls=[]
    def run(cmd,**kw):calls.append(cmd);return SimpleNamespace(returncode=2 if '+run=second' in cmd else 0)
    monkeypatch.setattr(worker.subprocess,'run',run)
    with pytest.raises(RuntimeError):worker.run()
    assert (out/'worker_failure.json').exists() and (out/'TERMINAL').exists() and not (out/'COMPLETED').exists()
    assert len(calls)==3 and [r['returncode'] for r in worker.rows(out/'operations.jsonl')]==[0,2]
    with pytest.raises(FileExistsError):worker.run()

def test_prepare_builds_fifteen_typed_jobs_with_frozen_shared_inputs_in_tmpdirs(tmp_path,monkeypatch):
    from belief_transfer.stages import measurements
    cfg=tmp_path/'configs';shutil.copytree(config.CONFIG_DIR,cfg);monkeypatch.setattr(config,'CONFIG_DIR',cfg);monkeypatch.chdir(tmp_path)
    for _,_,run in worker.run_ids():(cfg/'run'/(run+'.yaml')).unlink(missing_ok=True)
    proofs={};jobs=[]
    for arm,mode,run in mode_ids():
        j=config.load_job(['+run='+run]);b=j.pilot_bench;digest=None
        if b.adapter_path:
            p=Path(b.adapter_path)/'adapter_model.safetensors';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fixture weights, not loaded');digest=worker.sha(p)
        proofs[arm+'_'+mode]={'model_config':j.models.models[b.model].model_dump(),'decoder':b.measurement_decoding.model_dump(),
            'generation':b.cuda_generation.model_dump(),'max_new_tokens':b.max_new_tokens,'versions':{},'backend':{}}
        jobs.append({'model_arm':arm,'mode':mode,'arm':arm+'_'+mode,'run_id':run,'adapter_sha256':digest})
    g=Path('data/generated/ethical_pilot')/worker.CONTROLS
    write(g/'protocol.json',{'jobs':jobs,'runtime_evidence':proofs});write_rows(g/'bank_thinking.jsonl',[]);write_rows(g/'bank_nonthinking.jsonl',[])
    source=Path('data/generated/ethical_pilot/ethics_gpu_scoped_readout_v1')
    write(source/'analysis_groups.json',{'beliefs':groups()});write(source/'original_pilot_plan.json',{'frozen':'fixture'})
    natural=bank();controls=stance_model_controls('target_free_positions')
    manifest={'version':'fixture','banks':{'stance':fingerprint(natural)},'controls':{'stance':fingerprint(controls)},
        'source_manifest':{'targets_sha':'targets','wordings_sha':'wordings'}}
    monkeypatch.setattr(measurements,'prepare',lambda j:({'stance':natural},{'stance':controls},manifest))
    monkeypatch.setattr(worker,'token_counts',lambda rs,j:[12]*len(rs));monkeypatch.setattr(worker,'qualification',lambda:({'complete':True},{}))
    sha=worker.sha;monkeypatch.setattr(worker,'sha',lambda p:sha(p) if Path(p).exists() else 'a'*64)
    worker.prepare();gen,_=worker.registered();p=worker.read(gen/'protocol.json')
    assert p['expected_calls']==18480 and len(p['jobs'])==15 and len(worker.rows(gen/'review_selection.jsonl'))==72
    for item in p['jobs']:
        j=config.load_job(['+run='+item['run_id']]);assert config.config_sha(j)==item['resolved_config_sha']
    with pytest.raises(FileExistsError):worker.prepare()

def test_full_raw_analysis_retains_all_beliefs_missing_bounds_and_checks(tmp_path):
    natural=bank();controls=stance_model_controls('target_free_positions');g=groups()
    generated=tmp_path/'generated/ethical_pilot'/worker.MASTER;generated.mkdir(parents=True)
    write_rows(generated/'stance_bank.jsonl',natural);write_rows(generated/'control_bank.jsonl',controls)
    write(generated/'analysis_groups.json',{'beliefs':g});write_rows(generated/'review_selection.jsonl',worker.review_selection(g,natural))
    manifest={'version':'fixture','banks':{'stance':fingerprint(natural)},'controls':{'stance':fingerprint(controls)},
              'source_manifest':{'targets_sha':'targets','wordings_sha':'wordings'}}
    digest=measurement_bank_fingerprint(manifest)
    proof={'model_config':{},'backend':{},'decoder':{'thinking':True,'temperature':.6},'generation':{'revision':'pinned'},'max_new_tokens':4096,'versions':{}}
    jobs=[]
    for arm,seed,run in worker.run_ids():
        item,_,_,_=run_fixture(tmp_path,arm,seed,natural,controls,proof,missing=arm=='offtopic' and seed==7,manifest=manifest)
        old=tmp_path/'results/ethical_pilot'/item['run_id'];folder=old.with_name(run);old.rename(folder);item['run_id']=run
        p=folder/'measurement_summary.json';summary=json.loads(p.read_text());summary['measurement_bank_sha']=digest;summary['decoding']['batch_size']=64
        # Existing fixture creates valid shared-extractor observations; rebuild native metrics under new interface.
        summary['measurements']['stance']=summarize_measurement(natural,worker.rows(folder/'stance_observations.jsonl'))
        summary['meta_eval']['model_controls']['stance']=summarize_controls(controls,worker.rows(folder/'stance_controls.jsonl'))
        write(p,summary);jobs.append(item)
    write(generated/'protocol.json',{'jobs':jobs,'evaluation_seeds':worker.SEEDS,'measurement_bank_sha':digest,'runtime_evidence':{a:proof for a in worker.ARMS}})
    result=analysis.analyze(tmp_path);assert result['complete'] and len(result['models'])==5
    rows=worker.rows(tmp_path/'results/ethical_pilot'/worker.MASTER/'per_belief_results.jsonl');assert len(rows)==500
    off=result['models']['offtopic']['pooled_completed_seeds']['all'];assert off['missing']==1 and off['value'] is None
    assert result['models']['base']['same_prompt']['expected']==3600
    assert result['models']['base']['seeds']['42']['agreement']['order']['expected']==600
    assert result['models']['base']['seeds']['42']['agreement']['wording']['expected']==3000
    assert len(result['treatment_minus_control'])==12 and result['models']['base']['seeds']['42']['controls_passed']
    out=tmp_path/'results/ethical_pilot'/worker.MASTER;assert len(worker.rows(out/'natural_review.jsonl'))==72
    assert not worker.rows(out/'control_failures.jsonl') and not json.loads((out/'review_status.json').read_text())['agent_review_completed']
    with pytest.raises(FileExistsError):analysis.analyze(tmp_path)
