"""Forward policy and identity guards; no weights or real experimental writes."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest
from belief_transfer.config import load_job
from belief_transfer.evals.scope_controls import build_bank
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
def module(name):
    spec=importlib.util.spec_from_file_location(name+'_fixture',SCRIPTS/(name+'.py'))
    m=importlib.util.module_from_spec(spec);sys.path.insert(0,str(SCRIPTS))
    try:spec.loader.exec_module(m)
    finally:sys.path.remove(str(SCRIPTS))
    return m

def job():
    j=load_job(['+run=ethics_gpu_vllm_base_v1'])
    return j.model_copy(update={'pilot_bench':j.pilot_bench.model_copy(update={'stance_validation_run_id':None,
        'measurement_controls_source_run_id':None,'measurement_control_failure_policy':'collect_unqualified'})})

def scope_fixture(tmp_path,j):
    w=module('run_scoped_readout');folder=tmp_path/'scope';folder.mkdir()
    bank=build_bank();text=''.join(json.dumps(r)+'\n' for r in bank);(folder/'bank.jsonl').write_text(text)
    observed=[{**r,'answer':r['expected_word'],'correct':True,'strict_format':True,'error':None,'final_response':r['expected_word']} for r in bank]
    (folder/'observations.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in observed))
    b=j.pilot_bench
    manifest={'model_label':'base','model_config':j.models.models[b.model].model_dump(),'decoder':b.measurement_decoding.model_dump(),
      'max_new_tokens':b.max_new_tokens,'generation':b.cuda_generation.model_dump(),'adapter_sha256':None,
      'bank_sha256':w.sha(folder/'bank.jsonl'),'backend':{'backend':'fixture'},'versions':{'fixture':'1'}}
    (folder/'manifest.json').write_text(json.dumps(manifest));(folder/'summary.json').write_text('{}');(folder/'COMPLETED').write_text('collected')
    return w,folder,manifest,observed

def test_full_surface_config_and_evidence_identity(tmp_path):
    j=job();w,folder,manifest,_=scope_fixture(tmp_path,j);w.check_config(j)
    proof=w.evidence(j,folder,'base');assert proof['scoped_passed']
    with pytest.raises(ValueError,match='full frozen surface'):
        w.check_config(j.model_copy(update={'pilot_bench':j.pilot_bench.model_copy(update={'targets':j.pilot_bench.targets[:-1]})}))
    manifest['decoder']['temperature']=0;(folder/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='decoder'):w.evidence(j,folder,'base')

def test_failed_scope_performance_is_recorded_without_erasing_jobs(tmp_path):
    j=job();w,folder,_,observed=scope_fixture(tmp_path,j)
    observed[0].update(answer=None,correct=False,strict_format=False,error='fixture failed response')
    (folder/'observations.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in observed))
    proof=w.evidence(j,folder,'base')
    assert not proof['scoped_passed'] and len(w.run_ids())==5
    assert proof['splits']['development']['counts']['expected']==384

def test_changed_adapter_and_runtime_fail_before_inference(tmp_path):
    j=job();w,folder,_,_=scope_fixture(tmp_path,j);adapter=tmp_path/'adapter';adapter.mkdir()
    (adapter/'adapter_model.safetensors').write_text('fixture weights')
    other=j.model_copy(update={'pilot_bench':j.pilot_bench.model_copy(update={'adapter_path':str(adapter)})})
    with pytest.raises(ValueError,match='weight mismatch'):w.evidence(other,folder,'base')
    proof={'backend':{'backend':'cuda'},'versions':{'vllm':'pinned'}}
    w.validate_runtime(proof,proof['backend'],proof['versions'])
    with pytest.raises(ValueError,match='versions'):w.validate_runtime(proof,proof['backend'],{'vllm':'changed'})

def setup_worker(tmp_path,monkeypatch):
    w=module('run_scoped_readout');monkeypatch.chdir(tmp_path)
    paths=[f'{p}/ethical_pilot/{w.MASTER}' for p in ['generated','results']]+[f'results/ethical_pilot/{r}' for _,_,r in w.run_ids()]
    p=Path('configs/handoff.json');p.parent.mkdir();p.write_text(json.dumps({'include_paths':paths}))
    gen,result=w.registered();gen.mkdir(parents=True);return w,gen,result

def test_started_and_changed_workers_refuse_before_subprocess(tmp_path,monkeypatch):
    w,gen,result=setup_worker(tmp_path,monkeypatch)
    (gen/'protocol.json').write_text(json.dumps({'source_bindings':{}}));result.mkdir(parents=True)
    monkeypatch.setattr(w.subprocess,'run',lambda *a,**kw:pytest.fail('No inference allowed'))
    with pytest.raises(FileExistsError):w.run()
    result.rmdir();Path('input.txt').write_text('changed');(gen/'protocol.json').write_text(json.dumps({'source_bindings':{'input.txt':'0'*64}}))
    with pytest.raises(ValueError,match='changed'):w.run()
    assert not result.exists()

def test_partial_worker_failure_preserves_operations_and_does_not_retry(tmp_path,monkeypatch):
    w,gen,result=setup_worker(tmp_path,monkeypatch)
    (gen/'protocol.json').write_text(json.dumps({'source_bindings':{},'jobs':[{'run_id':'fixture','arm':'base'}]}))
    calls=[]
    def run(command,**kw):
        calls.append(command);return SimpleNamespace(returncode=0 if command[-1]=='check-runtime' else 1)
    monkeypatch.setattr(w.subprocess,'run',run);monkeypatch.setattr(w.subprocess,'check_output',lambda *a,**kw:'fixture')
    with pytest.raises(RuntimeError,match='child failed'):w.run()
    assert len(calls)==2 and (result/'worker_failure.json').exists() and (result/'TERMINAL').exists()
    assert len((result/'operations.jsonl').read_text().splitlines())==1 and (result/'operations.md').exists()
    with pytest.raises(FileExistsError):w.run()

def test_endpoint_bounds_keep_missing_answers_and_qualify_each_group():
    m=module('analyze_scoped_readout')
    b=[{'polarity':'positive','answer':'agree'},{'polarity':'negative','answer':'disagree'}]
    a=[b[0],{'polarity':'negative','answer':None,'error':'incomplete'}]
    r=m.endpoint(a,b,True,True)
    assert r['value'] is None and r['lower']==.5 and r['upper']==1 and not r['eligible_under_forward_policy']
    assert 'ENDPOINT_COVERAGE_BELOW_99PCT' in r['eligibility_codes']
    q=m.endpoint(b,b,False,True);assert not q['eligible_under_forward_policy'] and q['value']==1

def test_collected_identity_checks_include_request_rng_and_runtime():
    m=module('analyze_scoped_readout')
    proof={'model_config':{'pretrained':'fixture'},'backend':{'backend':'cuda'},'decoder':{'thinking':True,'temperature':.6},
           'max_new_tokens':4096,'generation':{'revision':'fixed','engine':'vllm'},'versions':{'vllm':'pinned'}}
    summary={'measurement_bank_sha':m.BANK_SHA,'model_config_sha':m.fingerprint(proof['model_config']),
      'backend':proof['backend'],'decoding':{**proof['decoder'],'max_new_tokens':4096,'execution':proof['generation'],
       'execution_versions':proof['versions'],'seed':42,'batch_size':256}}
    row={'prompt_sha':'0'*64,'generation_metadata':{'adapter_lora_id':None,'model_revision':'fixed',
         'sampling_seed':42,'execution_versions':proof['versions']}}
    m.validate_child(summary,[row],proof,None)
    row['generation_metadata']['sampling_seed']=43
    with pytest.raises(ValueError,match='Unverified request'):m.validate_child(summary,[row],proof,None)

def test_prepared_five_configs_keep_the_full_bank_and_evidence_links():
    w=module('run_scoped_readout')
    for arm,_,run in w.run_ids():
        j=load_job(['+run='+run]);w.check_config(j)
        assert f'ethics_gpu_scope_control_{arm}_v1' in j.related_runs
        assert (j.pilot_bench.adapter_path is None)==(arm=='base')

def test_runtime_preflight_checks_resolved_config_and_bank_before_weights(tmp_path,monkeypatch):
    from belief_transfer import config
    from belief_transfer.inference import backend
    from belief_transfer.stages import measurements
    w=module('run_scoped_readout');j=job();gen=tmp_path/'generated';gen.mkdir()
    proof={'backend':{'backend':'fixture'},'versions':{p:'fixture' for p in ['torch','transformers','vllm']}}
    (gen/'scope_evidence.json').write_text(json.dumps({'base':proof}))
    p={'jobs':[{'arm':'base','run_id':'fixture','resolved_config_sha':config.config_sha(j)}]}
    (gen/'protocol.json').write_text(json.dumps(p))
    monkeypatch.setattr(w,'registered',lambda:(gen,tmp_path/'results'))
    monkeypatch.setattr(w,'version',lambda p:'fixture')
    monkeypatch.setattr(config,'load_job',lambda *a,**kw:j)
    monkeypatch.setattr(backend,'backend_info',lambda **kw:SimpleNamespace(model_dump=lambda:proof['backend']))
    monkeypatch.setattr(measurements,'prepare',lambda j:({'stance':[None]*2400},{'stance':[None]*32},{}))
    monkeypatch.setattr(measurements,'measurement_bank_fingerprint',lambda b:w.BANK_SHA)
    w.check_runtime()
    monkeypatch.setattr(measurements,'measurement_bank_fingerprint',lambda b:'changed')
    with pytest.raises(ValueError,match='frozen instrument'):w.check_runtime()
    p['jobs'][0]['resolved_config_sha']='changed';(gen/'protocol.json').write_text(json.dumps(p))
    with pytest.raises(ValueError,match='Resolved config'):w.check_runtime()

def test_full_analysis_keeps_all_beliefs_and_missing_bounds(tmp_path):
    from belief_transfer.metrics.measurements import summarize_measurement
    m=module('analyze_scoped_readout');gen=tmp_path/'generated/ethical_pilot'/m.MASTER;gen.mkdir(parents=True)
    groups={f'b{i}':{'analysis_group':'target' if i<10 else 'related_untrained' if i<16 else 'other_untrained_ethical' if i<90 else 'offtopic_eval'} for i in range(100)}
    (gen/'analysis_groups.json').write_text(json.dumps({'beliefs':groups}))
    jobs=[{'arm':a,'run_id':a,'adapter_sha256':None if a=='base' else 'fixture'} for a in ['base','positive','negative']]
    (gen/'protocol.json').write_text(json.dumps({'jobs':jobs}));proofs={}
    bank=[]
    for bid in groups:
        for w in range(6):
            for polarity in ['positive','negative']:
                for arrangement in [0,1]:
                    identity=f'{bid}/{w}/{polarity}/{arrangement}'
                    bank.append({'presentation_id':identity,'belief_id':bid,'wording_id':f'w{w}','polarity':polarity,
                        'arrangement':arrangement,'measurement':'stance','frame':'neutral','options':['agree','disagree'],
                        'prompt':identity,'prompt_sha':'0'*64})
    for item in jobs:
        arm=item['arm'];proof={'model_config':{'pretrained':'fixture'},'backend':{'backend':'fixture'},
            'decoder':{'thinking':True,'temperature':.6},'max_new_tokens':4096,'generation':{'revision':'fixed','engine':'vllm'},
            'versions':{'vllm':'fixed'},'scoped_passed':True,'source_run_id':'scope_'+arm}
        proofs[arm]=proof;observed=[]
        for i,r in enumerate(bank):
            answer='agree' if arm=='base' else ('agree' if (r['polarity']=='positive')==(arm=='positive') else 'disagree')
            observed.append({**r,'answer':answer,'strict_format':True,'error':None,'generation_metadata':{
                'adapter_lora_id':None if arm=='base' else 1,'model_revision':'fixed','sampling_seed':42,
                'execution_versions':proof['versions'],'input_token_ids':[1,i]}})
        if arm=='positive':observed[0].update(answer=None,error='incomplete',strict_format=False)
        summary={'measurement_bank_sha':m.BANK_SHA,'model_config_sha':m.fingerprint(proof['model_config']),
            'backend':proof['backend'],'decoding':{**proof['decoder'],'max_new_tokens':4096,'execution':proof['generation'],
                'execution_versions':proof['versions'],'seed':42,'batch_size':256},
            'measurements':{'stance':summarize_measurement(bank,observed)},'meta_eval':{'model_controls':{'fixture':'retained'}}}
        folder=tmp_path/'results/ethical_pilot'/arm;folder.mkdir(parents=True)
        (folder/'measurement_summary.json').write_text(json.dumps(summary));(folder/'measurement_manifest.json').write_text('{}')
        for name,values in [('stance_bank',bank),('stance_observations',observed),('stance_controls',[{}]*32)]:
            (folder/(name+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in values))
    (gen/'scope_evidence.json').write_text(json.dumps(proofs))
    report=m.analyze(tmp_path);assert report['complete']
    cell=report['models']['positive']['endpoints']['target']
    assert cell['eligible_under_forward_policy'] and cell['value'] is None and cell['missing']==1
    contrast=report['positive_minus_negative_target_drift']
    assert contrast['value'] is None and contrast['lower']==pytest.approx(239/240) and contrast['upper']==1
    out=tmp_path/'results/ethical_pilot'/m.MASTER/'per_belief_results.jsonl'
    assert len(out.read_text().splitlines())==300 and out.with_suffix('.md').exists()
    with pytest.raises(FileExistsError):m.analyze(tmp_path)
