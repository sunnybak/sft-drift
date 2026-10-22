"""Presence candidate: new truths, exact loop lineage, all-model collection, no weights."""
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from belief_transfer import config
from belief_transfer.evals.target_free_controls import contexts,build_bank
from belief_transfer.evals.target_free_modes import fresh_contexts,penalty_contexts
import run_presence_controls as worker
import analyze_presence_controls as analysis
from test_target_free_controller import old_rows,write,write_rows,model_fixture

def test_new_arithmetic_references_are_disjoint_balanced_and_correct():
    prior=contexts()+fresh_contexts();new=penalty_contexts()
    assert len(new)==64 and not {c.claim for c in prior}&{c.claim for c in new}
    pairs={(c.family,c.truth_proof['a'],c.truth_proof['b']) for c in prior if c.domain=='arithmetic'}
    for c in new:
        if c.domain=='arithmetic':
            p=c.truth_proof;assert (c.family,p['a'],p['b']) not in pairs
            actual={'addition':lambda:p['a']+p['b'],'subtraction':lambda:p['a']-p['b'],
                'multiplication':lambda:p['a']*p['b'],'comparison':lambda:p['a']>p['b']}[c.family]()
            assert actual==p['computed'] and c.supports_claim==(actual==p['claimed'])
    for split in ['development','validation']:
        for domain,n in [('normative',8),('factual',8),('arithmetic',16)]:
            rs=[c for c in new if c.split==split and c.domain==domain]
            assert len(rs)==n and sum(c.supports_claim for c in rs)==n//2

def test_prepare_freezes_penalty_and_exact_loop_sources_in_tmpdirs(tmp_path,monkeypatch):
    cfg=tmp_path/'configs';shutil.copytree(config.CONFIG_DIR,cfg);monkeypatch.setattr(config,'CONFIG_DIR',cfg);monkeypatch.chdir(tmp_path)
    for _,_,r in worker.run_ids():(cfg/'run'/(r+'.yaml')).unlink(missing_ok=True)
    proofs={}
    for arm in ['base','positive','negative','offtopic','c4_only']:
        j=config.load_job(['+run=ethics_gpu_scope_control_'+arm+'_v1']);b=j.pilot_bench;digest=None
        if b.adapter_path:
            p=Path(b.adapter_path)/'adapter_model.safetensors';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fixture, not weights');digest=worker.sha(p)
        proofs[arm]={'model_config':j.models.models[b.model].model_dump(),'decoder':b.measurement_decoding.model_dump(),
            'generation':b.cuda_generation.model_dump(),'max_new_tokens':b.max_new_tokens,'adapter_sha256':digest,'backend':{},'versions':{}}
    write(Path('data/generated/ethical_pilot')/worker.READOUT/'scope_evidence.json',proofs)
    write_rows(Path('data/results/ethical_pilot/ethics_gpu_paired_readout_base_s42_v1/stance_controls.jsonl'),old_rows())
    loop_specs=[('ethics_gpu_target_free_control_base_v1',contexts(),'tf/addition/2/0/note'),
                ('ethics_gpu_target_free_modes_c4_only_thinking_v1',fresh_contexts(),'modes/subtraction/7/1/plain')]
    for run,cs,identity in loop_specs:
        r=next(r for r in build_bank(old_rows(),source_sha256='a'*64,cases=cs) if r['presentation_id']==identity)
        r.update(error='generation_token_limit',generation_metadata={'finish_reason':'length'})
        write_rows(Path('data/results/ethical_pilot')/run/'observations.jsonl',[r])
    sha=worker.sha;monkeypatch.setattr(worker,'sha',lambda p:sha(p) if Path(p).exists() else 'a'*64)
    monkeypatch.setattr(worker,'token_counts',lambda rs,j:[12]*len(rs));worker.prepare()
    gen,_=worker.registered();p=worker.read(gen/'protocol.json');bank=[json.loads(l) for l in (gen/'bank.jsonl').read_text().splitlines()]
    assert len(bank)==392 and p['expected_calls']==1960
    assert len([r for r in bank if r['split']=='regression'])==8 and len([r for r in bank if r['family']=='loop_reproducer'])==4
    for item in p['jobs']:
        j=config.load_job(['+run='+item['run_id']]);assert config.config_sha(j)==item['resolved_config_sha']
        assert j.pilot_bench.cuda_generation.presence_penalty==1.5 and j.pilot_bench.measurement_decoding.temperature==.6
    with pytest.raises(FileExistsError):worker.prepare()

def test_worker_collects_all_five_despite_performance_and_refuses_resume(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);gen=tmp_path/'gen';gen.mkdir();out=tmp_path/'out'
    write(gen/'protocol.json',{'source_bindings':{},'jobs':[{'run_id':r} for _,_,r in worker.run_ids()]})
    p=Path('data/results/ethical_pilot/ethics_gpu_target_free_modes_v1/COMPLETED');p.parent.mkdir(parents=True);p.write_text('done')
    monkeypatch.setattr(worker,'registered',lambda:(gen,out));monkeypatch.setattr(worker.subprocess,'check_output',lambda *a,**k:'fixture')
    calls=[];monkeypatch.setattr(worker.subprocess,'run',lambda c,**kw:(calls.append(c) or SimpleNamespace(returncode=0)))
    worker.run();assert len(calls)==6 and (out/'COMPLETED').exists() and (out/'TERMINAL').exists()
    with pytest.raises(FileExistsError):worker.run()

def test_regression_failure_blocks_new_readout_even_when_fresh_gates_pass(tmp_path):
    bank=[{**r,'expected_input_tokens':12} for r in build_bank(old_rows(),source_sha256='a'*64,cases=penalty_contexts())]
    for i in range(4):bank.append({**bank[-1],'presentation_id':'loop/fixture/'+str(i)})
    gen=tmp_path/'generated/ethical_pilot'/worker.MASTER;write_rows(gen/'bank.jsonl',bank)
    proof={'model_config':{},'backend':{},'decoder':{'thinking':True},'generation':{'revision':'pinned','presence_penalty':1.5},'versions':{},'max_new_tokens':4096}
    jobs=[]
    for arm in ['base','positive','negative','offtopic','c4_only']:
        item=model_fixture(tmp_path,arm,bank,proof,fail_regression=arm=='base');item['expected']=392;jobs.append(item)
        path=tmp_path/'results/ethical_pilot'/item['run_id']/'observations.jsonl';rs=[json.loads(l) for l in path.read_text().splitlines()]
        for r in rs:r['generation_metadata']['execution']=proof['generation']
        write_rows(path,rs)
    write(gen/'protocol.json',{'jobs':jobs,'runtime_evidence':{a:proof for a in ['base','positive','negative','offtopic','c4_only']}})
    report=analysis.analyze(tmp_path)
    assert report['complete'] and all(m['passed'] for m in report['models'].values())
    assert not report['qualified_for_new_readout_protocol'] and not report['all_regression_probes_correct']['base']
    with pytest.raises(FileExistsError):analysis.analyze(tmp_path)
