"""No model calls: parent preservation, typed configs, technical stops and raw replay."""
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import pytest
import yaml

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_scope_fact_clarity as worker
import analyze_scope_fact_clarity as analysis
from build_scope_fact_clarity import build_bank
from run_target_free_readout_v2 import run_ids as parent_ids
from belief_transfer import config
from belief_transfer.evals.target_free_readout import fresh_control_bank
from belief_transfer.metrics.response_interface_rca import summarize
from belief_transfer.validation.response_interface_rca import assess
from test_paired_readout import write,write_rows


def test_parent_requires_complete_analyzed_and_privately_preserved_grid(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    write(Path('configs/handoff.json'),{'repo_id':'fixture-private'})
    with pytest.raises(ValueError,match='Complete, copy'):worker.parent_preservation()
    result=Path('data/results/ethical_pilot')/worker.PARENT
    for name in ['COMPLETED','TERMINAL','operations.jsonl','cuda_worker.log']:
        p=result/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture')
    write(result/'analysis.json',{'complete':True,'pending':[],'models':dict.fromkeys(worker.ARMS,{})})
    jobs=[{'arm':a,'seed':s,'run_id':r} for a,s,r in parent_ids()]
    write(Path('data/generated/ethical_pilot')/worker.PARENT/'protocol.json',{'jobs':jobs})
    for item in jobs:
        folder=Path('data/results/ethical_pilot')/item['run_id']
        for name in ['config.resolved.yaml','measurement_summary.json','measurement_manifest.json','stance_bank.jsonl','stance_control_bank.jsonl','external_control_bank.jsonl','stance_observations.jsonl','stance_controls.jsonl']:
            p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture')
    files={str(p.relative_to('data')):{'sha256':worker.sha(p)} for p in Path('data/results').rglob('*') if p.is_file()}
    write(Path('data/.handoff-receipt.json'),{'repo_id':'fixture-private','revision':'verified-fixture','manifest':{'code_commit':'fixture','files':files}})
    proof,parent=worker.parent_preservation();assert len(parent['jobs'])==15 and len(proof['verified_parent_files'])==125
    (result/'cuda_worker.log').write_text('changed')
    with pytest.raises(ValueError,match='not preserved'):worker.parent_preservation()


def test_prepare_refuses_live_parent_before_any_output_mutation(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);gen=tmp_path/'new-generated';out=tmp_path/'new-results'
    monkeypatch.setattr(worker,'registered',lambda:(gen,out))
    with pytest.raises(ValueError,match='Complete, copy'):worker.prepare()
    assert not gen.exists() and not out.exists()


def test_prepare_composes_five_pinned_control_only_jobs_in_tmpdirs(tmp_path,monkeypatch):
    cfg=tmp_path/'configs';shutil.copytree(config.CONFIG_DIR,cfg);monkeypatch.setattr(config,'CONFIG_DIR',cfg);monkeypatch.chdir(tmp_path)
    parent={'runtime_evidence':{},'jobs':[]};adapters={}
    for arm in worker.ARMS:
        j=config.load_job(['+run=ethics_gpu_scope_control_'+arm+'_v1']);b=j.pilot_bench
        parent['runtime_evidence'][arm]={'model_config':j.models.models[b.model].model_dump(),'decoder':b.measurement_decoding.model_dump(),
            'generation':b.cuda_generation.model_dump(),'max_new_tokens':b.max_new_tokens,'backend':{},'versions':{}}
        digest=None
        if b.adapter_path:
            folder=Path(b.adapter_path);folder.mkdir(parents=True,exist_ok=True)
            (folder/'adapter_model.safetensors').write_bytes(b'fixture-not-weights');digest=worker.sha(folder/'adapter_model.safetensors')
            p=folder/'adapter_config.json';p.write_text('{}');adapters[str(p)]=worker.sha(p)
        parent['jobs'].append({'arm':arm,'adapter_sha256':digest})
    gen_parent=Path('data/generated/ethical_pilot')/worker.PARENT
    write_rows(gen_parent/'control_bank.jsonl',fresh_control_bank());write(gen_parent/'launch_receipt.json',{'adapter_config_hashes':adapters})
    monkeypatch.setattr(worker,'parent_preservation',lambda:({'revision':'fixture-parent'},parent))
    monkeypatch.setattr(worker,'token_counts',lambda bank,j:[20]*len(bank))
    sha=worker.sha;monkeypatch.setattr(worker,'sha',lambda p:sha(p) if Path(p).exists() else 'a'*64)
    worker.prepare();generated,_=worker.registered();p=worker.read(generated/'protocol.json')
    assert p['expected_calls']==640 and len(p['jobs'])==5 and len(worker.rows(generated/'bank.jsonl'))==128
    for item in p['jobs']:
        j=config.load_job(['+run='+item['run_id']]);worker.check_config(j,parent['runtime_evidence'][item['arm']])
        assert config.config_sha(j)==item['resolved_config_sha'] and j.response_interface_rca.expected_rows==128
    with pytest.raises(FileExistsError):worker.prepare()


def test_worker_preserves_boundary_and_never_retries_technical_failure(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);g=tmp_path/'gen';g.mkdir();out=tmp_path/'out'
    write(g/'protocol.json',{'source_bindings':{},'jobs':[{'run_id':x} for x in ['first','second','third']]})
    parent=Path('data/results/ethical_pilot')/worker.PARENT;parent.mkdir(parents=True)
    for name in ['COMPLETED','TERMINAL']:(parent/name).write_text('done')
    monkeypatch.setattr(worker,'registered',lambda:(g,out))
    monkeypatch.setattr(worker.subprocess,'check_output',lambda *a,**kw:'fixture')
    calls=[];monkeypatch.setattr(worker.subprocess,'run',lambda cmd,**kw:(calls.append(cmd) or SimpleNamespace(returncode=0)))
    inspected=[]
    def inspect(root,item,protocol):
        inspected.append(item['run_id'])
        if item['run_id']=='second':raise ValueError('raw metadata changed')
    monkeypatch.setattr(analysis,'inspect_model',inspect)
    with pytest.raises(ValueError,match='metadata'):worker.run()
    assert inspected==['first','second'] and len(calls)==3
    assert (out/'TERMINAL').exists() and (out/'worker_failure.json').exists() and not (out/'COMPLETED').exists()
    assert len(worker.rows(out/'operations.jsonl'))==2
    with pytest.raises(FileExistsError):worker.run()


def full_fixture(tmp_path,monkeypatch):
    cfg=tmp_path/'configs';shutil.copytree(config.CONFIG_DIR,cfg);monkeypatch.setattr(config,'CONFIG_DIR',cfg)
    generated=tmp_path/'generated/ethical_pilot'/worker.MASTER
    bank=build_bank(fresh_control_bank(),source_sha256='a'*64)
    for row in bank:row['expected_input_tokens']=2
    write_rows(generated/'bank.jsonl',bank);digest=worker.sha(generated/'bank.jsonl');jobs=[];proofs={}
    out=tmp_path/'results/ethical_pilot'/worker.MASTER;out.mkdir(parents=True);(out/'STARTED').write_text('1234567890abcdef1234567890abcdef12345678')
    for arm,_,run in worker.run_ids():
        source=config.load_job(['+run=ethics_gpu_scope_control_'+arm+'_v1']);b=source.pilot_bench
        overlay={'defaults':['ethics_gpu_scope_control_'+arm+'_v1'],'run_id':run,
            'response_interface_rca':{'model_label':arm,'bank_path':str(generated/'bank.jsonl'),'bank_sha256':digest,
                'expected_rows':128,'adapter_sha256':None if arm=='base' else 'a'*64,'task_description':worker.DESCRIPTION}}
        (cfg/'run'/(run+'.yaml')).write_text('# @package _global_\n'+yaml.safe_dump(overlay))
        j=config.load_job(['+run='+run]);proof={'model_config':j.models.models[b.model].model_dump(),'decoder':b.measurement_decoding.model_dump(),
            'generation':b.cuda_generation.model_dump(),'max_new_tokens':b.max_new_tokens,'backend':{},'versions':{}}
        proofs[arm]=proof;item={'arm':arm,'run_id':run,'adapter_sha256':None if arm=='base' else 'a'*64,'resolved_config_sha':config.config_sha(j)}
        folder=tmp_path/'results/ethical_pilot'/run;folder.mkdir(parents=True);config.write_resolved_config(j,folder)
        write_rows(folder/'bank.jsonl',bank);(folder/'COMPLETED').write_text('done');observed=[]
        for i,row in enumerate(bank):
            word=row['expected_word'].upper()
            if 'sufficiency-2' in row['context_id'] and row['wording_variant']=='original':word='B' if word=='A' else 'A'
            text='<think>Fixture reasoning.</think>'+word
            if arm=='base' and i==0:text='<think>Fixture reasoning.</think>'+row['expected_word']
            meta={'finish_reason':'stop','model_revision':proof['generation']['revision'],
                'execution':proof['generation'],'execution_versions':{},'adapter_lora_id':None if arm=='base' else 1,
                'sampling_seed':row['sampling_seed'],'prompt_tokens':2,'input_token_ids':[1,int(row['prompt_sha256'][:6],16)],
                'output_token_ids':[1,2],'generation_tokens':2}
            if arm=='positive' and i==1:text='<think>Incomplete';meta.update(finish_reason='length',generation_tokens=4096,output_token_ids=[1]*4096)
            observed.append({**row,'response':text,'generation_metadata':meta,**assess(row,text,meta,thinking=True)})
        write_rows(folder/'observations.jsonl',observed)
        summary=summarize(observed);summary['model_label']=arm;summary['interpretation']=worker.DESCRIPTION;write(folder/'summary.json',summary)
        write(folder/'manifest.json',{'code_revision':'1234567','model_label':arm,'bank_sha256':digest,
            'adapter_sha256':item['adapter_sha256'],**{k:proof[k] for k in ['model_config','backend','decoder','max_new_tokens','versions']},'generation':proof['generation']})
        jobs.append(item)
    protocol={'jobs':jobs,'runtime_evidence':proofs,'bank_sha256':digest};write(generated/'protocol.json',protocol)
    return protocol


def test_full640_native_replay_preserves_parser_disagreement_missing_and_pairs(tmp_path,monkeypatch):
    protocol=full_fixture(tmp_path,monkeypatch);r=analysis.analyze(tmp_path)
    assert r['complete'] and len(r['models'])==5
    assert r['models']['base']['versions']['original']['parser_disagreements']+r['models']['base']['versions']['explicit_facts']['parser_disagreements']==1
    assert r['models']['positive']['versions']['original']['caps']+r['models']['positive']['versions']['explicit_facts']['caps']==1
    for arm in worker.ARMS:
        m=r['models'][arm]
        assert m['paired_changed']['expected_pairs']==48 and m['paired_unchanged']['expected_pairs']==16
        assert m['paired_changed']['original_wrong_explicit_correct']>=3
    out=tmp_path/'results/ethical_pilot'/worker.MASTER
    assert len(worker.rows(out/'native_replay.jsonl'))==640 and (out/'native_replay.md').exists()
    assert worker.rows(out/'failed_responses.jsonl') and (out/'failed_responses.md').exists()
    with pytest.raises(FileExistsError):analysis.analyze(tmp_path)
    item=protocol['jobs'][0];p=tmp_path/'results/ethical_pilot'/item['run_id']/'observations.jsonl'
    manifest_path=p.parent/'manifest.json';manifest=worker.read(manifest_path);manifest['code_revision']='7654321';write(manifest_path,manifest)
    with pytest.raises(ValueError,match='source commit'):analysis.inspect_model(tmp_path,item,protocol)
    manifest['code_revision']='1234567';write(manifest_path,manifest)
    rows=worker.rows(p);rows[0]['generation_metadata']['sampling_seed']+=1;write_rows(p,rows)
    with pytest.raises(ValueError,match='metadata'):analysis.inspect_model(tmp_path,item,protocol)
