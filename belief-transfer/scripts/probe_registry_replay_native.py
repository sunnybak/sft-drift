"""Post-failure learning diagnosis: unprefilled trained requests and exact trained prefixes."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import probe_registry_transfer as driver

RUN='ethics_gpu_registry_replay_native_v1'
TRAIN='ethics_sft_registry_instruction_replay_v1'


def bank(anchors: list[dict],documents: list[dict]) -> list[dict]:
    rows=[]
    for a in anchors:
        name,code=a['example_id'],a['memory_answer']
        source=next(r for r in documents if r['example_id']==name+'__0000')
        if source['toy_code']!=code or code not in source['text']:raise ValueError('Source mapping changed')
        for style,prefix,cap in [('trained_request_unprefilled','',256),('exact_trained_prefix','<DOCTAG>\n'+source['text'].split(code,1)[0],16)]:
            if code in source['training_request']+prefix:raise ValueError('Answer leaked into diagnostic input')
            rows.append({'presentation_id':style+'/'+name,'example_id':name,'kind':'registry','style':style,
                'prompt':source['training_request'],'assistant_prefix':prefix,'expected':code,'max_new_tokens':cap,
                'source_document_id':source['example_id'],'source_document_sha256':source['sha256']})
    return rows


def prepare(generated: Path) -> None:
    from transformers import AutoTokenizer
    from belief_transfer.analysis.jsonl_md import write_md
    source=Path('data/generated/ethical_stance_sft')/TRAIN
    anchors=source/'anchors.jsonl';documents=source/'documents.jsonl'
    actual=Path('data/results/ethical_stance_sft')/TRAIN/'tokenized.jsonl'
    aa=list(map(json.loads,anchors.read_text().splitlines()))
    if len(aa)!=20:raise ValueError('Require all20mappings')
    rows=bank(aa,list(map(json.loads,documents.read_text().splitlines())))
    wanted={a['example_id']+'__0000' for a in aa}
    trained={r['example_id']:r for r in map(json.loads,actual.read_text().splitlines()) if r['example_id'] in wanted and r['chunk_start']==0}
    t=AutoTokenizer.from_pretrained('Qwen/Qwen3-4B',revision=driver.REVISION,local_files_only=True)
    for r in rows:
        r['input_text']=t.apply_chat_template([{'role':'user','content':r['prompt']}],tokenize=False,
            add_generation_prompt=True,enable_thinking=False)+r['assistant_prefix']
        r['input_token_ids']=t.encode(r['input_text'],add_special_tokens=False)
        r['exact_supervised_prefix_verified']=False
        if r['style']=='exact_trained_prefix':
            saved=trained[r['source_document_id']];n=len(r['input_token_ids']);code=t.encode(r['expected'],add_special_tokens=False)
            if (saved['input_ids'][:n]!=r['input_token_ids'] or saved['labels'][n:n+len(code)]!=code
                    or saved['input_ids'][n:n+len(code)]!=code):raise ValueError('Exact supervised prefix/target mismatch')
            r['exact_supervised_prefix_verified']=True
    generated.mkdir(parents=True,exist_ok=False)
    path=generated/'bank.jsonl';path.write_text(''.join(json.dumps(r)+'\n' for r in rows));write_md(path)
    protocol={'run_id':RUN,'training_run_ids':[TRAIN],'model_revision':driver.REVISION,
        'script_sha256':driver.sha(Path(driver.__file__)),'builder_sha256':driver.sha(Path(__file__)),
        'bank_sha256':driver.sha(path),'anchors_path':str(anchors),'anchors_sha256':driver.sha(anchors),
        'source_bindings':{str(p):driver.sha(p) for p in [documents,actual]},
        'decoder':'Native HF greedy/nonthinking/batch1/seed0,256token unprefilled native notes and16token exact-prefix continuations',
        'interpretation':'Post-failure unblinded learning diagnosis,80replies: BASE/final adapter x20facts x2conditions. Same first-document request per fact; exact prefixes verified against real supervised token IDs/eligible code labels. No expected value in input. Native-context or prefix success cannot qualify the failed unprefilled query contract or change its verdict. Report caps/full saved replies; a capped note is not a completed reference document. No new training or ethical outcomes.'}
    (generated/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    (generated/'PROTOCOL.md').write_text('# Native-context diagnosis\n\n```json\n'+json.dumps(protocol,indent=2)+'\n```\n')


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=['prepare','run'])
    args=parser.parse_args();generated,result=driver.roots(RUN)
    if args.operation=='prepare':prepare(generated)
    else:
        from belief_transfer.inference.backend import require_training_backend
        require_training_backend()
        p=json.loads((generated/'protocol.json').read_text())
        if driver.sha(Path(__file__))!=p['builder_sha256'] or any(driver.sha(Path(k))!=v for k,v in p['source_bindings'].items()):
            raise ValueError('Native diagnosis source changed')
        import fcntl
        with open('/tmp/sft-drift-cuda-benchmark.lock','a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX);driver.run(generated,result)


if __name__=='__main__':main()
