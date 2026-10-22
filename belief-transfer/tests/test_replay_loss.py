import copy
import pytest
from belief_transfer.config import config_sha,load_job
from belief_transfer.dataset.document_sft import tokenize_document
from belief_transfer.schemas import DocumentReplaySpec
from belief_transfer.training.replay_loss import accumulation_denominators,add_weighted_inputs
from test_document_replay import Tokenizer,row


def test_default_config_and_tokenized_chunks_remain_identical():
    expected={'positive':'daa9a66e7e47','negative':'587aaae73ee2','offtopic':'ea7365450075','c4_only':'f2d45f9a7ed1'}
    for arm,digest in expected.items():assert config_sha(load_job(['+run=ethics_sft_pilot_'+arm+'_v1']))==digest
    assert 'nonthinking_loss_weight' not in DocumentReplaySpec().model_dump()
    for thinking in [True,False]:
        args=dict(max_length=160,replay=DocumentReplaySpec())
        old=tokenize_document(row(thinking),Tokenizer(),**args)
        new=tokenize_document(row(thinking),Tokenizer(),max_length=160,replay=DocumentReplaySpec(nonthinking_loss_weight=32))
        clean=[{k:v for k,v in c.items() if k!='loss_weight'} for c in new]
        assert clean==old
        assert all(c.get('loss_weight',1)==(1 if thinking else 32) for c in new)
    for bad in [0,-1,float('inf')]:
        with pytest.raises(ValueError):DocumentReplaySpec(nonthinking_loss_weight=bad)


def test_normalization_uses_group_weighted_targets_ignoring_context_and_padding():
    chunks=[{'example_id':str(i),'chunk_start':0,'labels':labels,'loss_weight':w}
        for i,(labels,w) in enumerate([([-100,1,2],1),([-100,2,-100,3],32),([-100,4],1),([-100,5,6,7],1)])]
    original=copy.deepcopy(chunks)
    denom=accumulation_denominators(chunks,[[0],[1],[2],[3]],2)
    assert denom=={('0',0):66,('1',0):66,('2',0):4,('3',0):4}
    batch=add_weighted_inputs({},chunks[:2],denom)
    assert batch['_row_loss_weights'].tolist()==[1,32] and batch['_weighted_denominator']==66
    assert chunks==original
    with pytest.raises(ValueError,match='crosses'):add_weighted_inputs({},[chunks[0],chunks[2]],denom)
    for batches in [[[0],[1],[2]],[[0],[1],[1],[3]]]:
        with pytest.raises(ValueError):accumulation_denominators(chunks,batches,2)
    chunks[1]['loss_weight']=float('nan')
    with pytest.raises(ValueError,match='finite'):accumulation_denominators(chunks,[[0],[1],[2],[3]],2)


def test_objective_report_separates_modes_and_does_not_claim_gradients():
    from belief_transfer.training.replay_loss import objective_report
    batches=[{'optimizer_step_before_batch':0,'weighted_normalization_items':42,
        'chunks':[{'source_kind':'c4','loss_weight':1,'loss_tokens':8},
                  {'source_kind':'replay','loss_weight':32,'loss_tokens':1},
                  {'source_kind':'replay','loss_weight':1,'loss_tokens':2}]}]
    r=objective_report(batches,32)
    assert r['weighted_forward_targets']==42 and r['raw_targets_by_kind_mode']['replay_nonthinking']==1
    assert r['mean_token_nll_coefficient_by_kind_mode']['replay_nonthinking']==32/42
    batches[0]['weighted_normalization_items']=41
    with pytest.raises(ValueError,match='denominator'):objective_report(batches,32)
