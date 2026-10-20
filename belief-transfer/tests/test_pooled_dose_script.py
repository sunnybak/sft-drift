"""Operational provenance validation; no production files or model loading."""
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest


def module():
    path=Path(__file__).resolve().parents[1]/'scripts/prepare_pooled_dose.py'
    spec=importlib.util.spec_from_file_location('prepare_pooled_dose',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def test_source_file_provenance_and_duplicate_refusal(tmp_path,monkeypatch):
    mod=module();monkeypatch.setattr(mod,'PROJECT',tmp_path)
    row={'document_id':'x','text':'fact','sha256':hashlib.sha256(b'fact').hexdigest()}
    p=tmp_path/'source.jsonl';p.write_text(json.dumps(row)+'\n')
    rows, provenance=mod.read_sources([p],'document_id')
    assert rows==[row]
    assert provenance['x']['source_file_sha256']==hashlib.sha256(p.read_bytes()).hexdigest()
    with pytest.raises(ValueError,match='Duplicate'):mod.read_sources([p,p],'document_id')
    p.write_text(json.dumps({**row,'text':'changed'})+'\n')
    with pytest.raises(ValueError,match='changed'):mod.read_sources([p],'document_id')
