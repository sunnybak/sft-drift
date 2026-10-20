"""One immutable measurement bundle, independent passes, and layered meta-eval."""
from __future__ import annotations

import asyncio
import json

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.analysis.measurement_report import write_measurement_report
from belief_transfer.analysis.report import ROOT, build_result, write_result
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.evals.measurements import VERSION, DEFINITIONS, bank_checks, build_measurement_banks, build_measurement_controls
from belief_transfer.evals.pilot import build_banks, fingerprint, validate_wordings
from belief_transfer.evals.suite import load_rows, write_rows
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.local import local_model
from belief_transfer.inference.backend import backend_info
from belief_transfer.metrics.measurements import summarize_measurement, summarize_controls, summarize_stance_study
from belief_transfer.schemas import PilotWording
from belief_transfer.validation.measurements import EXTRACTOR_VERSION, extract_response, scorer_checks, format_compliant, measurement_response_text, observation_from_reply


def decoding_record(spec):
    d = spec.measurement_decoding
    execution = {}
    if spec.cuda_generation is not None:
        from belief_transfer.inference.execution import generation_identity

        execution = generation_identity(spec.cuda_generation)
    strategy = ('vllm-per-request-v1' if spec.cuda_generation is not None
                and spec.cuda_generation.engine == 'vllm' else 'per-token-v1')
    return {"temperature": d.temperature, "seed": spec.seed, "thinking": d.thinking,
            "max_new_tokens": spec.max_new_tokens,
            **({"batch_size": spec.measurement_batch_size, "sampling_seed_strategy": strategy}
               if spec.measurement_batch_size > 1 else {}),
            **{key: getattr(d, key) for key in ("top_p", "top_k", "min_p") if getattr(d, key) is not None},
            **execution}


def measurement_bank_fingerprint(bundle):
    """Common item identity excludes model-specific qualification evidence."""
    return fingerprint({"version": bundle["version"], "banks": bundle["banks"],
        "controls": bundle["controls"], "content": {key: bundle["source_manifest"][key]
            for key in ("targets_sha", "wordings_sha")}})


def prepare(job):
    spec = job.pilot_bench
    active_stance = len(spec.measurements) == 1 and spec.measurements[0].version in {"stance-v1", "stance-v2"}
    if not spec.targets or job.replicates != 1:
        raise ValueError("measurements require targets and replicates=1")
    source = ROOT / "data/generated" / job.experiment.id / spec.bank_run_id
    manifest = json.loads((source / "bank_manifest.json").read_text())
    wordings = [PilotWording.model_validate(r) for r in load_rows(source / "belief_wordings.jsonl")]
    validate_wordings(spec, wordings)
    if manifest["targets_sha"] != fingerprint([t.model_dump() for t in spec.targets]):
        raise ValueError("frozen targets changed")
    if manifest["wordings_sha"] != fingerprint([w.model_dump() for w in wordings]):
        raise ValueError("frozen wordings changed")
    if manifest.get("version", "ethical-pilot-v1") == "ethical-pilot-v2":
        if spec.version != "ethical-pilot-v2":
            raise ValueError("source content contract version changed")
    else:
        legacy = build_banks(spec, wordings)
        for name, rows in zip(("binary", "categorical"), legacy):
            if manifest[f"{name}_sha"] != fingerprint(rows) or rows != load_rows(source / f"{name}_bank.jsonl"):
                raise ValueError("frozen content bank changed")
    banks = build_measurement_banks(spec, wordings, smoke=job.smoke)
    controls = build_measurement_controls(banks, style=spec.measurement_prompt_style,
        rubrics=spec.conviction_rubrics, interface=spec.conviction_interface,
        versions={m.name: m.version for m in spec.measurements if m.version in {"stance-v1", "stance-v2"}},
        stance_interface=spec.stance_interface)
    meta = {"artifact": bank_checks(spec, wordings, banks, smoke=job.smoke),
            "harness": scorer_checks(["stance"] if active_stance else None,
                stance_interface=spec.stance_interface if active_stance and spec.measurements[0].version == "stance-v2" else None),
            "content_semantics": manifest["meta_eval"],
            "template_review": {"status": "agent_reviewed_exploratory", "version": VERSION,
                "human_alignment": "not performed; user authorized agent judgment",
                "specification": "configs/probe/stance_conviction_v1.md"}}
    if any(v["status"] != "passed" for v in meta["harness"].values()):
        raise ValueError("scorer controls failed")
    bundle = {"version": VERSION,
              "source_bank_run_id": spec.bank_run_id, "source_manifest": manifest,
              "smoke": job.smoke, "definitions": {k: DEFINITIONS[k] for k in banks},
              "banks": {k: fingerprint(v) for k, v in banks.items()},
              "controls": {k: fingerprint(v) for k, v in controls.items()}, "meta_eval": meta}
    if spec.measurement_prompt_style != "original":
        meta["template_review"].update(response_style=spec.measurement_prompt_style,
            version=VERSION + "/" + spec.measurement_prompt_style,
            review_basis="Response instructions only; selected on unchanged known-control correctness and improved exact-letter compliance.")
        bundle.update(version=VERSION + "/" + spec.measurement_prompt_style,
                      prompt_style=spec.measurement_prompt_style)
    if spec.conviction_rubrics:
        bundle.update(version="stance-conviction-v2/" + spec.measurement_prompt_style,
            conviction_design="one_factor_slices", conviction_rubrics=[r.model_dump() for r in spec.conviction_rubrics])
        meta["template_review"].update(version=bundle["version"],
            specification="configs/probe/conviction_rubrics_v2.md", rubric_count=6,
            review_basis="Six equivalent definitions with explicit unsettled-lean/no-lean boundaries; previous concise response instruction retained.",
            meaning_review="Agent reviewed settled judgment / unsettled lean / no lean equivalence; references provisional.")
    if spec.conviction_interface != "legacy":
        bundle.update(version="stance-conviction-v3/" + spec.conviction_interface + "/" + spec.measurement_prompt_style,
            conviction_interface=spec.conviction_interface,
            comprehension_reference_version="conviction-comprehension-v3")
        meta["template_review"].update(version=bundle["version"],
            specification="configs/probe/conviction_stability_v3.md",
            review_basis="Definitions attached to options; no ethical demonstrations. Development selection and held-out validation separately recorded.")
    if spec.conviction_meta:
        bundle["qualification_thresholds"] = spec.conviction_meta.model_dump()
    if spec.conviction_selection_run_id:
        selection_path = ROOT / 'data/results' / job.experiment.id / spec.conviction_selection_run_id / 'selection.json'
        selection = json.loads(selection_path.read_text())
        if not selection['development_passed'] or selection['selected'] != spec.conviction_interface:
            raise ValueError('validation requires a frozen, development-qualified interface')
        if not spec.conviction_meta or selection['thresholds'] != spec.conviction_meta.model_dump():
            raise ValueError('validation thresholds differ from frozen development selection')
        selected_bank = load_rows(selection_path.parent / (selection['selected'] + '_bank.jsonl'))
        selected_controls = [r for r in selected_bank if 'control_kind' in r]
        current_controls = [r for r in controls['conviction'] if r['control_kind'] != 'comprehension'
                            or r.get('reference_split') == 'development']
        if selected_controls != current_controls:
            raise ValueError('validation definitions or control interface differ from frozen selection')
        bundle['development_selection'] = {'run_id': spec.conviction_selection_run_id,
            'selection_sha': fingerprint(selection), 'development_controls_sha': fingerprint(selected_controls), 'selection': selection}
    if active_stance:
        bundle["version"] = spec.measurements[0].version + "/" + spec.measurement_prompt_style
        if spec.measurements[0].version == "stance-v2":
            bundle["version"] += "/" + spec.stance_interface
            bundle["stance_interface"] = spec.stance_interface
        meta["harness"] = {"stance": meta["harness"]["stance"]}
        meta["template_review"] = {
            "status": "agent_reviewed_exploratory", "version": bundle["version"],
            "human_alignment": "pending; previous content review remains provisional",
            "specification": "configs/probe/stance_v2.md" if spec.measurements[0].version == "stance-v2" else "configs/probe/stance_v1.md",
            "review_basis": "Existing Stance question and content retained; separate controls, coverage, order, wording and negation diagnostics."}
    if spec.stance_validation_run_id:
        bundle["stance_validation"] = verified_stance_validation(job, controls)
    return banks, controls, bundle


def verified_stance_validation(job, controls):
    """Replay the frozen validation before administering the larger bank."""
    spec = job.pilot_bench
    if set(controls) != {"stance"}:
        raise ValueError("Stance validation requires a Stance-only instrument")
    source = ROOT / "data/results" / job.experiment.id / spec.stance_validation_run_id
    if (source / "VOID.md").exists():
        raise ValueError("void Stance validation")
    selection = json.loads((source / "stance_study_summary.json").read_text())
    candidate = spec.stance_interface
    identity = {"model_config": job.models.models[spec.model].model_dump(mode="json"),
        "backend": backend_info(dtype=job.models.models[spec.model].dtype).model_dump(mode="json"),
        "adapter": spec.adapter_path, **decoding_record(spec)}
    if (selection["study"]["phase"] != "validation" or not selection["validation_passed"]
            or selection["selected"] != candidate or selection["identity"] != identity):
        raise ValueError("full-bank measurement requires the same validated interface and model/settings")
    bank = load_rows(source / f"{candidate}_bank.jsonl")
    raw = load_rows(source / f"{candidate}_observations.jsonl")
    if fingerprint(bank) != selection["banks"][candidate]:
        raise ValueError("Stance validation bank changed")
    if [r for r in bank if "control_kind" in r] != controls["stance"]:
        raise ValueError("Stance validation controls or response template changed")
    if summarize_stance_study(bank, raw, selection["thresholds"],
            qualify_natural_consistency=selection["study"].get("qualify_natural_consistency", True)) != selection["scores"][candidate]:
        raise ValueError("Stance validation qualification no longer reconstructs")
    for row in raw:
        if not row.get("error"):
            final = measurement_response_text(row)
            if (extract_response(final, row) != (row["answer"], row["answer_extraction"])
                    or format_compliant(final, row) != row["strict_format"]):
                raise ValueError("Stance validation extraction changed")
    return {"run_id": spec.stance_validation_run_id, "summary_sha": fingerprint(selection),
        "thresholds": selection["thresholds"], "identity": identity,
        "qualification_basis": selection["scores"][candidate]["qualification_basis"]}


def start(job, banks, controls, bundle):
    directory = ROOT / "data/results" / job.experiment.id / job.run_id
    if (directory / "measurement_manifest.json").exists():
        raise FileExistsError("use a fresh measurement run ID")
    directory.mkdir(parents=True, exist_ok=True)
    write_resolved_config(job, directory)
    artifacts = []
    for name, bank in banks.items():
        for suffix, rows in (("bank", bank), ("control_bank", controls[name])):
            p = write_rows(rows, directory / f"{name}_{suffix}.jsonl")
            write_md(p)
            artifacts.extend([p, p.with_suffix(".md")])
    path = directory / "measurement_manifest.json"
    path.write_text(json.dumps(bundle, indent=2) + "\n")
    artifacts.append(path)
    return directory, artifacts


def finish(job, metrics, artifacts):
    result = build_result(RunContext(), stage=job.stage, experiment_id=job.experiment.id,
        run_id=job.run_id, datapoints=metrics.get("presentation_count", 0), artifacts=artifacts,
        metrics=metrics, config_sha=config_sha(job),
        backend=backend_info(dtype=job.models.models[job.pilot_bench.model].dtype) if job.stage == "pilot_measurements" else None)
    write_result(result)
    return result


async def run_build(job):
    banks, controls, bundle = prepare(job)
    directory, artifacts = start(job, banks, controls, bundle)
    return finish(job, {"version": bundle["version"], "executed_model_calls": 0,
        "presentation_count": sum(len(b) for b in banks.values()), "meta_eval": bundle["meta_eval"],
        "bank_sha": fingerprint(bundle), "measurement_bank_sha": measurement_bank_fingerprint(bundle),
        "bank_identity_version": "measurement-bank-v1"}, artifacts)


async def run(job):
    banks, controls, bundle = prepare(job)
    spec = job.pilot_bench
    reused = {}
    if spec.measurement_controls_source_run_id:
        if spec.adapter_path is not None:
            raise ValueError('control reuse is restricted to unchanged BASE models; fine-tunes need fresh controls')
        source = ROOT / 'data/results' / job.experiment.id / spec.measurement_controls_source_run_id
        if (source / 'VOID.md').exists():
            raise ValueError('cannot reuse void control results')
        original = json.loads((source / 'measurement_summary.json').read_text())
        expected = {'version': bundle['version'], 'extractor_version': EXTRACTOR_VERSION,
            'model': job.models.models[spec.model].pretrained, 'adapter': None,
            'model_config_sha': fingerprint(job.models.models[spec.model].model_dump()),
            'backend': backend_info(dtype=job.models.models[spec.model].dtype).model_dump(mode='json'),
            'decoding': decoding_record(spec)}
        if any(original.get(k) != v for k, v in expected.items()):
            raise ValueError('control source model, backend, decoding or instrument changed')
        for name, bank in controls.items():
            if load_rows(source / f'{name}_control_bank.jsonl') != bank:
                raise ValueError('control source bank changed')
            rows = load_rows(source / f'{name}_controls.jsonl')
            from belief_transfer.metrics.measurements import align
            aligned = align(bank, rows)
            if any(r.get('error') for r in aligned):
                raise ValueError('control source is incomplete or invalid')
            for r in aligned:
                text = measurement_response_text(r)
                answer, mode = extract_response(text, r)
                if answer != r['answer'] or mode != r['answer_extraction'] or format_compliant(text, r) != r['strict_format']:
                    raise ValueError('control source extraction changed')
            reused[name] = {r['presentation_id']: {**r, 'control_observation_source': spec.measurement_controls_source_run_id} for r in aligned}
    directory, artifacts = start(job, banks, controls, bundle)
    model = local_model(spec.model, job.models, adapter_path=spec.adapter_path,
        max_new_tokens=spec.max_new_tokens, seed=spec.seed, enable_thinking=spec.measurement_decoding.thinking,
        **({'generation': spec.cuda_generation} if spec.cuda_generation is not None else {}),
        **{key: getattr(spec.measurement_decoding, key) for key in ("top_p", "top_k", "min_p")
           if getattr(spec.measurement_decoding, key) is not None})
    observed, control_observed = {}, {}
    for purpose, batches, storage in (("controls", controls, control_observed), ("observations", banks, observed)):
        for name, rows in batches.items():
            storage[name] = []
            path = directory / f"{name}_{purpose}.jsonl"
            path.touch()
            if purpose == "observations" and "stance_validation" in bundle:
                check = summarize_stance_study(controls[name] + rows, control_observed[name],
                    bundle["stance_validation"]["thresholds"], qualify_natural_consistency=False)
                if not all(check["controls"]["checks"].values()):
                    print("[measurements] factual controls failed; natural calls skipped", flush=True)
                    write_md(path)
                    artifacts.extend([path, path.with_suffix(".md")])
                    continue
            for batch_start in range(0, len(rows), spec.measurement_batch_size):
                batch = rows[batch_start:batch_start + spec.measurement_batch_size]
                if purpose == "controls" and name in reused:
                    replies = [reused[name][row["presentation_id"]] for row in batch]
                elif spec.measurement_batch_size > 1:
                    replies = await administer_batch(model, batch, spec)
                else:
                    row = batch[0]
                    if spec.measurement_decoding.temperature:
                        model.seed = (spec.seed ^ int(row["prompt_sha"][:8], 16)) & 0xffffffff
                    replies = [await administer(model, row, temperature=spec.measurement_decoding.temperature,
                                               thinking=spec.measurement_decoding.thinking)]
                for result in replies:
                    storage[name].append(result)
                    with path.open("a") as handle:
                        handle.write(json.dumps(result, ensure_ascii=False) + "\n")
                if len(storage[name]) % 24 == 0 or len(storage[name]) == len(rows):
                    print(f"[measurements] {name}/{purpose} {len(storage[name])}/{len(rows)}", flush=True)
            write_md(path)
            artifacts.extend([path, path.with_suffix(".md")])
    meta = {**bundle["meta_eval"], "model_controls": {
        k: summarize_controls(v, control_observed[k]) for k, v in controls.items()}}
    summary = {"version": bundle["version"], "extractor_version": EXTRACTOR_VERSION,
        "model": job.models.models[spec.model].pretrained, "adapter": spec.adapter_path,
        'model_config_sha': fingerprint(job.models.models[spec.model].model_dump()),
        'backend': backend_info(dtype=job.models.models[spec.model].dtype).model_dump(mode='json'),
        "source_bank_run_id": spec.bank_run_id, "bank_sha": fingerprint(bundle), "smoke": job.smoke,
        "measurement_bank_sha": measurement_bank_fingerprint(bundle),
        "bank_identity_version": "measurement-bank-v1",
        "decoding": decoding_record(spec),
        "measurements": {k: summarize_measurement(v, observed[k]) for k, v in banks.items()},
        "meta_eval": meta, "presentation_count": sum(map(len, banks.values())) + sum(map(len, controls.values())),
        "executed_model_calls": sum(r.get("response") is not None and 'control_observation_source' not in r for batch in
            [*observed.values(), *control_observed.values()] for r in batch),
        'reused_control_observations': sum('control_observation_source' in r for batch in control_observed.values() for r in batch),
        "interpretation": ("Generated Stance with independent instrument diagnostics; exploratory review; no internal-confidence or forgetting claim."
            if set(banks) == {"stance"} else
            "Historical independent generated Stance and self-reported Conviction; exploratory agent review; no calibration or forgetting claim.")}
    if "stance_validation" in bundle:
        check = summarize_stance_study(controls["stance"] + banks["stance"],
            control_observed["stance"] + observed["stance"], bundle["stance_validation"]["thresholds"],
            qualify_natural_consistency=False)
        meta["stance_operational_qualification"] = {
            "validation": bundle["stance_validation"], "controls": check["controls"],
            "passed": check["passed"], "qualification_basis": check["qualification_basis"]}
    if spec.conviction_meta:
        from belief_transfer.metrics.measurements import qualify_conviction
        summary["meta_eval"]["conviction_qualification"] = qualify_conviction(
            summary["measurements"]["conviction"], controls["conviction"], control_observed["conviction"],
            spec.conviction_meta.model_dump())
    path = directory / "measurement_summary.json"
    path.write_text(json.dumps(summary, indent=2) + "\n")
    artifacts.extend([path, *write_measurement_report(summary, spec.targets, directory, rubrics=spec.conviction_rubrics)])
    return finish(job, summary, artifacts)


async def administer(model, row, *, temperature=0, thinking=False):
    try:
        replies = await asyncio.to_thread(model.generate, [row["prompt"]], temperature=temperature)
        if len(replies) != 1:
            raise ValueError("incorrect response count")
        return observed_backend_reply(row, replies[0], getattr(model, "last_generation_metadata", None),
                                      thinking=thinking, seed=getattr(model, "seed", None))
    except Exception as exc:
        return {**row, "response": None, "answer": None, "strict_format": False,
                "error": f"{type(exc).__name__}: {exc}"}


async def administer_batch(model, rows, spec):
    """Explicit batch path with metadata and independent final-response extraction."""
    seeds = [(spec.seed ^ int(row["prompt_sha"][:8], 16)) & 0xffffffff for row in rows]
    try:
        if not hasattr(model, "generate_batch_with_metadata"):
            raise ValueError("this backend has no qualified batched generated-answer path")
        replies = await asyncio.to_thread(model.generate_batch_with_metadata, [row["prompt"] for row in rows],
            temperature=spec.measurement_decoding.temperature, seeds=seeds, batch_size=spec.measurement_batch_size)
        if len(replies) != len(rows):
            raise ValueError("incorrect batch response count")
        return [observed_backend_reply(row, text, metadata,
            thinking=spec.measurement_decoding.thinking, seed=seed)
            for row, (text, metadata), seed in zip(rows, replies, seeds)]
    except Exception as exc:
        return [{**row, "response": None, "answer": None, "strict_format": False,
                 "error": f"{type(exc).__name__}: {exc}"} for row in rows]


def observed_backend_reply(row, text, metadata, *, thinking, seed):
    result = observation_from_reply(row, text, metadata, thinking=thinking, seed=seed)
    if (metadata or {}).get('backend_error'):
        result.update(error=metadata['backend_error'], answer=None,
                      answer_extraction='backend-error', strict_format=False)
    return result
