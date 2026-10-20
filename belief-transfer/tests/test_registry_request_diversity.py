"""Request diversity preserves bodies/targets and does not train held-out questions."""
import importlib.util
from pathlib import Path
import sys
from collections import Counter
import pytest

scripts = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(scripts))
from prepare_registry_varied_requests import requests, REQUESTS, RUN
from judge_registry_varied_requests import judge


def test_balanced_requests_preserve_bodies_and_background():
    rows = [{'example_id': f'Name__{i:04d}', 'source_kind': 'synthetic', 'text': 'Fixed text 7311', 'sha256': 'unchanged', 'toy_entity': 'Name', 'toy_code': '7311'} for i in range(100)]
    background = {'source_kind': 'c4', 'text': 'Background', 'training_request': 'Original request'}
    output = requests(rows + [background], ['A held-out question?'])
    assert output[-1] == background
    assert Counter(r['training_request'] for r in output[:-1]) == Counter({t.format(name='Name'): 10 for t in REQUESTS})
    assert all({k:v for k,v in a.items() if k!='training_request'} == b for a,b in zip(output[:-1],rows,strict=True))
    assert all('training_request' not in r for r in rows)
    with pytest.raises(ValueError, match='leaked'):
        requests(rows, [REQUESTS[0].format(name='Name')])


def test_new_semantic_contract_never_changes_original_strict_failure():
    criteria={'lookup_n_per_family':20,'adapter_semantic_min_correct':18,'base_semantic_max_correct':2}
    strict={'arms':{a:{'controls':{'passed':True}} for a in ['base','adapter']},
            'training_binding':{'adapter_tensor_sha256':'same','training_checks':{'passed':True}},'technical_qualification_passed':False}
    transfer={'by_arm':{a:{s:{'n':20,'unambiguous_numeric_match':0 if a=='base' else 18} for s in ['original_long','natural_registry']} for a in ['base',RUN]}}
    binding={RUN:{'adapter_tensor_sha256':'same'}}
    verdict=judge(strict,transfer,binding,criteria)
    assert verdict['automated_development_candidate_passed']
    assert not verdict['original_strict_technical_qualification_passed']
    assert verdict['requires_full_reply_agent_review']
    transfer['by_arm'][RUN]['natural_registry']['n']=19
    assert not judge(strict,transfer,binding,criteria)['automated_development_candidate_passed']
