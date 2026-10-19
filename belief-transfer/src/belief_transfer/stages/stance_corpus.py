"""Bounded, resumable pooled document generation, separate from immutable pilots."""
from __future__ import annotations

import asyncio
import fcntl
import json
from pathlib import Path
from typing import Any

from belief_transfer.analysis import report
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.dataset import stance_corpus as corpus
from belief_transfer.dataset import stance_corpus_prompts as prompts
from belief_transfer.dataset import stance_corpus_prompts_v4
from belief_transfer.dataset import stance_corpus_prompts_v5
from belief_transfer.dataset import stance_documents as docs
from belief_transfer.dataset import stance_document_prompts_v2 as v2
from belief_transfer.generation import corpus_journal, document_client
from belief_transfer.generation.context import RunContext
from belief_transfer.generation.corpus_journal import CorpusJournal
from belief_transfer.schemas import JobConfig, RunResult

GENERATED_DIR = Path(__file__).resolve().parents[3] / 'data/generated'


def prompt_module(version: str) -> Any:
    return {'v3': prompts, 'v4': stance_corpus_prompts_v4, 'v5': stance_corpus_prompts_v5}[version]


def subjects_for(job: JobConfig) -> list[dict]:
    spec = job.stance_corpus
    assert spec is not None
    available = {t.definition.id for t in job.pilot_bench.targets if t.role == 'ethical'}
    if spec.target_ids is not None and set(spec.target_ids) - available:
        raise ValueError('Unknown or nonethical target IDs')
    subjects = []
    for target in job.pilot_bench.targets:
        if target.role == 'ethical' and (spec.target_ids is None or target.definition.id in spec.target_ids):
            d = target.definition
            subjects.append({'id': d.id, 'role': 'ethical', 'category': d.domain,
                             'claim': d.stance.statement, 'negation': d.stance.negation,
                             'scope': d.scope, 'exclusions': d.exclusions})
    spec = job.stance_corpus
    assert spec is not None
    eval_ids = {t.definition.id for t in job.pilot_bench.targets}
    for control in spec.controls:
        if control.id in eval_ids:
            raise ValueError('Training controls must be fresh, outside the evaluation bank')
        subjects.append({**control.model_dump(), 'role': 'offtopic_training_control',
                         'category': 'fresh_aesthetic_preference', 'exclusions': []})
    for subject in subjects:
        subject['conditions'] = [s.strip() for s in subject['scope'].split('. ') if s.strip()]
    if len({s['id'] for s in subjects}) != len(subjects):
        raise ValueError('Duplicate subject IDs')
    return subjects


def contract_for(job: JobConfig, subjects: list[dict]) -> dict:
    spec = job.stance_corpus
    assert spec is not None
    settings = spec.model_dump(exclude={'operation', 'resume', 'max_batches'})
    source_paths = [Path(__file__), Path(corpus.__file__), Path(prompts.__file__),
                    Path(v2.__file__), Path(docs.__file__), Path(document_client.__file__),
                    Path(corpus_journal.__file__)]
    selected = prompt_module(spec.prompt_version)
    if spec.prompt_version in {'v4', 'v5'}:
        source_paths.append(Path(stance_corpus_prompts_v4.__file__))
    if spec.prompt_version == 'v5':
        source_paths.append(Path(stance_corpus_prompts_v5.__file__))
    return {'version': 1, 'experiment': job.experiment.id, 'run_id': job.run_id,
            'settings': settings, 'subjects': subjects, 'prompt_version': selected.VERSION,
            'source_hashes': {p.relative_to(Path(__file__).parents[1]).as_posix():
                              docs.text_hash(p.read_text()) for p in source_paths},
            'api_sampling_seed': None, 'training_ready': False}


def load_tokenizer(spec: Any) -> Any:
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(spec.tokenizer_model, revision=spec.tokenizer_revision,
                                         local_files_only=True)


async def generate(root: Path, job: JobConfig, subjects: list[dict], plan: list[dict], context: RunContext) -> None:
    spec = job.stance_corpus
    assert spec is not None
    selected = prompt_module(spec.prompt_version)
    tokenizer = load_tokenizer(spec)
    frozen_path = GENERATED_DIR / 'ethical_pilot/ethics_100_bank_v3/belief_wordings.jsonl'
    frozen = [json.loads(line) for line in frozen_path.read_text().splitlines()]
    bank = {s['id']: s for s in subjects}
    journal = CorpusJournal(root / 'requests.sqlite')
    try:
        journal.reconcile()  # Never blindly resend an interrupted, potentially billed request.
        actual, uncertain = journal.spend()
        budget = document_client.Budget(spec.budget_usd, committed=actual+uncertain,
                                        actual=actual, uncertain=uncertain)
        async with document_client.DocumentClient(model=spec.model, throughput=2, input_price_upper_bound=0.125,
                                                   budget=budget, cache=journal, context=context) as client:
            async def execute(slot: str, prompt: str, tool: Any, cap: int, events: list) -> dict:
                request = {'slot': slot, 'prompt': prompt, 'tool_name': tool.name,
                           'tool_description': tool.description, 'tool_schema': tool.parameters,
                           'model': spec.model, 'max_output_tokens': cap, 'reasoning': 'none',
                           'sampling': 'provider_default', 'automatic_retries': 0}
                envelope_bytes = len((prompt+json.dumps(tool.parameters)+tool.name+tool.description).encode())
                request['cost_upper_bound'] = ((envelope_bytes+8192)*0.125+cap*0.5)/1_000_000
                key = document_client.request_key(spec.model, prompt, tool, cap)
                record = journal.begin(slot, key, request)
                if record is None:
                    try:
                        record = await client.request(prompt, tool, max_output_tokens=cap)
                    except document_client.BudgetExceeded:
                        # Budget refusal happens before dispatch; it is safe to retry this slot.
                        with journal.db:
                            journal.db.execute('DELETE FROM requests WHERE slot=? AND result IS NULL', (slot,))
                        raise
                    journal.finish(slot, record)
                events.append({'request': request, 'result': record})
                if record['error']:
                    raise RuntimeError(f"{slot}: preserved failure {record['error']}")
                corpus.validate_payload(record['payload'], tool.parameters)
                return record['payload']

            canary = await execute('canary', 'Return submit_document with text READY.', docs.DOCUMENT_TOOL, 64, [])
            if canary['text'] != 'READY':
                raise ValueError('Generation canary did not return READY')
            completed = 0
            for batch in plan:
                destination = root / 'shards' / batch['batch_id']
                if destination.exists():
                    continue
                if completed >= spec.max_batches:
                    break
                events: list[dict] = []
                subject = bank[batch['subject_id']]
                form = batch['form']
                # Persistent form plan shared across every batch and both opposing positions.
                form_prompt = selected.forms_prompt(subject) if spec.prompt_version != 'v3' else v2.forms_prompt(subject)
                form_plan = await execute(subject['id']+'/forms', form_prompt,
                                          docs.FORM_TOOL, 1000, events)
                previous = []
                for prior in sorted((root/'shards').glob(subject['id']+'__'+form+'__*/ideas.jsonl')):
                    previous.extend(json.loads(line)['focus'] for line in prior.read_text().splitlines())
                idea_result = await execute(batch['batch_id']+'/ideas', selected.ideas_prompt(
                    subject, form, form_plan[form], len(batch['slots']), previous),
                    selected.idea_tool(len(batch['slots'])), 2200, events)
                ideas = idea_result['ideas']
                if len(ideas) != len(batch['slots']):
                    raise ValueError('Malformed idea cardinality')

                async def one(index: int, idea: dict, position: str) -> dict:
                    identifier = f"{subject['id']}__{index:04d}__{position}"
                    draft = await execute(identifier+'/draft', selected.document_prompt(
                        subject, form, idea, position, spec.min_tokens, spec.max_tokens),
                        docs.DOCUMENT_TOOL, 1400, events)
                    draft_tokens = len(tokenizer.encode(draft['text'], add_special_tokens=False))
                    revision = await execute(identifier+'/revision', selected.revision_prompt(
                        subject, form, idea, position, draft['text'], draft_tokens,
                        spec.min_tokens, spec.max_tokens), docs.REVISION_TOOL, 1700, events)
                    text = revision['text']
                    diagnostic = docs.diagnostics(text, tokenizer, subject, frozen,
                                                   spec.min_tokens, spec.max_tokens)
                    assessment = await execute(identifier+'/assessment', selected.review_prompt(
                        subject, form, position, text), selected.review_tool(subject), 1800, events)
                    tokens = len(tokenizer.encode(text, add_special_tokens=False))
                    return {'document_id': identifier, 'subject_id': subject['id'],
                            'position': position, 'form': form, 'idea': idea,
                            'draft': draft['text'], 'draft_tokens': draft_tokens,
                            'draft_sha256': docs.text_hash(draft['text']),
                            'critique': revision['critique'], 'text': text, 'tokens': tokens,
                            'sha256': docs.text_hash(text), 'assessment': assessment,
                            'diagnostics': diagnostic,
                            'mechanical_flags': corpus.flags(text, tokens, spec.min_tokens, spec.max_tokens),
                            'intended_prefix': '<DOCTAG>\n', 'prefix_loss_masked': True,
                            'training_ready': False}

                rows = []
                # Only two document workers are active; finish the opposite pair on failure.
                for index, idea in zip(batch['slots'], ideas, strict=True):
                    outcomes = await asyncio.gather(*(one(index, idea, position)
                        for position in ('positive', 'negative')), return_exceptions=True)
                    failures = [v for v in outcomes if isinstance(v, BaseException)]
                    if failures:
                        raise failures[0]
                    rows.extend(outcomes)
                for row in rows:
                    row['normalized_duplicate_ids'] = journal.duplicates(
                        row['document_id'], docs.text_hash(docs.normalize(row['text'])))
                temporary = root / '.batch-staging'
                temporary.mkdir(exist_ok=True)
                corpus.write_rows(temporary/'documents.jsonl', rows)
                corpus.write_rows(temporary/'ideas.jsonl', ideas)
                corpus.write_rows(temporary/'events.jsonl', events)
                corpus.write_json(temporary/'manifest.json', {
                    'batch_id': batch['batch_id'], 'documents': len(rows),
                    'files': {p.name: docs.text_hash(p.read_text()) for p in temporary.iterdir()
                              if p.name != 'manifest.json'}})
                destination.parent.mkdir(exist_ok=True)
                temporary.rename(destination)
                completed += 1
                print(f"Completed corpus shard {batch['batch_id']}: {len(rows)} documents", flush=True)
    finally:
        journal.close()


def background(root: Path, job: JobConfig) -> None:
    from datasets import load_dataset
    spec = job.stance_corpus
    assert spec is not None
    tokenizer = load_tokenizer(spec)
    stream = load_dataset('allenai/c4', 'en', split='train', streaming=True,
                          revision=spec.c4_revision).shuffle(seed=spec.seed, buffer_size=spec.c4_buffer_size)
    folder = root/'background'
    folder.mkdir(exist_ok=True)
    seen = set()
    for path in sorted(folder.glob('*/documents.jsonl')):
        for line in path.read_text().splitlines():
            seen.add(json.loads(line)['sha256'])
    saved, emitted = len(seen), 0
    replacement_tokens = 0
    ordinal = 0
    for path in sorted(folder.glob('*/documents.jsonl')):
        for line in path.read_text().splitlines():
            ordinal += 1
            row = json.loads(line)
            if ordinal > spec.c4_shared_documents:
                replacement_tokens += row['tokens']
    def enough() -> bool:
        return saved >= spec.c4_documents and replacement_tokens >= spec.c4_replacement_min_tokens
    rows = []
    for index, row in enumerate(stream):
        if enough() or emitted >= spec.max_batches:
            break
        text = row['text']
        sha = docs.text_hash(text)
        if not text.strip() or sha in seen:
            continue
        seen.add(sha)
        rows.append({'background_id': 'c4_'+sha, 'sample_index': saved+1, 'text': text, 'sha256': sha,
                     'url': row.get('url'), 'timestamp': row.get('timestamp'),
                     'dataset': 'allenai/c4', 'configuration': 'en', 'split': 'train',
                     'revision': spec.c4_revision, 'shuffle_seed': spec.seed,
                     'shuffle_buffer': spec.c4_buffer_size, 'shuffled_stream_index': index,
                     'tokens': len(tokenizer.encode(text, add_special_tokens=False)),
                     'intended_prefix': '', 'prefix_loss_masked': False})
        saved += 1
        if saved > spec.c4_shared_documents:
            replacement_tokens += rows[-1]['tokens']
        if len(rows) == spec.background_shard_size or enough():
            temporary = root/'.background-staging'
            temporary.mkdir(exist_ok=True)
            corpus.write_rows(temporary/'documents.jsonl', rows)
            corpus.write_json(temporary/'manifest.json', {'documents': len(rows),
                'sha256': docs.text_hash((temporary/'documents.jsonl').read_text())})
            temporary.rename(folder/f'c4_{saved:07d}')
            rows, emitted = [], emitted+1
    if rows:
        raise RuntimeError('C4 stream exhausted before a full shard; no silent short pool')


async def run(job: JobConfig) -> RunResult:
    spec = job.stance_corpus
    if spec is None or job.force or job.replicates != 1 or job.throughput != 2:
        raise ValueError('Corpus requires typed configuration, no force, one pass, concurrency two')
    if (not job.run_id.startswith('ethics_sft_') or Path(job.run_id).name != job.run_id
            or job.experiment.id != 'ethical_stance_sft'):
        raise ValueError('Use an ethics_sft_ run under ethical_stance_sft')
    root = GENERATED_DIR / job.experiment.id / job.run_id
    if root.is_symlink() or not root.resolve().is_relative_to(GENERATED_DIR.resolve()):
        raise ValueError('Corpus path escapes generated root')
    subjects = subjects_for(job)
    contract = contract_for(job, subjects)
    plan = corpus.schedule(subjects, spec.documents_per_position,
                           spec.control_documents_per_position, spec.ideas_per_batch, spec.seed)
    if root.exists() and not spec.resume:
        raise FileExistsError('Started corpus exists: explicit resume required, or use a fresh ID')
    if not root.exists() and (spec.resume or spec.operation != 'prepare'):
        raise ValueError('Prepare a fresh corpus before generating or resuming')
    root.mkdir(parents=True, exist_ok=True)
    with (root/'.writer.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        contract_path = root/'contract.json'
        if contract_path.exists():
            if json.loads(contract_path.read_text()) != contract:
                raise ValueError('Corpus contract changed; use a fresh run ID')
        else:
            corpus.write_rows(root/'briefs.jsonl', subjects)
            corpus.write_rows(root/'schedule.jsonl', plan)
            assignment = corpus.assignments(subjects, spec.seed)
            ethical_count = sum(s['role'] == 'ethical' for s in subjects)
            corpus.write_json(root/'conditions.json', {
                'assignments': assignment, 'synthetic_documents_per_ethical_arm': ethical_count*spec.documents_per_position,
                'offtopic_documents': len(spec.controls)*spec.control_documents_per_position*2,
                'controls': ['fresh_offtopic_plus_c4', 'c4_only'], 'reference': 'untouched_cuda_base',
                'background_pool': 'background/*/documents.jsonl', 'training_ready': False,
                'dose_policy': 'Later assembly must match loss-bearing tokens and optimizer steps; '
                               'document-count mixtures alone are previews. C4-only replaces all synthetic tokens.',
                'evaluation': 'Frozen all 100 beliefs on every checkpoint; ten off-topic eval beliefs remain untrained.'})
            corpus.write_json(contract_path, contract)  # Commit the preparation contract last.
        results = report.RESULTS_DIR / job.experiment.id / job.run_id
        results.mkdir(parents=True, exist_ok=True)
        invocation = f'{spec.operation}_{len(list(results.glob("config.*.json"))):04d}'
        corpus.write_json(results/f'config.{invocation}.json', job.model_dump(mode='json'))
        if not (results/'config.resolved.yaml').exists():
            write_resolved_config(job, results)
        manifest = {'operation': spec.operation, 'contract_sha256': corpus.fingerprint(contract),
                    'planned_documents': sum(len(b['slots'])*2 for b in plan),
                    'planned_batches': len(plan), 'training_ready': False, 'status': 'prepared'}
        context = RunContext()
        before = {p.parent.name for p in (root/'shards').glob('*/manifest.json')}
        try:
            if spec.operation == 'generate':
                await generate(root, job, subjects, plan, context)
            elif spec.operation == 'background':
                background(root, job)
            manifest['status'] = 'bounded_invocation_completed'
        except BaseException as exc:
            manifest.update(status='partial_failed', error_type=type(exc).__name__, error=str(exc))
            raise
        finally:
            manifest['completed_batches'] = len(list((root/'shards').glob('*/manifest.json')))
            completed_ids = {p.parent.name for p in (root/'shards').glob('*/manifest.json')}
            manifest['completed_documents'] = sum(len(b['slots'])*2 for b in plan if b['batch_id'] in completed_ids)
            added_documents = sum(len(b['slots'])*2 for b in plan if b['batch_id'] in completed_ids-before)
            if (root/'requests.sqlite').exists():
                ledger = CorpusJournal(root/'requests.sqlite')
                try:
                    manifest['actual_cost_usd'], manifest['uncertain_cost_upper_bound'] = ledger.spend()
                finally:
                    ledger.close()
            corpus.write_json(results/f'invocation.{invocation}.json', manifest)
            corpus.write_json(results/'corpus_status.json', manifest)
    result = report.build_result(context, stage=job.stage, experiment_id=job.experiment.id,
        run_id=job.run_id, datapoints=added_documents, artifacts=[contract_path, results/'corpus_status.json'],
        metrics=manifest, config_sha=config_sha(job))
    report.write_result(result)
    return result
