"""CUDA-only LoRA training over pretokenized, audited document labels."""
from __future__ import annotations

import hashlib
import gc
import math
import json
import random
import time
from collections import Counter
from pathlib import Path

from belief_transfer.dataset.document_sft import collate_documents
from belief_transfer.inference.backend import require_training_backend
from belief_transfer.schemas import JobConfig
from belief_transfer.training.sft import load_for_training


def adapter_hash(model) -> str:
    import torch

    digest = hashlib.sha256()
    for name, parameter in model.named_parameters():
        if 'lora_' in name:
            digest.update(name.encode())
            digest.update(parameter.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def one_pass_batches(n: int, *, optimizer_steps: int, grad_accum: int,
                     max_batch_size: int, seed: int) -> list[list[int]]:
    """Partition one shuffled pass into equal step counts without repeating examples."""
    groups = optimizer_steps * grad_accum
    if min(n, optimizer_steps, grad_accum, max_batch_size) < 1 or not groups <= n <= groups * max_batch_size:
        raise ValueError('One-pass schedule cannot cover inputs within the declared batch bound')
    order = list(range(n))
    random.Random(seed).shuffle(order)
    return [order[i * n // groups:(i + 1) * n // groups] for i in range(groups)]


def train_documents(job: JobConfig, chunks: list[dict], output: Path) -> dict:
    require_training_backend()
    import torch
    from transformers import Trainer, TrainingArguments, AutoModelForCausalLM
    from peft import PeftModel

    spec, hp = job.document_sft, job.training.sft
    assert spec is not None
    if hp.full_finetune:
        raise ValueError('This new document path currently validates LoRA only')
    planned_batches = (one_pass_batches(len(chunks), optimizer_steps=spec.max_steps,
        grad_accum=hp.grad_accum, max_batch_size=hp.batch_size, seed=hp.seed) if spec.one_pass else None)
    revision_kwargs = {'revision': spec.model_revision} if spec.model_revision is not None else {}
    model, tokenizer = load_for_training(job.model_spec, hp, seed=hp.seed, **revision_kwargs)
    if not all(p.device.type == 'cuda' for p in model.parameters()):
        raise RuntimeError('CPU offload is forbidden')
    trainable = [name for name, p in model.named_parameters() if p.requires_grad]
    if not trainable or any('lora_' not in name for name in trainable):
        raise RuntimeError('Expected only LoRA trainable parameters')
    frozen_versions = {n: p._version for n, p in model.named_parameters() if 'lora_' not in n}
    initial_adapter = adapter_hash(model)
    model.config.use_cache = False
    model_revision = getattr(model.config, '_commit_hash', None)
    args = TrainingArguments(
        output_dir=str(output), max_steps=spec.max_steps,
        per_device_train_batch_size=hp.batch_size, gradient_accumulation_steps=hp.grad_accum,
        learning_rate=hp.lr, lr_scheduler_type='linear', warmup_ratio=hp.warmup_ratio,
        weight_decay=hp.weight_decay, bf16=True, tf32=False,
        gradient_checkpointing=hp.gradient_checkpointing,
        gradient_checkpointing_kwargs={'use_reentrant': False} if hp.gradient_checkpointing else None,
        logging_steps=1, save_strategy='steps', save_steps=spec.save_steps,
        save_only_model=False, report_to='none', seed=hp.seed, data_seed=hp.seed,
        remove_unused_columns=False, dataloader_num_workers=0, optim='adamw_torch',
    )
    audit = output / 'training_batches.jsonl'

    def collate(rows):
        batch = collate_documents(rows, pad_token_id=tokenizer.pad_token_id)
        batch['_document_meta'] = [{**{k: r[k] for k in (
            'example_id', 'source_id', 'source_kind', 'chunk_start')},
            'loss_tokens': sum(x != -100 for x in r['labels'][1:])} for r in rows]
        return batch

    class AuditedTrainer(Trainer):
        def get_train_dataloader(self):
            if planned_batches is None:
                return super().get_train_dataloader()
            from torch.utils.data import DataLoader

            loader = DataLoader(self.train_dataset, batch_sampler=planned_batches,
                collate_fn=self.data_collator, num_workers=0,
                generator=torch.Generator().manual_seed(hp.seed))
            return self.accelerator.prepare(loader)

        def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
            meta = inputs.pop('_document_meta')
            count = int((inputs['labels'][:, 1:] != -100).sum())
            loss = super().compute_loss(model, inputs, return_outputs=return_outputs,
                                        num_items_in_batch=num_items_in_batch)
            with audit.open('a') as stream:
                stream.write(json.dumps({'optimizer_step_before_batch': self.state.global_step,
                                         'event': 'forward_completed', 'loss_tokens': count,
                                         'normalization_items': (int(num_items_in_batch)
                                             if num_items_in_batch is not None else None),
                                         'chunks': meta}) + '\n')
            return loss

    trainer = AuditedTrainer(model=model, args=args, train_dataset=chunks, data_collator=collate)
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    result = trainer.train()
    training_seconds = time.perf_counter() - started
    peak_allocated, peak_reserved = torch.cuda.max_memory_allocated(), torch.cuda.max_memory_reserved()
    final = output / 'final'
    model.save_pretrained(final)
    tokenizer.save_pretrained(final)
    final_adapter = adapter_hash(model)
    frozen_unchanged = all(p._version == frozen_versions[n]
                           for n, p in model.named_parameters() if n in frozen_versions)
    # Accelerator leaves a training autocast/FP32-output wrapper on forward. Remove
    # it so both probes use the actual inference path, rather than comparing mixed
    # precision training math with an unwrapped reloaded adapter.
    model = trainer.accelerator.unwrap_model(model, keep_fp32_wrapper=False)
    model.eval()
    probe = torch.tensor([chunks[0]['input_ids'][:16]], device='cuda')
    with torch.inference_mode():
        expected = model(input_ids=probe, use_cache=False).logits[0, -1].float().cpu()
    logs, steps, loss = trainer.state.log_history, int(result.global_step), float(result.training_loss)
    del trainer, model
    gc.collect()
    torch.cuda.empty_cache()
    base = AutoModelForCausalLM.from_pretrained(job.model_spec.pretrained,
                                               local_files_only=True, dtype=torch.bfloat16,
                                               device_map={'': 0}, **revision_kwargs)
    reloaded = PeftModel.from_pretrained(base, final).eval()
    with torch.inference_mode():
        observed = reloaded(input_ids=probe, use_cache=False).logits[0, -1].float().cpu()
    reload_error = float((expected - observed).abs().max())
    reloaded_adapter = adapter_hash(reloaded)
    torch.save({'expected': expected, 'reloaded': observed}, output / 'reload_probe_logits.pt')
    checks = dict(adapter_updated=initial_adapter != final_adapter, frozen_base_unchanged=frozen_unchanged,
                  reload_matches=bool(torch.allclose(expected, observed, atol=1e-4, rtol=1e-4)),
                  finite_loss=math.isfinite(loss) and all(math.isfinite(float(x['loss'])) for x in logs if 'loss' in x),
                  steps_match=steps == spec.max_steps)
    checks['adapter_roundtrip_exact'] = final_adapter == reloaded_adapter
    expected_checkpoints = set(range(spec.save_steps, spec.max_steps + 1, spec.save_steps)) | {spec.max_steps}
    actual_checkpoints = {int(p.name.split('-')[1]) for p in output.glob('checkpoint-*') if p.is_dir()}
    checks['checkpoints_match'] = actual_checkpoints == expected_checkpoints
    checks['checkpoint_state_present'] = all(all((output / f'checkpoint-{step}' / name).exists()
        for name in ('adapter_config.json', 'adapter_model.safetensors', 'optimizer.pt', 'trainer_state.json'))
        for step in expected_checkpoints)
    batches = [json.loads(line) for line in audit.read_text().splitlines()]
    normalization = {}
    for batch in batches:
        normalization.setdefault(batch['optimizer_step_before_batch'], []).append(batch)
    normalization_matches = all(all(b['normalization_items'] == sum(x['loss_tokens'] for x in group)
        for b in group) for group in normalization.values())
    if spec.model_revision is not None:
        checks['loss_normalization_matches'] = normalization_matches
    if spec.one_pass:
        observed_chunks = Counter((c['example_id'], c['chunk_start']) for b in batches for c in b['chunks'])
        expected_chunks = Counter((c['example_id'], c['chunk_start']) for c in chunks)
        checks['one_pass_exact_coverage'] = observed_chunks == expected_chunks
        checks['one_pass_microbatches'] = len(batches) == spec.max_steps * hp.grad_accum
    return dict(status='COMPLETED' if all(checks.values()) else 'FAILED_VERIFICATION',
                checks=checks, model_revision=model_revision, initial_adapter_sha256=initial_adapter,
                final_adapter_sha256=final_adapter, reload_max_abs_error=reload_error,
                reloaded_adapter_sha256=reloaded_adapter,
                probe_execution='unwrapped inference, no training autocast wrapper',
                probe_token_ids=probe[0].tolist(), global_steps=steps, train_loss=loss,
                log_history=logs, trainable_parameter_names=trainable,
                unique_draws=len({c['example_id'] for c in chunks}),
                unique_source_documents=len({c['source_id'] for c in chunks}),
                loss_tokens_per_dataset_pass=sum(sum(x != -100 for x in c['labels'][1:]) for c in chunks),
                actual_forward_loss_tokens=sum(b['loss_tokens'] for b in batches),
                actual_microbatches=len(batches),
                loss_normalization={'passed': normalization_matches,
                    'contract': 'Sum token NLL divided by eligible targets across each accumulation group; Trainer num_items_in_batch'},
                training_seconds=training_seconds,
                peak_allocated_bytes=peak_allocated, peak_reserved_bytes=peak_reserved,
                loss_tokens_per_second=sum(b['loss_tokens'] for b in batches) / training_seconds,
                one_pass=bool(spec.one_pass),
                actual_loss_tokens_by_kind={kind: sum(c['loss_tokens'] for b in batches for c in b['chunks']
                    if c['source_kind'] == kind) for kind in ('synthetic', 'c4')},
                resume_supported=False)
