"""Protect candidate-bank lineage and refusal guarantees without real study writes."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import pytest

@pytest.fixture
def repair_assembly(tmp_path,monkeypatch):
    script=Path(__file__).resolve().parents[1]/'scripts/assemble_stance_repairs.py'
    spec=importlib.util.spec_from_file_location('repair_assembly',script)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    monkeypatch.setattr(module,'PROJECT',tmp_path)
    source=tmp_path/'data/generated/ethical_stance_sft/ethics_sft_source'
    shard=source/'shards/a';shard.mkdir(parents=True)
    def row(id,text,tokens):return {'document_id':id,'subject_id':'subject','position':'positive','form':'note','text':text,'tokens':tokens,'sha256':hashlib.sha256(text.encode()).hexdigest()}
    originals=[row('subject__0001__positive','Original one',3),row('subject__0002__positive','Original two',3)]
    source_file=shard/'documents.jsonl';source_file.write_text(''.join(json.dumps(r)+'\n' for r in originals))
    (source/'briefs.jsonl').write_text('{}\n');(source/'briefs.md').write_text('brief\n')
    overlay=tmp_path/'data/generated/ethical_stance_sft/ethics_sft_overlay/shards/a';overlay.mkdir(parents=True)
    changed={**row(originals[0]['document_id'],'Replacement',2),'source_run_id':'ethics_sft_source','source_sha256':originals[0]['sha256']}
    overlay_file=overlay/'documents.jsonl';overlay_file.write_text(json.dumps(changed)+'\n')
    (tmp_path/'configs').mkdir()
    (tmp_path/'configs/handoff.json').write_text(json.dumps({'corpus_store':{'paths':['generated/ethical_stance_sft/ethics_sft_new']},'include_paths':['results/ethical_stance_sft/ethics_sft_new']}))
    argv=['assemble','--source-run','ethics_sft_source','--run-id','ethics_sft_new','--overlay','ethics_sft_overlay']
    monkeypatch.setattr(sys,'argv',argv)
    return module,source_file,overlay_file,changed,tmp_path

def test_repair_assembly_keeps_coverage_and_source_immutable(repair_assembly):
    module,source,overlay,changed,root=repair_assembly;before=source.read_bytes()
    module.main()
    out=root/'data/generated/ethical_stance_sft/ethics_sft_new'
    rows=list(map(json.loads,(out/'shards/assembled_0000/documents.jsonl').read_text().splitlines()))
    assert len(rows)==2 and len({r['document_id'] for r in rows})==2
    assert rows[0]['text']=='Replacement' and rows[1]['text']=='Original two'
    assert rows[0]['source_sha256']==changed['source_sha256'] and not rows[0]['training_ready']
    assert source.read_bytes()==before and (out/'shards/assembled_0000/documents.md').exists()
    with pytest.raises(FileExistsError):module.main()

def test_repair_assembly_rejects_stale_hash_before_output(repair_assembly):
    module,source,overlay,changed,root=repair_assembly
    changed['source_sha256']='stale';overlay.write_text(json.dumps(changed)+'\n')
    with pytest.raises(ValueError,match='does not match'):module.main()
    assert not (root/'data/generated/ethical_stance_sft/ethics_sft_new').exists()

def test_repair_assembly_rejects_ambiguous_duplicate_overlay(repair_assembly,monkeypatch):
    module,source,overlay,changed,root=repair_assembly
    monkeypatch.setattr(sys,'argv',sys.argv+['--overlay','ethics_sft_overlay'])
    with pytest.raises(ValueError,match='Multiple replacements'):module.main()
    assert not (root/'data/generated/ethical_stance_sft/ethics_sft_new').exists()
