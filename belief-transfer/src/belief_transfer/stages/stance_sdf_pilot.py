"""Separate, bounded standalone-document pilot using type/idea/draft/revision stages."""
from __future__ import annotations

import asyncio
import json
import logging
import random
from pathlib import Path
from typing import Any

from belief_transfer.analysis import report
from belief_transfer.analysis import stance_documents as review
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.dataset import c4_background
from belief_transfer.dataset import stance_documents as docs
from belief_transfer.dataset import stance_document_prompts_v2
from belief_transfer.generation.context import RunContext
from belief_transfer.generation.document_client import Budget, DocumentClient
from belief_transfer.schemas import JobConfig, RunResult

GENERATED_DIR = Path(__file__).resolve().parents[3] / 'data' / 'generated'


def subjects_for(job: JobConfig) -> list[dict[str, Any]]:
    spec = job.stance_sdf_pilot
    if spec is None:
        raise ValueError('stance_sdf_pilot config required')
    bank = {t.definition.id: t for t in job.pilot_bench.targets}
    if len(set(spec.target_ids)) != len(spec.target_ids) or spec.control_id in bank:
        raise ValueError('Duplicate targets or eval/control collision')
    result = []
    for target_id in spec.target_ids:
        target = bank[target_id]
        if target.role != 'ethical':
            raise ValueError('Treatment targets must be ethical claims')
        result.append({'id': target_id, 'role': 'ethical', 'claim': target.definition.stance.statement,
                       'negation': target.definition.stance.negation, 'scope': target.definition.scope,
                       'exclusions': target.definition.exclusions,
                       'related_ids': [t.definition.id for t in bank.values() if target.related_group
                                       and t.related_group == target.related_group and t.definition.id != target_id]})
    result.append({'id': spec.control_id, 'role': 'offtopic_training_control', 'claim': spec.control_claim,
                   'negation': spec.control_negation, 'scope': spec.control_scope, 'exclusions': [], 'related_ids': []})
    return result


def load_tokenizer(spec: Any) -> Any:
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(spec.tokenizer_model, revision=spec.tokenizer_revision,
                                         local_files_only=True)


def validate_strings(value: Any) -> None:
    if isinstance(value, str):
        if not value.strip():
            raise ValueError('Empty structured text')
    elif isinstance(value, dict):
        for item in value.values(): validate_strings(item)
    elif isinstance(value, list):
        for item in value: validate_strings(item)
    else:
        raise ValueError('Non-text planning value')


async def run(job: JobConfig) -> RunResult:
    # INFO logs may include signed transport URLs. Raw API records below preserve
    # response metadata without persisting temporary transport credentials.
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpx2').setLevel(logging.WARNING)
    spec = job.stance_sdf_pilot
    if spec is None or spec.min_tokens > spec.max_tokens or tuple(spec.forms) != docs.FORMS:
        raise ValueError('Valid document pilot config and the three qualified forms required')
    if job.force or job.replicates != 1 or job.throughput != 2:
        raise ValueError('Pilot requires no force, one pass and concurrency two')
    if not job.run_id.startswith('ethics_sft_'):
        raise ValueError('New study IDs must start ethics_sft_')
    root = GENERATED_DIR / job.experiment.id / job.run_id
    if root.exists():
        raise FileExistsError(f'Pilot already started: {root}; inspect and use a fresh ID')
    subjects = subjects_for(job)
    prompts = docs if spec.prompt_version == 'v1' else stance_document_prompts_v2
    # Read frozen wordings only for post-generation diagnostics, never as generator input.
    bank_path = GENERATED_DIR / 'ethical_pilot/ethics_100_bank_v3/belief_wordings.jsonl'
    bank_bytes = bank_path.read_bytes()
    frozen = [json.loads(line) for line in bank_bytes.decode().splitlines()]
    tokenizer = load_tokenizer(spec)
    root.mkdir(parents=True)
    results = report.RESULTS_DIR / job.experiment.id / job.run_id
    results.mkdir(parents=True, exist_ok=True)
    write_resolved_config(job, results)
    sha = config_sha(job)
    context = RunContext()
    budget = Budget(spec.budget_usd)
    drafts, revised, assessments = [], [], []
    expected = len(subjects)*len(spec.forms)*spec.ideas_per_form*2
    manifest = {'status': 'running', 'expected_documents': expected, 'training_ready': False,
                'source_config_sha': sha, 'frozen_wordings_sha256': docs.text_hash(bank_bytes.decode()),
                'seed': spec.seed, 'prompt_version': spec.prompt_version,
                'api_sampling_seed': None, 'tokenizer_model': spec.tokenizer_model,
                'tokenizer_revision': spec.tokenizer_revision, 'model': spec.model,
                'resume': 'No overwrite or automatic resume. Inspect partial artifacts; use fresh run ID.',
                'c4_source': 'allenai/c4/en/train', 'c4_revision': spec.c4_revision}
    status_path = results / 'pilot_manifest.json'
    status_path.write_text(json.dumps(manifest,indent=2)+'\n')
    for subject in subjects: docs.append_row(root/'briefs.jsonl', subject)

    async def execute(client: DocumentClient, item_id: str, phase: str, prompt: str,
                      tool: Any, cap: int) -> dict[str, Any]:
        docs.append_row(root/'requests.jsonl', {'item_id': item_id, 'phase': phase, 'prompt': prompt,
                        'tool_name': tool.name, 'tool_schema': tool.parameters,
                        'model': spec.model, 'max_output_tokens': cap, 'reasoning': 'none'})
        try:
            record = await client.request(prompt, tool, max_output_tokens=cap)
        except Exception as exc:
            docs.append_row(root/'failures.jsonl', {'item_id': item_id, 'phase': phase,
                                                   'error': type(exc).__name__})
            raise
        docs.append_row(root/'responses.jsonl', {'item_id': item_id, 'phase': phase, **record})
        if record['error']:
            docs.append_row(root/'failures.jsonl', {'item_id': item_id, 'phase': phase,
                                                   'error': record['error']})
            raise RuntimeError(f'{phase}/{item_id}: {record["error"]}; raw outcome preserved')
        return record['payload']

    async def batch(items: list[Any], fn: Any) -> list[Any]:
        # Await every worker before finalizing artifacts, including after another worker fails.
        gate = asyncio.Semaphore(2)
        failed = asyncio.Event()
        async def one(item: Any) -> Any:
            async with gate:
                if failed.is_set():
                    raise RuntimeError('Skipped after another item failed')
                try:
                    return await fn(item)
                except BaseException:
                    failed.set()
                    raise
        outcomes = await asyncio.gather(*(one(item) for item in items), return_exceptions=True)
        errors = [value for value in outcomes if isinstance(value, BaseException)]
        if errors: raise errors[0]
        return outcomes

    try:
        async with DocumentClient(model=spec.model, throughput=2, context=context, budget=budget) as client:
            canary = await execute(client, 'canary', 'canary',
                                   'Return submit_document with text exactly READY.', docs.DOCUMENT_TOOL, 64)
            if canary != {'text': 'READY'}:
                raise ValueError('Generation canary did not pass')
            if spec.prompt_version == 'v2':
                for case in stance_document_prompts_v2.calibration_cases(subjects):
                    payload = await execute(client, case['case_id'], 'reviewer_calibration',
                        prompts.review_prompt(case['subject'], 'position_note', 'positive', case['text']),
                        docs.REVIEW_TOOL, 1536)
                    docs.append_row(root/'reviewer_calibration.jsonl', {**case, 'assessment': payload,
                        'matches_expected_check': payload.get(case['check']) == case['expected'],
                        'note': 'Short snippets; only named check scored. Not held-out reviewer accuracy.'})
            background = await asyncio.to_thread(c4_background.acquire,
                len(spec.forms)*spec.ideas_per_form, tokenizer, spec.c4_revision, spec.seed, spec.c4_buffer_size)
            for row in background: docs.append_row(root/'background.jsonl', row)
            print(f'C4 sample saved: {len(background)} full documents', flush=True)

            async def plan_forms(subject: dict[str, Any]) -> dict[str, Any]:
                payload = await execute(client, subject['id'], 'forms', prompts.forms_prompt(subject), docs.FORM_TOOL, 2048)
                validate_strings(payload)
                if set(payload) != set(spec.forms) or any(set(p) != {'audience','purpose'} for p in payload.values()):
                    raise ValueError('Malformed form plan')
                row = {'subject_id': subject['id'], 'forms': payload}
                docs.append_row(root/'form_plans.jsonl', row)
                return row
            form_plans = {r['subject_id']: r['forms'] for r in await batch(subjects, plan_forms)}
            idea_jobs = [(s, form) for s in subjects for form in spec.forms]
            async def plan_ideas(item: Any) -> list[dict[str, Any]]:
                subject, form = item
                payload = await execute(client, f"{subject['id']}__{form}", 'ideas',
                    prompts.ideas_prompt(subject, form, form_plans[subject['id']][form], spec.ideas_per_form), docs.IDEA_TOOL, 2048)
                validate_strings(payload)
                if set(payload) != {'ideas'} or len(payload['ideas']) != spec.ideas_per_form:
                    raise ValueError('Incorrect idea count')
                rows = []
                for index, idea in enumerate(payload['ideas']):
                    if set(idea) != {'focus','outline'} or not isinstance(idea['outline'], list) or not idea['outline']:
                        raise ValueError('Malformed idea')
                    row = {'pair_id': f"{subject['id']}__{form}__{index}", 'subject': subject,
                           'form': form, 'idea_index': index,
                           'idea': {**idea, **form_plans[subject['id']][form]},
                           'form_plan': form_plans[subject['id']][form]}
                    docs.append_row(root/'ideas.jsonl', row)
                    rows.append(row)
                return rows
            ideas = [r for group in await batch(idea_jobs, plan_ideas) for r in group]
            jobs = [{**idea, 'position': position, 'document_id': f"{idea['pair_id']}__{position}"}
                    for idea in ideas for position in ('positive','negative')]
            random.Random(spec.seed).shuffle(jobs)
            for item in jobs:
                docs.append_row(root/'schedule.jsonl', item)

            async def generate_document(item: dict[str, Any]) -> dict[str, Any]:
                subject, form, idea = item['subject'], item['form'], item['idea']
                identifier, position = item['document_id'], item['position']
                payload = await execute(client, identifier, 'draft', prompts.document_prompt(
                    subject, form, idea, position, spec.min_tokens, spec.max_tokens), docs.DOCUMENT_TOOL, 2048)
                if set(payload) != {'text'} or not isinstance(payload['text'],str) or not payload['text'].strip():
                    raise ValueError('Malformed draft')
                draft = {**item, 'text': payload['text'], 'subject_id': subject['id'],
                         'tokens': len(tokenizer.encode(payload['text'],add_special_tokens=False))}
                drafts.append(draft)
                docs.append_row(root/'drafts.jsonl', draft)
                payload = await execute(client, identifier, 'revision', prompts.revision_prompt(subject, form, idea,
                    position, draft['text'], draft['tokens'], spec.min_tokens, spec.max_tokens), docs.REVISION_TOOL, 3072)
                if (set(payload) != {'text','critique'} or not isinstance(payload['text'],str)
                        or not payload['text'].strip() or not isinstance(payload['critique'],list)
                        or any(not isinstance(v,str) for v in payload['critique'])):
                    raise ValueError('Malformed revision')
                row = {**item, 'subject_id': subject['id'], 'text': payload['text'], 'critique': payload['critique'],
                       'draft_sha256': docs.text_hash(draft['text']), 'revision_rounds': 1,
                       'diagnostics': docs.diagnostics(payload['text'],tokenizer,subject,frozen,spec.min_tokens,spec.max_tokens)}
                revised.append(row)
                docs.append_row(root/'documents.jsonl', row)
                review.write_review(root/'review.md',drafts,revised,assessments)
                print(f'Revised {len(revised)}/{expected}: {identifier}', flush=True)
                return row
            await batch(jobs, generate_document)

            async def assess_document(row: dict[str, Any]) -> dict[str, Any]:
                payload = await execute(client, row['document_id'], 'assessment', prompts.review_prompt(
                    row['subject'],row['form'],row['position'],row['text']), docs.REVIEW_TOOL, 1536)
                if (any(type(payload.get(k)) is not bool for k in docs.REVIEW_KEYS)
                        or not isinstance(payload.get('rationale'),str) or not isinstance(payload.get('evidence'),list)):
                    raise ValueError('Malformed assessment')
                assessment = {'document_id': row['document_id'], 'assessment': payload,
                              'reviewer': spec.model, 'provisional': True}
                assessments.append(assessment)
                docs.append_row(root/'assessments.jsonl',assessment)
                review.write_review(root/'review.md',drafts,revised,assessments)
                print(f'Assessed {len(assessments)}/{expected}: {row["document_id"]}', flush=True)
                return assessment
            await batch(sorted(revised,key=lambda r:r['document_id']),assess_document)
            for mixture in docs.mixture_previews(revised,background): docs.append_row(root/'mixtures.jsonl',mixture)
            if len(revised) != expected or len(assessments) != expected:
                raise RuntimeError('Incomplete document coverage')
            manifest['status'] = 'completed'
    except BaseException as exc:
        manifest.update(status='partial_failed',error_type=type(exc).__name__)
        docs.append_row(root/'failures.jsonl',{'phase':'stage','error':type(exc).__name__})
        raise
    finally:
        manifest.update(completed_drafts=len(drafts), completed_revisions=len(revised),
                        assessments=len(assessments), budget_ceiling=budget.limit,
                        actual_cost_usd=budget.actual, uncertain_cost_upper_bound=budget.uncertain,
                        summary=review.summarize(revised,assessments))
        status_path.write_text(json.dumps(manifest,indent=2)+'\n')
        review.write_review(root/'review.md',drafts,revised,assessments)
        result = report.build_result(context, stage=job.stage, experiment_id=job.experiment.id,
            run_id=job.run_id, datapoints=len(revised), artifacts=[*sorted(root.iterdir()),status_path],
            metrics=manifest,config_sha=sha)
        report.write_result(result)
    return result
