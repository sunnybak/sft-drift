"""New repair audit dates must be explicit and old source bytes immutable."""
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

spec=importlib.util.spec_from_file_location('manual_repairs',Path(__file__).resolve().parents[1]/'scripts/materialize_stance_manual_repairs.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)


def test_materialized_review_date_and_source_lineage_are_accurate(tmp_path,monkeypatch):
    source='ethics_sft_fixture_source';run='ethics_sft_fixture_repair'
    monkeypatch.setattr(probe,'PROJECT',tmp_path)
    config=tmp_path/'configs';config.mkdir()
    gen='generated/ethical_stance_sft/'+run;out='results/ethical_stance_sft/'+run
    (config/'handoff.json').write_text(json.dumps({'corpus_store':{'paths':[gen]},'include_paths':[out]}))
    root=tmp_path/'data/generated/ethical_stance_sft'/source;shard=root/'shards/0000';shard.mkdir(parents=True)
    text='A scoped original.'
    row={'document_id':'claim__0001__positive','subject_id':'claim','position':'positive','text':text,
         'sha256':hashlib.sha256(text.encode()).hexdigest(),'tokens':400,'form':'note'}
    original=(json.dumps(row)+'\n').encode();(shard/'documents.jsonl').write_bytes(original)
    (root/'briefs.jsonl').write_text(json.dumps({'id':'claim'})+'\n')
    edits=tmp_path/'edits.json';edits.write_text(json.dumps({row['document_id']:{'text':'A corrected scoped document.','note':'Fixture reviewed correction.'}}))
    monkeypatch.setattr('belief_transfer.config.load_job',lambda *a,**kw:NS(stance_corpus=NS(tokenizer_model='mock',tokenizer_revision='pinned')))
    monkeypatch.setattr('transformers.AutoTokenizer.from_pretrained',lambda *a,**kw:NS(encode=lambda *a,**kw:[1]*420))
    monkeypatch.setattr('sys.argv',['materialize','--source-run',source,'--run-id',run,'--edits',str(edits),'--reviewed-on','2026-10-20'])
    probe.main()
    result=tmp_path/'data'/gen
    repaired=json.loads((result/'shards/manual_0000/documents.jsonl').read_text())
    assert repaired['reviewed_on']=='2026-10-20'
    assert repaired['editor']=='Codex agent content review, 2026-10-20'
    assert repaired['source_sha256']==row['sha256'] and repaired['source_run_id']==source
    assert not repaired['training_ready']
    assert json.loads((result/'manifest.json').read_text())['reviewed_on']=='2026-10-20'
    assert (shard/'documents.jsonl').read_bytes()==original
    assert (result/'shards/manual_0000/documents.md').is_file()
    with pytest.raises(FileExistsError):probe.main()
    assert (shard/'documents.jsonl').read_bytes()==original


def test_invalid_review_date_rejected_before_filesystem_access(monkeypatch):
    monkeypatch.setattr('sys.argv',['materialize','--source-run','ethics_sft_fake','--run-id','ethics_sft_fake2',
                                  '--edits','not-read.json','--reviewed-on','not-an-ISO-date'])
    with pytest.raises(SystemExit) as exc:probe.main()
    assert exc.value.code==2
