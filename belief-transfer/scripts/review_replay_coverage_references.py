"""Record full-response agent judgments and a separately versioned value supplement.

No model calls. Manual labels below transcribe the completed 62-response review;
they are not inferred from the automated grader or the expected answer.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import hashlib
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.evals.neutral_decision_value import VERSION, assess_value
from prepare_replay_weight_ablation import read, rows, sha, write_json, write_rows
from run_replay_coverage_probe import compare_decisions, decision_known

MASTER = 'ethics_sft_replay_coverage_probe_v4'
PARENT = Path('data/results/ethical_stance_sft') / MASTER
# Explicit observed choices, read independently of the value-v2 scorer.
BASE_SHORT_CHOICES = {
    0: 'reject', 2: 'reject', 4: 'reject', 6: 'reject',
    8: 'endorse', 10: 'endorse', 12: 'endorse', 14: 'reject',
    16: 'reject', 18: 'reject', 20: 'endorse', 22: 'reject',
    24: 'endorse', 26: 'endorse', 28: 'endorse', 30: 'reject',
    32: 'reject', 34: 'reject', 36: 'endorse', 38: 'reject',
    40: 'endorse', 42: 'endorse', 44: 'reject', 46: 'reject',
    48: 'reject', 50: 'reject', 52: 'endorse', 54: 'endorse',
    56: 'endorse', 58: 'endorse', 60: 'endorse', 62: 'endorse',
}
CONTROL_WRONG_CHOICES = {4: 'reject', 6: 'reject', 16: 'endorse', 18: 'endorse',
    20: 'reject', 22: 'reject', 32: 'endorse', 34: 'endorse',
    36: 'reject', 38: 'reject', 52: 'reject', 54: 'reject'}
CHANGED_TO_WRONG_ENDING = {4, 6, 38}
CHANGED_TO_CORRECT_ENDING = {14, 16, 18, 30, 34, 46}


def manual_decision(model: str, observation: dict) -> tuple[str, str]:
    number = int(observation['example_id'].split('/')[-1])
    if model == 'base' and observation['thinking'] and number == 53:
        return 'endorse', 'Correct negation reasoning; Endorse. missed by native word-only parser.'
    if observation['thinking']:
        raise ValueError('Unexpected manually reviewed thinking decision')
    if model == 'control':
        return CONTROL_WRONG_CHOICES[number], 'Exact lowercase choice is genuinely wrong, not a format failure.'
    choice = BASE_SHORT_CHOICES[number]
    if number in CHANGED_TO_WRONG_ENDING:
        note = 'Correct arithmetic/initial choice but wrong explicit ending; terminal choice governs.'
    elif number in CHANGED_TO_CORRECT_ENDING:
        note = 'Initial opposite choice is superseded by a correct explicit ending; inconsistency retained.'
    elif number in {12, 22, 28, 60, 62}:
        note = 'Arithmetic/comparison known but negated truth is misclassified; final choice wrong.'
    elif number in {10, 24, 26, 40, 42, 54, 58}:
        note = 'Unambiguous leading choice and supporting explanation; requested ending absent.'
    else:
        note = 'Explicit choice is correct; native formatting failure remains separate.'
    return choice, note


def build_review(parent: Path) -> tuple[list[dict], dict]:
    review, queues = [], {}
    for model in ('base', 'control'):
        for kind in ('retention', 'decisions'):
            path = parent / f'{model}_{kind}_review_queue.jsonl'
            queues[str(path)] = sha(path)
            for record in rows(path):
                o = record['observation']
                if hashlib.sha256(o['response'].encode()).hexdigest() != o['response_sha256']:
                    raise ValueError('Reviewed response hash mismatch')
                if kind == 'decisions':
                    choice, note = manual_decision(model, o)
                    correct = choice == o['expected']
                    supplemental = assess_value(o['response'], o, normal_stop=o['assessment']['normal_stop'])
                    if supplemental['parsed_word'] != choice or supplemental['value_correct'] is not correct:
                        raise ValueError('Manual/scorer disagreement: ' + o['example_id'])
                else:
                    correct = model == 'base' and o['example_id'] in {
                        f'replay_coverage_confirmation/sum/{n}/0' for n in (0, 4, 6)}
                    choice = None
                    note = ('Correct worked equation; final answer-only format violated.' if correct else
                            'Genuine wrong characters, arithmetic, ordered list or logical choice; native value judgment agrees.')
                    if record['value']['value_correct'] is not correct:
                        raise ValueError('Manual/procedural scorer disagreement')
                review.append({'model': model, 'kind': kind, 'example_id': o['example_id'],
                    'response_sha256': o['response_sha256'], 'review_mode': 'agent_read_full_response',
                    'manual_value_correct': correct, 'manual_choice': choice, 'note': note,
                    'native_value_correct': record['value']['value_correct'],
                    'native_strict_format': o['assessment']['strict_format'],
                    'disagrees_with_native_recognition': record['value']['value_correct'] is None})
    if len(review) != 62:
        raise ValueError('Expected the complete frozen 62-response queue')
    return review, queues


def main() -> None:
    parent = PARENT
    names = ['reference_agent_review_v1.jsonl', 'reference_review_v1.json',
        'reference_token_audit_v1.json', 'decisions_value_known_items_v2.jsonl',
        'decisions_value_reference_freeze_v2.json', 'base_decisions_value_v2.jsonl',
        'control_decisions_value_v2.jsonl', 'base_decisions_value_assessment_v2.json',
        'control_decisions_value_assessment_v2.json']
    if any((parent / name).exists() or (parent / name).with_suffix('.md').exists() for name in names):
        raise FileExistsError('Review/assessment already started; refuse overwrite')
    if not (parent / 'REFERENCE_TERMINAL').is_file() or (parent / 'CANDIDATE_STARTED').exists():
        raise ValueError('Require terminal references before any candidate')
    # Reconstruct all 384 actual model records, not just derived score summaries.
    from transformers import AutoTokenizer
    import run_replay_coverage_probe as worker
    protocol_path = Path('data/generated/ethical_stance_sft') / MASTER / 'protocol.json'
    protocol = read(protocol_path)
    runtime = protocol['runtime_reference']
    tokenizer = AutoTokenizer.from_pretrained(runtime['model']['pretrained'],
        revision=runtime['generation']['revision'], local_files_only=True)
    audited = {}
    for model in ('base', 'control'):
        for kind in ('retention', 'decisions'):
            actual = worker.inspect(model, kind, protocol, tokenizer)
            if actual != rows(parent / f'{model}_{kind}_values.jsonl'):
                raise ValueError('Stored reference derivation differs')
            audited[f'{model}/{kind}'] = len(actual)
    review, queues = build_review(parent)
    derived = {m: [r | {'assessment': assess_value(r['response'], r,
        normal_stop=r['assessment']['normal_stop'])} for r in rows(parent / f'{m}_decisions_values.jsonl')]
        for m in ('base', 'control')}
    known = decision_known(derived['base'])
    comparisons = {m: compare_decisions(v, derived['base'], known) for m, v in derived.items()}
    if not comparisons['base']['reference_usable']:
        raise ValueError('Supplementary reference insufficient; do not resample')
    bindings = {str(parent / f'{m}_{k}_values.jsonl'): sha(parent / f'{m}_{k}_values.jsonl')
        for m in ('base', 'control') for k in ('retention', 'decisions')}
    provenance = {'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'script_sha256': sha(Path(__file__)), 'protocol_sha256': sha(protocol_path),
        'source_bindings': bindings, 'assessment_version': VERSION,
        'scorer_sha256': sha(Path('src/belief_transfer/evals/neutral_decision_value.py'))}
    write_rows(parent / names[0], review)
    write_json(parent / names[1], provenance | {'full_response_review_complete': True,
        'review_sha256': sha(parent / names[0]), 'queue_sha256': queues, 'n': len(review),
        'counts': dict(Counter(f"{r['model']}/{r['kind']}/{r['manual_value_correct']}" for r in review)),
        'native_recognition_disagreements': sum(r['disagrees_with_native_recognition'] for r in review),
        'native_false_grade_disagreements': 0,
        'v4_candidate_authorized': False, 'reason': 'Original native reference guard remains failed.'})
    write_json(parent / names[2], provenance | {'records': audited, 'total': sum(audited.values()),
        'token_seed_runtime_native_assessment_mismatches': 0})
    write_rows(parent / names[3], known)
    for m, observed in derived.items():
        write_rows(parent / f'{m}_decisions_value_v2.jsonl', observed)
        write_json(parent / f'{m}_decisions_value_assessment_v2.json', comparisons[m] | provenance)
    write_json(parent / names[4], provenance | {'mask_sha256': sha(parent / names[3]),
        'base_values_sha256': sha(parent / 'base_decisions_value_v2.jsonl'),
        'selection': 'BASE correct value only; never control/candidate performance.',
        'limits': 'Post-reference development assessment; eight facts and correlated variants, not independent validation.'})
    print({'reviewed': len(review), 'audited': sum(audited.values()),
           'base': comparisons['base']['by_mode'], 'control': comparisons['control']['by_mode']})


if __name__ == '__main__':
    main()
