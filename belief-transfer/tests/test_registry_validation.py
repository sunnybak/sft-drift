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
