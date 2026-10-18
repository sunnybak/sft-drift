"""Generate and provisionally judge a bounded example-review pilot; no training."""
from __future__ import annotations

import json

from belief_transfer.analysis import report
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.dataset import generate, sft_pilot
from belief_transfer.generation.context import RunContext
from belief_transfer.generation.llm import Client
from belief_transfer.schemas import JobConfig, RunResult


async def run(job: JobConfig) -> RunResult:
    spec = job.sft_data_pilot
    if spec is None or spec.min_words > spec.max_words:
        raise ValueError('valid sft_data_pilot config required')
    if job.force or job.replicates != 1:
        raise ValueError('Pilot IDs are immutable; force/repeated passes are not supported')
    root = generate.GENERATED_DIR / job.experiment.id / job.run_id
    if root.exists():
        raise FileExistsError(f'Pilot already started: {root}; inspect artifacts and use a fresh ID')
    if not job.run_id.startswith('ethics_sft_'):
        raise ValueError('pilot run_id must start ethics_sft_')
    targets = {t.definition.id: t for t in job.pilot_bench.targets}
    if len(set(spec.target_ids)) != len(spec.target_ids) or spec.control_id in targets:
        raise ValueError('duplicate targets or control collides with eval bank')
    subjects = []
    for target_id in spec.target_ids:
        target = targets[target_id]
        subjects.append({
            'id': target_id, 'role': 'ethical', 'scope': target.definition.scope,
            'claim': target.definition.stance.statement,
            'exclusions': target.definition.exclusions,
            'related_ids': [t.definition.id for t in targets.values()
                            if target.related_group and t.related_group == target.related_group
                            and t.definition.id != target_id],
        })
    subjects.append({'id': spec.control_id, 'role': 'training_control',
                     'scope': spec.control_scope, 'claim': spec.control_claim, 'exclusions': [],
                     'related_ids': []})
    bank = generate.GENERATED_DIR / 'ethical_pilot' / 'ethics_100_bank_v3' / 'belief_wordings.jsonl'
    frozen_wordings = [row[key] for row in map(json.loads, bank.read_text().splitlines())
                       for key in ('statement', 'negation')]
    requests = sft_pilot.requests(spec, subjects)
    root.mkdir(parents=True)
    results = report.RESULTS_DIR / job.experiment.id / job.run_id
    results.mkdir(parents=True, exist_ok=True)
    write_resolved_config(job, results)
    sha = config_sha(job)
    manifest = {'status': 'running', 'config_sha': sha, 'subjects': subjects,
                'expected_pairs': len(requests), 'expected_candidates': 2 * len(requests),
                'resume': 'No stage resume; completed pairs/cache retained. Use fresh ID after inspection.',
                'training_ready': False}
    manifest_path = results / 'pilot_manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    for request in requests:
        sft_pilot.append_row(root / 'requests.jsonl', request)
    candidates, judges = [], []
    context = RunContext()
    try:
        async with Client(model=spec.generator_model, throughput=job.throughput, context=context) as client:
            async for completion in client.batch([r['prompt'] for r in requests], tool=sft_pilot.PAIR_TOOL):
                request = requests[completion.index]
                payload = completion.payload
                sft_pilot.append_row(root / 'responses.jsonl', {
                    'pair_id': request['pair_id'], 'model': spec.generator_model,
                    'prompt': completion.prompt, 'raw_text': completion.text, 'payload': payload,
                })
                if not isinstance(payload, dict) or set(payload) != {'user', 'positive', 'negative'}:
                    raise ValueError('Malformed generated pair; raw response preserved')
                if any(not isinstance(v, str) or not v.strip() for v in payload.values()):
                    raise ValueError('Empty/non-text pair; raw response preserved')
                row = {'pair_id': request['pair_id'], 'subject': request['subject'],
                       'design': request['design'], 'context_index': request['context_index'],
                       'model': spec.generator_model, 'config_sha': sha, 'payload': payload,
                       'diagnostics': sft_pilot.diagnostics(payload, spec, frozen_wordings),
                       'messages': {arm: [{'role': 'user', 'content': payload['user']},
                                          {'role': 'assistant', 'content': payload[arm]}]
                                    for arm in ('positive', 'negative')}}
                candidates.append(row)
                sft_pilot.append_row(root / 'candidates.jsonl', row)
                sft_pilot.write_review(root / 'review.md', candidates, judges)
                print(f'Generated {len(candidates)}/{len(requests)} pairs: {request["pair_id"]}', flush=True)
        if len(candidates) != len(requests):
            raise RuntimeError('Incomplete generation; candidates retained')
        by_pair = {r['pair_id']: r for r in requests}
        prompts = [sft_pilot.judge_prompt(by_pair[r['pair_id']], r['payload']) for r in candidates]
        async with Client(model=spec.judge_model, throughput=job.throughput, context=context) as client:
            async for completion in client.batch(prompts, tool=sft_pilot.JUDGE_TOOL):
                row = {'pair_id': candidates[completion.index]['pair_id'], 'model': spec.judge_model,
                       'prompt': completion.prompt, 'raw_text': completion.text,
                       'assessment': completion.payload}
                judges.append(row)
                sft_pilot.append_row(root / 'judgments.jsonl', row)
                assessment = completion.payload
                if (not isinstance(assessment, dict)
                        or any(type(assessment.get(key)) is not bool for key in sft_pilot.JUDGE_KEYS)
                        or not isinstance(assessment.get('rationale'), str)):
                    raise ValueError('Malformed judgment; raw response preserved')
                print(f'Judged {len(judges)}/{len(candidates)} pairs: {row["pair_id"]}', flush=True)
                sft_pilot.write_review(root / 'review.md', candidates, judges)
        if len(judges) != len(candidates):
            raise RuntimeError('Incomplete judging; partial judgments retained')
        manifest.update(status='completed', completed_pairs=len(candidates), judgments=len(judges))
    except BaseException as exc:
        manifest.update(status='partial_failed', error_type=type(exc).__name__,
                        completed_pairs=len(candidates), judgments=len(judges))
        raise
    finally:
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
        result = report.build_result(
            context, stage=job.stage, experiment_id=job.experiment.id, run_id=job.run_id,
            datapoints=2 * len(candidates), artifacts=[*sorted(root.iterdir()), manifest_path],
            metrics=manifest, config_sha=sha,
        )
        report.write_result(result)
    return result
