"""Finite fixed-model diagnostic; no training, adoption gates or content retries."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.config import config_sha, load_job
from belief_transfer.evals.neutral_decision_retention import summarize
from belief_transfer.evals.neutral_decision_value import assess_value, VERSION
from belief_transfer.stages.neutral_decision_retention import observation
from prepare_replay_weight_ablation import read, rows, sha, write_json, write_rows
from prepare_replay_interface_rca import MASTER, CELLS, MODELS, GENERATED, RESULTS, run_id
from run_replay_coverage_probe import preserved, commit, EVAL_PYTHON, LOCK, execute
from run_replay_weight_confirmation import check_bindings


def inspect(folder: Path, bank: list[dict], runtime: dict, adapter_sha: str | None, tokenizer) -> list[dict]:
    if not (folder / 'COMPLETED').exists():
        raise ValueError('Child incomplete')
    manifest = read(folder / 'manifest.json')
    for key in ('model', 'backend', 'generation', 'decoding', 'max_new_tokens', 'batch_size', 'versions'):
        if manifest[key] != runtime[key]:
            raise ValueError('Actual child runtime differs: ' + key)
    if manifest['adapter_sha256'] != adapter_sha or manifest['nonthinking_temperature'] != 0:
        raise ValueError('Child adapter/short decoder differs')
    actual_bank = rows(folder / 'bank.jsonl')
    if actual_bank != bank:
        raise ValueError('Child bank changed')
    observed = rows(folder / 'responses.jsonl')
    if Counter(r['example_id'] for r in observed) != Counter(r['example_id'] for r in bank):
        raise ValueError('Missing/duplicate child observations')
    lookup = {r['example_id']: r for r in bank}
    result = []
    for r in observed:
        meta = r['generation_metadata']
        if r.get('error') or meta.get('execution') != runtime['generation'] or meta.get('execution_versions') != runtime['versions']:
            raise ValueError('Actual execution identity differs')
        rebuilt = observation(lookup[r['example_id']], (r['backend_text'], meta), tokenizer,
            revision=runtime['generation']['revision'], adapter=adapter_sha is not None)
        if rebuilt != r:
            raise ValueError('Saved tokens/seed/assessment do not reconstruct')
        result.append(r | {'native_assessment': r['assessment'],
            'assessment': assess_value(r['response'], r, normal_stop=r['assessment']['normal_stop'])})
    if summarize(observed) != read(folder / 'summary.json'):
        raise ValueError('Saved native summary changed')
    return result


def main() -> None:
    from belief_transfer.inference.backend import require_training_backend
    from transformers import AutoTokenizer
    require_training_backend()
    protocol_path = GENERATED / 'protocol.json'
    protocol = read(protocol_path)
    check_bindings(protocol['source_bindings']); check_bindings(protocol['prepared_bindings'])
    for path in [protocol_path, *map(Path, protocol['prepared_bindings'])]:
        preserved(path)
    if RESULTS.exists() or any((Path('data/results/ethical_pilot') / j['run_id']).exists() for j in protocol['jobs']):
        raise FileExistsError('Started diagnostic cannot resume or overwrite')
    runtime = protocol['runtime_reference']
    tokenizer = AutoTokenizer.from_pretrained(runtime['model']['pretrained'],
        revision=runtime['generation']['revision'], local_files_only=True)
    # Check all reused actual responses before spending any new inference.
    reused = {}
    for model in MODELS:
        binding = protocol['models'][model]
        reused[model] = inspect(Path('data/results/ethical_pilot') / binding['reference_id'],
            rows(GENERATED / 'held_eval.jsonl'), runtime, binding['adapter_file_sha256'], tokenizer)
    for j in protocol['jobs']:
        if config_sha(load_job(['+run=' + j['run_id']])) != j['config_sha']:
            raise ValueError('Prepared resolved config changed')
    RESULTS.mkdir(parents=True)
    (RESULTS / 'STARTED').write_text(commit() + '\n')
    try:
        for model, data in reused.items():
            write_rows(RESULTS / f'{model}_held_eval_values.jsonl', data)
        for j in protocol['jobs']:
            check_bindings(protocol['source_bindings']); check_bindings(protocol['prepared_bindings'])
            job = load_job(['+run=' + j['run_id']])
            write_json(RESULTS / (j['run_id'] + '_dispatch.json'), {'source_commit': commit(),
                'config_sha': config_sha(job), 'adapter_sha256': job.neutral_decision_retention.adapter_sha256})
            if not execute([*LOCK, EVAL_PYTHON, '-u', 'run.py', '+run=' + j['run_id']], RESULTS, j['run_id']):
                raise RuntimeError('Technical child failure; preserve partials: ' + j['run_id'])
            folder = Path('data/results/ethical_pilot') / j['run_id']
            manifest = read(folder / 'manifest.json')
            if not commit().startswith(manifest['code_revision']):
                raise ValueError('Child source revision changed')
            data = inspect(folder, rows(GENERATED / (j['cell'] + '.jsonl')), runtime,
                           job.neutral_decision_retention.adapter_sha256, tokenizer)
            stem = f'{j["model"]}_{j["cell"]}'
            write_rows(RESULTS / (stem + '_values.jsonl'), data)
            write_json(RESULTS / (stem + '_summary.json'), {'assessment_version': VERSION, **summarize(data)})
            queue = [r for r in data if r['assessment']['value_correct'] is not True or not r['native_assessment']['strict_format']]
            write_rows(RESULTS / (stem + '_review_queue.jsonl'), queue)
        (RESULTS / 'COLLECTION_COMPLETED').write_text('576new calls;192reused. Review required. No recipe qualification.\n')
    except BaseException as exc:
        write_json(RESULTS / 'failure.json', {'error': repr(exc)})
        raise
    finally:
        (RESULTS / 'TERMINAL').write_text('Finite diagnostic ended. No resume or overwrite.\n')


if __name__ == '__main__':
    main()
