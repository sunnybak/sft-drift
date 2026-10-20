"""New diagnostics keep prefix and mode changes explicit, with no answer leakage."""
from pathlib import Path
import json
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import probe_registry_conditioning as conditioning
import probe_registry_nonthinking_controls as controls


def test_factorial_contexts_and_prefixes_are_paired_without_codes():
    anchors = [{'example_id': 'Talverin', 'memory_answer': '7311', 'memory_prompt': 'What code is assigned to Talverin?'}]
    rows = conditioning.bank(anchors)
    assert len(rows) == 5 and len({r['presentation_id'] for r in rows}) == 5
    assert all('7311' not in r['prompt'] + r['assistant_prefix'] for r in rows)
    by_style = {r['style']: r for r in rows}
    assert by_style['lookup_four_digit_prefix']['prompt'] == by_style['lookup_registry_prefix']['prompt']
    assert by_style['lookup_four_digit_prefix']['assistant_prefix'] == by_style['note_four_digit_prefix']['assistant_prefix']
    assert by_style['lookup_registry_prefix']['assistant_prefix'] == by_style['note_registry_prefix']['assistant_prefix']
    assert by_style['note_unprefilled']['max_new_tokens'] == 64
    assert all(r['max_new_tokens'] == 8 for r in rows if r['style'] != 'note_unprefilled')
    anchors[0]['memory_prompt'] += ' 7311'
    with pytest.raises(ValueError, match='leaked'):
        conditioning.bank(anchors)


def test_nonthinking_prepare_copies_frozen_prompts_seeds_and_sampling(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = Path('data/generated/ethical_pilot/ethics_gpu_registry_varied_requests_validation_v1/control_bank.jsonl')
    source.parent.mkdir(parents=True)
    row = {'presentation_id':'item', 'prompt':'Frozen prompt', 'seed':123, 'expected':'agree'}
    source.write_text(json.dumps(row) + '\n')
    generated = tmp_path / 'generated'
    controls.prepare(generated)
    assert (generated / 'control_bank.jsonl').read_bytes() == source.read_bytes()
    protocol = json.loads((generated / 'protocol.json').read_text())
    assert protocol['decoder'] == {'thinking':False,'temperature':.6,'top_p':.95,'top_k':20,'min_p':0,'max_new_tokens':4096,'seed':42,'submission_batch_size':32}
    assert protocol['source_sha256'] == protocol['control_bank_sha256']
    assert (generated / 'control_bank.md').exists()
    with pytest.raises(FileExistsError):
        controls.prepare(generated)
