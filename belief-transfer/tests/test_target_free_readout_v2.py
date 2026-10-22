"""Error-aware full-surface controller and reconstruction, isolated from study data."""
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import pytest
import yaml

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_target_free_readout_v2 as worker
import analyze_target_free_readout_v2 as analysis
import analyze_target_free_controls as calibration
from run_target_free_modes import run_ids as mode_ids
from belief_transfer import config
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.evals.target_free_readout import fresh_control_bank
from belief_transfer.metrics.measurements import request_sampling_seed,summarize_measurement,summarize_controls
from belief_transfer.stages.measurements import observed_backend_reply,measurement_bank_fingerprint
from belief_transfer.validation.measurements import EXTRACTOR_VERSION
from test_paired_readout import write,write_rows
from test_target_free_readout import bank,groups


def controls():
    fresh=fresh_control_bank()
    return fresh+[{**fresh[0],'presentation_id':f'stress/{i}','control_role':'stress','control_kind':'stress'} for i in range(8)]


def configs(tmp_path,monkeypatch):
    cfg=tmp_path/'configs';shutil.copytree(config.CONFIG_DIR,cfg);monkeypatch.setattr(config,'CONFIG_DIR',cfg)
    return cfg


def test_all_fifteen_configs_use_external_controls_and_original_sampler(tmp_path,monkeypatch):
    cfg=configs(tmp_path,monkeypatch)
    declaration={'path':'fixture/controls.jsonl','sha256':'a'*64,'count':488}
    for arm,seed,run in worker.run_ids():
        write_overlay=worker.overlay(arm,seed,None if arm=='base' else 'fixture/'+arm,declaration)
        (cfg/'run'/(run+'.yaml')).write_text('# @package _global_\n'+yaml.safe_dump(write_overlay))
        j=config.load_job(['+run='+run]);worker.check_config(j,seed)
        assert j.pilot_bench.cuda_generation.presence_penalty is None
        assert j.pilot_bench.measurement_decoding.thinking and j.pilot_bench.max_new_tokens==4096
    assert len(worker.run_ids())==15 and all(run.endswith('_v2') for _,_,run in worker.run_ids())


def test_prior_failures_are_retained_as_evidence_not_a_launch_veto(tmp_path,monkeypatch):
    folder=tmp_path/'results/ethical_pilot'/worker.CONTROLS;folder.mkdir(parents=True)
    (folder/'COMPLETED').write_text('done')
    jobs=[{'model_arm':a,'mode':m,'run_id':r,'arm':a+'_'+m} for a,m,r in mode_ids()]
    models={j['arm']:{'passed':False,'sources':[]} for j in jobs}
    write(folder/'analysis.json',{'complete':True,'pending':[],'qualified_modes':[],'models':models})
    write(tmp_path/'generated/ethical_pilot'/worker.CONTROLS/'protocol.json',{'jobs':jobs})
    calls=[]
    def inspect(root,item,protocol,**kwargs):calls.append(item['arm']);return models[item['arm']]
    monkeypatch.setattr(calibration,'inspect_model',inspect)
    report,_=worker.diagnostic_evidence(tmp_path)
    assert report['qualified_modes']==[] and len(calls)==10
    models['base_thinking']['passed']=True
    with pytest.raises(ValueError,match='reconstruct'):worker.diagnostic_evidence(tmp_path)


def test_controller_continues_performance_failures_but_stops_technical_failure(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);gen=tmp_path/'gen';gen.mkdir();out=tmp_path/'out'
    write(gen/'protocol.json',{'source_bindings':{},'jobs':[{'run_id':r} for r in ['first','second','third']]})
    monkeypatch.setattr(worker,'registered',lambda:(gen,out))
    monkeypatch.setattr(worker,'diagnostic_evidence',lambda:({},{}))
    monkeypatch.setattr(worker.subprocess,'check_output',lambda *a,**kw:'fixture')
    calls=[]
    monkeypatch.setattr(worker.subprocess,'run',lambda cmd,**kw:(calls.append(cmd) or SimpleNamespace(returncode=0)))
    verified=[]
    def verify(root,item,protocol):
        verified.append(item['run_id'])
        if item['run_id']=='second':raise ValueError('TECHNICAL_BACKEND_FAILURE')
        return {'performance_passed':False}
    monkeypatch.setattr(analysis,'verify_child',verify)
    with pytest.raises(ValueError,match='TECHNICAL'):worker.run()
    assert verified==['first','second'] and len(calls)==3
    assert (out/'TERMINAL').exists() and (out/'worker_failure.json').exists() and not (out/'COMPLETED').exists()
    assert len(worker.rows(out/'operations.jsonl'))==2
    with pytest.raises(FileExistsError):worker.run()


def test_prepare_fifteen_configs_binds_control_bytes_and_preselects_review(tmp_path,monkeypatch):
    from belief_transfer.stages import measurements
    cfg=configs(tmp_path,monkeypatch);monkeypatch.chdir(tmp_path)
    cb=controls();natural=bank();proofs={};jobs=[]
    for arm,mode,run in mode_ids():
        j=config.load_job(['+run='+run]);b=j.pilot_bench;digest=None
        if b.adapter_path:
            p=Path(b.adapter_path)/'adapter_model.safetensors';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fixture weights');digest=worker.sha(p)
        proofs[arm+'_'+mode]={'model_config':j.models.models[b.model].model_dump(),'decoder':b.measurement_decoding.model_dump(),
            'generation':b.cuda_generation.model_dump(),'max_new_tokens':b.max_new_tokens,'versions':{},'backend':{}}
        jobs.append({'model_arm':arm,'mode':mode,'arm':arm+'_'+mode,'run_id':run,'adapter_sha256':digest})
    g=Path('data/generated/ethical_pilot')/worker.CONTROLS
    write(g/'protocol.json',{'jobs':jobs,'runtime_evidence':proofs})
    for name in ['bank_thinking.jsonl','bank_nonthinking.jsonl']:write_rows(g/name,[])
    source=Path('data/generated/ethical_pilot/ethics_gpu_scoped_readout_v1')
    write(source/'analysis_groups.json',{'beliefs':groups()});write(source/'original_pilot_plan.json',{'frozen':'fixture'})
    write_rows(Path('data/generated/ethical_pilot/ethics_gpu_presence_controls_v1/bank.jsonl'),[])
    import belief_transfer.evals.target_free_readout as factory
    monkeypatch.setattr(factory,'native_stress_controls',lambda _:cb[-8:])
    def banks(j):
        declared=j.pilot_bench.measurement_control_bank
        actual=worker.rows(declared.path)
        bundle={'version':'fixture','banks':{'stance':fingerprint(natural)},'controls':{'stance':fingerprint(actual)},
            'source_manifest':{'targets_sha':'targets','wordings_sha':'wordings'},
            'external_control_bank':{'sha256':declared.sha256,'count':488}}
        return {'stance':natural},{'stance':actual},bundle
    monkeypatch.setattr(measurements,'prepare',banks)
    monkeypatch.setattr(worker,'token_counts',lambda rs,j:[12]*len(rs))
    monkeypatch.setattr(worker,'diagnostic_evidence',lambda:({'complete':True},{}))
    sha=worker.sha;monkeypatch.setattr(worker,'sha',lambda p:sha(p) if Path(p).exists() else 'a'*64)
    worker.prepare();gen,_=worker.registered();protocol=worker.read(gen/'protocol.json')
    assert protocol['expected_calls']==25320 and len(protocol['jobs'])==15
    assert len(worker.rows(gen/'review_selection.jsonl'))==72
    assert len(worker.rows(gen/'control_bank.jsonl'))==488
    assert str(gen/'control_bank.jsonl') in protocol['source_bindings']
    for item in protocol['jobs']:
        j=config.load_job(['+run='+item['run_id']]);assert config.config_sha(j)==item['resolved_config_sha']
    with pytest.raises(FileExistsError):worker.prepare()


def full_fixture(tmp_path,monkeypatch):
    cfg=configs(tmp_path,monkeypatch);natural=bank();cb=controls();g=groups()
    for i in range(10,16):g[f'b{i}']['analysis_group']='related_untrained'
    generated=tmp_path/'generated/ethical_pilot'/worker.MASTER
    write_rows(generated/'stance_bank.jsonl',natural);write_rows(generated/'control_bank.jsonl',cb)
    write(generated/'analysis_groups.json',{'beliefs':g})
    write_rows(generated/'review_selection.jsonl',worker.review_selection(g,natural))
    write(generated/'token_audit.json',{'lengths':[2]*1688})
    manifest={'version':'fixture','banks':{'stance':fingerprint(natural)},'controls':{'stance':fingerprint(cb)},
        'source_manifest':{'targets_sha':'targets','wordings_sha':'wordings'},
        'external_control_bank':{'sha256':worker.sha(generated/'control_bank.jsonl'),'count':488}}
    digest=measurement_bank_fingerprint(manifest);jobs=[];proofs={}
    declaration={'path':str(generated/'control_bank.jsonl'),'sha256':manifest['external_control_bank']['sha256'],'count':488}
    for arm,seed,run in worker.run_ids():
        adapter=None if arm=='base' else 'fixture/'+arm
        (cfg/'run'/(run+'.yaml')).write_text('# @package _global_\n'+yaml.safe_dump(worker.overlay(arm,seed,adapter,declaration)))
        j=config.load_job(['+run='+run]);b=j.pilot_bench
        proof={'model_config':j.models.models[b.model].model_dump(),'decoder':b.measurement_decoding.model_dump(),
            'generation':b.cuda_generation.model_dump(),'max_new_tokens':b.max_new_tokens,'backend':{},'versions':{}}
        proofs[arm]=proof;item={'arm':arm,'seed':seed,'run_id':run,'adapter_path':adapter,
            'adapter_sha256':None if arm=='base' else 'weight-'+arm,'resolved_config_sha':config.config_sha(j)}
        folder=tmp_path/'results/ethical_pilot'/run;folder.mkdir(parents=True)
        config.write_resolved_config(j,folder);observed=[];control_rows=[]
        for dest,reference in [(observed,natural),(control_rows,cb)]:
            for i,r in enumerate(reference):
                answer=r.get('expected', 'disagree' if arm=='negative' else 'agree')
                word='AB'[r['options'].index(answer)]
                seed_value=request_sampling_seed(r,seed)
                m={'finish_reason':'stop','model_revision':proof['generation']['revision'],
                    'adapter_lora_id':None if arm=='base' else 1,'sampling_seed':seed_value,
                    'execution_versions':{},'execution':proof['generation'],'prompt_tokens':2,
                    'input_token_ids':[1,i],'output_token_ids':[1,2],'generation_tokens':2}
                raw='<think>Fixture.</think>'+word
                if (arm=='offtopic' and seed==7 and i==0 and dest is observed
                    or arm=='c4_only' and seed==42 and i==487 and dest is control_rows):
                    raw='<think>Incomplete';m.update(finish_reason='length',generation_tokens=4096,output_token_ids=[1]*4096)
                dest.append(observed_backend_reply(r,raw,m,thinking=True,seed=seed_value))
        summary={'measurement_bank_sha':digest,'bank_sha':fingerprint(manifest),'extractor_version':EXTRACTOR_VERSION,
            'model_config_sha':fingerprint(proof['model_config']),'backend':{},'adapter':adapter,
            'decoding':{**proof['decoder'],'execution':proof['generation'],'execution_versions':{},'seed':seed,'batch_size':64,'max_new_tokens':4096},
            'measurements':{'stance':summarize_measurement(natural,observed)},
            'meta_eval':{'model_controls':{'stance':summarize_controls(cb,control_rows)}}}
        write(folder/'measurement_summary.json',summary);write(folder/'measurement_manifest.json',manifest)
        for name,rs in [('stance_bank',natural),('stance_control_bank',cb),('stance_observations',observed),('stance_controls',control_rows)]:write_rows(folder/(name+'.jsonl'),rs)
        (folder/'external_control_bank.jsonl').write_bytes((generated/'control_bank.jsonl').read_bytes());jobs.append(item)
    protocol={'jobs':jobs,'measurement_bank_sha':digest,'runtime_evidence':proofs,'evaluation_seeds':worker.SEEDS,'policy_id':worker.POLICY,
        'source_bindings':{str(generated/name):worker.sha(generated/name) for name in ['analysis_groups.json','review_selection.jsonl','stance_bank.jsonl','control_bank.jsonl','token_audit.json']}}
    write(generated/'protocol.json',protocol)
    return generated,protocol


def test_full_raw_analysis_retains_all500_rows_stress_failures_and_precision_bounds(tmp_path,monkeypatch):
    gen,protocol=full_fixture(tmp_path,monkeypatch)
    result=analysis.analyze(tmp_path)
    assert result['complete'] and len(result['models'])==5
    off=result['models']['offtopic'];endpoint=off['seeds']['7']['endpoints']['target']
    assert endpoint['value'] is None and endpoint['precision_passed'] and endpoint['missing']==1
    assert endpoint['conditional_frequency']==1 and endpoint['bound_width']==1/120
    c4=result['models']['c4_only'];assert c4['operational_precision_passed']
    assert not c4['seeds']['42']['model_checks']['stress']['all_correct']
    assert not c4['semantic_review_completed']
    out=tmp_path/'results/ethical_pilot'/worker.MASTER
    belief_rows=worker.rows(out/'per_belief_results.jsonl')
    assert len(belief_rows)==500 and all('precision_passed' not in r for r in belief_rows)
    assert len(worker.rows(out/'natural_review.jsonl'))==72
    assert len(worker.rows(out/'control_failures.jsonl'))==1
    assert 'GENERATION_TOKEN_LIMIT' in worker.rows(out/'control_failures.jsonl')[0]['error_codes']
    assert off['same_prompt']['expected']==3600 and len(result['specificity'])==5
    with pytest.raises(FileExistsError):analysis.analyze(tmp_path)
    item=protocol['jobs'][0];folder=tmp_path/'results/ethical_pilot'/item['run_id']
    p=folder/'stance_controls.jsonl';saved=p.read_bytes();altered=worker.rows(p)
    altered[0]['generation_metadata']['execution']['max_num_seqs']=1;write_rows(p,altered)
    with pytest.raises(ValueError,match='RUNTIME_METADATA'):analysis.verify_child(tmp_path,item,protocol)
    p.write_bytes(saved)
    p=folder/'external_control_bank.jsonl';p.write_bytes(p.read_bytes()+b' ')
    with pytest.raises(ValueError,match='CONTROL_BYTES'):analysis.verify_child(tmp_path,item,protocol)


def test_missing_precision_threshold_is_not_a_point_estimate_or_semantic_guarantee():
    reference=[{**bank()[0],'answer':'agree','error':None} for _ in range(100)]
    changed=[dict(r) for r in reference];changed[0].update(answer=None,error='missing')
    e=analysis.endpoint(changed,reference)
    assert e['precision_passed'] and e['value'] is None and e['bound_width']==.01
    changed[1].update(answer=None,error='missing');e=analysis.endpoint(changed,reference)
    assert not e['precision_passed'] and e['precision_error_codes']==['AGGREGATE_MISSING_BOUND_ABOVE_1PP']
