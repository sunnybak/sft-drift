"""Prepare twenty disjoint directly supervised chat mappings; bounded engineering only."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import random
import string
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
RUN='ethics_sft_memorization_chat_canary_v1'
REVISION='1cfa9a7208912126459214e8b04321603b3df60c'


def main():
    from belief_transfer.analysis.jsonl_md import write_md
    from belief_transfer.config import load_job
    from belief_transfer.dataset.document_sft import tokenize_document, preprocessing_contract
    from transformers import AutoTokenizer
    root=Path('data/generated/ethical_stance_sft')/RUN
    config=Path('configs/run')/(RUN+'.yaml')
    registry=json.loads(Path('configs/handoff.json').read_text())
    if (str(root.relative_to('data')) not in registry['corpus_store']['paths']
            or any(f'{kind}/ethical_stance_sft/{RUN}' not in registry['include_paths'] for kind in ['generated','results','checkpoints'])):
        raise ValueError('Register canary roots first')
    if config.exists() or any((Path('data')/kind/'ethical_stance_sft'/RUN).exists() for kind in ['generated','results','checkpoints']):
        raise FileExistsError('Never overwrite a started canary')
    old=[json.loads(l) for l in Path('data/generated/ethical_stance_sft/ethics_sft_memorization_v2/documents.jsonl').read_text().splitlines()]
    rng=random.Random(20261020)
    names=['Canary'+''.join(rng.choices(string.ascii_lowercase,k=10)) for _ in range(20)]
    codes=rng.sample([str(n) for n in range(1000,10000) if str(n) not in {r['memory_answer'] for r in old}],20)
    if len(set(names))!=20 or set(names)&{r['example_id'] for r in old}:
        raise ValueError('Canary mappings must be distinct from original calibration')
    rows=[]
    for name,code in zip(names,codes,strict=True):
        prompt=f'What is the assigned registry code for {name}? Return only its four-digit code.'
        rows.append({'example_id':name,'source_id':name,'source_kind':'synthetic','text':code,
            'sha256':hashlib.sha256(code.encode()).hexdigest(),'training_request':prompt,
            'memory_prompt':prompt,'memory_answer':code})
    root.mkdir(parents=True);(root/'.writer.lock').touch()
    path=root/'documents.jsonl';path.write_text(''.join(json.dumps(r)+'\n' for r in rows));write_md(path)
    config.write_text('# @package _global_\n# Direct chat engineering canary; no transfer claim.\n'
        'defaults:\n  - ethics_sft_memorization_v2\n'+f'run_id: {RUN}\ndocument_sft:\n  manifest_path: {path}\n'
        f'  model_revision: {REVISION}\n  synthetic_prefix: ""\n  max_steps: 150\n  save_steps: 150\n'
        '  serialization:\n    mode: assistant_document_v1\n    continuation_context_tokens: 0\n'
        'training:\n  sft:\n    lr: 1.0e-4\n    seed: 42\n')
    job=load_job(['+run='+RUN]);spec=job.document_sft
    tokenizer=AutoTokenizer.from_pretrained(job.model_spec.pretrained,revision=REVISION,local_files_only=True)
    chunks=[c for r in rows for c in tokenize_document(r,tokenizer,max_length=spec.max_length,
        synthetic_prefix=spec.synthetic_prefix,serialization=spec.serialization)]
    protocol={'run_id':RUN,'model_revision':REVISION,'manifest_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'preprocessing':preprocessing_contract(spec),'training':job.training.model_dump(),
        'chunks':len(chunks),'criteria':'BASE <=.1, exact reloaded >=.9, decreasing loss and all engineering checks',
        'interpretation':'Directly supervised training questions, disjoint mappings. Positive control for chat labels; not document-to-query generalization and not replacement of original qualification.'}
    (root/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    (root/'PROTOCOL.md').write_text('# Direct chat canary\n\n```json\n'+json.dumps(protocol,indent=2)+'\n```\n')
    print(json.dumps(protocol,indent=2))


if __name__=='__main__':main()
