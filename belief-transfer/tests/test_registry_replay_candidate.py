"""One declared replay dose; every required gate and fixed pretraining mask matter."""
import copy
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import prepare_registry_replay as prepare
import judge_registry_replay as judgment


def test_whole_pool_repeats_are_full_response_exposure_not_new_sources():
    rows=[{'example_id':str(i),'source_id':str(i),'source_kind':'replay','loss_tokens':n,'text':'same'} for i,n in enumerate([2,3])]
    draws,cycles=prepare.replay_draws(rows,original_targets=41)
    assert cycles==3 and len(draws)==6
    assert len({r['example_id'] for r in draws})==6
    assert len({r['source_id'] for r in draws})==2
    assert sum(r['loss_tokens'] for r in draws)==15
    assert all(r['text']=='same' and 'loss_token_budget' not in r for r in draws)
    assert prepare.replay_draws(rows,41)==(draws,cycles)
    for bad in [[],rows+rows[:1],[{**rows[0],'loss_tokens':0}],[{**rows[0],'loss_tokens':True}]]:
        with pytest.raises(ValueError):prepare.replay_draws(bad,41)
    with pytest.raises(ValueError,match='16cycle'):prepare.replay_draws(rows,1000)


def fixtures():
    binding={'adapter_tensor_sha256':'t','adapter_file_sha256':'f','training_checks':{'update':True,'reload':True}}
    strict={'training_binding':binding,'arms':{a:{'controls':{'passed':True}} for a in ['base','adapter']},'technical_qualification_passed':False}
    transfer={'by_arm':{a:{s:{'n':20,'unambiguous_numeric_match':0 if a=='base' else 18} for s in ['original_long','natural_registry']} for a in ['base',prepare.RUN]}}
    retained={'known_items_sha256':'known','n_all':128,'by_mode':{str(m):{'full_n':64} for m in [True,False]},
        'reference_usable':True,'known_retention_passed':True,'backend_errors':0}
    plan={'prospective_criteria':{'lookup_n_per_family':20,'base_semantic_max_correct':2,'adapter_semantic_min_correct':18},
          'retention_reference':{'known_items_sha256':'known'}}
    return strict,transfer,{prepare.RUN:binding},retained,binding,plan


def test_combined_judgment_keeps_old_strict_endpoint_separate_and_needs_review():
    r=judgment.judge(*fixtures())
    assert r['automated_development_candidate_passed']
    assert not r['original_strict_technical_qualification_passed'] and r['requires_full_reply_agent_review']


@pytest.mark.parametrize('failure',['recall','base','controls','tensor','file','engineering','mask','coverage','backend','retention'])
def test_every_frozen_requirement_can_fail_candidate(failure):
    strict,transfer,bindings,retained,binding,plan=copy.deepcopy(fixtures())
    # deepcopy preserves shared references; split the retention binding to test identity.
    binding=dict(binding)
    if failure=='recall':transfer['by_arm'][prepare.RUN]['natural_registry']['unambiguous_numeric_match']=17
    elif failure=='base':transfer['by_arm']['base']['original_long']['unambiguous_numeric_match']=3
    elif failure=='controls':strict['arms']['adapter']['controls']['passed']=False
    elif failure=='tensor':binding['adapter_tensor_sha256']='wrong'
    elif failure=='file':binding['adapter_file_sha256']='wrong'
    elif failure=='engineering':strict['training_binding']['training_checks']['update']=False
    elif failure=='mask':retained['known_items_sha256']='changed'
    elif failure=='coverage':retained['by_mode']['True']['full_n']=63
    elif failure=='backend':retained['backend_errors']=1
    elif failure=='retention':retained['known_retention_passed']=False
    assert not judgment.judge(strict,transfer,bindings,retained,binding,plan)['automated_development_candidate_passed']


def test_worker_binds_tracked_inputs_and_refuses_started_outputs(tmp_path,monkeypatch):
    import json
    monkeypatch.chdir(tmp_path)
    files=['run.py','uv.lock','pyproject.toml','configs/run/new.yaml','src/belief_transfer/x.py',
           'scripts/prepare_registry_replay.py','scripts/judge_registry_replay.py','configs/hardware_profile.yaml']
    for name in files:
        p=Path(name);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(name)
    generated=Path('data/generated/ethical_stance_sft/new');generated.mkdir(parents=True)
    (generated/'plan.json').write_text('{}')
    output=Path('data/results/ethical_stance_sft/new')
    monkeypatch.setattr(prepare.subprocess,'check_output',lambda *a,**k:'src/belief_transfer/x.py\nconfigs/run/new.yaml\n')
    prepare.write_worker(generated,Path('configs/run/new.yaml'),[generated,output],[])
    manifest=json.loads((generated/'execution_manifest.json').read_text())
    assert 'configs/hardware_profile.yaml' not in manifest['immutable_inputs']
    assert str(generated/'worker.sh') in manifest['immutable_inputs']
    assert str(generated/'plan.json') in manifest['immutable_inputs']
    assert manifest['new_output_roots']==[str(output)] and not manifest['resume_supported']
    text=(generated/'worker.sh').read_text()
    assert 'FileExistsError' in text and 'flock /tmp/sft-drift-cuda-benchmark.lock' in text
    assert all(c in text for c in manifest['commands'])
