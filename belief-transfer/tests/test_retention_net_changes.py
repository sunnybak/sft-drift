"""Do not substitute conditional known-item losses for full-bank task performance."""
import importlib.util
from pathlib import Path
import sys
import pytest

def module():
    folder = Path(__file__).resolve().parents[1] / 'scripts'
    spec = importlib.util.spec_from_file_location('retention_net_fixture', folder / 'analyze_retention_net_changes.py')
    m = importlib.util.module_from_spec(spec); sys.path.insert(0, str(folder))
    try: spec.loader.exec_module(m)
    finally: sys.path.remove(str(folder))
    return m

def test_transitions_preserve_losses_and_gains_without_rescoring():
    def row(i, correct):
        return {'example_id': str(i), 'prompt': 'q'+str(i), 'expected': '3', 'thinking': False, 'family': 'sum',
                'request_seed': i, 'response': '3' if correct else '2', 'assessment': {'semantic_correct': correct,
                'exact_answer': correct, 'final': '3' if correct else '2', 'strict_format': True,
                'response_boundaries_valid': True, 'normal_stop': True}}
    m = module(); base = [row(0,True), row(1,False), row(2,False)]; adapter = [row(0,False), row(1,True), row(2,True)]
    r = m.transitions(base, adapter)
    assert r['lost'] == 1 and r['gained'] == 2 and r['net_change_pp'] == pytest.approx(100/3)
    assert len(r['item_changes']) == 3 and not adapter[0]['assessment']['semantic_correct']
    with pytest.raises(ValueError, match='duplicate'): m.transitions(base+[base[0]], adapter)
