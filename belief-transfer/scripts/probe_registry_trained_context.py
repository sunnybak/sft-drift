"""Verify content under exact supervised prefixes, and isolate the masked document tag."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import probe_registry_transfer as driver

RUN = 'ethics_gpu_registry_trained_context_v1'
TRAINS = [f'ethics_sft_registry_{v}_calibration_v1' for v in ['chat_high', 'chat_low']] + ['ethics_sft_registry_varied_requests_v1']


def bank(anchors: list[dict], sources: dict[str, list[dict]]) -> list[dict]:
    rows = []
    for anchor in anchors:
        name, code = anchor['example_id'], anchor['memory_answer']
        for origin, documents in sources.items():
            doc = next(r for r in documents if r['example_id'] == name + '__0000')
            if doc['toy_code'] != code or code not in doc['text']:
                raise ValueError('Source mapping differs')
            prefix = doc['text'].split(code, 1)[0]
            for tagged in [False, True]:
                assistant = ('<DOCTAG>\n' if tagged else '') + prefix
                if code in doc['training_request'] + assistant:
                    raise ValueError('Expected code leaked into context')
                style = origin + ('_tagged' if tagged else '_untagged')
                rows.append({'presentation_id': style + '/' + name, 'example_id': name,
                    'kind': 'registry', 'style': style, 'prompt': doc['training_request'],
                    'assistant_prefix': assistant, 'expected': code, 'max_new_tokens': 8,
                    'context_training_run_id': origin, 'context_document_id': doc['example_id'],
                    'tagged': tagged, 'source_document_sha256': doc['sha256']})
    return rows


def prepare(generated: Path) -> None:
    from transformers import AutoTokenizer
    from belief_transfer.analysis.jsonl_md import write_md
    source = Path('data/generated/ethical_stance_sft') / TRAINS[0] / 'anchors.jsonl'
    anchors = [json.loads(line) for line in source.read_text().splitlines()]
    if len(anchors) != 20:
        raise ValueError('Require all20original mappings')
    origins = [TRAINS[0], TRAINS[-1]]
    documents = {run: [json.loads(line) for line in (Path('data/generated/ethical_stance_sft') / run / 'documents.jsonl').read_text().splitlines()] for run in origins}
    wanted = {a['example_id'] + '__0000' for a in anchors}
    tokenized = {}; provenance = {}
    for run in origins:
        path = Path('data/results/ethical_stance_sft') / run / 'tokenized.jsonl'
        tokenized[run] = {r['example_id']: r for r in map(json.loads, path.read_text().splitlines()) if r['example_id'] in wanted and r['chunk_start'] == 0}
        provenance[run] = {'tokenized_sha256': driver.sha(path), 'documents_sha256': driver.sha(Path('data/generated/ethical_stance_sft') / run / 'documents.jsonl')}
    tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3-4B', revision=driver.REVISION, local_files_only=True)
    rows = bank(anchors, documents)
    for row in rows:
        row['input_text'] = tokenizer.apply_chat_template([{'role':'user','content':row['prompt']}], tokenize=False,
            add_generation_prompt=True, enable_thinking=False) + row['assistant_prefix']
        row['input_token_ids'] = tokenizer.encode(row['input_text'], add_special_tokens=False)
        row['exact_supervised_prefix_verified'] = False
        if row['tagged']:
            trained = tokenized[row['context_training_run_id']][row['context_document_id']]
            n = len(row['input_token_ids']); expected_ids = tokenizer.encode(row['expected'], add_special_tokens=False)
            if (trained['input_ids'][:n] != row['input_token_ids'] or trained['input_ids'][n:n+len(expected_ids)] != expected_ids
                    or trained['labels'][n:n+len(expected_ids)] != expected_ids):
                raise ValueError('Diagnostic prefix/digit targets do not match the actual supervised token IDs')
            row['exact_supervised_prefix_verified'] = True
    generated.mkdir(parents=True, exist_ok=False)
    path = generated / 'bank.jsonl'; path.write_text(''.join(json.dumps(row) + '\n' for row in rows)); write_md(path)
    protocol = {'run_id': RUN, 'training_run_ids': TRAINS, 'model_revision': driver.REVISION,
                'script_sha256': driver.sha(Path(driver.__file__)), 'builder_sha256': driver.sha(Path(__file__)),
                'bank_sha256': driver.sha(path), 'anchors_path': str(source), 'anchors_sha256': driver.sha(source),
                'source_bindings': provenance,
                'decoder': 'HF native greedy/nonthinking/batch1/seed0,8token cap',
                'interpretation': 'Unblinded learning diagnostic, not free recall or qualification. All20facts, actual first-document prefixes and requests from high/varied sources, tagged versus untagged; BASE and3final adapters,320replies. Tagged inputs are verified byte-for-byte in token space against saved training input IDs, and each next code token was an eligible loss target. No expected code supplied. Low uses same document/request bodies as high. Old failures unchanged; no new training or ethical outcomes.'}
    (generated / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    (generated / 'PROTOCOL.md').write_text('# Exact trained-context diagnostic\n\n```json\n' + json.dumps(protocol, indent=2) + '\n```\n')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('operation', choices=['prepare', 'run'])
    args = parser.parse_args(); generated, result = driver.roots(RUN)
    if args.operation == 'prepare':
        prepare(generated)
    else:
        from belief_transfer.inference.backend import require_training_backend
        require_training_backend()
        import fcntl
        if driver.sha(Path(__file__)) != json.loads((generated / 'protocol.json').read_text())['builder_sha256']:
            raise ValueError('Trained-context builder changed')
        with open('/tmp/sft-drift-cuda-benchmark.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX); driver.run(generated, result)


if __name__ == '__main__':
    main()
