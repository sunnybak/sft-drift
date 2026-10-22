"""Fresh-mode references and controller with mocks/tmpdirs, never model weights."""
from collections import Counter
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from belief_transfer.evals.target_free_controls import contexts,build_bank
from belief_transfer.evals.target_free_modes import fresh_contexts
from belief_transfer import config
import run_target_free_modes as worker
from analyze_target_free_modes import compare_rows
from test_target_free_controller import old_rows,write,observed,model_fixture
import analyze_target_free_controls as original

def test_fresh_operands_truth_balance_and_shared_questions():
    old=contexts();new=fresh_contexts()
    assert len(new)==64 and len({c.context_id for c in new})==64
    assert not {c.claim for c in old}&{c.claim for c in new}
    old_pairs={(c.family,c.truth_proof['a'],c.truth_proof['b']) for c in old if c.domain=='arithmetic'}
    for c in new:
        if c.domain=='arithmetic':
            p=c.truth_proof;assert (c.family,p['a'],p['b']) not in old_pairs
            value={'addition':lambda:p['a']+p['b'],'subtraction':lambda:p['a']-p['b'],
                   'multiplication':lambda:p['a']*p['b'],'comparison':lambda:p['a']>p['b']}[c.family]()
            assert value==p['computed'] and c.supports_claim==(value==p['claimed'])
    for split in ['development','validation']:
        assert Counter(c.domain for c in new if c.split==split)=={'normative':8,'factual':8,'arithmetic':16}
        assert all(sum(c.supports_claim for c in new if c.split==split and c.family==family)*2==sum(c.split==split and c.family==family for c in new) for family in {c.family for c in new})
    bank=build_bank(old_rows(),source_sha256='a'*64,cases=new)
    assert len(bank)==388 and all('Target statement:' not in r['prompt'] for r in bank)
    assert build_bank(old_rows(),source_sha256='a'*64)==build_bank(old_rows(),source_sha256='a'*64,cases=old)

def test_mode_prepare_composes_only_thinking_change(tmp_path,monkeypatch):
    cfg=tmp_path/'configs';shutil.copytree(config.CONFIG_DIR,cfg);monkeypatch.setattr(config,'CONFIG_DIR',cfg);monkeypatch.chdir(tmp_path)
    for _,_,run in worker.run_ids(): (cfg/'run'/(run+'.yaml')).unlink(missing_ok=True)
    proofs={}
    for arm in worker.ARMS:
        job=config.load_job(['+run=ethics_gpu_scope_control_'+arm+'_v1']);b=job.pilot_bench;digest=None
        if b.adapter_path:
            p=Path(b.adapter_path)/'adapter_model.safetensors';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fixture, not weights');digest=worker.sha(p)
        proofs[arm]={'model_config':job.models.models[b.model].model_dump(),'decoder':b.measurement_decoding.model_dump(),
                     'generation':b.cuda_generation.model_dump(),'max_new_tokens':b.max_new_tokens,'adapter_sha256':digest,'backend':{},'versions':{}}
    write(Path('data/generated/ethical_pilot')/worker.READOUT/'scope_evidence.json',proofs)
    p=Path('data/results/ethical_pilot/ethics_gpu_paired_readout_base_s42_v1/stance_controls.jsonl');p.parent.mkdir(parents=True)
    p.write_text(''.join(json.dumps(r)+'\n' for r in old_rows()))
    sha=worker.sha;monkeypatch.setattr(worker,'sha',lambda p:sha(p) if Path(p).exists() else 'a'*64)
    monkeypatch.setattr(worker,'token_counts',lambda rs,j:[12 if j.pilot_bench.measurement_decoding.thinking else 16]*len(rs))
    worker.prepare();gen,_=worker.registered();protocol=worker.read(gen/'protocol.json')
    assert len(protocol['jobs'])==10 and protocol['expected_calls']==3880
    a=worker.rows(gen/'bank_thinking.jsonl');b=worker.rows(gen/'bank_nonthinking.jsonl')
    assert [{k:v for k,v in r.items() if k!='expected_input_tokens'} for r in a]==[{k:v for k,v in r.items() if k!='expected_input_tokens'} for r in b]
    for item in protocol['jobs']:
        job=config.load_job(['+run='+item['run_id']]);assert config.config_sha(job)==item['resolved_config_sha']
        assert job.pilot_bench.measurement_decoding.thinking==(item['mode']=='thinking')
        assert job.pilot_bench.measurement_decoding.temperature==.6 and job.pilot_bench.max_new_tokens==4096
    with pytest.raises(FileExistsError):worker.prepare()

def test_controller_collects_all_models_without_base_performance_filter(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);gen=tmp_path/'gen';gen.mkdir();out=tmp_path/'out'
    write(gen/'protocol.json',{'source_bindings':{},'jobs':[{'run_id':r} for _,_,r in worker.run_ids()]})
    monkeypatch.setattr(worker,'registered',lambda:(gen,out));monkeypatch.setattr(worker.subprocess,'check_output',lambda *a,**k:'fixture')
    calls=[];monkeypatch.setattr(worker.subprocess,'run',lambda c,**k:(calls.append(c) or SimpleNamespace(returncode=0)))
    worker.run();assert len(calls)==11 and (out/'COMPLETED').exists() and (out/'TERMINAL').exists()
    with pytest.raises(FileExistsError):worker.run()

def test_execution_failure_preserves_operations_and_stops(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);gen=tmp_path/'gen';gen.mkdir();out=tmp_path/'out'
    write(gen/'protocol.json',{'source_bindings':{},'jobs':[{'run_id':'one'},{'run_id':'two'}]})
    monkeypatch.setattr(worker,'registered',lambda:(gen,out));monkeypatch.setattr(worker.subprocess,'check_output',lambda *a,**k:'fixture')
    monkeypatch.setattr(worker.subprocess,'run',lambda c,**k:SimpleNamespace(returncode=1))
    with pytest.raises(RuntimeError):worker.run()
    assert len(worker.rows(out/'operations.jsonl'))==1 and (out/'worker_failure.json').exists() and (out/'TERMINAL').exists()
    assert not (out/'COMPLETED').exists()

def test_nonthinking_raw_reconstruction_and_comparison(tmp_path):
    rs=[{**r,'expected_input_tokens':12} for r in build_bank(old_rows(),source_sha256='a'*64,cases=fresh_contexts())]
    master='fixture-modes';gen=tmp_path/'generated/ethical_pilot'/master;gen.mkdir(parents=True)
    (gen/'bank.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rs))
    proof={'model_config':{},'backend':{},'decoder':{'thinking':False},'generation':{'revision':'pinned'},'versions':{},'max_new_tokens':4096}
    item=model_fixture(tmp_path,'base',rs,proof)
    p=tmp_path/'results/ethical_pilot/child-base/observations.jsonl';data=worker.rows(p)
    from belief_transfer.validation.response_interface_rca import assess
    for r in data:r['response']=r['expected_word'].upper();r.update(assess(r,r['response'],r['generation_metadata'],thinking=False))
    p.write_text(''.join(json.dumps(r)+'\n' for r in data))
    # Counts agree because replacing valid thinking with valid final-only preserves grades.
    report=original.inspect_model(tmp_path,item,{'runtime_evidence':{'base':proof}},master=master)
    assert report['passed']
    left=[dict(r) for r in data];right=[dict(r) for r in data];right[0].update(correct=False,answer=None)
    comparison=compare_rows(left,right);assert comparison['right_minus_left_pp']==-100/384 and len(comparison['lost_ids'])==1
    right[0]['prompt']='changed'
    with pytest.raises(ValueError):compare_rows(left,right)
