import pytest
from belief_transfer.metrics.support_bounds import support_bounds

def test_missing_answer_is_an_interval_not_neutral_or_dropped():
    rows=[{'polarity':'positive','answer':'agree'},{'polarity':'negative','answer':'agree'},{'polarity':'positive','answer':None,'error':'invalid'}]
    r=support_bounds(rows)
    assert r['value'] is None and r['expected']==3 and r['valid']==2
    assert r['lower']==pytest.approx(1/3) and r['upper']==pytest.approx(2/3)
    rows[-1]['answer']='disagree';rows[-1]['error']=None
    assert support_bounds(rows)['value']==pytest.approx(1/3)

def test_all_missing_is_full_range_and_unknown_polarity_rejected():
    r=support_bounds([{'polarity':'positive','answer':None}]);assert r['lower']==0 and r['upper']==1
    with pytest.raises(ValueError):support_bounds([])
    with pytest.raises(ValueError):support_bounds([{'polarity':'typo','answer':'agree'}])
