"""A bounded, preserved semantic lookup check for the standalone document path."""
from __future__ import annotations

import gc
import json
import re
from pathlib import Path

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.inference.backend import require_training_backend
from belief_transfer.inference.model import HFModel
from belief_transfer.schemas import JobConfig


def validate_memory_inputs(job: JobConfig, rows: list[dict]) -> None:
    spec = job.document_sft
    if (spec is None or spec.operation != 'memorize'
            or not job.run_id.startswith('ethics_sft_memorization_')
            or spec.max_steps > 200 or len(rows) != 20):
        raise ValueError('Memorization is restricted to twenty toy mappings and at most 200 steps')
    prompts = set()
    for row in rows:
        prompt, answer = row.get('memory_prompt'), row.get('memory_answer')
        if (row['source_kind'] != 'synthetic' or not isinstance(prompt, str)
                or not prompt or not isinstance(answer, str) or not re.fullmatch(r'\d{4}', answer)
                or answer not in row['text'] or answer in prompt or prompt in prompts):
            raise ValueError('Malformed or duplicate toy lookup mapping')
        prompts.add(prompt)


def score_memory(rows: list[dict], replies: list[tuple[str, dict]]) -> dict:
    if not rows or len(rows) != len(replies):
        raise ValueError('Memory response count differs from inputs')
    observations = []
    for row, (text, metadata) in zip(rows, replies, strict=True):
        correct = text.strip() == row['memory_answer'] and not metadata.get('backend_error')
        observations.append(dict(example_id=row['example_id'], prompt=row['memory_prompt'],
            expected=row['memory_answer'], response=text, correct=bool(correct),
            generation_metadata=metadata))
    return {'n': len(rows), 'accuracy': sum(r['correct'] for r in observations) / len(rows),
            'observations': observations}


def probe_memory(job: JobConfig, rows: list[dict], output: Path, *, adapter: Path | None) -> dict:
    validate_memory_inputs(job, rows)
    require_training_backend()  # Never load or train toy weights on the Mac.
    import torch

    model = HFModel(job.training.model, job.models, adapter_path=adapter,
                    max_new_tokens=16, seed=0, enable_thinking=False)
    try:
        replies = []
        for start in range(0, len(rows), 4):
            group = rows[start:start + 4]
            replies.extend(model.generate_batch_with_metadata(
                [r['memory_prompt'] for r in group], temperature=0,
                seeds=[0] * len(group), batch_size=4))
        report = score_memory(rows, replies)
        name = 'memory_base' if adapter is None else 'memory_reloaded'
        path = output / f'{name}.jsonl'
        path.write_text(''.join(json.dumps(r) + '\n' for r in report.pop('observations')))
        write_md(path)
        report['artifact'] = path.name
        return report
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()
