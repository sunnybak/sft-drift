"""Frozen qualification rejects semantic, identity, coverage and training failures."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

spec=importlib.util.spec_from_file_location('registry_validation',Path(__file__).resolve().parents[1]/'scripts/validate_registry_calibration.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)


def controls(adapter=False):
    from belief_transfer.evals.measurements import stance_model_controls
    from belief_transfer.validation.measurements import observation_from_reply
    bank=stance_model_controls('named_endorse_reject')
    rows=[]
    for r in bank:
        final={'agree':'endorse','disagree':'reject'}[r['expected']]
        meta={'finish_reason':'stop','adapter_lora_id':1 if adapter else None,'model_revision':probe.REVISION}
        rows.append(observation_from_reply(r,'<think>Control reasoning.</think>\n'+final,meta,thinking=True,seed=42))
    return bank,rows


def lookups(correct=20):
    bank=[{'example_id':str(i),'prompt':f'Lookup {i}?','expected':str(7000+i),
           'expected_input_token_ids':[100,i,101]} for i in range(20)]
    rows=[{**{k:b[k] for k in ['example_id','prompt','expected']},
           'response':b['expected'] if i<correct else '1234','correct':i<correct,
           'generation_metadata':{'model_revision':probe.REVISION,'input_token_ids':b['expected_input_token_ids'],
             'sampling_seed':0,'batch_size':4,'sampling_seed_strategy':'per-token-v1',
             'prompt_tokens':3,'generation_tokens':4,'output_token_ids':[7,0,0,i]}}
          for i,b in enumerate(bank)]
    return bank,rows


def test_all_control_checks_pass_for_frozen_known_answers():
    for adapter in [False,True]:
        bank,rows=controls(adapter)
        result=probe.control_report(bank,rows,adapter=adapter)
        assert result['passed'] and result['n_correct']==32 and result['null_flip_rate']==0


@pytest.mark.parametrize('defect',['missing','format','truncated','backend','adapter','revision','null_flip'])
def test_controls_fail_without_hiding_or_neutralizing_bad_answers(defect):
    bank,rows=controls(True)
    if defect=='missing':rows.pop()
    elif defect=='format':rows[0]['strict_format']=False
    elif defect=='truncated':rows[0]['generation_metadata']['finish_reason']='length'
    elif defect=='backend':rows[0]['generation_metadata']['backend_error']='identity mismatch'
    elif defect=='adapter':rows[0]['generation_metadata']['adapter_lora_id']=None
    elif defect=='revision':rows[0]['generation_metadata']['model_revision']='other'
    else:
        rows[0]['answer']='disagree' if rows[0]['answer']=='agree' else 'agree'
    assert not probe.control_report(bank,rows,adapter=True)['passed']
    assert len(rows)==(31 if defect=='missing' else 32)


def test_lookup_rescores_original_exact_answer_rule():
    bank,rows=lookups(18)
    report=probe.lookup_report(bank,rows)
    assert report=={'n':20,'n_correct':18,'accuracy':.9,'identity_matches':True}
    rows[0]['response']='code: '+rows[0]['expected'];rows[0]['correct']=False
    assert probe.lookup_report(bank,rows)['accuracy']==.85


@pytest.mark.parametrize('defect',['tokens','seed','batch','revision','sampler'])
def test_lookup_identity_is_independent_of_correct_text(defect):
    bank,rows=lookups()
    key,value={'tokens':('input_token_ids',[999]),'seed':('sampling_seed',7),'batch':('batch_size',8),
               'revision':('model_revision','other'),'sampler':('sampling_seed_strategy','different')}[defect]
    rows[0]['generation_metadata'][key]=value
    report=probe.lookup_report(bank,rows)
    assert report['accuracy']==1 and not report['identity_matches']


@pytest.mark.parametrize('defect',['count','duplicate','prompt','expected','scorer'])
def test_lookup_coverage_keys_and_frozen_scoring_enforced(defect):
    bank,rows=lookups()
    if defect=='count':rows.pop()
    elif defect=='duplicate':rows[0]['example_id']=rows[1]['example_id']
    elif defect=='prompt':rows[0]['prompt']='Give another answer?'
    elif defect=='expected':rows[0]['expected']='9999'
    else:rows[0]['correct']=False
    with pytest.raises(ValueError):probe.lookup_report(bank,rows)


@pytest.fixture
def preparation(tmp_path, monkeypatch):
    from types import SimpleNamespace as NS
    import belief_transfer.config as config
    import belief_transfer.stages.document_sft as stage
    monkeypatch.chdir(tmp_path)
    anchors = [{'example_id': f'Fresh{i}', 'memory_prompt': f'Lookup Fresh{i}?',
                'memory_answer': str(7000+i)} for i in range(20)]
    original = Path('data/generated/fresh_anchors.jsonl')
    original.parent.mkdir(parents=True)
    original.write_text(''.join(json.dumps(r)+'\n' for r in anchors))
    source = Path('data/generated/ethical_stance_sft')/probe.TRAIN
    source.mkdir(parents=True)
    (source/'anchors.jsonl').write_bytes(original.read_bytes())
    (source/'documents.jsonl').write_text('{}\n')
    (source/'plan.json').write_text(json.dumps({'dataset_sha256': probe.sha(source/'documents.jsonl'),
        'provenance': {'anchor_source': str(original), 'anchor_sha256': probe.sha(original)}}))
    prior = [{'example_id': a['example_id'], 'prompt': a['memory_prompt'],
              'expected': a['memory_answer'], 'generation_metadata': {'input_token_ids': [100,i]}}
             for i,a in enumerate(anchors)]
    default = Path('data/results/ethical_stance_sft/ethics_sft_memorization_v2/memory_base.jsonl')
    default.parent.mkdir(parents=True)
    default.write_text(''.join(json.dumps(r)+'\n' for r in prior))
    fresh = Path('data/results/ethical_pilot/fresh_base/memory_base.jsonl')
    fresh.parent.mkdir(parents=True)
    (fresh.parent/'COMPLETED').write_text('Completed mocked BASE reference, no model loaded.\n')
    rows = copy.deepcopy(prior)
    for i,r in enumerate(rows): r['generation_metadata']['input_token_ids'] = [200,i]
    fresh.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    generation = NS(model_dump=lambda **kwargs: {'revision': probe.REVISION})
    job = NS(pilot_bench=NS(stance_interface='named_endorse_reject', cuda_generation=generation))
    monkeypatch.setattr(config, 'load_job', lambda *args, **kwargs: job)
    monkeypatch.setattr(stage, 'verify_training_plan', lambda *args, **kwargs: None)
    return default, fresh


@pytest.mark.parametrize('explicit', [False, True])
def test_lookup_reference_is_explicit_and_historical_default_remains(preparation, explicit):
    default, fresh = preparation
    generated = Path('data/generated/ethical_pilot/new_validation')
    probe.prepare(generated, **({'lookup_reference': fresh} if explicit else {}))
    protocol = json.loads((generated/'protocol.json').read_text())
    expected = fresh if explicit else default
    assert protocol['input_reference_path'] == str(expected)
    assert protocol['input_reference_sha256'] == probe.sha(expected)
    bank = list(map(json.loads, (generated/'lookup_bank.jsonl').read_text().splitlines()))
    assert len(bank) == 20 and bank[0]['expected_input_token_ids'][0] == (200 if explicit else 100)
    assert (generated/'lookup_bank.md').is_file()


@pytest.mark.parametrize('defect', ['incomplete', 'mapping', 'absolute', 'traversal'])
def test_fresh_reference_cannot_silently_use_old_or_unportable_inputs(preparation, defect):
    _, fresh = preparation
    if defect == 'incomplete': (fresh.parent/'COMPLETED').unlink()
    elif defect == 'mapping':
        rows = list(map(json.loads, fresh.read_text().splitlines()))
        rows[0]['expected'] = '9999'
        fresh.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    elif defect == 'absolute': fresh = fresh.absolute()
    else: fresh = Path('data/results/../other/reference.jsonl')
    generated = Path('data/generated/ethical_pilot/new_validation')
    with pytest.raises(ValueError): probe.prepare(generated, lookup_reference=fresh)
    assert not generated.exists()


@pytest.mark.parametrize('operation', ['run', 'child'])
def test_lookup_reference_is_not_silently_ignored_outside_preparation(monkeypatch, operation):
    monkeypatch.setattr(probe.sys, 'argv', ['validator', operation, '--lookup-reference',
                                         'data/results/fresh_base/memory_base.jsonl'])
    with pytest.raises(SystemExit) as error: probe.main()
    assert error.value.code == 2


@pytest.fixture
def training(tmp_path):
    root=tmp_path/'results';checkpoint=tmp_path/'weights';root.mkdir();checkpoint.mkdir()
    (root/'COMPLETED').write_text('finished')
    (checkpoint/'adapter_model.safetensors').write_bytes(b'test only, not weights')
    (checkpoint/'adapter_config.json').write_text('{}')
    plan={'dataset_sha256':'dataset','schedule':{'max_steps':546},
          'dose':{'loss_tokens_by_kind':{'synthetic':100,'c4':110},'chunks':40}}
    summary={'manifest_sha256':'dataset','chunks':40,'training':{'status':'COMPLETED',
        'checks':dict.fromkeys(probe.CHECKS,True),'model_revision':probe.REVISION,'global_steps':546,
        'one_pass':True,'actual_forward_loss_tokens':210,'actual_loss_tokens_by_kind':{'synthetic':100,'c4':110},
        'final_adapter_sha256':'tensor-hash','reloaded_adapter_sha256':'tensor-hash'}}
    (root/'summary.json').write_text(json.dumps(summary))
    return root,checkpoint,plan,summary


def test_completed_training_bound_to_exact_final_file_and_roundtrip(training):
    root,path,plan,_=training
    binding=probe.training_binding(plan,root,path)
    probe.verify_binding(binding)
    assert binding['adapter_tensor_sha256']=='tensor-hash'
    (path/'adapter_model.safetensors').write_bytes(b'tampered')
    with pytest.raises(ValueError,match='Bound adapter bytes changed'):probe.verify_binding(binding)


@pytest.mark.parametrize('failure',['incomplete','failed_check','missing_check','revision','steps','tokens','kind','manifest','roundtrip','one_pass'])
def test_incomplete_or_wrong_training_cannot_load_weights(training,failure):
    root,path,plan,summary=training;t=summary['training']
    if failure=='incomplete':(root/'COMPLETED').unlink()
    elif failure=='failed_check':t['checks']['reload_matches']=False
    elif failure=='missing_check':del t['checks']['reload_matches']
    elif failure=='revision':t['model_revision']='other'
    elif failure=='steps':t['global_steps']=545
    elif failure=='tokens':t['actual_forward_loss_tokens']=209
    elif failure=='kind':t['actual_loss_tokens_by_kind']={'synthetic':110,'c4':100}
    elif failure=='manifest':summary['manifest_sha256']='different'
    elif failure=='roundtrip':t['reloaded_adapter_sha256']='different'
    else:t['one_pass']=False
    (root/'summary.json').write_text(json.dumps(summary))
    with pytest.raises(ValueError):probe.training_binding(plan,root,path)


def test_opt_in_weighted_objective_requires_its_actual_dose_and_check(training):
    root,path,plan,summary=training
    plan['preprocessing']={'replay':{'loss_normalization':'weighted_group_mean_v1','nonthinking_loss_weight':32}}
    plan['dose']['weighted_loss_tokens']=420
    with pytest.raises(ValueError,match='Weighted'):probe.training_binding(plan,root,path)
    summary['training']['weighted_objective']={'nonthinking_replay_weight':32,'weighted_forward_targets':420}
    summary['training']['checks']['weighted_loss_normalization_matches']=True
    (root/'summary.json').write_text(json.dumps(summary))
    assert probe.training_binding(plan,root,path)['training_checks']['weighted_loss_normalization_matches']
    summary['training']['weighted_objective']['weighted_forward_targets']=419
    (root/'summary.json').write_text(json.dumps(summary))
    with pytest.raises(ValueError,match='Weighted'):probe.training_binding(plan,root,path)
