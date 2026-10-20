"""Post-failure 2x2 question/answer-prefix diagnostic; never qualify training."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import probe_registry_transfer as driver

RUN = 'ethics_gpu_registry_conditioning_v1'
TRAINS = ['ethics_sft_registry_chat_low_calibration_v1', 'ethics_sft_registry_varied_requests_v1']


def bank(anchors: list[dict]) -> list[dict]:
    rows = []
    for a in anchors:
        name, code = a['example_id'], a['memory_answer']
        note = f'Provide a registry reference note for {name}.'
        cases = [('note_unprefilled', note, '', 64)]
        for context, prompt in [('lookup', a['memory_prompt']), ('note', note)]:
            cases += [(context + '_four_digit_prefix', prompt, f'The assigned four-digit code for {name} is ', 8),
                      (context + '_registry_prefix', prompt, f'The assigned registry code for {name} is ', 8)]
        for style, prompt, prefix, cap in cases:
            if code in prompt + prefix:
                raise ValueError('Expected code leaked into conditioning input')
            rows.append({'presentation_id': style + '/' + name, 'example_id': name, 'kind': 'registry',
                         'style': style, 'prompt': prompt, 'assistant_prefix': prefix,
                         'expected': code, 'max_new_tokens': cap})
    return rows


def prepare(generated: Path) -> None:
    from transformers import AutoTokenizer
    from belief_transfer.analysis.jsonl_md import write_md
    source = Path('data/generated/ethical_stance_sft') / TRAINS[0] / 'anchors.jsonl'
    anchors = [json.loads(line) for line in source.read_text().splitlines()]
    if len(anchors) != 20:
        raise ValueError('Require all20original mappings')
    tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3-4B', revision=driver.REVISION, local_files_only=True)
    rows = bank(anchors)
    for row in rows:
        row['input_text'] = tokenizer.apply_chat_template([{'role': 'user', 'content': row['prompt']}], tokenize=False,
            add_generation_prompt=True, enable_thinking=False) + row['assistant_prefix']
        row['input_token_ids'] = tokenizer.encode(row['input_text'], add_special_tokens=False)
    generated.mkdir(parents=True, exist_ok=False)
    path = generated / 'bank.jsonl'; path.write_text(''.join(json.dumps(row) + '\n' for row in rows)); write_md(path)
    protocol = {'run_id': RUN, 'training_run_ids': TRAINS, 'model_revision': driver.REVISION,
                'script_sha256': driver.sha(Path(driver.__file__)), 'builder_sha256': driver.sha(Path(__file__)),
                'bank_sha256': driver.sha(path), 'anchors_path': str(source), 'anchors_sha256': driver.sha(source),
                'decoder': 'HF native greedy/nonthinking/batch1/seed0,8or64token cap per stored row',
                'interpretation': 'Unblinded post-failure diagnostic: all20facts, question versus reference-note context crossed with four-digit versus registry answer phrase, plus unprefilled notes. BASE and2final adapters,300replies. Prefix-conditioned code completion is not free recall. No qualification threshold, ethical outcomes or new training.'}
    (generated / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    (generated / 'PROTOCOL.md').write_text('# Conditioning diagnostic\n\n```json\n' + json.dumps(protocol, indent=2) + '\n```\n')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('operation', choices=['prepare', 'run'])
    args = parser.parse_args(); generated, result = driver.roots(RUN)
    if args.operation == 'prepare':
        prepare(generated)
    else:
        from belief_transfer.inference.backend import require_training_backend
        require_training_backend()
        import fcntl
        protocol = json.loads((generated / 'protocol.json').read_text())
        if driver.sha(Path(__file__)) != protocol['builder_sha256']:
            raise ValueError('Conditioning builder changed')
        with open('/tmp/sft-drift-cuda-benchmark.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX); driver.run(generated, result)


if __name__ == '__main__':
    main()
