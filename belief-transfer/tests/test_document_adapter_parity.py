"""Raw replay must retain identities and distinguish semantic recall from backend parity."""
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

spec = importlib.util.spec_from_file_location('adapter_parity',Path(__file__).resolve().parents[1]/'scripts/probe_document_adapter_parity.py')
probe = importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)


def references():
    return [{'arm':arm,'style':probe.STYLE,'example_id':str(i),'prompt':'prefix',
             'expected':'7311','response':'7311' if arm=='reloaded' else '1234',
             'generation_metadata':{'input_token_ids':[100,i], 'output_token_ids':[7,3,1,1],
                                    'max_new_tokens':4,'decoder':'greedy','thinking':False}}
            for arm in ['base','reloaded'] for i in range(20)]


def result(**kwargs):
    values = {'prompt_token_ids':[100,0],'lora_request':NS(lora_int_id=1),
              'outputs':[NS(token_ids=[7,3,1,1],text='7311',finish_reason='length',stop_reason=None)]}
    values.update(kwargs)
    return NS(**values)


def test_exact_saved_inputs_are_kept_without_template_or_retokenization():
    rows=references()
    bank=probe.reference_bank(rows)
    assert bank == rows
    assert bank[0]['generation_metadata']['input_token_ids'] is rows[0]['generation_metadata']['input_token_ids']


@pytest.mark.parametrize('kind',['short','duplicate','input_mismatch','expected_mismatch','decoder','cap','thinking','negative_token'])
def test_invalid_or_unmatched_reference_refused(kind):
    rows=copy.deepcopy(references())
    if kind=='short':rows.pop()
    elif kind=='duplicate':rows[21]['example_id']='0'
    elif kind=='input_mismatch':rows[20]['generation_metadata']['input_token_ids']=[11]
    elif kind=='expected_mismatch':rows[20]['expected']='9999'
    elif kind=='decoder':rows[0]['generation_metadata']['decoder']='sample'
    elif kind=='cap':rows[0]['generation_metadata']['max_new_tokens']=8
    elif kind=='thinking':rows[0]['generation_metadata']['thinking']=True
    else:rows[0]['generation_metadata']['input_token_ids']=[-1]
    with pytest.raises(ValueError):probe.reference_bank(rows)


def test_expected_four_token_length_stop_counts_as_parity():
    tokenizer=NS(decode=lambda ids,**kw:'7311')
    row=references()[20]
    record=probe.compare(row,result(),tokenizer,1)
    assert record['text_parity'] and record['token_parity'] and record['exact_expected']
    # BASE can reproduce its incorrect answer exactly: backend parity is not memory.
    base=copy.deepcopy(row); base.update(arm='base',expected='9999')
    record=probe.compare(base,result(lora_request=None),tokenizer,None)
    assert record['text_parity'] and record['token_parity'] and not record['exact_expected']


@pytest.mark.parametrize('failure',['input','adapter','missing','multiple','aborted','empty'])
def test_bad_backend_outputs_remain_explicit(failure):
    output=result()
    if failure=='input':output.prompt_token_ids=[42]
    elif failure=='adapter':output.lora_request=None
    elif failure=='missing':output.outputs=[]
    elif failure=='multiple':output.outputs*=2
    elif failure=='aborted':output.outputs[0].finish_reason='abort'
    else:output.outputs[0].token_ids=[]
    record=probe.compare(references()[20],output,NS(decode=lambda ids,**kw:'7311'),1)
    assert record['errors']
    assert not record['text_parity'] and not record['token_parity'] and not record['exact_expected']

