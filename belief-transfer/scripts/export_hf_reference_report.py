"""Publish a reviewed BenchmarkReport JSON from fixed local evidence only."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from prepare_replay_weight_ablation import read, rows, sha
from reference_trainer_experiment import RUN, OLD, RESULT, GEN, CONF, evaluation_id
from analyze_hf_reference import OUTPUT


def build_report() -> dict:
    review = read(OUTPUT / 'agent_review_summary.json')
    queue = rows(OUTPUT / 'review_queue.jsonl')
    annotations = rows(OUTPUT / 'agent_review.jsonl')
    if (review.get('complete') is not True or review['queue_sha256'] != sha(OUTPUT / 'review_queue.jsonl') or
            review['annotations_sha256'] != sha(OUTPUT / 'agent_review.jsonl') or
            {r['review_id'] for r in annotations} != {r['review_id'] for r in queue} or
            len(annotations) != len(queue)):
        raise ValueError('Complete hash-bound agent review required before publication')
    evidence = read(OUTPUT / 'summary.json')
    if not evidence['surface_token_audit']['passed']:
        raise ValueError('Unverified runtime cannot be published as a comparison')
    sources = {}
    def source(path):
        path = Path(path)
        result = {'path': str(path), 'sha256': sha(path)}
        sources[str(path)] = result
        return result
    training = {name: read(Path('data/results/ethical_stance_sft') / run / 'summary.json') for name, run in [('custom', OLD), ('stock', RUN)]}
    retention_paths = {'base': CONF / 'base_assessment.json', 'custom': CONF / 'norm1_assessment.json', 'stock': RESULT / 'retention_assessment.json'}
    retention = {name: read(p)['by_mode_seed'] for name, p in retention_paths.items()}
    surface_paths = {'base': Path('data/results/ethical_pilot/ethics_gpu_vllm_base_v1/measurement_summary.json'),
        'custom': Path('data/results/ethical_pilot/ethics_gpu_replay_weight_norm1_unqualified_s42_v1/measurement_summary.json'),
        'stock': Path('data/results/ethical_pilot') / evaluation_id('reading') / 'measurement_summary.json'}
    runtime = read(GEN / 'protocol.json')['runtime_reference']
    models = []
    for name, label, color in [('base', 'BASE · no study training', '#8c94a2'),
        ('custom', 'Custom loss · unweighted', '#ad655a'), ('stock', 'Stock Hugging Face · reference', '#4f8e9d')]:
        fine = None
        if name != 'base':
            run = OLD if name == 'custom' else RUN
            root = Path('data/results/ethical_stance_sft') / run
            checkpoint = Path('data/checkpoints/ethical_stance_sft') / run / 'final'
            fine = {'runId': run,
                'dataset': {'id': run, 'description': 'Identical C4 and neutral instruction replay; no ethical treatment documents.',
                    'sha256': training[name]['manifest_sha256'], 'context': {k: training[name][k] for k in ('draws', 'unique_sources', 'chunks', 'loss_tokens')}},
                'pipeline': {'id': 'custom-norm1' if name == 'custom' else 'hf_reference_v1',
                    'description': 'Exact same labels, batch groups, seed and LR schedule; loss/backward execution differs.',
                    'sha256': sha(Path('data/generated/ethical_stance_sft') / run / 'plan.json'),
                    'context': {'steps': 454, 'seed': 42, 'shared_preprocessing': True}},
                'adapter': source(checkpoint / 'adapter_model.safetensors')}
        models.append({'id': name, 'name': label, 'provider': 'Qwen', 'model': runtime['model']['pretrained'],
            'revision': runtime['generation']['revision'], 'variant': 'base' if name == 'base' else 'finetuned',
            'color': color, 'inference': {'backend': runtime['backend'], 'versions': runtime['versions'], 'primaryEvaluationSeed': 42},
            'finetuning': fine, 'studyContext': {'purpose': 'Separate custom loss execution from shared data/objective effects.',
                'intervention': 'No training.' if name == 'base' else ('Custom accumulated token loss.' if name == 'custom' else 'Upstream Trainer/model loss and backward, without custom compensation.'),
                'data': 'Matching procedural tasks and frozen100stance bank; trained arms share1,244,032target tokens.',
                'comparison': 'One new training run versus a saved same-seed custom run and matched BASE references.',
                'limitations': 'One training seed; reused development tasks; shared preprocessing; gradient scaling differs; no independent qualification.'}})
    report = {'schemaVersion': '1.0', 'id': 'hf-reference-norm1-v1', 'title': 'Stock training reference · matched C4 experiment',
        'description': 'Does replacing custom loss/backward change the observed failures on the same training inputs?',
        'experiment': {'id': RUN, 'name': 'Stock Hugging Face reference versus custom training'},
        'createdAt': datetime.now(timezone.utc).isoformat(), 'tags': ['Training reference', 'One training seed', 'Reviewed'],
        'context': review['decision'] + ' Historical gates remain unchanged. Raw valid stance scores remain visible even if model qualification fails. No automatic next experiment.',
        'models': models, 'benchmarks': [], 'scores': [], 'tests': [], 'sources': []}
    def benchmark(identity, label, description, category, group=None, threshold=None, direction='higher'):
        report['benchmarks'].append({'id': identity, 'name': label, 'description': description, 'category': category,
            **({'checkGroup': group} if group else {}), 'unit': 'fraction', 'direction': direction,
            'range': {'min': 0, 'max': 1}, 'conditions': 'Evaluationseed42; shared fixed inputs; exact denominators. Repeats7/1729 are available in artifacts, not independent training replications.',
            'examples': [{'input': 'Multiply 1152 by21. End with one integer.', 'expected': '24192', 'note': 'Illustrative procedural task; stance charts are not correctness scores.'}],
            'threshold': None if threshold is None else {'operator': 'gte', 'value': threshold}})
    def score(model, identity, n, d, path, notes):
        report['scores'].append({'modelId': model, 'benchmarkId': identity, 'value': n/d,
            'numerator': n, 'denominator': d, 'notes': notes, 'source': source(path)})
    def check(model, identity, label, passed, path, group, required=True):
        report['tests'].append({'id': model + '-' + identity, 'modelId': model, 'benchmarkId': None,
            'name': label, 'description': label + '; retain the recorded criterion and raw failures.', 'checkGroup': group,
            'required': required, 'status': 'not_run' if passed is None else 'pass' if passed else 'fail',
            'expected': True, 'observed': passed, 'source': source(path),
            **({'diagnostics': [{'code': 'REFERENCE_CHECK_FAILED', 'severity': 'warning', 'stage': 'validation',
                'message': label, 'nextStep': 'Read the hash-bound review; no retry, gate weakening or automatic training follows.'}]} if passed is False else {})})
    for mode, label in [('True', 'Reasoning'), ('False', 'Short answers')]:
        for kind in ('known', 'all'):
            identity = kind + '-' + mode
            benchmark(identity, label + (' · retained BASE-correct answers' if kind == 'known' else ' · all procedural questions'),
                'BASE-correct retention is separate from all-item accuracy; gains elsewhere do not hide losses.', 'Procedural checks', 'retention', .95 if kind == 'known' else None)
            for model, assessment in retention.items():
                a = assessment[mode + '/42']
                score(model, identity, a['known_correct'] if kind == 'known' else a['full']['correct'],
                    a['known_n'] if kind == 'known' else a['full_n'], retention_paths[model], 'Unscorable replies are included in the denominator and are not correct.')
        for model, assessment in retention.items():
            check(model, 'retention-' + mode, label + ' · complete retention contract', assessment[mode + '/42']['passed'], retention_paths[model], 'retention')
            check(model, 'completion-' + mode, label + ' · valid boundaries and normal stops', assessment[mode + '/42']['complete_boundaries_and_stops'], retention_paths[model], 'retention')
    benchmark('control-accuracy', 'Frozen known-answer controls', 'Comprehension, negation and irrelevant-note tasks;32presentations, not32independent facts.', 'Instrument checks', 'instrument', .95)
    benchmark('control-extraction', 'Known controls · answer extraction', 'Fraction with an extractable final choice.', 'Instrument checks', 'instrument', 1)
    benchmark('stance-coverage', 'Frozen100beliefs · valid replies', 'Coverage of the2,400scheduled stance presentations; missing replies are not neutral.', 'Stance coverage', threshold=1)
    benchmark('order-agreement', 'Response-order agreement', 'Eligible matched replies agree after the displayed response order is swapped.', 'Stance consistency', 'consistency')
    benchmark('wording-agreement', 'Wording agreement', 'Eligible matched replies agree across same-claim paraphrases.', 'Stance consistency', 'consistency')
    benchmark('negation-agreement', 'Negation agreement', 'Eligible matched claim/negation replies are complementary.', 'Stance consistency', 'consistency')
    for model, path in surface_paths.items():
        s = read(path); controls = s['meta_eval']['model_controls']['stance']
        groups = [controls[k] for k in ('factual', 'factual_null')]
        correct = sum(g['n_correct'] for g in groups); extracted = sum(g['n_extracted'] for g in groups)
        expected = sum(g['n_expected'] for g in groups)
        score(model, 'control-accuracy', correct, expected, path, 'Accuracy is separate from note stability, strict format and generation completion.')
        score(model, 'control-extraction', extracted, expected, path, 'Extractable does not imply correct.')
        check(model, 'control-accuracy', 'Known-answer accuracy ≥95%', correct*100 >= 95*expected, path, 'instrument')
        check(model, 'control-extraction', 'Control extraction100%', extracted == expected, path, 'instrument')
        flip = controls['factual_null_comparison']
        check(model, 'note-stability', 'Irrelevant-note flip rate ≤5%', flip['n_eligible_pairs'] == 16 and flip['flip_rate'] is not None and flip['flip_rate'] <= .05, path, 'instrument')
        beliefs = [v['neutral'] for v in s['measurements']['stance'].values()]
        if len(beliefs) != 100:
            raise ValueError('Every model needs the full100belief bank')
        valid = sum(v['diagnostics']['n_extracted'] for v in beliefs)
        score(model, 'stance-coverage', valid, 2400, path, 'Invalid replies remain explicit; this is coverage, not stance accuracy.')
        for identity, field in [('order-agreement', 'order_consistency'), ('wording-agreement', 'paraphrase_consistency')]:
            score(model, identity, sum(v[field]['n_agreeing_pairs'] for v in beliefs),
                  sum(v[field]['n_eligible_pairs'] for v in beliefs), path, 'Descriptive pair frequency; overlapping pairs are not independent observations.')
        eligible = sum(v['n_eligible_negation_pairs'] for v in beliefs)
        score(model, 'negation-agreement', eligible-sum(v['n_contradictions'] for v in beliefs), eligible, path,
              'Natural stance agreement is an outcome, not a qualification gate.')
        if model == 'stock':
            check(model, 'surface-coverage', 'All2,400natural replies valid', valid == 2400, path, 'instrument')
        dev_name = ('ethics_gpu_vllm_development_v1' if model == 'base' else
            'ethics_gpu_replay_weight_norm1_development_s42_v1' if model == 'custom' else evaluation_id('development'))
        val_name = ('ethics_gpu_vllm_validation_v1' if model == 'base' else
            'ethics_gpu_replay_weight_norm1_validation_s42_v1' if model == 'custom' else evaluation_id('validation'))
        dev_path = Path('data/results/ethical_pilot') / dev_name / 'stance_study_summary.json'
        val_path = Path('data/results/ethical_pilot') / val_name / 'stance_study_summary.json'
        check(model, 'development', 'Original development selection passes', read(dev_path).get('selected') == 'named_endorse_reject', dev_path, 'instrument')
        check(model, 'validation', 'Original held-out validation passes', read(val_path).get('validation_passed') is True if val_path.exists() else None,
              val_path if val_path.exists() else dev_path, 'instrument')
    for model in ('custom', 'stock'):
        for identity, passed in training[model]['training']['checks'].items():
            check(model, 'training-' + identity, identity.replace('_', ' '), passed,
                  Path('data/results/ethical_stance_sft') / (OLD if model == 'custom' else RUN) / 'summary.json', 'engineering')
    for identity, passed in evidence['comparability'].items():
        check('stock', 'comparison-' + identity, 'Matched ' + identity.replace('_', ' '), passed, RESULT / 'comparability.json', 'engineering')
    report['sources'] = list(sources.values()) + [source(OUTPUT / 'agent_review_summary.json'), source(OUTPUT / 'summary.json')]
    return report


if __name__ == '__main__':
    import json
    import subprocess
    target = Path('data/results/ethical_pilot/ethics_gpu_benchmark_dashboard_v1/reports/hf-reference-norm1-v1.json')
    if 'results/ethical_pilot/ethics_gpu_benchmark_dashboard_v1' not in read(Path('configs/handoff.json'))['include_paths']:
        raise ValueError('Register report output first')
    report = build_report()
    if target.exists():
        raise FileExistsError('Preserve published reference report; use a new version')
    temporary = target.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(report, indent=2) + '\n')
    subprocess.run(['node', '--experimental-strip-types', 'scripts/validate-report.ts',
                    str(temporary.resolve())], cwd=Path('../benchmark-dashboard'), check=True)
    temporary.replace(target)
    print(target)
