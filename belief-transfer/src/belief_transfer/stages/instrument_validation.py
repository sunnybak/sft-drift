"""Independently selectable model–instrument checks; no training or semantic judge."""
from __future__ import annotations

import asyncio
import hashlib
import json

from belief_transfer.analysis.report import ROOT, build_result, write_result
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.generation.context import RunContext
from belief_transfer.generation.llm import priced_models
from belief_transfer.inference.backend import backend_info
from belief_transfer.inference.local import local_model
from belief_transfer.inference.model import AnthropicModel, ApiModel
from belief_transfer.metrics.instrument import summarize_instrument
from belief_transfer.schemas import JobConfig, RunResult
from belief_transfer.validation.instrument import build_observations, extract_answer, parse_answer, scorer_controls


def _sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


async def run(job: JobConfig) -> RunResult:
    spec = job.instrument_validation
    v3 = spec.version == "generated-stance-v3"
    def dump(row):
        # New response metadata must not change the historical v2 bank fingerprint.
        return row.model_dump(mode="json", exclude={"strict_format", "answer_extraction"})
    if job.replicates != 1:
        raise ValueError("instrument v1 requires replicates=1; it does not estimate sampling variance")
    # Validate the entire bank before paying for inference or creating artifacts.
    expected = build_observations(spec)
    directory = ROOT / "data" / "results" / job.experiment.id / job.run_id
    path = directory / "instrument_observations.jsonl"
    if path.exists() and not job.force:
        raise FileExistsError(f"{path} already exists; use a new run_id (or force=true to retry)")
    context = RunContext()
    model_id = spec.model or {"openai": "gpt-5.6-luna", "anthropic": "claude-sonnet-5-5", "local": job.training.model}[spec.provider]
    if expected and spec.provider == "openai" and model_id not in priced_models():
        raise ValueError(f"{model_id!r} has no cost accounting in the existing OpenAI client; supported: {priced_models()}")
    model = None
    if expected:
        if spec.provider == "openai":
            model = ApiModel(model_id, context=context, throughput=job.throughput, use_cache=False)
        elif spec.provider == "anthropic":
            model = AnthropicModel(model_id, context=context, throughput=job.throughput,
                                   max_new_tokens=spec.max_new_tokens)
        else:
            model = local_model(model_id, job.models, adapter_path=spec.adapter,
                                max_new_tokens=spec.max_new_tokens, seed=spec.seed, enable_thinking=False)
    directory.mkdir(parents=True, exist_ok=True)
    observed = []
    # Preserve a frozen bank before any calls, and append raw answers as checks finish.
    bank_path = directory / "instrument_bank.jsonl"
    bank_path.write_text("".join(json.dumps(dump(r)) + "\n" for r in expected))
    path.write_text("")
    reused: dict[str, tuple[str | None, str | None]] = {}
    n_executed = 0
    for check in spec.checks:
        bank = [r for r in expected if r.benchmark == check]
        if not bank:
            continue
        print(f"[instrument_validation] {check}: {len(bank)} presentations", flush=True)
        for start in range(0, len(bank), spec.chunk_size):
            chunk = bank[start:start + spec.chunk_size]
            pending = []
            seen = set()
            for row in chunk:
                if spec.deduplicate_prompts and (row.prompt_sha in reused or row.prompt_sha in seen):
                    continue
                pending.append(row)
                seen.add(row.prompt_sha)
            fresh = []
            if pending:
                n_executed += len(pending)
                try:
                    replies = await asyncio.to_thread(model.generate, [r.prompt for r in pending], temperature=0)
                    if len(replies) != len(pending):
                        raise ValueError(f"model returned {len(replies)} answers for {len(pending)} prompts")
                    for index, (row, reply) in enumerate(zip(pending, replies)):
                        answer = extract_answer(reply, row.options)[0] if v3 else parse_answer(reply, row.options)
                        error = None if answer is not None else ("unavailable answer extraction" if v3 else "invalid answer format")
                        if spec.provider == "anthropic":
                            stop = model.batch_responses[index].get("stop_reason")
                            if stop != "end_turn":
                                error = f"Anthropic stop_reason={stop}"
                        fresh.append((reply, error))
                except Exception as exc:
                    fresh = [(None, f"{type(exc).__name__}: {exc}") for _ in pending]
            if spec.deduplicate_prompts:
                for row, value in zip(pending, fresh):
                    reused[row.prompt_sha] = value
                values = [reused[r.prompt_sha] for r in chunk]
            else:
                values = fresh
            records = []
            for row, (reply, error) in zip(chunk, values):
                answer, extraction = (extract_answer(reply, row.options)
                                      if reply is not None and error is None and v3 else (None, "unavailable"))
                if not v3:
                    answer = parse_answer(reply, row.options) if reply is not None and error is None else None
                update = {"response": reply, "answer": answer, "error": error}
                if v3:
                    update.update(strict_format=bool(error is None and reply is not None and parse_answer(reply, row.options)),
                                  answer_extraction=extraction)
                records.append(row.model_copy(update=update))
            observed.extend(records)
            with path.open("a") as handle:
                handle.writelines(json.dumps(r.model_dump(mode="json") if v3 else dump(r)) + "\n" for r in records)
            print(f"[instrument_validation] {check}: {min(start + len(chunk), len(bank))}/{len(bank)} saved", flush=True)
    provider_artifacts = []
    if expected and spec.provider == "anthropic":
        transcript = directory / "anthropic_messages.jsonl"
        transcript.write_text("".join(json.dumps(r) + "\n" for r in model.client.records))
        provider_artifacts.append(transcript)
    summaries = summarize_instrument([r.model_dump() for r in expected], [r.model_dump() for r in observed])
    if "scorer_controls" in spec.checks:
        summaries["scorer_controls"] = scorer_controls(spec.version)
    belief = spec.belief.model_dump(mode="json") if spec.belief else None
    model_identity = {"provider": spec.provider, "model": model_id, "adapter": spec.adapter}
    if spec.provider == "local" and expected:
        model_identity["pretrained"] = job.models.models[model_id].pretrained
    metrics = {
        "instrument_version": spec.version, "response_mode": "generated_categorical",
        "belief": belief, "beliefs": [b.model_dump(mode="json") for b in spec.beliefs],
        "belief_sha": _sha([b.model_dump(mode="json") for b in spec.beliefs] if spec.beliefs else belief),
        "presentation_count": len(expected), "executed_prompt_count": n_executed,
        "deduplicate_prompts": spec.deduplicate_prompts,
        "bank_sha": _sha([dump(r) for r in expected]),
        "model": model_identity,
        "decoding": ({"temperature": None, "reasoning_effort": "none", "sampling": "provider_default", "use_cache": False}
                     if spec.provider == "openai" else
                     {"temperature": 0, "seed": spec.seed, "max_new_tokens": spec.max_new_tokens, "thinking": False}),
        "checks": summaries,
        "interpretation": "Diagnostics only; no overall validity verdict or internal-belief probability.",
    }
    if v3:
        metrics["answer_policy"] = "Complete single label, matching labelled option, or exact option word; extra prose/conflicts rejected."
    if expected and spec.provider == "anthropic":
        metrics["decoding"] = {"temperature": None, "sampling": "provider_default",
                               "thinking": "between_tools", "effort": "provider_default",
                               "max_tokens": spec.max_new_tokens, "use_cache": False}
        metrics["model"]["returned_models"] = sorted({r["response"].get("model", "") for r in model.client.records})
    if not expected:
        metrics["model"] = None
        metrics["decoding"] = None
    metrics["execution_status"] = "failed" if any(r.error and r.response is None for r in observed) else "completed"
    summary_path = directory / "instrument_summary.json"
    summary_path.write_text(json.dumps(metrics, indent=2) + "\n")
    result = build_result(context, stage="instrument_validation", experiment_id=job.experiment.id,
                          run_id=job.run_id, datapoints=len(observed),
                          artifacts=[bank_path, path, summary_path, *provider_artifacts], metrics=metrics, config_sha=config_sha(job),
                          backend=backend_info(dtype=job.models.models[model_id].dtype) if expected and spec.provider == "local" else None)
    result_path = write_result(result)
    write_resolved_config(job, result_path.parent)
    return result
