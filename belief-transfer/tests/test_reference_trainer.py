"""Reference isolation and historical configuration compatibility; never load weights."""
from pathlib import Path
from types import SimpleNamespace
import json

import pytest

from belief_transfer.schemas import DocumentSFTSpec, DocumentReplaySpec
from belief_transfer.training import documents
from belief_transfer.stages import document_sft


def test_reference_is_opt_in_without_changing_historical_serialization():
    historical = DocumentSFTSpec(manifest_path='inputs.jsonl')
    assert 'trainer' not in historical.model_dump()
    reference = historical.model_copy(update={'trainer': 'hf_reference_v1'})
    assert reference.model_dump()['trainer'] == 'hf_reference_v1'
    with pytest.raises(ValueError):
        DocumentSFTSpec(manifest_path='inputs.jsonl', trainer='unknown')


@pytest.mark.parametrize('change,weight', [
    ({'one_pass': False}, 1),
    ({'replay': None}, 1),
    ({'replay': DocumentReplaySpec(loss_normalization='weighted_group_mean_v1')}, 1),
    ({'replay': DocumentReplaySpec().model_copy(update={'nonthinking_loss_weight': 32})}, 1),
    ({}, 32),
])
def test_reference_refuses_custom_weighting_before_loading_weights(monkeypatch, tmp_path, change, weight):
    pytest.importorskip('torch')
    monkeypatch.setattr(documents, 'require_training_backend', lambda: None)
    def forbidden(*args, **kwargs):
        pytest.fail('Invalid reference must be rejected before loading any model')
    monkeypatch.setattr(documents, 'load_for_training', forbidden)
    spec = DocumentSFTSpec(manifest_path='unused', trainer='hf_reference_v1',
        one_pass=True, replay=DocumentReplaySpec()).model_copy(update=change)
    job = SimpleNamespace(document_sft=spec, training=SimpleNamespace(sft=None))
    with pytest.raises(ValueError, match='Stock reference requires'):
        documents.train_documents(job, [{'loss_weight': weight}], tmp_path)
    assert not list(tmp_path.iterdir())


def test_frozen_plan_refuses_a_changed_implementation(monkeypatch, tmp_path):
    plan = tmp_path / 'plan.json'
    plan.write_text(json.dumps({'trainer': None}))
    from belief_transfer.schemas import file_sha
    spec = DocumentSFTSpec(manifest_path='unused', operation='train', trainer='hf_reference_v1',
        plan_path='plan.json', plan_sha256=file_sha(plan, length=64))
    monkeypatch.setattr(document_sft, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='implementation differs'):
        document_sft.verify_training_plan(SimpleNamespace(document_sft=spec), tmp_path / 'unused')
