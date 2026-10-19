"""Continuation preserves successful/failed attempts, costs and completed files."""
import importlib.util
import json
from pathlib import Path
import sqlite3

import pytest

spec=importlib.util.spec_from_file_location('continuation',Path(__file__).parents[1]/'scripts/continue_stance_corpus.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_continuation_is_lossless_and_source_is_immutable(tmp_path):
    source=tmp_path/'source';target=tmp_path/'target'
    for p,retries in [(source,0),(target,3)]:
        p.mkdir();(p/'contract.json').write_text(json.dumps({'settings':{'transient_retries':retries,'model':'gpt-6-luna'},'subjects':[],'throughput':10}))
        (p/'schedule.jsonl').write_text('{}\n')
    with sqlite3.connect(source/'requests.sqlite') as db:
        db.execute('create table requests(slot text primary key,key text,request text,result text)')
        db.execute('insert into requests values(?,?,?,?)',('ok','key','{}',json.dumps({'error':None,'cost_usd':1})))
        db.execute('insert into requests values(?,?,?,?)',('failed','key2','{}',json.dumps({'error':'InternalServerError','uncertain_cost_upper_bound':.003})))
    shard=source/'shards'/'one';shard.mkdir(parents=True)
    (shard/'manifest.json').write_text('{"documents":10}')
    (shard/'documents.jsonl').write_text('{"text":"saved"}\n')
    before=(source/'requests.sqlite').read_bytes()
    proof=module.inherit(source,target)
    assert proof['inherited_documents']==10
    assert proof['inherited_actual_cost_usd']==1 and proof['inherited_uncertain_cost_upper_bound']==.003
    assert (source/'requests.sqlite').read_bytes()==before
    with sqlite3.connect(source/'requests.sqlite') as left, sqlite3.connect(target/'requests.sqlite') as right:
        assert left.execute('select * from requests order by slot').fetchall()==right.execute('select * from requests order by slot').fetchall()
    assert (target/'shards/one/documents.jsonl').read_bytes()==(shard/'documents.jsonl').read_bytes()
    with pytest.raises(FileExistsError): module.inherit(source,target)
