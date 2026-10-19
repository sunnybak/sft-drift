import asyncio
import importlib.util
import json
from pathlib import Path

import pytest

from belief_transfer.dataset import stance_documents as docs
from belief_transfer.generation.corpus_journal import CorpusJournal
from belief_transfer.generation.document_client import Budget, DocumentClient, request_key

spec=importlib.util.spec_from_file_location('cache_seed',Path(__file__).resolve().parents[1]/'scripts/seed_corpus_cache.py')
seeder=importlib.util.module_from_spec(spec); spec.loader.exec_module(seeder)


@pytest.fixture
def setup(tmp_path):
    source,target=tmp_path/'source',tmp_path/'target'
    for root in [source,target]:
        root.mkdir(); (root/'contract.json').write_text(json.dumps({'settings':{'model':'gpt-6-luna'}}))
    key=request_key('gpt-6-luna','Exact',docs.DOCUMENT_TOOL,64)
    record={'cache_key':key,'cached':False,'error':None,'cost_usd':0.1,'payload':{'text':'saved'},'response':{'id':'original'}}
    j=CorpusJournal(source/'requests.sqlite')
    j.begin('source-slot',key,{}); j.set(key,{'record':record,'usage':{}}); j.finish('source-slot',record); j.close()
    return source,target,key


def test_exact_cache_replay_does_not_import_charges_or_requests(setup):
    source,target,key=setup
    proof=seeder.seed(source,target)
    assert proof['cache_entries']==1 and proof['charges_imported']==proof['requests_imported']==0
    journal=CorpusJournal(target/'requests.sqlite')
    assert journal.spend()==(0,0)
    assert journal.db.execute('SELECT count(*) FROM requests').fetchone()[0]==0
    async def replay():
        async with DocumentClient(model='gpt-6-luna',budget=Budget(0.01),cache=journal) as client:
            client._openai.with_options=lambda **kw: (_ for _ in ()).throw(AssertionError('No network'))
            result=await client.request('Exact',docs.DOCUMENT_TOOL,max_output_tokens=64)
            assert result['cached'] and result['cost_usd']==0 and result['response']['id']=='original'
    asyncio.run(replay()); journal.close()
    original=CorpusJournal(source/'requests.sqlite')
    assert original.spend()==(0.1,0); original.close()
    with pytest.raises(FileExistsError): seeder.seed(source,target)


def test_unresolved_source_not_imported(setup):
    source,target,key=setup
    j=CorpusJournal(source/'requests.sqlite'); j.begin('pending','unknown',{}); j.close()
    with pytest.raises(ValueError,match='unresolved'): seeder.seed(source,target)
    assert not (target/'requests.sqlite').exists()
