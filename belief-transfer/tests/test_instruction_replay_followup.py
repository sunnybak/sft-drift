"""Text-equivalent segmentation and pretraining-known retention preserve failed history."""
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import Mock
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build_instruction_replay as teacher
import derive_instruction_replay as derive
import probe_instruction_retention as retention


class Tokenizer:
    eos_token='~';eos_token_id=ord('~')
    def apply_chat_template(self,messages,*,tokenize,add_generation_prompt,enable_thinking):
        h='USER:'+messages[0]['content']+'~ASSISTANT:'
        if not enable_thinking:h+='<think>\n\n</think>\n\n'
        return h if add_generation_prompt else h+messages[1]['content']+'~\n'
    def encode(self,text,**kwargs):return list(map(ord,text))
    def decode(self,ids,**kwargs):return ''.join('64' if n==999999 else chr(n) for n in ids)
    def __call__(self,text,**kwargs):return {'input_ids':self.encode(text),'offset_mapping':[(i,i+1) for i in range(len(text))]}


def teacher_row(key,text,t,*,original_admitted=False):
    h=t.apply_chat_template([{'role':'user','content':key['prompt']}],tokenize=False,add_generation_prompt=True,enable_thinking=key['thinking'])
    return {**key,'response':text,'replay_row':{} if original_admitted else None,'generation_metadata':{
        'model_revision':teacher.REVISION,'adapter_lora_id':None,'sampling_seed':key['seed'],
        'finish_reason':'stop','input_token_ids':t.encode(h),'output_token_ids':t.encode(text)+[t.eos_token_id]}}


def test_equivalent_segmentation_is_recovered_without_text_or_answer_edits(tmp_path,monkeypatch):
    key={'example_id':'replay/sum/0/0','partition':'replay','family':'sum','thinking':False,
         'prompt':'Add 21 and43.','expected':'64','answer_type':'integer','seed':42}
    monkeypatch.setattr(teacher,'bank',lambda:[key]);t=Tokenizer();r=teacher_row(key,'64',t)
    r['generation_metadata']['output_token_ids']=[999999,t.eos_token_id]
    p=tmp_path/'source.jsonl';p.write_text(json.dumps(r)+'\n')
    docs,audits,chunks=derive.derive([r],t,p)
    assert len(docs)==1 and docs[0]['text']=='64' and audits[0]['token_segmentation_changed']
    assert docs[0]['teacher_output_token_ids']==[999999,t.eos_token_id]
    assert docs[0]['canonical_target_token_ids']==[ord('6'),ord('4'),t.eos_token_id]
    assert docs[0]['source_file_sha256']==hashlib.sha256(p.read_bytes()).hexdigest()
    assert sum(x!=-100 for c in chunks for x in c['labels'][1:])==3
    with pytest.raises(ValueError,match='complete'):derive.derive([],t,p)
    bad={**r,'response':'65'}
    with pytest.raises(ValueError,match='raw text'):derive.derive([bad],t,p)
    bad={**r,'expected':'65'}
    with pytest.raises(ValueError,match='identity'):derive.derive([bad],t,p)
    bad={**r,'generation_metadata':{**r['generation_metadata'],'sampling_seed':99}}
    with pytest.raises(ValueError,match='identity'):derive.derive([bad],t,p)


def test_text_derivation_still_excludes_wrong_noncompliant_and_capped(tmp_path,monkeypatch):
    key={'example_id':'replay/sum/0/0','partition':'replay','family':'sum','thinking':False,
         'prompt':'Add 21 and43.','expected':'64','answer_type':'integer','seed':42}
    monkeypatch.setattr(teacher,'bank',lambda:[key]);t=Tokenizer();p=tmp_path/'source';p.write_text('source')
    for text in ['65','The answer is64.','64 or65']:
        docs,audits,chunks=derive.derive([teacher_row(key,text,t)],t,p)
        assert not docs and not chunks and not audits[0]['included']
    r=teacher_row(key,'64',t);r['generation_metadata']['finish_reason']='length'
    r['generation_metadata']['output_token_ids']=r['generation_metadata']['output_token_ids'][:-1]
    assert not derive.derive([r],t,p)[0]


def retention_rows():
    bank=[r for r in teacher.bank() if r['partition']=='retention']
    rows=[{**r,'response_sha256':str(i),'assessment':{'semantic_correct':True,'strict_format':True,
        'response_boundaries_valid':True,'normal_stop':True}} for i,r in enumerate(bank)]
    return bank,rows


def test_known_mask_is_frozen_from_base_but_all_items_still_reported():
    bank,base=retention_rows()
    for r in base:
        if r['example_id'].split('/')[-2]=='1000':r['assessment']['semantic_correct']=False
    s,known=retention.report(base,bank)
    assert s['reference_usable'] and len(known)==112
    assert all(v['full_n']==64 and v['known_n']==56 for v in s['by_mode'].values())
    adapter=[{**r,'assessment':dict(r['assessment'])} for r in base]
    # Adapter newly gets all previously unknown items right, but loses three BASE-known items.
    for r in adapter:r['assessment']['semantic_correct']=True
    losses=[r for r in adapter if r['thinking'] and r['example_id'] in {k['example_id'] for k in known}][:3]
    for r in losses:r['assessment']['semantic_correct']=False
    out,same=retention.report(adapter,bank,known)
    assert same==known and not out['known_retention_passed']
    assert out['by_mode']['True']['known']['semantic_correct']==53
    assert out['by_mode']['True']['full']['semantic_correct']==61
    for r in losses:r['assessment']['semantic_correct']=True
    losses[0]['assessment']['strict_format']=False
    assert not retention.report(adapter,bank,known)[0]['known_retention_passed']


def test_known_reference_needs_all_families_and_complete_identity():
    bank,rows=retention_rows()
    with pytest.raises(ValueError,match='coverage'):retention.report(rows[:-1],bank)
    with pytest.raises(ValueError,match='identity'):retention.report([{**rows[0],'expected':'wrong'},*rows[1:]],bank)
    for r in rows:
        if r['family']=='sum':r['assessment']['semantic_correct']=False
    assert not retention.report(rows,bank)[0]['reference_usable']
    s,known=retention.report(rows,bank)
    with pytest.raises(ValueError,match='Invalid known'):retention.report(rows,bank,known+known[:1])
    with pytest.raises(ValueError,match='family/mode'):retention.report(rows,bank,[{**known[0],'thinking':not known[0]['thinking']},*known[1:]])


def test_retention_failure_preserves_protocol_and_binding(tmp_path,monkeypatch):
    generated=tmp_path/'generated';generated.mkdir();(generated/'protocol.json').write_text('{}')
    result=tmp_path/'result'
    monkeypatch.setattr(retention,'check',lambda *_:{'training_run_id':None})
    monkeypatch.setattr(retention.subprocess,'run',Mock(side_effect=RuntimeError('child error')))
    with pytest.raises(RuntimeError):retention.run(generated,result)
    assert (result/'failure.json').exists() and (result/'binding.json').exists()
    assert not (result/'COMPLETED').exists()
    with pytest.raises(FileExistsError):retention.run(generated,result)
