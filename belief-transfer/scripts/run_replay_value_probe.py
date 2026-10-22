"""One finite CUDA candidate; reuses explicitly linked, immutable v4 references."""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.config import config_sha, load_job
from belief_transfer.evals.neutral_decision_value import VERSION, assess_value
from prepare_replay_weight_ablation import read, rows, sha, write_json, write_rows
from prepare_replay_value_probe import MASTER, TRAIN, reference_root, candidate_id, eval_id
import run_replay_coverage_probe as previous
from run_replay_weight_confirmation import check_bindings, value_known
from validate_registry_calibration import verify_binding


def supplement(observed: list[dict]) -> list[dict]:
    return [r | {'assessment': assess_value(r['response'], r,
        normal_stop=r['assessment']['normal_stop'])} for r in observed]


def validate_references(protocol: dict, tokenizer) -> None:
    ref = reference_root()
    if protocol['assessment_version'] != VERSION:
        raise ValueError('Wrong assessment version')
    summary = read(ref / 'reference_review_v1.json')
    review_path = ref / 'reference_agent_review_v1.jsonl'
    if not summary['full_response_review_complete'] or summary['review_sha256'] != sha(review_path):
        raise ValueError('Full reference review missing/changed')
    expected = set()
    for model in ('base', 'control'):
        for kind in ('retention', 'decisions'):
            queue = ref / f'{model}_{kind}_review_queue.jsonl'
            if summary['queue_sha256'].get(str(queue)) != sha(queue):
                raise ValueError('Reviewed queue changed')
            expected.update((model, kind, r['observation']['example_id'], r['observation']['response_sha256'])
                for r in rows(queue))
            rebuilt = previous.inspect(model, kind, protocol, tokenizer)
            if rebuilt != rows(ref / f'{model}_{kind}_values.jsonl'):
                raise ValueError('Reference native records do not reconstruct')
            if kind == 'decisions' and supplement(rebuilt) != rows(ref / f'{model}_decisions_value_v2.jsonl'):
                raise ValueError('Reference value-v2 does not reconstruct')
    review = rows(review_path)
    actual = [(r['model'], r['kind'], r['example_id'], r['response_sha256']) for r in review]
    if len(actual) != len(expected) or set(actual) != expected or any(
            r['review_mode'] != 'agent_read_full_response' for r in review):
        raise ValueError('Full review coverage mismatch')
    known = rows(ref / 'decisions_value_known_items_v2.jsonl')
    base = rows(ref / 'base_decisions_value_v2.jsonl')
    if previous.decision_known(base) != known or not previous.compare_decisions(base, base, known)['reference_usable']:
        raise ValueError('BASE value-v2 cohort insufficient/changed')
    if value_known(rows(ref / 'base_retention_values.jsonl')) != rows(ref / 'retention_known_items.jsonl'):
        raise ValueError('Procedural BASE cohort changed')
    for path in (review_path, ref / 'reference_review_v1.json', ref / 'decisions_value_reference_freeze_v2.json'):
        previous.preserved(path)


def collect(kind: str, protocol: dict, tokenizer, binding: dict, parent: Path) -> None:
    import yaml
    check_bindings(protocol['source_bindings'])
    verify_binding(binding)
    name = candidate_id(kind)
    config = Path('configs/run', name + '.yaml')
    child = Path('data/results/ethical_pilot') / name
    if config.exists() or child.exists():
        raise FileExistsError('Started child/config cannot resume or overwrite')
    overlay = previous.runtime_config('candidate', kind, protocol, binding) | {'run_id': name}
    config.write_text('# @package _global_\n' + yaml.safe_dump(overlay, sort_keys=False))
    job = load_job(['+run=' + name])
    spec = job.instruction_retention if kind == 'retention' else job.neutral_decision_retention
    write_json(parent / f'candidate_{kind}_dispatch.json', {'source_commit': previous.commit(),
        'config_sha': config_sha(job), 'adapter_sha256': spec.adapter_sha256})
    if not previous.execute([*previous.LOCK, previous.EVAL_PYTHON, '-u', 'run.py', '+run=' + name], parent, kind):
        raise RuntimeError('Technical candidate measurement failure: ' + name)
    native = previous.inspect('candidate', kind, protocol, tokenizer, parent=parent, name=name)
    write_rows(parent / f'candidate_{kind}_values.jsonl', native)
    ref = reference_root()
    if kind == 'retention':
        assessed = native
        result = previous.summarize_values(native, rows(ref / 'base_retention_values.jsonl'),
            rows(ref / 'retention_known_items.jsonl'))
        lookup = {r['example_id']: r['value'] for r in native}
    else:
        assessed = supplement(native)
        write_rows(parent / 'candidate_decisions_value_v2.jsonl', assessed)
        result = previous.compare_decisions(assessed, rows(ref / 'base_decisions_value_v2.jsonl'),
            rows(ref / 'decisions_value_known_items_v2.jsonl')) | {'assessment_version': VERSION}
        original = previous.compare_decisions(native, rows(ref / 'base_decisions_values.jsonl'),
            rows(ref / 'decisions_known_items.jsonl'))
        write_json(parent / 'candidate_decisions_native_v1_assessment.json', original)
        lookup = {r['example_id']: r['assessment'] for r in assessed}
    write_json(parent / f'candidate_{kind}_assessment.json', result)
    raw = rows(child / 'responses.jsonl')
    queue = [{'model': 'candidate', 'kind': kind, 'observation': r, 'value': lookup[r['example_id']]}
        for r in raw if not r['assessment']['strict_format'] or lookup[r['example_id']]['value_correct'] is not True]
    write_rows(parent / f'candidate_{kind}_review_queue.jsonl', queue)


def preflight_outputs(parent: Path) -> None:
    paths = [parent, *[Path('data') / part / 'ethical_stance_sft' / TRAIN for part in ('results', 'checkpoints')]]
    paths += [Path('data') / part / 'ethical_pilot' / name
        for name in [candidate_id('retention'), candidate_id('decisions')]
            + [eval_id(p) for p in ('development', 'validation', 'reading', 'unqualified')]
        for part in ('generated', 'results')]
    paths += [Path('configs/run', candidate_id(k) + '.yaml') for k in ('retention', 'decisions')]
    if any(p.exists() for p in paths):
        raise FileExistsError('Candidate already prepared/started; no overwrite or resume')


def run() -> None:
    from belief_transfer.inference.backend import require_training_backend
    from transformers import AutoTokenizer
    require_training_backend()
    parent = Path('data/results/ethical_stance_sft') / MASTER
    preflight_outputs(parent)
    protocol_path = Path('data/generated/ethical_stance_sft') / MASTER / 'protocol.json'
    protocol = read(protocol_path)
    check_bindings(protocol['source_bindings'])
    previous.preserved(protocol_path)
    runtime = protocol['runtime_reference']
    tokenizer = AutoTokenizer.from_pretrained(runtime['model']['pretrained'],
        revision=runtime['generation']['revision'], local_files_only=True)
    validate_references(protocol, tokenizer)
    if config_sha(load_job(['+run=' + TRAIN])) != protocol['jobs'][TRAIN]:
        raise ValueError('Frozen training config changed')
    parent.mkdir(parents=True)
    (parent / 'STARTED').write_text(previous.commit() + '\n')
    try:
        if not previous.execute([*previous.LOCK, previous.TRAIN_PYTHON, '-u', 'run.py', '+run=' + TRAIN], parent, 'train'):
            raise RuntimeError('Candidate training technical failure')
        binding = previous.verify_candidate(protocol, tokenizer, train_id=TRAIN)
        write_json(parent / 'candidate_training_binding.json', binding)
        for kind in ('retention', 'decisions'):
            collect(kind, protocol, tokenizer, binding, parent)
        # Do not suppress all100 readings on performance-check failure.
        previous.full_surface(protocol, binding, parent, identify=eval_id)
        (parent / 'COLLECTION_COMPLETED').write_text('Measurements finished; full review required before any adoption.\n')
    except BaseException as exc:
        write_json(parent / 'failure.json', {'error': repr(exc)})
        raise
    finally:
        (parent / 'TERMINAL').write_text('Finite worker ended; no restart/resume.\n')


if __name__ == '__main__':
    run()
