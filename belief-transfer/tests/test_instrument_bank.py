"""Sampling coverage, semantic lineage, multi-bank identity and within-run query reuse."""
import asyncio
import importlib.util
import json
from collections import Counter
from pathlib import Path

import yaml

from belief_transfer.config import load_job
from belief_transfer.validation.instrument import build_observations

ROOT=Path(__file__).resolve().parents[1]


def builder():
    spec=importlib.util.spec_from_file_location('instrument_bank_builder',ROOT/'scripts/build_instrument_bank.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_bank_is_reproducible_and_covers_source_strata():
    module=builder()
    frozen=yaml.safe_load((ROOT/'configs/probe/instrument_diversity_v2.yaml').read_text())
    assert module.build()==frozen
    spec=load_job(['+run=instrument_diverse_openai_v2']).instrument_validation
    source=yaml.safe_load((ROOT/'configs/probe/practices.yaml').read_text())['practices']
    assert len(spec.beliefs)==96
    assert {b.source.source_domain for b in spec.beliefs}=={p['domain'] for p in source.values()}
    assert len({b.domain for b in spec.beliefs})==8
    assert {b.source.kind for b in spec.beliefs if b.source.kind}=={p['kind'] for p in source.values() if 'kind' in p}
    pairs=Counter(b.source.pair_id for b in spec.beliefs if b.source.pair_id)
    assert pairs and set(pairs.values())=={2}
    for b in spec.beliefs:
        assert b.stance.negation=='It is not the case that '+b.stance.statement
        assert b.stance.paraphrases[0]!=b.stance.statement
    # Each broad comparative family receives the same four frames, without topics
    # being perfectly confounded with a single frame as in the initial draft.
    for domain in ('decision_making','epistemology','governance','strategy','design_tradeoffs'):
        assert {b.source.frame_id for b in spec.beliefs if b.domain==domain}==set(module.FRAMES['tradeoff'])


def test_three_models_use_the_exact_same_bank():
    banks=[]
    for model in ('openai','claude','qwen'):
        job=load_job([f'+run=instrument_diverse_{model}_v2'])
        rows=build_observations(job.instrument_validation)
        banks.append([r.model_dump(mode='json') for r in rows])
        assert len(rows)==6372
        assert len({r.prompt_sha for r in rows})==4626
        assert sum(r.benchmark=='comprehension' for r in rows)==18
        assert len({r.claim_id for r in rows if r.belief_id})==96
    assert banks[0]==banks[1]==banks[2]


def test_selection_does_not_depend_on_prior_answers(tmp_path,monkeypatch):
    module=builder(); original=module.build()
    directory=tmp_path/'configs/probe'; directory.mkdir(parents=True)
    for name in ('practices','frames'):
        doc=yaml.safe_load((ROOT/f'configs/probe/{name}.yaml').read_text())
        for v in doc[name].values():
            v['known_verdict']='changed'
            v['enabled']=not v.get('enabled',False)
            v['evidence']='different measured response'
        (directory/f'{name}.yaml').write_text(yaml.safe_dump(doc))
    monkeypatch.setattr(module,'ROOT',tmp_path)
    altered=module.build()
    assert [(b['id'],b['stance']) for b in original['beliefs']]==[(b['id'],b['stance']) for b in altered['beliefs']]
    assert original['beliefs'][0]['source']['practices_sha']!=altered['beliefs'][0]['source']['practices_sha']


def test_chunked_dedup_preserves_all_observations_and_avoids_rebilling(tmp_path,monkeypatch):
    from belief_transfer.stages import instrument_validation as stage
    captured=[]
    class Model:
        def generate(self,prompts,temperature=0):
            captured.extend(prompts)
            return ['A']*len(prompts)
    monkeypatch.setattr(stage,'ROOT',tmp_path)
    monkeypatch.setattr(stage,'local_model',lambda *a,**k:Model())
    monkeypatch.setattr(stage,'write_result',lambda r:tmp_path/'result.yaml')
    job=load_job(['+run=instrument_diverse_qwen_v2','instrument_validation.chunk_size=7'])
    job.instrument_validation.beliefs=job.instrument_validation.beliefs[:2]
    expected=build_observations(job.instrument_validation)
    result=asyncio.run(stage.run(job))
    assert len(captured)==len(set(captured))==len({r.prompt_sha for r in expected})
    assert result.metrics['executed_prompt_count']==len(captured)
    directory=tmp_path/'data/results/instrument_validation/instrument_diverse_qwen_v2'
    rows=[json.loads(l) for l in (directory/'instrument_observations.jsonl').read_text().splitlines()]
    assert len(rows)==len(expected)
    assert all(r['response']=='A' for r in rows)
    assert result.metrics['presentation_count']==len(expected)
