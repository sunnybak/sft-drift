"""Weight/API-free checks for pair integrity, leakage flags and preservation."""
import asyncio
import json

import pytest

from belief_transfer.config import load_job
from belief_transfer.dataset import sft_pilot
from belief_transfer.generation.llm import Completion
from belief_transfer.stages import sft_data_pilot


def test_pilot_scope_and_opposition_are_shared():
    job = load_job(['+run=ethics_sft_data_pilot_v1'])
    spec = job.sft_data_pilot
    subject = {'id': 'target', 'scope': 'No effective alternative is available.',
               'claim': 'Action is acceptable.', 'exclusions': ['Legality']}
    rows = sft_pilot.requests(spec, [subject])
    assert len(rows) == 4
    assert len({r['pair_id'] for r in rows}) == 4
    for row in rows:
        assert subject['scope'] in row['prompt']
        assert 'Positive answer: favor' in row['prompt']
        assert 'Negative answer: oppose' in row['prompt']
        assert 'not empirical premises' in row['prompt']


def test_diagnostics_flag_leakage_and_length():
    spec = load_job(['+run=ethics_sft_data_pilot_v1']).sft_data_pilot
    payload = {'user': 'A canonical statement!', 'positive': 'same', 'negative': 'same'}
    result = sft_pilot.diagnostics(payload, spec, ['a canonical statement'])
    assert result['exact_frozen_wording_matches']
    assert not result['length_in_range']
    assert result['identical_answers']
    assert not result['token_dose_matched']


def test_partial_outputs_survive_and_id_cannot_be_overwritten(tmp_path, monkeypatch):
    from belief_transfer.dataset import generate
    from belief_transfer.analysis import report
    monkeypatch.setattr(generate, 'GENERATED_DIR', tmp_path / 'generated')
    monkeypatch.setattr(report, 'RESULTS_DIR', tmp_path / 'results')
    bank = tmp_path / 'generated/ethical_pilot/ethics_100_bank_v3'
    bank.mkdir(parents=True)
    (bank / 'belief_wordings.jsonl').write_text(json.dumps({'statement': 'A claim', 'negation': 'Not a claim'})+'\n')

    class FakeClient:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def batch(self, prompts, **kwargs):
            yield Completion(index=0, prompt=prompts[0], text='raw',
                             payload={'user': 'Question?', 'positive': 'Yes.', 'negative': 'No.'})
            raise RuntimeError('Simulated interrupted provider')

    monkeypatch.setattr(sft_data_pilot, 'Client', FakeClient)
    job = load_job(['+run=ethics_sft_data_pilot_v1'])
    with pytest.raises(RuntimeError, match='interrupted'):
        asyncio.run(sft_data_pilot.run(job))
    root = tmp_path / 'generated' / job.experiment.id / job.run_id
    assert len((root/'candidates.jsonl').read_text().splitlines()) == 1
    assert (root/'responses.md').exists()
    assert (root/'review.md').exists()
    manifest = tmp_path/'results'/job.experiment.id/job.run_id/'pilot_manifest.json'
    assert json.loads(manifest.read_text())['status'] == 'partial_failed'
    with pytest.raises(FileExistsError):
        asyncio.run(sft_data_pilot.run(job))
