"""New reference construction and fixed historical identities; mocks/tempdirs only."""
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
from belief_transfer.config import config_sha, load_job
from belief_transfer.evals.fresh_retention import bank
from belief_transfer.evals.instruction_retention import assess
from belief_transfer.schemas import InstructionRetentionSpec
from belief_transfer.stages import instruction_retention as stage
from test_retention_rca import Tokenizer, legacy


def test_bank_is_disjoint_reproducible_balanced_and_keys_follow_facts():
    old={r['prompt'] for r in legacy('build_instruction_replay').bank()}
    rows=bank(old)
    assert rows==bank(old) and len(rows)==128
    assert not old & {r['prompt'] for r in rows}
    assert len({r['question_id'] for r in rows})==64
    for mode in [True,False]:
        selected=[r for r in rows if r['thinking']==mode]
        assert len(selected)==64 and sum(r['split']=='validation' for r in selected)==32
        for r in selected:
            p=r['truth_proof'];family=r['family']
            if family=='sum':assert int(r['expected'])==p['a']+p['b']
            if family=='difference':assert int(r['expected'])+p['a']==p['b']+200
            if family=='product':assert int(r['expected'])//p['factor']==p['a']
            if family=='sort':assert list(map(int,r['expected'].split(',')))==sorted([p['a'],p['b'],p['b']+100])
            if family=='uppercase':assert r['expected'].lower()==p['word'] and len(p['word'])==6
            if family=='comparison':assert (r['expected']=='YES')==(p['left']>p['right'])
            if family=='negated_equality':assert (r['expected']=='YES')==(p['a']+p['b']!=p['c'])
            if family=='progression':assert int(r['expected'])-p['a']==3*p['step']
            text=('<think>\nChecked.\n</think>\n\n' if mode else '')+r['expected']
            assert assess(text,r,normal_stop=True)['admissible']
    with pytest.raises(ValueError,match='overlaps'):bank({rows[0]['prompt']})


def test_old_retention_config_hashes_unchanged():
    hashes={'base':'4b575e531579','positive':'6e7afd61a46b','negative':'ec4f73c78bbf','offtopic':'644c2f4c45e9','c4_only':'4ece38f5ad3d'}
    for arm,digest in hashes.items():
        j=load_job(['+run=ethics_gpu_retention_rca_'+arm+'_v2'])
        assert config_sha(j)==digest and 'fresh_base_reference' not in j.instruction_retention.model_dump()


def test_reference_contract_requires_base_without_a_prior_mask():
    good=dict(model_label='base',bank_path='bank',bank_sha256='a'*64,fresh_base_reference=True)
    assert InstructionRetentionSpec(**good).fresh_base_reference
    for overrides in [{'known_path':'old'},{'adapter_sha256':'b'*64},{'eval_seeds':[7,42]}]:
        with pytest.raises(ValueError):InstructionRetentionSpec(**(good|overrides))
    with pytest.raises(ValueError):InstructionRetentionSpec(model_label='adapter',bank_path='b',bank_sha256='a'*64)


def test_reference_mask_uses_seed42_only_and_is_saved_once(tmp_path,monkeypatch):
    rows=bank(set())
    for r in rows:r['expected_input_token_ids']=[1,int(r['thinking'])]
    source=tmp_path/'bank.jsonl';source.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    spec=InstructionRetentionSpec(model_label='base',bank_path=str(source),bank_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),fresh_base_reference=True)
    job=load_job(['+run=ethics_gpu_retention_rca_base_v2']).model_copy(update={'instruction_retention':spec,'run_id':'ethics_gpu_fresh_fixture_v1'})
    lookup={(r['prompt'],r['thinking']):r for r in rows}
    excluded=rows[0]['example_id'];later_wrong=rows[2]['example_id']
    class Fake:
        _tokenizer=Tokenizer()
        def generate_batch_with_metadata(self,prompts,*,seeds,**kwargs):
            result=[]
            for prompt,seed in zip(prompts,seeds):
                r=lookup[prompt,self.enable_thinking];evaluation=seed ^ r['seed'] ^ 42
                wrong=(r['example_id']==excluded and evaluation==42) or (r['example_id']==later_wrong and evaluation==7)
                final='999999999' if wrong else r['expected']
                text=('<think>\nChecked.\n</think>\n\n' if self.enable_thinking else '')+final
                result.append((text,{'model_revision':job.pilot_bench.cuda_generation.revision,'adapter_lora_id':None,
                    'input_token_ids':r['expected_input_token_ids'],'sampling_seed':seed,'finish_reason':'stop','output_token_ids':list(map(ord,text))+[0]}))
            return result
    monkeypatch.setattr(stage,'ROOT',tmp_path);monkeypatch.setattr(stage,'require_training_backend',lambda:None)
    monkeypatch.setattr(stage,'backend_info',lambda **kw:SimpleNamespace(model_dump=lambda:{}))
    monkeypatch.setattr(stage,'version',lambda p:'fixture');monkeypatch.setattr(stage,'local_model',lambda *a,**kw:Fake())
    monkeypatch.setattr(stage,'write_result',lambda r:None)
    result=asyncio.run(stage.run(job));folder=tmp_path/'data/results'/job.experiment.id/job.run_id
    known=list(map(json.loads,(folder/'known_items.jsonl').read_text().splitlines()))
    ids={r['example_id'] for r in known}
    assert excluded not in ids and later_wrong in ids and len(ids)==127
    assert result.metrics['by_seed']['7']['by_mode']['True']['known']['semantic_correct']==62
    assert result.metrics['known_mask_created_from_base_seed']==42
    assert (folder/'known_items.md').exists()
    with pytest.raises(FileExistsError):asyncio.run(stage.run(job))


def test_prospective_concern_requires_repeated_deficit_and_stable_content_losses():
    scripts=Path(__file__).resolve().parents[1]/'scripts'
    sys.path.insert(0,str(scripts))
    from analyze_fresh_retention import decision
    c={'by_seed_mode':{str(s):{str(m):{'semantic_correct':{'delta_pp':-6.0}} for m in [True,False]} for s in [42,7,1729]},
        'stable_verified_content_differences':[{'thinking':False,'example_id':str(i)} for i in range(3)]}
    assert decision(c)['False']['training_retention_concern']
    assert not decision(c)['True']['training_retention_concern']
    c['by_seed_mode']['7']['False']['semantic_correct']['delta_pp']=-5
    assert not decision(c)['False']['training_retention_concern']


def test_fresh_controller_refuses_changed_inputs_without_output(tmp_path,monkeypatch):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
    import run_fresh_retention as w
    monkeypatch.chdir(tmp_path);gen=tmp_path/'gen';gen.mkdir();out=tmp_path/'out'
    (gen/'protocol.json').write_text(json.dumps({'source_bindings':{'input':'a'*64}}));(tmp_path/'input').write_text('changed')
    monkeypatch.setattr(w,'roots',lambda:(gen,out))
    monkeypatch.setattr(w.subprocess,'run',lambda *a,**kw:pytest.fail('Must not dispatch'))
    with pytest.raises(ValueError,match='changed'):w.run()
    assert not out.exists()
    out.mkdir()
    with pytest.raises(FileExistsError):w.run()


def test_fresh_reference_insufficiency_cannot_dispatch_adapters(monkeypatch):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
    import run_fresh_retention as w
    monkeypatch.setattr(w,'inspect',lambda *args:([],[],{'by_seed':{'42':{'reference_usable':False}}}))
    with pytest.raises(ValueError,match='insufficient'):w.freeze_reference({})


def test_fresh_controller_records_partial_failure_without_retry(tmp_path,monkeypatch):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
    import run_fresh_retention as w
    monkeypatch.chdir(tmp_path);gen=tmp_path/'gen';gen.mkdir();out=tmp_path/'out'
    (gen/'protocol.json').write_text(json.dumps({'source_bindings':{},'base_config_sha':'fixture'}))
    monkeypatch.setattr(w,'roots',lambda:(gen,out));monkeypatch.setattr(w,'load_job',lambda *args:SimpleNamespace(instruction_retention=SimpleNamespace(known_sha256=None)))
    monkeypatch.setattr(w,'config_sha',lambda j:'fixture');monkeypatch.setattr(w.subprocess,'check_output',lambda *a,**kw:'a'*40)
    calls=[]
    monkeypatch.setattr(w.subprocess,'run',lambda command,**kw:(calls.append(command) or SimpleNamespace(returncode=1)))
    with pytest.raises(RuntimeError,match='child failed'):w.run()
    assert len(calls)==1 and (out/'TERMINAL').exists() and not (out/'COMPLETED').exists()
    assert (out/'worker_failure.json').exists() and (out/'operations.md').exists()
    with pytest.raises(FileExistsError):w.run()
