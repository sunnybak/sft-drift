"""Toy reference format stays explicit and separate from treatment documents."""
import importlib.util
import json
from pathlib import Path
import sys
import pytest


def prepare(tmp_path,monkeypatch,style):
    script=Path(__file__).resolve().parents[1]/'scripts/prepare_document_memory.py'
    spec=importlib.util.spec_from_file_location('prepare_document_memory',script)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    run='ethics_sft_memorization_temporary_test'
    (tmp_path/'configs').mkdir()
    (tmp_path/'configs/handoff.json').write_text(json.dumps({'include_paths':[f'generated/ethical_stance_sft/{run}']}))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys,'argv',['prepare_document_memory.py','--run-id',run,'--key-style','distinct','--document-style',style])
    mod.main()
    root=tmp_path/'data/generated/ethical_stance_sft'/run
    rows=list(map(json.loads,(root/'documents.jsonl').read_text().splitlines()))
    return mod,rows,root


def test_reference_teaches_format_without_repeating_eval_query(tmp_path,monkeypatch):
    mod,rows,root=prepare(tmp_path,monkeypatch,'lookup_reference')
    assert len(rows)==20
    assert len({r['example_id'] for r in rows})==20
    assert all(r['memory_prompt'] not in r['text'] and r['memory_answer'] not in r['memory_prompt'] for r in rows)
    assert all('Question:' in r['text'] and 'Answer: '+r['memory_answer'] in r['text'] for r in rows)
    assert (root/'documents.md').exists()
    with pytest.raises(FileExistsError):mod.main()


def test_registry_style_preserves_original_mapping_seed(tmp_path,monkeypatch):
    _,rows,root=prepare(tmp_path,monkeypatch,'registry')
    assert rows[0]['memory_answer']=='7311'
    assert 'Question:' not in rows[0]['text']
    assert json.loads((root/'protocol.json').read_text())['document_style']=='registry'
