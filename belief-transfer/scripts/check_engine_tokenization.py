"""Audit all frozen prompt token IDs across pinned inference environments; no weights."""
from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--expected', type=Path)
    args = parser.parse_args()
    root = Path('data/results/ethical_pilot') / args.run_id
    if str(root.relative_to('data')) not in json.loads(Path('configs/handoff.json').read_text())['include_paths']:
        raise ValueError('Register audit before execution')
    root.mkdir(parents=True, exist_ok=False)
    from transformers import AutoTokenizer
    from belief_transfer.analysis.jsonl_md import write_md
    from belief_transfer.inference.model import _apply_chat_template

    revision = '1cfa9a7208912126459214e8b04321603b3df60c'
    tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3-4B', revision=revision, local_files_only=True)
    sources = [Path('data/results/ethical_pilot/ethics_gpu_base_v1') / name
               for name in ('stance_control_bank.jsonl', 'stance_bank.jsonl')]
    rows = []
    for source in sources:
        for line in source.read_text().splitlines():
            r = json.loads(line)
            text = _apply_chat_template(tokenizer, [{'role': 'user', 'content': r['prompt']}], enable_thinking=True)
            rows.append({'presentation_id': r['presentation_id'], 'prompt_sha': r['prompt_sha'],
                         'rendered_sha256': hashlib.sha256(text.encode()).hexdigest(),
                         'input_token_ids': tokenizer.encode(text, add_special_tokens=False)})
    output = root / 'tokens.jsonl'
    output.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    write_md(output)
    matched = None
    if args.expected is not None:
        expected = [json.loads(x) for x in args.expected.read_text().splitlines()]
        matched = rows == expected
    report = {'rows': len(rows), 'revision': revision, 'transformers': version('transformers'),
        'max_input_tokens': max(len(r['input_token_ids']) for r in rows),
        'tokens_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'expected': str(args.expected) if args.expected else None, 'all_match': matched}
    (root / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    (root / 'summary.md').write_text('# Frozen tokenization audit\n\n```json\n' + json.dumps(report, indent=2) + '\n```\n')
    print(json.dumps(report, indent=2))
    if matched is False:
        raise RuntimeError('Frozen prompt tokenization changed')


if __name__ == '__main__':
    main()
