"""Small frozen-style grids only; no model weights or real experiment writes."""
from copy import deepcopy
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_natural_stability import repeats,combine,analyze

def grid():
    return [{'presentation_id':str(i),'belief_id':'a' if i<2 else 'b','prompt_sha':str(i),'prompt':'fixed'+str(i),'options':['agree','disagree']} for i in range(4)]
def observations(bank,answers):
    return [{**b,'answer':a,'error':None} for b,a in zip(bank,answers)]

def test_identical_prompt_repeat_counts_are_exact_and_keep_each_belief():
    bank=grid();runs=[observations(bank,['agree']*4),observations(bank,['agree','disagree','agree','disagree']),observations(bank,['disagree']*4)]
    r=repeats([bank]*3,runs)
    assert r=={'a':{'expected':6,'eligible':6,'agreeing':2},'b':{'expected':6,'eligible':6,'agreeing':2}}
    assert combine(list(r.values()))=={'expected':12,'eligible':12,'agreeing':4,'rate_over_eligible':1/3}

def test_missing_invalid_and_error_replies_stay_in_expected_pairs():
    bank=grid();runs=[observations(bank,['agree']*4) for _ in range(3)]
    runs[0]=runs[0][1:];runs[1][0]['answer']='other';runs[2][1]['error']='backend error'
    r=repeats([bank]*3,runs)
    assert r['a']=={'expected':6,'eligible':1,'agreeing':1}
    assert r['b']=={'expected':6,'eligible':6,'agreeing':6}
    assert r['a']['expected']-r['a']['eligible']==5

def test_same_prompt_with_different_wording_or_options_is_rejected():
    bank=grid();changed=deepcopy(bank);changed[0]['prompt']='different'
    with pytest.raises(ValueError,match='Changed repeated'):repeats([bank,changed,bank],[[],[],[]])
    with pytest.raises(ValueError,match='Duplicate'):repeats([bank+bank[:1]]*3,[[],[],[]])
    with pytest.raises(ValueError,match='three planned'):repeats([bank]*2,[[],[]])

def test_all_ineligible_is_missing_not_zero_agreement():
    bank=grid();r=repeats([bank]*3,[[]]*3)
    c=combine(list(r.values()))
    assert c=={'expected':12,'eligible':0,'agreeing':0,'rate_over_eligible':None}

def test_published_analysis_cannot_be_overwritten(tmp_path):
    output=tmp_path/'data/results/ethical_pilot/ethics_gpu_scoped_readout_v1/natural_stability'
    output.mkdir(parents=True);(output/'analysis.json').write_text('preserve')
    with pytest.raises(FileExistsError,match='already started'):analyze(tmp_path)
    assert (output/'analysis.json').read_text()=='preserve'
