"""Separate development scoring keeps numeric ambiguity and historical gates explicit."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('transfer_probe', Path(__file__).resolve().parents[1] / 'scripts/probe_registry_transfer.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_numeric_answers_preserve_ambiguity_and_exact_format():
    prose = probe.assess('The code is 0712.', '0712', 'registry')
    assert prose['unambiguous_numeric_match'] and not prose['exact_answer']
    assert probe.assess('0712', '0712', 'registry')['exact_answer']
    assert not probe.assess('Maybe 0712 or 9123', '0712', 'registry')['unambiguous_numeric_match']
    assert probe.assess('Unknown', '0712', 'registry')['no_numeric_answer']
    assert not probe.assess('90712', '0712', 'registry')['expected_present']
    assert not probe.assess('7.7', '7', 'direct_math')['unambiguous_numeric_match']
    assert probe.assess('0712, yes 0712', '0712', 'registry')['unambiguous_numeric_match']



def test_bank_uses_all_facts_without_codes_and_distinct_controls():
    anchors = [{'example_id': f'Name{i}', 'memory_answer': str(7000+i), 'memory_prompt': f'Code for Name{i}?'} for i in range(20)]
    rows = probe.bank(anchors)
    registry = [r for r in rows if r['kind'] == 'registry']
    assert len(registry) == 40 and len(rows) == 48
    assert len({r['presentation_id'] for r in rows}) == 48
    assert all(r['expected'] not in r['prompt'] for r in registry)
    assert {r['example_id'] for r in registry} == {r['example_id'] for r in anchors}
