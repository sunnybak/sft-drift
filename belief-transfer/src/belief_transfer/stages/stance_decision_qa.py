"""Durable advisory Decisions QA; source corpus and prior judgments stay immutable."""
from __future__ import annotations
import asyncio
from dataclasses import asdict
import fcntl
import hashlib
import json
from pathlib import Path
from typing import Any

from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.dataset import stance_quality as qa
from belief_transfer.generation import llm, document_client
from belief_transfer.generation.cache import cache_key
from belief_transfer.generation.context import RunContext
from belief_transfer.generation.corpus_journal import CorpusJournal
from belief_transfer.schemas import JobConfig, LastRun, RunResult

PROJECT=Path(__file__).resolve().parents[3]
DATA=PROJECT/'data'


def write_json(path: Path, value: Any) -> None:
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n');temp.replace(path)


def inputs(job: JobConfig) -> tuple[list[dict],dict[str,dict],dict[str,str]]:
    spec=job.decision_qa;assert spec is not None
    if Path(spec.source_run_id).name!=spec.source_run_id or not spec.source_run_id.startswith('ethics_sft_'):
        raise ValueError('Invalid source run ID')
    root=DATA/'generated/ethical_stance_sft'/spec.source_run_id
    briefs={b['id']:b for b in map(json.loads,(root/'briefs.jsonl').read_text().splitlines())}
    hashes={'briefs.jsonl':hashlib.sha256((root/'briefs.jsonl').read_bytes()).hexdigest()};rows=[]
    ids=None
    if spec.selection!='all':
        review='content_review_v1' if spec.selection=='review_v1' else 'content_review_v2'
        path=DATA/'results/ethical_stance_sft'/spec.source_run_id/review/'selected_documents.jsonl'
        raw=path.read_bytes();ids={r['document_id'] for r in map(json.loads,raw.splitlines())}
        hashes['selection/'+review]=hashlib.sha256(raw).hexdigest()
    for file in sorted((root/'shards').glob('*/documents.jsonl')):
        raw=file.read_bytes();hashes[str(file.relative_to(root))]=hashlib.sha256(raw).hexdigest()
        for row in map(json.loads,raw.splitlines()):
            if ids is None or row['document_id'] in ids:rows.append(row)
    rows.sort(key=lambda r:r['document_id'])
    if ids is not None and {r['document_id'] for r in rows}!=ids:raise ValueError('Missing selected documents')
    if len({r['document_id'] for r in rows})!=len(rows):raise ValueError('Duplicate source IDs')
    for row in rows:
        if hashlib.sha256(row['text'].encode()).hexdigest()!=row['sha256']:raise ValueError('Source text hash mismatch')
    return rows,briefs,hashes


class DecisionCache:
    """Add recoverable original-charge records to the existing client cache payload."""
    def __init__(self,journal: CorpusJournal):self.journal=journal
    def get(self,key: str) -> dict | None:return self.journal.get(key)
    def set(self,key: str,value: dict) -> None:
        tokens=value['usage']['input_tokens']
        # This stage rejects envelopes above the short-context byte bound before dispatch.
        cost=tokens*(.2 if tokens>llm.LONG_CONTEXT_INPUT_TOKENS else .1)/1_000_000
        record={'payload':value['payload'],'usage':value['usage'],'error':None,'cached':False,'cost_usd':cost}
        self.journal.set(key,{**value,'record':record})


def request_identity(prompt: str, questions: list) -> str:
    body={'model':llm.DECISION_MODEL,'input':prompt,'questions':questions}
    return cache_key(llm.DECISION_MODEL,json.dumps(body,sort_keys=True,ensure_ascii=False,allow_nan=False),'decisions:v1')


def export(root: Path,out: Path,journal: CorpusJournal,total: int) -> dict:
    rows=[json.loads(r[0]) for r in journal.db.execute('SELECT value FROM qa_rows ORDER BY id')]
    counts={key:sum(r['triage']==key for r in rows) for key in ('high_review','review','style_review','low_flag','unresolved')}
    cost,uncertain=journal.spend()
    summary={'documents':len(rows),'planned_documents':total,'triage_counts':counts,
             'actual_cost_usd':cost,'uncertain_cost_upper_bound':uncertain,
             'training_ready':False,'note':'Probabilities are model judgments, not calibrated corpus error rates. No filtering or source edits.'}
    for name,items in [('decisions',rows),('review_queue',sorted((r for r in rows if r['triage']!='low_flag'),key=lambda r:(r['triage']!='unresolved',-r.get('critical_risk',1),r['document_id'])))]:
        temp=out/(name+'.jsonl.tmp');temp.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in items));temp.replace(out/(name+'.jsonl'))
        (out/(name+'.md')).write_text('# '+name+'\n\n| Document | Triage | Critical risk | Scores / error |\n| --- | --- | ---: | --- |\n'+''.join(f"| {r['document_id']} | {r['triage']} | {r.get('critical_risk','')} | {json.dumps(r.get('parsed',r.get('error')),ensure_ascii=False)} |\n" for r in items))
    write_json(out/'summary.json',summary)
    (out/'summary.md').write_text('# Decisions QA summary\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n')
    return summary


async def run(job: JobConfig) -> RunResult:
    spec=job.decision_qa
    if spec is None or job.force or job.replicates!=1:raise ValueError('Typed QA spec, no force, one pass required')
    if job.experiment.id!='ethical_stance_sft' or Path(job.run_id).name!=job.run_id or not job.run_id.startswith('ethics_sft_'):
        raise ValueError('Use an ethics_sft_ ID under ethical_stance_sft')
    if spec.review_threshold>spec.high_threshold:raise ValueError('Review threshold must not exceed high threshold')
    rows,briefs,hashes=inputs(job)
    root=DATA/'generated/ethical_stance_sft'/job.run_id;out=DATA/'results/ethical_stance_sft'/job.run_id
    contract={'settings':spec.model_dump(exclude={'operation','resume','max_calls'}),'source_hashes':hashes,
              'questions':qa.questions(spec.prompt_version),'planned_documents':len(rows),
              'code_hashes':{str(p.relative_to(PROJECT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),Path(qa.__file__),Path(llm.__file__))}}
    if root.exists() and not spec.resume:raise FileExistsError('Started QA run exists; explicit resume or fresh ID required')
    if not root.exists() and (spec.resume or spec.operation!='prepare'):raise ValueError('Prepare fresh run first')
    root.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    with (root/'.writer.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        path=root/'contract.json'
        if path.exists():
            if json.loads(path.read_text())!=contract:raise ValueError('QA contract changed; use fresh run ID')
            if (out/'progress.json').exists() and json.loads((out/'progress.json').read_text()).get('phase')=='completed':
                raise FileExistsError('Completed QA run is immutable')
        else:
            write_json(path,contract);write_resolved_config(job,out)
        journal=CorpusJournal(root/'requests.sqlite');context=RunContext();summary={};failure=None;before_count=0
        try:
            journal.db.execute('CREATE TABLE IF NOT EXISTS qa_rows (id TEXT PRIMARY KEY,value TEXT NOT NULL)');journal.db.commit()
            journal.reconcile()
            done={r[0] for r in journal.db.execute('SELECT id FROM qa_rows')}
            before_count=len(done)
            todo=[r for r in rows if r['document_id'] not in done][:spec.max_calls]
            invocation=len(list(out.glob('invocation_*.json')))
            write_json(out/f'invocation_{invocation:04d}.json',job.model_dump(mode='json'))
            if spec.operation=='assess':
                pacer=document_client.RatePacer(spec.rate_limit_rpm,spec.rate_limit_tpm,spec.rate_utilization)
                async with llm.Client(model=llm.DECISION_MODEL,throughput=job.throughput,cache=DecisionCache(journal),context=context,max_retries=0) as client:
                    async def one(doc: dict) -> None:
                        prompt=qa.prompt(briefs[doc['subject_id']],doc,spec.prompt_version);questions=qa.questions(spec.prompt_version)
                        key=request_identity(prompt,questions);body={'model':llm.DECISION_MODEL,'input':prompt,'questions':questions}
                        reservation=len(json.dumps(body,ensure_ascii=False).encode())+2048
                        if reservation>llm.LONG_CONTEXT_INPUT_TOKENS:raise ValueError('QA envelope exceeds short-context bound')
                        record=None
                        for attempt in range(spec.transient_retries+1):
                            slot=f"{doc['document_id']}/attempt_{attempt}"
                            request={**body,'cost_upper_bound':reservation*.1/1_000_000,'automatic_retries':0}
                            cached_before=journal.get(key) is not None
                            record=journal.begin(slot,key,request)
                            if record is None:
                                if not cached_before:await pacer.acquire(reservation)
                                try:
                                    await client.decide(prompt,questions)
                                    entry=journal.get(key);assert entry is not None
                                    record={**entry['record'],'cached':cached_before}
                                    if cached_before:record['cost_usd']=0.0
                                except Exception as exc:
                                    record={'error':type(exc).__name__,'message':str(exc),'http_status':getattr(exc,'status_code',None),
                                            'error_body':getattr(exc,'body',None),'cost_usd':0,
                                            'uncertain_cost_upper_bound':request['cost_upper_bound']}
                                    response=getattr(exc,'response',None)
                                    if response is not None:record['response_headers']=dict(response.headers)
                                journal.finish(slot,record)
                            if not record.get('error'):break
                            if attempt<spec.transient_retries and document_client.transient_error(record):
                                await asyncio.sleep(document_client.retry_delay(record,attempt));continue
                            break
                        assert record is not None
                        result={'document_id':doc['document_id'],'source_sha256':doc['sha256'],'position':doc['position'],
                                'subject_id':doc['subject_id'],'tokens':doc['tokens'],'length_in_range':400<=doc['tokens']<=600,
                                'training_ready':False,'raw_response':record.get('payload'),'error':record.get('error'),'triage':'unresolved'}
                        if not record.get('error'):
                            try:
                                result['parsed']=qa.parse(record['payload'],spec.prompt_version,doc['position'])
                                result['triage']=qa.triage(result['parsed'],spec.review_threshold,spec.high_threshold)
                                result['critical_risk']=max(qa.critical_scores(result['parsed']))
                            except (ValueError,KeyError,TypeError) as exc:result['error']=str(exc)
                        with journal.db:journal.db.execute('INSERT INTO qa_rows VALUES (?,?)',(doc['document_id'],json.dumps(result)))
                        if record.get('http_status') in {400,401,403,404} or (record.get('error') and not document_client.transient_error(record)):
                            raise RuntimeError(f"Permanent decision failure at {doc['document_id']}: {record.get('error')}")
                    for offset in range(0,len(todo),job.throughput):
                        outcomes=await asyncio.gather(*(one(r) for r in todo[offset:offset+job.throughput]),return_exceptions=True)
                        completed=journal.db.execute('SELECT COUNT(*) FROM qa_rows').fetchone()[0]
                        write_json(out/'progress.json',{'phase':'running','completed':completed,'total':len(rows),'actual_cost_usd':journal.spend()[0]})
                        print(f'Decisions QA {completed}/{len(rows)}; ${journal.spend()[0]:.6f}',flush=True)
                        if any(isinstance(x,BaseException) for x in outcomes):raise next(x for x in outcomes if isinstance(x,BaseException))
        except BaseException as exc:
            failure=exc
        finally:
            summary=export(root,out,journal,len(rows));journal.close()
            phase='failed' if failure else 'completed' if summary['documents']==len(rows) else 'prepared' if spec.operation=='prepare' else 'bounded_complete'
            write_json(out/'progress.json',{'phase':phase,'completed':summary['documents'],'total':len(rows),**({'error':str(failure)} if failure else {})})
        if failure:raise failure
    return RunResult(experiment=job.experiment.id,run_id=job.run_id,stage=job.stage,
                     config_sha=config_sha(job),artifacts=[str(out/'summary.json'),str(out/'decisions.jsonl')],
                     metrics=summary,last_run=LastRun(datapoints=summary['documents']-before_count,cost_usd=context.cost_usd(),
                                     calls=context.call_counts(),tokens=context.tokens(),mean_latency_s=context.mean_latency_s()))
