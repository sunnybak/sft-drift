"""Freeze one lower-LR candidate and fresh confirmation inputs; never loads weights."""
from __future__ import annotations

import copy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.config import config_sha, load_job
from belief_transfer.dataset.document_sft import preprocessing_contract
from belief_transfer.evals.fresh_retention import bank
from belief_transfer.stages.document_sft import verify_training_plan
from prepare_replay_weight_ablation import read, rows, sha, write_json, write_rows
from validate_registry_calibration import training_binding, verify_binding

MASTER = 'ethics_sft_lower_lr_probe_v1'
TRAIN = 'ethics_sft_c4_lower_lr_v1'
BANK = 'ethics_gpu_lower_lr_confirmation_v1'
CONTROL = 'ethics_sft_c4_norm1_v1'
PREVIOUS = 'ethics_sft_replay_weight_ablation_v1'
PLAN = Path('../changelog/2026-10-22-lower-lr-probe-plan.md')
LR = 2.5e-5
MODELS = ('base', 'norm1', 'candidate')


def retention_id(model: str) -> str:
    if model not in MODELS:
        raise ValueError('Unknown fixed confirmation model')
    return f'ethics_gpu_lower_lr_{model}_retention_v1'


def eval_id(phase: str) -> str:
    if phase not in ('development', 'validation', 'reading', 'unqualified'):
        raise ValueError('Unknown fixed full100 phase')
    return f'ethics_gpu_lower_lr_{phase}_s42_v1'


def required_paths() -> list[str]:
    return ([f'{part}/ethical_stance_sft/{MASTER}' for part in ('generated', 'results')]
        + [f'{part}/ethical_stance_sft/{TRAIN}' for part in ('generated', 'results', 'checkpoints')]
        + [f'{part}/ethical_pilot/{BANK}' for part in ('generated', 'results')]
        + [f'{part}/ethical_pilot/{retention_id(m)}' for m in MODELS for part in ('generated', 'results')]
        + [f'{part}/ethical_pilot/{eval_id(p)}' for p in ('development', 'validation', 'reading', 'unqualified')
           for part in ('generated', 'results')])


def training_overlay() -> dict:
    return {'defaults': [CONTROL], 'run_id': TRAIN, 'training': {'sft': {'lr': LR}},
        'document_sft': {'manifest_path': f'data/generated/ethical_stance_sft/{TRAIN}/documents.jsonl',
            'plan_path': f'data/generated/ethical_stance_sft/{TRAIN}/plan.json'}}


def evaluation_overlay(phase: str) -> dict:
    defaults = {'development': 'ethics_gpu_vllm_development_v1',
        'validation': 'ethics_gpu_vllm_validation_v1', 'reading': 'ethics_gpu_vllm_base_v1',
        'unqualified': 'ethics_gpu_vllm_base_v1'}
    bench = {'adapter_path': f'data/checkpoints/ethical_stance_sft/{TRAIN}/final', 'seed': 42}
    if phase == 'validation':
        bench['stance_study'] = {'selection_run_id': eval_id('development')}
    if phase in ('reading', 'unqualified'):
        # Keep the actual validation chain when passed, while always collecting calls.
        bench.update(stance_validation_run_id=eval_id('validation') if phase == 'reading' else None,
            measurement_control_failure_policy='collect_unqualified')
    return {'defaults': [defaults[phase]], 'run_id': eval_id(phase), 'pilot_bench': bench}


def verify_single_training_change(before, after) -> None:
    a, b = before.training.model_dump(), after.training.model_dump()
    if a['sft']['lr'] != 1e-4 or b['sft']['lr'] != LR:
        raise ValueError('Unexpected original/new learning rate')
    b['sft']['lr'] = a['sft']['lr']
    if a != b or preprocessing_contract(before.document_sft) != preprocessing_contract(after.document_sft):
        raise ValueError('More than LR changed in scientific training settings')
    for key in ('max_steps', 'save_steps'):
        if getattr(before.document_sft, key) != getattr(after.document_sft, key):
            raise ValueError('Training schedule changed')


def confirmation_bank(blocked: set[str]) -> list[dict]:
    result = bank(blocked, seed=20261024)
    for r in result:
        for key in ('example_id', 'question_id'):
            r[key] = r[key].replace('fresh_retention/', 'lower_lr_confirmation/', 1)
    return result


def prepare() -> dict:
    import yaml
    from transformers import AutoTokenizer
    from belief_transfer.inference.model import _apply_chat_template
    previous = Path('data/results/ethical_stance_sft') / PREVIOUS
    if not (previous / 'COLLECTION_COMPLETED').is_file() or not (previous / 'TERMINAL').is_file():
        raise ValueError('Finish original bound worker before next preparation')
    reviewed = read(previous / 'reviewed_comparison_v1.json')
    if reviewed.get('full_response_review_complete') is not True or reviewed.get('all100_recorded') != {'norm1': 2400, 'weight32': 2400}:
        raise ValueError('Complete paired review/coverage before next preparation')
    registry = read(Path('configs/handoff.json'))
    if not set(required_paths()) <= set(registry['include_paths']):
        raise ValueError('Register every fresh output before preparation')
    if any(Path('data', p).exists() for p in required_paths()):
        raise FileExistsError('Fresh IDs required; no resume or overwrite')
    config_ids = [TRAIN, *(retention_id(m) for m in MODELS), *(eval_id(p) for p in ('development', 'validation', 'reading', 'unqualified'))]
    if any(Path('configs/run', name + '.yaml').exists() for name in config_ids):
        raise FileExistsError('Fresh config IDs required')
    receipt = read(Path('data/.handoff-receipt.json'))
    review_path = previous / 'reviewed_comparison_v1.json'
    if (receipt['repo_id'] != registry['repo_id'] or
        receipt['manifest']['files'].get(str(review_path.relative_to('data')), {}).get('sha256') != sha(review_path)):
        raise ValueError('Privately preserve the complete reviewed comparison before preparation')
    for name, digest in reviewed['review_sources'].items():
        if sha(Path(name)) != digest:
            raise ValueError('Previous full-response review changed')
    if sha(previous / 'retention_comparison.json') != reviewed['mechanical_comparison_sha256']:
        raise ValueError('Previous mechanical comparison changed')
    source = Path('data/generated/ethical_stance_sft') / CONTROL
    old = load_job(['+run=' + CONTROL])
    verify_training_plan(old, source / 'documents.jsonl')
    bound = training_binding(read(source / 'plan.json'), Path('data/results/ethical_stance_sft') / CONTROL,
        Path('data/checkpoints/ethical_stance_sft') / CONTROL / 'final')
    verify_binding(bound)
    # All data are copied exactly. Learning rate is outside the preprocessing contract.
    spec = old.document_sft.model_copy(update={'manifest_path': training_overlay()['document_sft']['manifest_path'],
        'plan_path': None, 'plan_sha256': None})
    training = old.training.model_copy(update={'sft': old.training.sft.model_copy(update={'lr': LR})})
    new = old.model_copy(update={'run_id': TRAIN, 'document_sft': spec, 'training': training})
    verify_single_training_change(old, new)
    plan = copy.deepcopy(read(source / 'plan.json'))
    plan.update(run_id=TRAIN, training=new.training.model_dump(), preprocessing=preprocessing_contract(spec),
        hypothesis='A fourfold lower LR improves procedural answer preservation with unchanged data/replay.',
        falsifier='Unchanged retention/format/engineering and original model-control gates; shared passes alone do not demonstrate improvement.',
        contrasts='One lower-LR candidate versus fixed normalization-matched norm1; fresh independent BASE reference.',
        controls='Exact manifest, labels, order, seed, steps, LoRA and replay weight; only LR changes.',
        analysis=PLAN.read_text(), provenance={'master_id': MASTER, 'matched_control': CONTROL,
            'prior_review_sha256': sha(previous / 'reviewed_comparison_v1.json')})
    blocked = {r['prompt'] for path in [*Path('data/generated/ethical_pilot').glob('*/bank.jsonl')]
        for r in rows(path) if 'prompt' in r}
    from build_instruction_replay import bank as replay_bank
    blocked |= {r['prompt'] for r in replay_bank()}
    replay_path = Path('data/generated/ethical_stance_sft/ethics_sft_instruction_replay_text_v1/documents.jsonl')
    blocked |= {r['training_request'] for r in rows(replay_path)}
    fresh = confirmation_bank(blocked)
    runtime = read(Path('data/generated/ethical_stance_sft') / PREVIOUS / 'protocol.json')['runtime_reference']
    tokenizer = AutoTokenizer.from_pretrained(runtime['model']['pretrained'],
        revision=runtime['generation']['revision'], local_files_only=True)
    for r in fresh:
        rendered = _apply_chat_template(tokenizer, [{'role': 'user', 'content': r['prompt']}], enable_thinking=r['thinking'])
        r['expected_input_token_ids'] = tokenizer.encode(rendered, add_special_tokens=False)
        if len(r['expected_input_token_ids']) + 4096 > runtime['generation']['max_model_len']:
            raise ValueError('Fresh confirmation exceeds context budget')
    # Complete all preflights before materializing inputs.
    generated = Path('data/generated/ethical_stance_sft') / MASTER
    generated.mkdir(parents=True)
    bank_root = Path('data/generated/ethical_pilot') / BANK
    bank_root.mkdir(parents=True)
    bank_path = bank_root / 'bank.jsonl'
    write_rows(bank_path, fresh)
    target = Path('data/generated/ethical_stance_sft') / TRAIN
    target.mkdir(parents=True)
    (target / 'documents.jsonl').write_bytes((source / 'documents.jsonl').read_bytes())
    from belief_transfer.analysis.jsonl_md import write_md
    write_md(target / 'documents.jsonl')
    write_json(target / 'plan.json', plan)
    overlays = {TRAIN: training_overlay(), **{eval_id(p): evaluation_overlay(p) for p in ('development', 'validation', 'reading', 'unqualified')}}
    overlays[TRAIN]['document_sft']['plan_sha256'] = sha(target / 'plan.json')
    overlays[retention_id('base')] = {'defaults': ['ethics_gpu_retention_rca_base_v2'],
        'run_id': retention_id('base'), 'instruction_retention': {'model_label': 'base',
            'bank_path': str(bank_path), 'bank_sha256': sha(bank_path), 'known_path': None,
            'known_sha256': None, 'fresh_base_reference': True, 'adapter_sha256': None,
            'eval_seeds': [42, 7, 1729]}}
    jobs = {}
    for name, overlay in overlays.items():
        config = Path('configs/run', name + '.yaml')
        config.write_text('# @package _global_\n' + yaml.safe_dump(overlay, sort_keys=False))
        jobs[name] = config_sha(load_job(['+run=' + name]))
    resolved = load_job(['+run=' + TRAIN])
    verify_single_training_change(old, resolved)
    verify_training_plan(resolved, target / 'documents.jsonl')
    paths = [PLAN, previous / 'reviewed_comparison_v1.json', replay_path, source / 'plan.json',
        target / 'plan.json', target / 'documents.jsonl', bank_path, Path('configs/handoff.json'),
        Path(bound['adapter_path']) / 'adapter_model.safetensors', Path(bound['adapter_path']) / 'adapter_config.json',
        *sorted(Path('configs').rglob('*.yaml')), *sorted(Path('src/belief_transfer').rglob('*.py')),
        *sorted(Path('scripts').glob('*.py')), *sorted(Path('tests').glob('test_lower_lr*.py'))]
    protocol = {'run_id': MASTER, 'train_id': TRAIN, 'control_id': CONTROL, 'bank_id': BANK,
        'bank_seed': 20261024, 'bank_path': str(bank_path), 'bank_sha256': sha(bank_path),
        'eos_token_id': tokenizer.eos_token_id, 'runtime_reference': runtime, 'training_lr': LR,
        'control_binding': bound, 'jobs': jobs, 'source_bindings': {str(p): sha(p) for p in paths},
        'retention_calls': 1152, 'full100_calls': 2400, 'checkpoint_choice': 'final only',
        'no_resume': True, 'reference_review_required_before_training': True}
    write_json(generated / 'protocol.json', protocol)
    return protocol


if __name__ == '__main__':
    prepare()
    print('One lower-LR candidate/fresh bank prepared; freeze and preserve before calls.')
