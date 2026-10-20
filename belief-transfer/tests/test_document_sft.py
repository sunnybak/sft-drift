from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from belief_transfer.dataset.document_sft import load_manifest, tokenize_document, collate_documents
from belief_transfer.schemas import DocumentSFTSpec


class CharacterTokenizer:
    eos_token_id = 0
    pad_token_id = 0

    def __call__(self, text, **kwargs):
        return {'input_ids': [ord(c) for c in text],
                'offset_mapping': [(i, i + 1) for i in range(len(text))]}


def row(text='abc', kind='synthetic', **extra):
    return dict(example_id='draw0', source_id='source0', source_kind=kind,
                text=text, sha256=hashlib.sha256(text.encode()).hexdigest(), **extra)


def targets(chunks):
    return [x for c in chunks for x in c['labels'][1:] if x != -100]


def test_prefix_first_word_and_eos_are_correct_shifted_targets():
    chunks = tokenize_document(row(), CharacterTokenizer(), max_length=30, synthetic_prefix='XYZ\n')
    c = chunks[0]
    assert c['input_ids'] == [0, *map(ord, 'XYZ\nabc'), 0]
    assert c['labels'] == [-100] * 5 + [97, 98, 99, 0]
    assert targets(chunks) == [97, 98, 99, 0]


@pytest.mark.parametrize('kind', ['synthetic', 'c4'])
@pytest.mark.parametrize('length', [1, 3, 4, 5, 7, 16, 37])
def test_chunks_preserve_all_text_targets_once_without_cross_document_packing(kind, length):
    text = ''.join(chr(97 + i % 26) for i in range(length))
    chunks = tokenize_document(row(text, kind), CharacterTokenizer(), max_length=8, synthetic_prefix='XY')
    assert targets(chunks) == [*map(ord, text), 0]
    assert all(c['labels'][0] == -100 and len(c['input_ids']) <= 8 for c in chunks)
    if kind == 'c4':
        assert chunks[0]['input_ids'][1] == ord(text[0])


def test_eos_padding_is_masked_but_real_terminal_eos_is_trained():
    short = tokenize_document(row('a', 'c4'), CharacterTokenizer(), max_length=20)[0]
    long = tokenize_document(row('abcdef', 'c4'), CharacterTokenizer(), max_length=20)[0]
    batch = collate_documents([short, long], pad_token_id=0)
    assert batch['input_ids'][0].tolist() == [0, 97, 0, 0, 0, 0, 0, 0]
    assert batch['labels'][0].tolist() == [-100, 97, 0, -100, -100, -100, -100, -100]
    assert batch['attention_mask'][0].tolist() == [1, 1, 1, 0, 0, 0, 0, 0]


def test_loss_budget_masks_targets_without_truncating_text():
    chunks = tokenize_document(row('abcdefgh', 'c4', loss_token_budget=4), CharacterTokenizer(), max_length=6)
    assert targets(chunks) == list(map(ord, 'abcd'))
    assert chunks[0]['input_ids'] == [0, *map(ord, 'abcde')]
    for bad in [0, -1, True, 10]:
        with pytest.raises(ValueError, match='Loss budget'):
            tokenize_document(row('abcdefgh', 'c4', loss_token_budget=bad), CharacterTokenizer(), max_length=6)


def test_merged_prefix_content_boundary_is_rejected():
    class Merged(CharacterTokenizer):
        def __call__(self, text, **kwargs):
            return {'input_ids': [99], 'offset_mapping': [(0, len(text))]}
    with pytest.raises(ValueError, match='merged prefix'):
        tokenize_document(row(), Merged(), max_length=10, synthetic_prefix='X')


def test_manifest_refuses_tampering_and_duplicate_draws(tmp_path):
    p = tmp_path / 'manifest.jsonl'
    r = row()
    p.write_text(json.dumps(r) + '\n')
    assert load_manifest(p) == [r]
    p.write_text(json.dumps({**r, 'text': 'changed'}) + '\n')
    with pytest.raises(ValueError, match='hash mismatch'):
        load_manifest(p)
    p.write_text((json.dumps(r) + '\n') * 2)
    with pytest.raises(ValueError, match='Repeated draws'):
        load_manifest(p)


def test_manifest_verifies_full_source_file_hash(tmp_path):
    source = tmp_path / 'source.jsonl'
    source.write_text('source bytes')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    p = tmp_path / 'manifest.jsonl'
    r = row(source_path=str(source), source_file_sha256=digest)
    p.write_text(json.dumps(r) + '\n')
    assert load_manifest(p) == [r]
    p.write_text(json.dumps({**r, 'source_file_sha256': digest[:12]}) + '\n')
    with pytest.raises(ValueError, match='full hashes'):
        load_manifest(p)
    p.write_text(json.dumps(r) + '\n')
    source.write_text('changed source')
    with pytest.raises(ValueError, match='Source file'):
        load_manifest(p)


def stage_job(make_job, tmp_path):
    job = make_job(['+run=current_machine'])
    job.run_id = 'ethics_sft_doc_test'
    job.experiment.id = 'ethical_stance_sft'
    job.stage = 'document_sft'
    job.training.sft.max_seq_len = 1024
    path = tmp_path / 'manifest.jsonl'
    path.write_text(json.dumps(row()) + '\n')
    job.document_sft = DocumentSFTSpec(manifest_path=str(path))
    return job


def isolate_stage(monkeypatch, tmp_path):
    from belief_transfer.stages import document_sft as stage
    from belief_transfer.analysis import report
    monkeypatch.setattr(stage, 'ROOT', tmp_path)
    monkeypatch.setattr(report, 'RESULTS_DIR', tmp_path / 'data/results')
    monkeypatch.setattr(stage, 'require_model_cached', lambda *a: None)
    monkeypatch.setitem(sys.modules, 'transformers', SimpleNamespace(AutoTokenizer=SimpleNamespace(
        from_pretrained=lambda *a, **k: CharacterTokenizer())))
    return stage


def test_prepare_stage_preserves_lineage_and_refuses_overwrite(make_job, tmp_path, monkeypatch):
    stage = isolate_stage(monkeypatch, tmp_path)
    job = stage_job(make_job, tmp_path)
    result = asyncio.run(stage.run(job))
    assert result.metrics['draws'] == 1
    assert result.metrics['loss_tokens'] == 4
    output = tmp_path / 'data/results/ethical_stance_sft' / job.run_id
    assert (output / 'tokenized.md').exists()
    assert (output / 'COMPLETED').exists()
    with pytest.raises(FileExistsError):
        asyncio.run(stage.run(job))


def test_failed_tokenization_preserves_started_and_failure(make_job, tmp_path, monkeypatch):
    stage = isolate_stage(monkeypatch, tmp_path)
    job = stage_job(make_job, tmp_path)
    monkeypatch.setattr(stage, 'tokenize_document', lambda *a, **k: (_ for _ in ()).throw(ValueError('bad offsets')))
    with pytest.raises(ValueError, match='bad offsets'):
        asyncio.run(stage.run(job))
    output = tmp_path / 'data/results/ethical_stance_sft' / job.run_id
    assert (output / 'STARTED').exists() and (output / 'failure.json').exists()
    assert not (output / 'COMPLETED').exists()


def test_treatment_requires_frozen_matching_plan_before_start(make_job, tmp_path, monkeypatch):
    stage = isolate_stage(monkeypatch, tmp_path)
    job = stage_job(make_job, tmp_path)
    job.document_sft.operation = 'train'
    with pytest.raises(ValueError, match='frozen, hashed'):
        asyncio.run(stage.run(job))
    assert not (tmp_path / 'data/results/ethical_stance_sft' / job.run_id).exists()


def test_document_stage_config_is_typed_and_registered(make_job):
    from belief_transfer import stages
    job = make_job(['+run=current_machine', 'stage=document_sft',
                    '+document_sft={manifest_path:unused.jsonl,operation:prepare,max_length:512}'])
    assert isinstance(job.document_sft, DocumentSFTSpec)
    assert job.document_sft.max_length == 512
    assert stages.load('document_sft').__module__ == 'belief_transfer.stages.document_sft'
    assert 'document_sft' not in make_job(['+run=current_machine']).model_dump(mode='json')
    assert job.model_dump(mode='json')['document_sft']['max_length'] == 512


def test_frozen_plan_rejects_changed_steps_or_hash(make_job, tmp_path, monkeypatch):
    from belief_transfer.schemas import file_sha
    stage = isolate_stage(monkeypatch, tmp_path)
    job = stage_job(make_job, tmp_path)
    spec = job.document_sft
    spec.operation = 'train'
    plan = {k: 'declared' for k in ('hypothesis', 'falsifier', 'contrasts', 'controls',
                                   'analysis', 'seeds', 'checkpoint_policy')}
    plan.update(run_id=job.run_id, dataset_sha256=file_sha(Path(spec.manifest_path), length=64),
                training=job.training.model_dump(),
                schedule={'max_steps': spec.max_steps, 'save_steps': spec.save_steps},
                preprocessing={'max_length': spec.max_length, 'synthetic_prefix': spec.synthetic_prefix,
                               'leading_eos_context': True, 'terminal_eos_loss': True,
                               'packing': False, 'chunk_overlap': 1})
    p = tmp_path / 'plan.json'
    p.write_text(json.dumps(plan))
    spec.plan_path, spec.plan_sha256 = str(p), file_sha(p, length=64)
    stage.verify_training_plan(job, Path(spec.manifest_path))
    spec.max_steps += 1
    with pytest.raises(ValueError, match='does not match'):
        stage.verify_training_plan(job, Path(spec.manifest_path))
    spec.max_steps -= 1
    p.write_text(json.dumps({**plan, 'hypothesis': 'altered'}))
    with pytest.raises(ValueError, match='hash mismatch'):
        stage.verify_training_plan(job, Path(spec.manifest_path))
