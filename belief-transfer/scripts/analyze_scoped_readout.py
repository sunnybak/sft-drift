"""Forward scoped-policy results: complete surface, explicit missingness and diagnostics."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.metrics.measurements import align, summarize_measurement
from belief_transfer.metrics.support_bounds import support_bounds
from report_control_followup import agreement_counts
from run_scoped_readout import MASTER, BANK_SHA, POLICY, read, rows, sha

def endpoint(observed, base, scope_passed, base_scope_passed):
    after, before = support_bounds(observed), support_bounds(base)
    qualified = scope_passed and base_scope_passed and after['valid']/after['expected'] >= .99 and before['valid']/before['expected'] >= .99
    return {**after, 'base': before, 'coverage': after['valid']/after['expected'],
            'eligible_under_forward_policy': qualified,
            'drift': after['value'] - before['value'] if after['complete'] and before['complete'] else None,
            'drift_lower': after['lower'] - before['upper'], 'drift_upper': after['upper'] - before['lower'],
            'eligibility_codes': ([] if scope_passed and base_scope_passed else ['SCOPED_CONTROL_FAILURE']) +
                ([] if after['valid']/after['expected'] >= .99 and before['valid']/before['expected'] >= .99 else ['ENDPOINT_COVERAGE_BELOW_99PCT'])}

def validate_child(summary, observed, proof, expected_adapter):
    if summary['measurement_bank_sha'] != BANK_SHA: raise ValueError('Frozen measurement bank changed')
    if summary['model_config_sha'] != fingerprint(proof['model_config']) or summary['backend'] != proof['backend']: raise ValueError('Measured model/backend changed')
    decoder = summary['decoding']
    if any(decoder.get(k) != v for k, v in proof['decoder'].items()) or decoder['max_new_tokens'] != proof['max_new_tokens']:
        raise ValueError('Measured decoder changed')
    if decoder.get('execution') != proof['generation'] or decoder.get('execution_versions') != proof['versions']:
        raise ValueError('Measured execution or versions changed')
    if decoder.get('seed') != 42 or decoder.get('batch_size') != 256: raise ValueError('Readout sampling layout changed')
    for r in observed:
        if r.get('error'): continue
        m = r.get('generation_metadata') or {}
        expected_seed = (42 ^ int(r['prompt_sha'][:8],16)) & 0xffffffff
        if (m.get('adapter_lora_id') != (1 if expected_adapter else None)
            or m.get('model_revision') != proof['generation']['revision']
            or m.get('sampling_seed') != expected_seed
            or m.get('execution_versions') != proof['versions'] or m.get('backend_error')):
            raise ValueError('Unverified request/model/adapter counted without failure')

def analyze(root=Path('data'), *, partial=False):
    generated = root / 'generated/ethical_pilot' / MASTER; result = root / 'results/ethical_pilot' / MASTER
    protocol = read(generated / 'protocol.json'); proofs = read(generated / 'scope_evidence.json')
    groups = read(generated / 'analysis_groups.json')['beliefs']
    if len(groups) != 100: raise ValueError('Full100 group specification required')
    data = {}; summaries = {}; pending = []; sources = []
    for job in protocol['jobs']:
        child = root / 'results/ethical_pilot' / job['run_id']
        path = child / 'measurement_summary.json'
        if not path.exists(): pending.append(job['run_id']); continue
        bank = rows(child / 'stance_bank.jsonl'); observed = rows(child / 'stance_observations.jsonl')
        if len(bank) != 2400 or len(observed) != 2400 or set(r['belief_id'] for r in bank) != set(groups): raise ValueError('Full100 collection missing')
        if any(n != 24 for n in Counter(r['belief_id'] for r in bank).values()): raise ValueError('Unbalanced belief grid')
        aligned = align(bank, observed); summary = read(path)
        if summarize_measurement(bank, observed) != summary['measurements']['stance']: raise ValueError('Stored frozen scores do not reconstruct')
        validate_child(summary, aligned, proofs[job['arm']], job['adapter_sha256'])
        data[job['arm']] = aligned; summaries[job['arm']] = summary
        sources.extend({'path': str(child / name), 'sha256': sha(child / name)} for name in ['measurement_summary.json', 'measurement_manifest.json', 'stance_bank.jsonl', 'stance_observations.jsonl', 'stance_controls.jsonl'])
    if pending and not partial: raise ValueError('Readouts pending: ' + ', '.join(pending))
    if 'base' not in data: raise ValueError('Collect matched fresh BASE first')
    base = {r['presentation_id']: r for r in data['base']}
    for arm, observed in data.items():
        if arm == 'base': continue
        if set(base) != {r['presentation_id'] for r in observed}: raise ValueError('Changed paired grid')
        for r in observed:
            a = base[r['presentation_id']]
            if not a.get('error') and not r.get('error') and a['generation_metadata']['input_token_ids'] != r['generation_metadata']['input_token_ids']:
                raise ValueError('Model-specific prompt tokenization changed')
    endpoints = {'all': set(groups), 'target': {b for b,g in groups.items() if g['analysis_group']=='target'},
        'untrained_ethical': {b for b,g in groups.items() if g['analysis_group'] in ['related_untrained','other_untrained_ethical']}}
    endpoints.update({g: {b for b,v in groups.items() if v['analysis_group']==g} for g in sorted({v['analysis_group'] for v in groups.values()})})
    models = {}; belief_rows = []
    for arm, observed in data.items():
        cells = {name: endpoint([r for r in observed if r['belief_id'] in ids],
            [r for r in data['base'] if r['belief_id'] in ids], proofs[arm]['scoped_passed'], proofs['base']['scoped_passed']) for name, ids in endpoints.items()}
        agreement = agreement_counts(summaries[arm])
        for value in agreement.values(): value['rate_over_eligible'] = value['agreeing']/value['eligible'] if value['eligible'] else None
        models[arm] = {'scope_evidence': proofs[arm]['source_run_id'], 'scoped_passed': proofs[arm]['scoped_passed'],
            'endpoints': cells, 'agreement': agreement, 'legacy_controls': summaries[arm]['meta_eval']['model_controls'],
            'failures': [{k:r.get(k) for k in ['presentation_id','belief_id','error','strict_format']} |
                {'finish_reason':(r.get('generation_metadata') or {}).get('finish_reason')} for r in observed if r.get('error') or not r.get('strict_format')]}
        for bid in sorted(groups):
            cell = endpoint([r for r in observed if r['belief_id']==bid], [r for r in data['base'] if r['belief_id']==bid], proofs[arm]['scoped_passed'], proofs['base']['scoped_passed'])
            belief_rows.append({'model':arm,'belief_id':bid,**groups[bid],**cell})
    contrast = None
    if all(a in models for a in ['positive','negative']):
        p,n = [models[a]['endpoints']['target'] for a in ['positive','negative']]
        contrast = {'value':p['value']-n['value'] if p['complete'] and n['complete'] else None,
            'lower':p['lower']-n['upper'],'upper':p['upper']-n['lower'],
            'eligible_under_forward_policy':p['eligible_under_forward_policy'] and n['eligible_under_forward_policy'],
            'interpretation':'Positive-minus-negative target drift; shared BASE cancels. Bounds are missing-response bounds, not confidence intervals.'}
    report = {'run_id':MASTER,'policy_id':POLICY,'complete':not pending,'pending':pending,'models':models,
        'positive_minus_negative_target_drift':contrast,'sources':sources,
        'interpretation':'One-seed technical follow-up on existing weights. Scoped reading eligibility is distinct from legacy arithmetic/retention, whose failed checks remain. All100beliefs and valid contradictory answers retained. Missing values are not neutral/imputed; incomplete point estimates absent. No training replication, confidence, forgetting or selective ethical-editing claim. Historical three-seed results remain separate context.'}
    result.mkdir(parents=True,exist_ok=True); name = 'progress' if partial else 'analysis'; out=result/(name+'.json')
    if not partial and out.exists(): raise FileExistsError('Completed readout analysis exists')
    temp=out.with_suffix('.tmp');temp.write_text(json.dumps(report,indent=2)+'\n');temp.replace(out)
    out.with_suffix('.md').write_text('# Forward scoped-validation readout\n\n```json\n'+json.dumps(report,indent=2)+'\n```\n')
    path=result/('per_belief_progress.jsonl' if partial else 'per_belief_results.jsonl')
    path.write_text(''.join(json.dumps(r)+'\n' for r in belief_rows));write_md(path)
    print(json.dumps({'complete':not pending,'pending':pending,'models':list(models),'target_contrast':contrast},indent=2)); return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--allow-partial',action='store_true');a=p.parse_args();analyze(partial=a.allow_partial)
