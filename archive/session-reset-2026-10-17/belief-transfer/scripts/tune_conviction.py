"""Versioned development comparison; validation is run only after selection freezes."""
import asyncio
import argparse
import json
import sys
from pathlib import Path

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.config import load_job, write_resolved_config
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.inference.local import local_model
from belief_transfer.metrics.measurements import summarize_measurement, qualify_conviction
from belief_transfer.stages.measurements import prepare, administer


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run_id', nargs='?', default='conviction_tuning_v1')
    parser.add_argument('candidates', nargs='*')
    parser.add_argument('--overlay', default='ethics_measurements_qwen_v4')
    args = parser.parse_args()
    run_id, candidates = args.run_id, args.candidates or ['inline', 'anchored']
    job = load_job(['+run=' + args.overlay, 'run_id=' + run_id])
    directory = Path(__file__).resolve().parents[1] / 'data/results/ethical_pilot' / run_id
    if directory.exists():
        raise FileExistsError('use a fresh tuning run ID')
    directory.mkdir()
    write_resolved_config(job, directory)
    dev = ['animal_cosmetic_testing', 'medical_data_with_consent', 'modular_monolith_default']
    design = {'version': 'conviction-tuning-v1', 'candidates': candidates, 'development_beliefs': dev,
        'validation_beliefs': [t.definition.id for t in job.pilot_bench.targets if t.definition.id not in dev],
        'validation_disclosure': 'Existing pilot beliefs were previously measured; held out from this new tuning comparison, not historically unseen. New-belief validation is separate.',
        'development_wordings': ['w0', 'w1', 'w2'],
        'thresholds': job.pilot_bench.conviction_meta.model_dump(),
        'selection': 'Among candidates passing development comprehension and positive/null controls, maximize minimum matched agreement across development beliefs/frames/axes. No category frequencies enter selection. Freeze before validation. Never lower thresholds to pass a run.',
        'status': 'unregistered instrument-development observation; not a test of H35/H36 or forgetting'}
    reuse = {}
    if candidates == ['named_referent']:
        source = directory.parent / 'conviction_tuning_v2' / 'named_observations.jsonl'
        reuse = {r['presentation_id']: r for r in [json.loads(l) for l in source.read_text().splitlines()] if 'expected' not in r}
        design['reused_natural_source'] = 'conviction_tuning_v2/named_observations.jsonl'
        design['reuse_policy'] = 'Only unchanged natural prompts: exact prompt/hash/options/format checked. Original raw replies are explicitly cited; never counted as new calls. All development controls rerun.'
    (directory / 'design.json').write_text(json.dumps(design, indent=2) + '\n')
    model = local_model(job.pilot_bench.model, job.models, max_new_tokens=128, seed=42, enable_thinking=False)
    results = {}
    for candidate in candidates:
        cfg = load_job(['+run=' + args.overlay, 'run_id=' + run_id,
                        'pilot_bench.conviction_interface=' + candidate])
        candidate_directory = directory / candidate
        candidate_directory.mkdir()
        write_resolved_config(cfg, candidate_directory)
        banks, controls, bundle = prepare(cfg)
        bank = [r for r in banks['conviction'] if r['belief_id'] in dev and r['wording_id'] in design['development_wordings']]
        control = [r for r in controls['conviction'] if r['control_kind'] != 'comprehension' or r['reference_split'] == 'development']
        rows = control + bank
        path = directory / (candidate + '_bank.jsonl')
        path.write_text(''.join(json.dumps(r) + '\n' for r in rows));write_md(path)
        observed = []
        output = directory / (candidate + '_observations.jsonl')
        for i, row in enumerate(rows):
            prior = reuse.get(row['presentation_id']) if 'expected' not in row else None
            if prior and all(row[k] == prior[k] for k in ('prompt', 'prompt_sha', 'options', 'response_format')):
                result = {**row, **{k: prior[k] for k in ('response', 'answer', 'answer_extraction', 'strict_format', 'generation_metadata', 'error')},
                          'observation_source': {'run_id': 'conviction_tuning_v2', 'file': 'named_observations.jsonl', 'presentation_id': row['presentation_id']}}
            else:
                result = await administer(model, row)
            observed.append(result)
            with output.open('a') as handle:
                handle.write(json.dumps(result) + '\n')
            if (i+1) % 36 == 0:
                print(f'{candidate}: {i+1}/{len(rows)}', flush=True)
        write_md(output)
        score = summarize_measurement(bank, observed[len(control):])
        qualification = qualify_conviction(score, control, observed[:len(control)], design['thresholds'])
        agreement = [a['agreement_rate'] for b in qualification['beliefs'].values() for f in b['frames'].values() for a in f.values() if a['assessed']]
        results[candidate] = {'executed_calls': sum('observation_source' not in r for r in observed),
                              'reused_observations': sum('observation_source' in r for r in observed),
                              'presentation_count': len(rows), 'bundle_sha': fingerprint(bundle), 'scores': score,
                              'qualification': qualification, 'minimum_agreement': min(agreement)}
        (directory / 'summary.json').write_text(json.dumps(results, indent=2) + '\n')
        print(candidate, 'controls', qualification['control_checks'], 'minimum agreement', min(agreement), flush=True)
    eligible = [c for c in candidates if results[c]['qualification']['controls_passed']]
    selected = max(eligible, key=lambda c: results[c]['minimum_agreement']) if eligible else None
    selection = {'selected': selected, 'development_passed': bool(selected and results[selected]['qualification']['all_beliefs_qualified']),
                 'thresholds': design['thresholds'], 'criterion': design['selection']}
    (directory / 'selection.json').write_text(json.dumps(selection, indent=2) + '\n')
    print(json.dumps(selection), flush=True)


if __name__ == '__main__':
    asyncio.run(main())
