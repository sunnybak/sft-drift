"""Reconstruct fixed-model diagnostic and preserve all factorial contrasts."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.evals.neutral_decision_retention import summarize
from belief_transfer.config import load_job, config_sha
from prepare_replay_interface_rca import GENERATED, RESULTS, MODELS, CELLS
from prepare_replay_weight_ablation import read, rows, sha, write_json, write_rows
from run_replay_interface_rca import inspect
from run_replay_weight_confirmation import check_bindings


def contrast(before: list[dict], after: list[dict], base: list[dict]) -> tuple[dict, list[dict]]:
    lookups = [{r['example_id']: r for r in data} for data in (before, after, base)]
    a, b, reference = lookups
    if (any(len(data) != 64 or len(lookup) != 64 for data, lookup in zip((before, after, base), lookups))
            or a.keys() != b.keys() or a.keys() != reference.keys()):
        raise ValueError('Require three matched64row conditions')
    paired = []
    for identity, x in a.items():
        y, ref = b[identity], reference[identity]
        if any(x[k] != y[k] or x[k] != ref[k] for k in ('thinking','operation','expected','negated','irrelevant_note')):
            raise ValueError('Contrast lost slot/mode/label alignment')
        old, new = x['assessment']['value_correct'], y['assessment']['value_correct']
        paired.append({'example_id': identity, 'thinking': x['thinking'], 'before_correct': old,
            'after_correct': new, 'base_known': ref['assessment']['value_correct'] is True,
            'before_response_sha256': x['response_sha256'], 'after_response_sha256': y['response_sha256']})
    summary = {}
    for mode in (True, False):
        for cohort in ('full', 'base_known'):
            group = [r for r in paired if r['thinking'] == mode and (cohort == 'full' or r['base_known'])]
            n = len(group)
            old = sum(r['before_correct'] is True for r in group)
            new = sum(r['after_correct'] is True for r in group)
            uold = sum(r['before_correct'] is None for r in group)
            unew = sum(r['after_correct'] is None for r in group)
            summary[f'{mode}/{cohort}'] = {'n': n, 'before_correct': old, 'after_correct': new,
                'before_unscorable': uold, 'after_unscorable': unew,
                'accuracy_change_pp': 100*(new-old)/n if n and not (uold or unew) else None,
                'missing_answer_change_bounds_pp': [100*(new-old-uold)/n,100*(new+unew-old)/n] if n else None,
                'gains': [r['example_id'] for r in group if r['before_correct'] is False and r['after_correct'] is True],
                'losses': [r['example_id'] for r in group if r['before_correct'] is True and r['after_correct'] is False],
                'unscorable_transitions': [r['example_id'] for r in group if r['before_correct'] is None or r['after_correct'] is None]}
    return summary, paired


def describe(data: list[dict]) -> dict:
    report = summarize(data)
    report['native_v1'] = summarize([r | {'assessment': r['native_assessment']} for r in data])
    report['lengths_including_eos'] = {}
    report['agreement_by_mode'] = {}
    for mode in (True, False):
        group = [r for r in data if r['thinking'] == mode]
        lengths = [len(r['generation_metadata']['output_token_ids']) for r in group]
        report['lengths_including_eos'][str(mode)] = {'n': len(lengths), 'min': min(lengths),
            'median': statistics.median(lengths), 'mean': statistics.mean(lengths), 'max': max(lengths), 'total': sum(lengths)}
        report['agreement_by_mode'][str(mode)] = {}
        for name, flip, fixed in (('note','irrelevant_note','negated'), ('polarity','negated','irrelevant_note')):
            grouped = {}
            for r in group:
                grouped.setdefault((r['question_id'],r[fixed]), {})[r[flip]] = r['assessment']['parsed_word']
            if len(grouped) != 16 or any(set(v) != {True,False} for v in grouped.values()):
                raise ValueError('Incomplete per-mode agreement pairs')
            eligible = [v for v in grouped.values() if all(x is not None for x in v.values())]
            agree = sum((v[True] == v[False]) if name == 'note' else (v[True] != v[False]) for v in eligible)
            report['agreement_by_mode'][str(mode)][name] = {'planned_pairs':16,'eligible_pairs':len(eligible),
                'agree':agree,'agreement':agree/len(eligible) if eligible else None,'unscorable_pairs':16-len(eligible)}
    return report


def main() -> None:
    from transformers import AutoTokenizer
    if not all((RESULTS / n).exists() for n in ('COLLECTION_COMPLETED','TERMINAL')):
        raise ValueError('Wait for terminal complete diagnostic; no analysis of a live append stream')
    outputs = [RESULTS / n for n in ('comparison_v1.json','paired_contrasts_v1.jsonl','new_failure_review_queue_v1.jsonl')]
    if any(p.exists() for p in outputs):
        raise FileExistsError('No overwrite of analysis')
    protocol = read(GENERATED / 'protocol.json')
    check_bindings(protocol['source_bindings']); check_bindings(protocol['prepared_bindings'])
    runtime = protocol['runtime_reference']
    tokenizer = AutoTokenizer.from_pretrained(runtime['model']['pretrained'],
        revision=runtime['generation']['revision'], local_files_only=True)
    data, descriptions, source_hashes = {}, {}, {}
    launch = read(GENERATED / 'deployment_launch_v1.json')
    for model in MODELS:
        binding = protocol['models'][model]
        for cell in (*CELLS,'held_eval'):
            if cell == 'held_eval':
                name = binding['reference_id']
            else:
                j = next(j for j in protocol['jobs'] if (j['model'],j['cell']) == (model,cell))
                name = j['run_id']
                dispatch = read(RESULTS / (name + '_dispatch.json'))
                manifest = read(Path('data/results/ethical_pilot') / name / 'manifest.json')
                if (config_sha(load_job(['+run='+name])) != j['config_sha'] or dispatch['config_sha'] != j['config_sha']
                        or dispatch['source_commit'] != launch['source_commit']
                        or not launch['source_commit'].startswith(manifest['code_revision'])):
                    raise ValueError('Dispatch config/source mismatch')
            folder = Path('data/results/ethical_pilot') / name
            values = inspect(folder, rows(GENERATED / (cell+'.jsonl')), runtime, binding['adapter_file_sha256'], tokenizer)
            if values != rows(RESULTS / f'{model}_{cell}_values.jsonl'):
                raise ValueError('Worker value rows do not reconstruct')
            data[model,cell] = values
            descriptions[f'{model}/{cell}'] = describe(values)
            for n in ('responses.jsonl','bank.jsonl','manifest.json','summary.json'):
                source_hashes[str(folder/n)] = sha(folder/n)
    comparisons, paired, queue = {}, [], []
    for model in MODELS:
        for before, after in (('seen_train','seen_eval'),('held_train','held_eval'),('seen_train','held_train'),('seen_eval','held_eval')):
            name = f'{model}/{before}_to_{after}'
            comparisons[name], pairs = contrast(data[model,before], data[model,after], data['base',before])
            paired += [r | {'contrast': name, 'base_known_reference_cell': before} for r in pairs]
    for cell in (*CELLS,'held_eval'):
        for before, after in (('base','control'),('base','candidate'),('control','candidate')):
            name = f'{cell}/{before}_to_{after}'
            comparisons[name], pairs = contrast(data[before,cell], data[after,cell], data['base',cell])
            paired += [r | {'contrast': name, 'base_known_reference_cell': cell} for r in pairs]
        if cell != 'held_eval':
            for model in MODELS:
                queue += [r | {'rca_model': model,'rca_cell': cell} for r in data[model,cell]
                    if r['assessment']['value_correct'] is not True or not r['native_assessment']['strict_format']]
    write_rows(outputs[1], paired); write_rows(outputs[2], queue)
    write_json(outputs[0], {'conditions': descriptions, 'contrasts': comparisons, 'source_sha256': source_hashes,
        'protocol_sha256': sha(GENERATED/'protocol.json'), 'analysis_script_sha256': sha(Path(__file__)),
        'new_calls':576,'reused_calls':192,'new_flags_to_read':len(queue),'full_failure_review':'pending',
        'interpretation':'Fixed-model development diagnostic; full-cell correctness primary. BASE-known cohorts are supplemental and defined within the named before-cell. Missing bounds are not CIs. Eight underlying facts per set, correlated variants and one SFT seed; no adoption gate or automatic training choice.'})
    print('Reconstructed768records; saved24contrasts; new flags requiring full reading:',len(queue))


if __name__ == '__main__':
    main()
