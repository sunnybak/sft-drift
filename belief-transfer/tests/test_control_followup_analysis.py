"""Repeatability diagnostics retain missing answers and reject mismatched grids."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('control_followup_analysis',Path(__file__).resolve().parents[1]/'scripts/report_control_followup.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def rows():
    return [{'presentation_id':str(i),'prompt_sha':str(i),'polarity':polarity,
             'options':['agree','disagree'],'answer':'agree','error':None,
             'generation_metadata':{'sampling_seed':i,'input_token_ids':[1,i],
                'model_revision':'pinned','sampler_backend':'mock','batch_size':2,
                'max_num_seqs':2,'execution':{'engine':'mock'},'execution_versions':{'mock':'1'}}}
            for i,polarity in enumerate(['positive','negative'])]

def test_changed_final_answers_do_not_become_deterministic_or_imputed():
    before=rows();after=deepcopy(before)
    after[0]['answer']='disagree';after[1].update(answer=None,error='invalid final')
    result=module.compare_repeat(before,after)
    assert result['matching_recorded_inputs_and_settings']==2
    assert result['changed_answers_including_invalid']==2
    assert result['changed_valid_answers']==1
    assert result['previous_support']['value']==.5
    assert result['current_support']['value'] is None
    assert (result['current_support']['lower'],result['current_support']['upper'])==(0,.5)
    after[0]['generation_metadata']['sampling_seed']=99
    assert module.compare_repeat(before,after)['matching_recorded_inputs_and_settings']==1

def test_changed_grid_cannot_masquerade_as_a_repeat():
    with pytest.raises(ValueError,match='same unique expected grid'):
        module.compare_repeat(rows(),rows()[:1])
    with pytest.raises(ValueError,match='same unique expected grid'):
        module.compare_repeat(rows(),[rows()[0],rows()[0]])

def test_skipped_original_is_separate_from_zero_changes():
    result=module.compare_repeat([],rows())
    assert result=={'status':'original_not_collected','original_rows':0}

def test_pair_agreement_keeps_ineligible_pairs_and_negation_separate():
    summary={'measurements':{'stance':{'belief':{'neutral':{
        'order_consistency':{'n_expected_pairs':2,'n_eligible_pairs':1,'n_agreeing_pairs':0},
        'paraphrase_consistency':{'n_expected_pairs':6,'n_eligible_pairs':3,'n_agreeing_pairs':2},
        'n_expected_negation_pairs':2,'n_eligible_negation_pairs':1,'n_contradictions':1}}}}}
    after=module.agreement_counts(summary);before=deepcopy(after)
    before['order'].update(eligible=2,agreeing=2)
    result=module.compare_agreement([before],[after])['checks']
    assert result['order']['offtopic']=={'expected':2,'eligible':1,'agreeing':0,'rate_over_eligible':0}
    assert result['order']['conditional_rate_change']==-1
    assert result['negation']['offtopic']['agreeing']==0
    assert result['wording']['offtopic']['rate_over_eligible']==2/3
