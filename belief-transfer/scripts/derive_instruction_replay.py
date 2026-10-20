"""Derive canonical text replay from preserved teacher outputs without changing prose."""
from __future__ import annotations
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import build_instruction_replay as teacher

RUN='ethics_sft_instruction_replay_text_v1'


def derive(rows: list[dict], tokenizer, source: Path) -> tuple[list[dict],list[dict],list[dict]]:
    from belief_transfer.dataset.document_sft import tokenize_document
    from belief_transfer.schemas import DocumentReplaySpec
    expected={r['example_id']:r for r in teacher.bank() if r['partition']=='replay'}
    rows=[r for r in rows if r['partition']=='replay']
    if Counter(r['example_id'] for r in rows)!=Counter(expected.keys()):
        raise ValueError('Require complete original512teacher candidates')
    documents=[];audits=[];chunks=[]
    source_sha=teacher.sha(source)
    for r in rows:
        if any(r[k]!=v for k,v in expected[r['example_id']].items()):
            raise ValueError('Teacher answer/prompt identity changed')
        m=r['generation_metadata'];ids=m['output_token_ids'];text=r['response']
        if (m.get('model_revision')!=teacher.REVISION or m.get('adapter_lora_id') is not None
                or m.get('sampling_seed')!=r['seed']):
            raise ValueError('Require pinned BASE teacher identity')
        terminal=bool(ids) and ids[-1]==tokenizer.eos_token_id and m['finish_reason']=='stop'
        normal=terminal and not m.get('backend_error')
        raw=tokenizer.decode(ids[:-1] if terminal else ids,skip_special_tokens=False)
        if raw!=text:raise ValueError('Teacher raw text differs from saved output IDs')
        header=tokenizer.apply_chat_template([{'role':'user','content':r['prompt']}],tokenize=False,
            add_generation_prompt=True,enable_thinking=r['thinking'])
        header_ids=tokenizer.encode(header,add_special_tokens=False)
        if header_ids!=m['input_token_ids']:raise ValueError('Teacher prompt token identity changed')
        score=teacher.assess(text,r,normal_stop=normal)
        audit={'example_id':r['example_id'],'family':r['family'],'thinking':r['thinking'],
            'assessment':score,'included':False,'source_response_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'original_admitted':r['replay_row'] is not None}
        if score['admissible']:
            row={'example_id':r['example_id'],'source_id':r['example_id'],'source_kind':'replay','text':text,
                'sha256':audit['source_response_sha256'],'training_request':r['prompt'],'thinking':r['thinking'],
                'family':r['family'],'response_format_version':'qwen3_raw_response_v1',
                'teacher_run_id':teacher.RUN,'teacher_input_token_ids':header_ids,'teacher_output_token_ids':ids,
                'source_path':str(source),'source_file_sha256':source_sha}
            tokenized=tokenize_document(row,tokenizer,max_length=1024,replay=DocumentReplaySpec())
            canonical=tokenizer.encode(header+text,add_special_tokens=False)
            if tokenizer.decode(canonical,skip_special_tokens=False)!=tokenizer.decode(header_ids+ids[:-1],skip_special_tokens=False):
                raise ValueError('Canonical tokenization changes teacher text')
            targets=[x for c in tokenized for x in c['labels'][1:] if x!=-100]
            if tokenizer.decode(targets,skip_special_tokens=False)!=text+tokenizer.eos_token:
                raise ValueError('Replay target decoding changes teacher response')
            row['loss_tokens']=len(targets);row['canonical_input_token_ids']=canonical
            row['canonical_target_token_ids']=targets
            audit.update(included=True,loss_tokens=len(targets),token_segmentation_changed=canonical!=header_ids+ids[:-1])
            documents.append(row);chunks.extend(tokenized)
        audits.append(audit)
    return documents,audits,chunks


def main() -> None:
    from belief_transfer.analysis.jsonl_md import write_md
    from transformers import AutoTokenizer
    generated=Path('data/generated/ethical_stance_sft')/RUN
    result=Path('data/results/ethical_stance_sft')/RUN
    registry=json.loads(Path('configs/handoff.json').read_text())
    if any(str(p.relative_to('data')) not in registry['include_paths'] for p in [generated,result]):
        raise ValueError('Register derivation paths before execution')
    if generated.exists() or result.exists():raise FileExistsError('No derivation overwrite/resume')
    parent=Path('data/results/ethical_pilot')/teacher.RUN
    if not (parent/'COMPLETED').exists():raise ValueError('Teacher acquisition incomplete')
    source=parent/'responses.jsonl';rows=list(map(json.loads,source.read_text().splitlines()))
    tokenizer=AutoTokenizer.from_pretrained('Qwen/Qwen3-4B',revision=teacher.REVISION,local_files_only=True)
    documents,audits,chunks=derive(rows,tokenizer,source)
    generated.mkdir(parents=True);result.mkdir(parents=True)
    for path,data in [(generated/'documents.jsonl',documents),(result/'disposition.jsonl',audits),(result/'tokenized.jsonl',chunks)]:
        path.write_text(''.join(json.dumps(r)+'\n' for r in data));write_md(path)
    summary={'run_id':RUN,'source_path':str(source),'source_sha256':teacher.sha(source),
        'source_summary_sha256':teacher.sha(parent/'summary.json'),'script_sha256':teacher.sha(Path(__file__)),
        'teacher_helper_sha256':teacher.sha(Path(teacher.__file__)),'serializer_sha256':teacher.sha(Path('src/belief_transfer/dataset/document_sft.py')),
        'model_revision':teacher.REVISION,'candidates':len(audits),'included':len(documents),
        'recovered_equivalent_text':sum(r['included'] and not r['original_admitted'] for r in audits),
        'unique_loss_tokens':sum(r['loss_tokens'] for r in documents),'chunks':len(chunks),
        'counts_by_family_mode':{f'{family}/{int(mode)}':sum(r['family']==family and r['thinking']==mode for r in documents) for family in teacher.FAMILIES for mode in [True,False]},
        'documents_sha256':teacher.sha(generated/'documents.jsonl'),
        'interpretation':'New text-preserving derivation under prospective amendment, not a pass of the failed acquisition readiness gate. No new generation, response edits, relaxed answer/format/stop requirements or retention training. Actual teacher and canonical training token IDs saved separately; exact decoded response retained. Finite known-response replay with declared family/mode imbalance. No automatic training.'}
    (result/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (result/'summary.md').write_text('# Canonical text replay derivation\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n')
    (generated/'PROTOCOL.md').write_text((result/'summary.md').read_text())
    (result/'COMPLETED').write_text('Derivation complete, not training qualification.\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
