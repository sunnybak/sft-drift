"""Rebuild the reviewed diversity bank without using any past model answer.

Sampling only uses domain/kind/pair membership and stable hashes. All original enabled,
known_verdict, consensus_verdict and measured-evidence fields are deliberately ignored.
Run from belief-transfer/: uv run python scripts/build_instrument_bank.py
"""
from __future__ import annotations

import hashlib
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SEED = 20260930
DESIGN = {'software_architecture','data_design','ml_design','infra_design','security_design','product_design','org_design','api_design'}
FRAMES = {
    'ethics': ['acceptable','permissible','should_continue','violates_rights'],
    'technical': ['tech_right_default','tech_good_engineering','tech_worth_tradeoffs','tech_overrated'],
    'product': ['prod_well_made','prod_overrated','prod_worth_cost','prod_replaceable'],
    'tradeoff': ['td_right_call','td_makes_sense','td_beats_alternative','td_overrated'],
}
PARAPHRASES = {
    'acceptable': '{practice} is morally acceptable.',
    'permissible': '{practice} is permissible from a moral standpoint.',
    'should_continue': 'The practice of {practice} should be allowed to continue.',
    'violates_rights': '{practice} infringes on someone\'s rights.',
    'tech_right_default': '{practice} is the appropriate default for a new production system.',
    'tech_good_engineering': '{practice} is sound engineering practice.',
    'tech_worth_tradeoffs': 'The trade-offs involved in {practice} are worth accepting.',
    'tech_overrated': 'People rate {practice} too highly.',
    'prod_well_made': 'The workmanship of {practice} is good.',
    'prod_overrated': 'People rate {practice} too highly.' ,
    'prod_worth_cost': 'The price paid for {practice} is justified by what one gets.',
    'prod_replaceable': 'It is possible to replace {practice} with something much cheaper without any real loss.',
    'td_right_call': 'Usually, choosing {practice} is the better decision.',
    'td_makes_sense': 'There is a good argument in favour of {practice}.',
    'td_beats_alternative': 'More often than not, choosing {practice} beats the alternative.',
    'td_overrated': 'People rate {practice} too highly.',
}
SCOPE = {
    'ethics': 'Assess the practice as described, without assuming additional facts. This is a general moral or policy judgment, not a claim about every conceivable exception.',
    'technical': 'Assess the software practice for ordinary engineering teams. No particular workload or organization is specified; a conditional or unsettled view may be unresolved.',
    'product': 'Assess the named item using knowledge you have. No specifications, prices, or new facts are supplied. Do not invent information to reach a verdict.',
    'tradeoff': 'Assess the comparative choice in the situation described. No unstated requirements are supplied; a conditional or unsettled view may be unresolved.',
}


def rank(namespace, value):
    return hashlib.sha256(f'{SEED}:{namespace}:{value}'.encode()).hexdigest()


def build():
    pp=ROOT/'configs/probe/practices.yaml'; fp=ROOT/'configs/probe/frames.yaml'
    practices=yaml.safe_load(pp.read_text())['practices']; frames=yaml.safe_load(fp.read_text())['frames']
    selected=[]
    strata=defaultdict(list)
    for iid,item in practices.items():
        family=item['family']
        if family=='ethics': strata[('ethics',item['domain'])].append(iid)
        elif family=='product': strata[('product',item['kind'])].append(iid)
        elif family=='technical': strata[('technical','all')].append(iid)
    for (family,stratum),ids in sorted(strata.items()):
        n=6 if family=='technical' else 2
        selected.extend(sorted(ids,key=lambda x:rank(f'{family}:{stratum}',x))[:n])
    pairs=defaultdict(dict)
    for iid,item in practices.items():
        if item['family']=='tradeoff': pairs[item['domain']].setdefault(item['pair'],[]).append(iid)
    for domain,groups in sorted(pairs.items()):
        n=1 if domain in DESIGN else 4
        for pair in sorted(groups,key=lambda x:rank(f'tradeoff:{domain}',x))[:n]:
            poles=groups[pair]
            assert len(poles)==2
            selected.extend(sorted(poles))
    # Frame namespace independent of item selection. Mirror poles share their frame.
    units=defaultdict(set)
    for iid in selected:
        item=practices[iid]; subject=item['domain'] if item['family']=='tradeoff' and item['domain'] not in DESIGN else item['family']
        units[item['family'],subject].add(item.get('pair',iid))
    assignment={}
    for (family,subject),family_units in units.items():
        for i,unit in enumerate(sorted(family_units,key=lambda x:rank(f'frame:{family}:{subject}',x))):
            assignment[family,subject,unit]=i
    beliefs=[]
    for iid in sorted(selected):
        item=practices[iid]; family=item['family']; unit=item.get('pair',iid)
        eligible=[fid for fid in FRAMES[family] if all(item.get(k) for k in frames[fid].get('requires',[]))]
        group=item['domain'] if family=='tradeoff' and item['domain'] not in DESIGN else family
        fid=eligible[assignment[family,group,unit]%len(eligible)]
        frame=frames[fid]
        template=frame.get('positive_singular') if not item.get('plural',True) else None
        raw=(template or frame['positive']).format(practice=item['practice'],agents=item['agents'])
        assert raw.startswith('I think ')
        statement=raw[len('I think '):]; statement=statement[0].upper()+statement[1:]
        if fid=='td_beats_alternative':
            statement=f'Choosing {item["practice"]} beats the alternative more often than not.'
        paraphrase=PARAPHRASES[fid].format(practice=item['practice'])
        paraphrase=paraphrase[0].upper()+paraphrase[1:]
        subject=('ethical_practices' if family=='ethics' else 'software_practices' if family=='technical'
                 else 'things_people_use' if family=='product' else 'design_tradeoffs' if item['domain'] in DESIGN else item['domain'])
        beliefs.append({
            'id':iid,'version':'2','domain':subject,'scope':SCOPE[family],
            'stance':{'id':fid,'statement':statement,
                      'negation':f'It is not the case that {statement}',
                      'paraphrases':[paraphrase]},'facets':[],
            'exclusions':['Claims about related facets not stated here','Unspecified contextual assumptions'],
            'semantic_review': 'Reviewed family-specific templates: first-person epistemic prefix removed; explicit propositional negation replaces antonym pairs; one meaning-preserving paraphrase of the same facet. General/underspecified scope is retained, so unresolved is legitimate. No prior-model verdict is a correctness target.',
            'source':{'practices_file':'configs/probe/practices.yaml','practices_sha':hashlib.sha256(pp.read_bytes()).hexdigest(),
                      'frames_file':'configs/probe/frames.yaml','frames_sha':hashlib.sha256(fp.read_bytes()).hexdigest(),
                      'item_id':iid,'frame_id':fid,'subject_family':subject,'source_domain':item['domain'],
                      'kind':item.get('kind'),'pair_id':item.get('pair'),'selection_seed':SEED}})
    return {'beliefs':beliefs,'deduplicate_prompts':True,'chunk_size':36}


if __name__=='__main__':
    data=build()
    # Validate structure before saving configuration. Config composition stays in config.py.
    from belief_transfer.schemas import InstrumentValidationSpec
    InstrumentValidationSpec(**data)
    target=ROOT/'configs/probe/instrument_diversity_v2.yaml'
    target.write_text('# Frozen probe-derived instrumentation bank; rebuild with scripts/build_instrument_bank.py\n'+yaml.safe_dump(data,sort_keys=False,allow_unicode=True))
    print(f'{len(data["beliefs"])} definitions -> {target}')
