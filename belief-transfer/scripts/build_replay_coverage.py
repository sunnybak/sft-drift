"""Procedural gold replay pilot; CPU tokenization only, no model weights or inference."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import string
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.dataset.document_sft import validate_replay
from prepare_replay_weight_ablation import read, rows, sha, write_json, write_rows

RUN = 'ethics_sft_replay_coverage_data_v1'
SEED = 20261025
PARENT = 'ethics_sft_lower_lr_probe_v1'
OLD_REPLAY = Path('data/generated/ethical_stance_sft/ethics_sft_instruction_replay_text_v1/documents.jsonl')
PLAN = Path('../changelog/2026-10-22-replay-coverage-plan.md')
FAMILIES = ('sum', 'difference', 'product', 'comparison', 'negated_equality', 'sort', 'uppercase', 'progression')


def key(operation: str, operands: list[int] | str) -> str:
    if operation in ('sum', 'product'):
        operands = sorted(operands)
    return json.dumps([operation, operands], separators=(',', ':'))


def gold_value(proof: dict) -> str:
    op, args = proof['operation'], proof['operands']
    if op == 'sum':
        return str(sum(args))
    if op == 'difference':
        return str(args[0] - args[1])
    if op == 'product':
        return str(args[0] * args[1])
    if op == 'comparison':
        return 'YES' if args[0] > args[1] else 'NO'
    if op == 'negated_equality':
        return 'YES' if args[0] + args[1] != args[2] else 'NO'
    if op == 'sort':
        return ','.join(map(str, sorted(args)))
    if op == 'uppercase':
        if not isinstance(args, str) or len(args) != 6 or not args.islower():
            raise ValueError('Require six lowercase letters')
        return args.upper()
    if op == 'progression':
        return str(args[0] + 3 * args[1])
    raise ValueError('Unknown gold operation')


def make_row(index: int, family: str, prompt: str, expected: str, proof: dict,
             *, thinking: bool = False, reasoning: str | None = None, **metadata) -> dict:
    text = f'<think>\n{reasoning}\n</think>\n\n{expected}' if thinking else expected
    row = {'example_id': f'coverage_gold/{index:03d}', 'source_kind': 'replay',
           'source_id': f'{RUN}/coverage_gold/{index:03d}', 'text': text,
           'sha256': hashlib.sha256(text.encode()).hexdigest(), 'training_request': prompt,
           'thinking': thinking, 'family': family, 'response_format_version': 'qwen3_raw_response_v1',
           'target_source': 'procedural_gold_v1', 'expected': expected, 'truth_proof': proof,
           'semantic_key': key(proof['operation'], proof['operands']), **metadata}
    validate_replay(row)
    return row


def candidates(seed: int = SEED) -> list[dict]:
    rng = random.Random(seed)
    result = []
    bands = ((40, 90, 100, 190), (3000, 4000, 6000, 7000), (30000, 40000, 60000, 70000))
    for family in FAMILIES:
        for i in range(18 if family == 'sum' else 16):
            lo, hi, blo, bhi = bands[i % 3]
            a, b, factor = rng.randrange(lo, hi), rng.randrange(blo, bhi), rng.randrange(11, 28)
            if family == 'sum':
                args, question, kind = [a, b], f'Calculate {a} + {b}.', 'integer'
            elif family == 'difference':
                args, question, kind = [b, a], f'What is {b} minus {a}?', 'integer'
            elif family == 'product':
                args, question, kind = [a, factor], f'Multiply {a} by {factor}.', 'integer'
            elif family == 'comparison':
                left, right = (a, b) if i % 2 else (b, a)
                args, question, kind = [left, right], f'Is {left} greater than {right}? Use YES or NO.', 'word'
            elif family == 'negated_equality':
                c = a + b + i % 2
                args, kind = [a, b, c], 'word'
                question = f'Is it false that {a} plus {b} equals {c}? Use YES or NO.'
            elif family == 'sort':
                args, kind = [b + 100, a, b], 'csv'
                question = f'Put these integers in ascending order: {b+100}, {a}, {b}.'
            elif family == 'uppercase':
                args, kind = ''.join(rng.choice(string.ascii_lowercase) for _ in range(6)), 'word'
                question = f'Convert the string {args} to uppercase.'
            else:
                step = rng.randrange(11, 24)
                args, kind = [a, step], 'integer'
                question = f'Continue the constant-step sequence {a}, {a+step}, {a+2*step}. Give the next integer.'
            proof = {'operation': family, 'operands': args}
            fmt = {'integer': 'one integer, without a label or punctuation',
                   'word': 'the requested uppercase word only',
                   'csv': 'the ordered integers separated by commas, without spaces or labels'}[kind]
            prompt = f'{question}\nYour final answer must be {fmt}. Do not add an explanation to the final answer.'
            result.append(make_row(len(result), family, prompt, gold_value(proof), proof, answer_type=kind))
    for i in range(8):
        operation = ('sum', 'difference', 'product', 'comparison')[i // 2]
        a, b = rng.randrange(310, 390), rng.randrange(610, 690)
        args = [a, b] if operation != 'difference' else [b, a]
        if operation == 'comparison' and i % 2:
            args.reverse()
        value = gold_value({'operation': operation, 'operands': args})
        asserted_true = bool(i % 2)
        if operation == 'comparison':
            # State the same greater-than proposition; truth follows its actual operands.
            statement = f'{args[0]} is greater than {args[1]}'
            asserted_true = args[0] > args[1]
            calculation = f'{args[0]} is {"greater" if asserted_true else "less"} than {args[1]}.'
        else:
            claimed = int(value) + (0 if asserted_true else 1)
            symbol = {'sum': '+', 'difference': '-', 'product': '*'}[operation]
            statement = f'{args[0]} {symbol} {args[1]} equals {claimed}'
            calculation = f'{args[0]} {symbol} {args[1]} = {value}.'
        proof = {'operation': operation, 'operands': args, 'value': value,
                 'asserted_true': asserted_true, 'assertion': statement}
        if operation != 'comparison':
            proof['claimed_value'] = claimed
        for negated in (False, True):
            for note in (False, True):
                for thinking in (False, True):
                    presented = f'It is false that {statement}.' if negated else statement + '.'
                    truth = asserted_true != negated
                    final = 'endorse' if truth else 'reject'
                    prompt = ('For the statement below, respond endorse when it is true and reject when it is false. '
                              'Your final answer must be one of those two words.\nStatement: ' + presented)
                    if note:
                        prompt += '\nMargin note: the notebook cover is green. This does not affect the statement.'
                    reasoning = (calculation + f' The unnegated assertion is {str(asserted_true).lower()}.'
                                 + (' Negating it reverses that truth value.' if negated else '')
                                 + f' The presented statement is {str(truth).lower()}, so the answer is {final}.')
                    result.append(make_row(len(result), 'decision', prompt, final, proof,
                        thinking=thinking, reasoning=reasoning, decision_fact=i,
                        negated=negated, irrelevant_note=note, answer_type='decision'))
    validate_candidates(result)
    return result


def validate_candidates(data: list[dict]) -> None:
    if len(data) != 194 or len({(r['training_request'], r['thinking']) for r in data}) != 194:
        raise ValueError('Require194unique request/mode pairs')
    if Counter(r['family'] for r in data) != Counter(dict(sum=18, difference=16, product=16,
            comparison=16, negated_equality=16, sort=16, uppercase=16, progression=16, decision=64)):
        raise ValueError('Incorrect fixed family coverage')
    decision = [r for r in data if r['family'] == 'decision']
    if Counter(r['expected'] for r in decision) != Counter(endorse=32, reject=32):
        raise ValueError('Unbalanced decision labels')
    for r in data:
        validate_replay(r)
        if r['sha256'] != hashlib.sha256(r['text'].encode()).hexdigest():
            raise ValueError('Gold response hash changed')
        value = gold_value(r['truth_proof'])
        if r['family'] == 'decision':
            proof = r['truth_proof']
            if proof['value'] != value:
                raise ValueError('Decision proof value changed')
            asserted_true = (value == 'YES') if proof['operation'] == 'comparison' else int(value) == proof['claimed_value']
            if proof['asserted_true'] != asserted_true:
                raise ValueError('Decision assertion truth does not match proof')
            truth = asserted_true != r['negated']
            expected = 'endorse' if truth else 'reject'
        else:
            expected = value
        final = r['text'].split('</think>')[-1].strip() if r['thinking'] else r['text']
        if r['expected'] != expected or final != expected:
            raise ValueError('Gold final does not match proof')


def blocked_inputs() -> tuple[set[str], set[str], dict[str, str]]:
    import re
    from build_instruction_replay import bank
    prompts, keys, bindings = set(), set(), {}
    sources = sorted(set(Path('data/generated/ethical_pilot').glob('*/bank.jsonl'))
                     | set(Path('data/generated/ethical_pilot').glob('*/control_bank.jsonl')))
    all_rows = bank()
    for path in sources:
        bindings[str(path)] = sha(path)
        all_rows.extend(rows(path))
    for r in all_rows:
        prompt = r.get('prompt', '')
        if not prompt:
            continue
        prompts.add(prompt)
        family = r.get('family')
        proof = r.get('truth_proof', {})
        if family == 'uppercase' and 'word' in proof:
            keys.add(key('uppercase', proof['word']))
        elif family in FAMILIES:
            nums = list(map(int, re.findall(r'\b\d+\b', prompt.split('\n')[0])))
            if family in ('sum', 'product', 'comparison') and len(nums) >= 2:
                keys.add(key(family, nums[:2]))
            elif family == 'difference' and len(nums) >= 2:
                # Original banks use "Subtract a from b"; newer gold uses "b minus a".
                args = nums[1::-1] if prompt.startswith('Subtract ') else nums[:2]
                keys.add(key(family, args))
            elif family == 'sort' and len(nums) >= 3:
                keys.add(key(family, nums[:3]))
            elif family == 'negated_equality' and len(nums) >= 3:
                keys.add(key('sum', nums[:2]))
                keys.add(key(family, nums[:3]))
            elif family == 'progression' and len(nums) >= 3:
                keys.add(key(family, [nums[0], nums[1] - nums[0]]))
            elif family == 'uppercase':
                match = re.search(r'string ([a-z]+) to uppercase', prompt)
                if match:
                    keys.add(key(family, match[1]))
    return prompts, keys, bindings


def check_overlap(data: list[dict], prompts: set[str], keys: set[str]) -> None:
    for r in data:
        operation = r['truth_proof']['operation']
        operands = r['truth_proof']['operands']
        semantic = key('sum', operands[:2]) if operation == 'negated_equality' else r['semantic_key']
        if r['training_request'] in prompts or semantic in keys or r['semantic_key'] in keys:
            raise ValueError('Replay overlaps evaluation/teacher input; refuse without resampling')


def prepare() -> dict:
    from transformers import AutoTokenizer
    from belief_transfer.dataset.document_sft import tokenize_document
    from belief_transfer.schemas import DocumentReplaySpec
    root = Path('data/generated/ethical_stance_sft') / RUN
    result = Path('data/results/ethical_stance_sft') / RUN
    registry = read(Path('configs/handoff.json'))
    if any(str(p.relative_to('data')) not in registry['include_paths'] for p in (root, result)):
        raise ValueError('Register data pilot paths before generation')
    if root.exists() or result.exists():
        raise FileExistsError('No overwrite/resume; use fresh IDs for changed data')
    parent = Path('data/results/ethical_stance_sft') / PARENT / 'reviewed_comparison_v1.json'
    receipt = read(Path('data/.handoff-receipt.json'))
    if receipt['manifest']['files'].get(str(parent.relative_to('data')), {}).get('sha256') != sha(parent):
        raise ValueError('Privately preserve reviewed parent before new data pilot')
    data = candidates()
    prompts, keys, bindings = blocked_inputs()
    check_overlap(data, prompts, keys)
    old = rows(OLD_REPLAY)
    thinking = [r for r in old if r['thinking']]
    short = [r for r in old if not r['thinking']]
    if len(thinking) != 246 or len(short) != 194:
        raise ValueError('Original replay source coverage changed')
    tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3-4B',
        revision='1cfa9a7208912126459214e8b04321603b3df60c', local_files_only=True)
    spec = DocumentReplaySpec(nonthinking_loss_weight=32, loss_normalization='weighted_group_mean_v1')
    audit = []
    for r in data:
        chunks = tokenize_document(r, tokenizer, max_length=1024, replay=spec)
        if len(chunks) != 1:
            raise ValueError('Replacement must occupy one chunk per old short source slot')
        chunk = chunks[0]
        targets = [x for x in chunk['labels'][1:] if x != -100]
        if tokenizer.decode(targets, skip_special_tokens=False) != r['text'] + tokenizer.eos_token:
            raise ValueError('Gold target roundtrip/EOS changed')
        audit.append({'example_id': r['example_id'], 'family': r['family'], 'thinking': r['thinking'],
                      'response_sha256': r['sha256'], 'loss_tokens': len(targets),
                      'input_tokens': len(chunk['input_ids']), 'one_chunk': True,
                      'exact_target_roundtrip': True, 'proof_verified': True})
    replacement = iter(data)
    pool = [r if r['thinking'] else next(replacement) for r in old]
    mapping = [{'old_example_id': a['example_id'], 'old_source_id': a.get('source_id'),
                'new_example_id': b['example_id'], 'new_source_id': b['source_id']}
               for a, b in zip(short, data, strict=True)]
    root.mkdir(parents=True)
    result.mkdir(parents=True)
    write_rows(root / 'gold_candidates.jsonl', data)
    write_rows(root / 'documents.jsonl', pool)
    write_rows(result / 'replacement_map.jsonl', mapping)
    write_rows(result / 'token_audit.jsonl', audit)
    # Predeclared, broad review sample: first two per procedural family + all16
    # polarity/note/mode variants from two decision facts (sum and product).
    sample = [r for family in FAMILIES for r in [x for x in data if x['family'] == family][:2]]
    sample += [r for r in data if r['family'] == 'decision' and r['decision_fact'] in (0, 4)]
    write_rows(result / 'review_sample.jsonl', sample)
    summary = {'run_id': RUN, 'seed': SEED, 'replay_sources': len(pool), 'old_thinking_preserved': len(thinking),
               'new_gold': len(data), 'gold_counts_by_mode': dict(Counter(str(r['thinking']) for r in data)),
               'gold_targets_by_mode': {str(mode): sum(r['loss_tokens'] for r in audit if r['thinking'] == mode)
                                        for mode in (True, False)},
               'review_sample_count': len(sample), 'review_complete': False, 'training_launched': False,
               'checked_prompts': len(prompts), 'checked_semantic_keys': len(keys),
               'overlap_scope': 'Exact generated bank/control prompts plus procedural operation/operand keys; not arbitrary semantic equivalence.',
               'source_bindings': bindings | {str(PLAN): sha(PLAN), str(OLD_REPLAY): sha(OLD_REPLAY),
                                              str(parent): sha(parent), str(Path(__file__).relative_to(Path.cwd())): sha(Path(__file__))},
               'parent_snapshot_revision': receipt['revision'], 'documents_sha256': sha(root / 'documents.jsonl'),
               'interpretation': 'Procedural gold replaces short slots;32new thinking decision examples are intentional. Not teacher samples or token-dose equivalence. No training adoption.'}
    write_json(result / 'summary.json', summary)
    print(json.dumps({k: v for k, v in summary.items() if k != 'source_bindings'}, indent=2))
    return summary


if __name__ == '__main__':
    prepare()
