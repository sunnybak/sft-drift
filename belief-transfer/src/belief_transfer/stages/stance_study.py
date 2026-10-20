"""Frozen Stance-format comparison on reviewed content; no training or Conviction."""
from __future__ import annotations

import json

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.analysis.report import ROOT, build_result, write_result
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.evals.measurements import build_measurement_banks, stance_model_controls
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.evals.suite import load_rows, write_rows
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.backend import backend_info
from belief_transfer.inference.local import local_model
from belief_transfer.metrics.measurements import select_stance_candidate, summarize_stance_study
from belief_transfer.schemas import PilotBenchSpec, PilotWording
from belief_transfer.stages.measurements import administer, administer_batch, prepare, decoding_record
from belief_transfer.validation.measurements import EXTRACTOR_VERSION, extract_response, format_compliant, measurement_response_text

THRESHOLDS = ("control_accuracy", "extraction", "order_agreement", "wording_agreement", "negation_coherence", "null_flip_max")


def study_controls(candidate):
    return stance_model_controls(candidate)

async def run(job):
    spec = job.pilot_bench
    study = spec.stance_study
    if study is None:
        raise ValueError("stance_study requires a frozen study specification")
    _, _, source_bundle = prepare(job)
    wordings = [PilotWording.model_validate(r) for r in load_rows(
        ROOT / "data/generated" / job.experiment.id / spec.bank_run_id / "belief_wordings.jsonl")]
    if set(study.belief_ids) - {t.definition.id for t in spec.targets}:
        raise ValueError("unknown study target")
    if set(study.wording_ids) - {w.wording_id for w in wordings}:
        raise ValueError("unknown study wording")
    thresholds = {key: getattr(study, key) for key in THRESHOLDS}
    identity = {"model_config": job.models.models[spec.model].model_dump(mode="json"),
        "backend": backend_info(dtype=job.models.models[spec.model].dtype).model_dump(mode="json"),
        "adapter": spec.adapter_path, **decoding_record(spec)}
    selection = None
    if study.phase == "validation":
        selection_path = ROOT / "data/results" / job.experiment.id / study.selection_run_id / "stance_study_summary.json"
        if (selection_path.parent / "VOID.md").exists():
            raise ValueError("void development selection")
        selection = json.loads(selection_path.read_text())
        if selection["selected"] != study.candidates[0] or not selection["scores"][study.candidates[0]]["passed"]:
            raise ValueError("validation requires a development-qualified frozen candidate")
        if selection["thresholds"] != thresholds or selection["identity"] != identity:
            raise ValueError("validation thresholds or model/settings changed")
        if selection["study"].get("qualify_natural_consistency", True) != study.qualify_natural_consistency:
            raise ValueError("validation qualification policy differs from development")
        if set(selection["study"]["belief_ids"]) & set(study.belief_ids):
            raise ValueError("validation needs different belief definitions")
        saved_bank = load_rows(selection_path.parent / f"{study.candidates[0]}_bank.jsonl")
        saved_raw = load_rows(selection_path.parent / f"{study.candidates[0]}_observations.jsonl")
        if fingerprint(saved_bank) != selection["banks"][study.candidates[0]]:
            raise ValueError("development bank changed")
        if [r for r in saved_bank if "control_kind" in r] != study_controls(study.candidates[0]):
            raise ValueError("validation template or controls changed")
        if summarize_stance_study(saved_bank, saved_raw, thresholds,
                qualify_natural_consistency=study.qualify_natural_consistency) != selection["scores"][study.candidates[0]]:
            raise ValueError("development qualification no longer reconstructs")
        for row in saved_raw:
            if not row.get("error"):
                final = measurement_response_text(row)
                if extract_response(final, row) != (row["answer"], row["answer_extraction"]):
                    raise ValueError("development extraction changed")
                if format_compliant(final, row) != row["strict_format"]:
                    raise ValueError("development format compliance changed")
    directory = ROOT / "data/results" / job.experiment.id / job.run_id
    if (directory / "stance_study_manifest.json").exists() or any(directory.glob("*_observations.jsonl")):
        raise FileExistsError("use a fresh Stance study run ID")
    directory.mkdir(parents=True, exist_ok=True)
    write_resolved_config(job, directory)
    banks, artifacts = {}, []
    for candidate in study.candidates:
        candidate_spec = PilotBenchSpec.model_validate({**spec.model_dump(),
            "stance_interface": candidate, "measurements": [{"name": "stance", "version": "stance-v2"}]})
        natural = build_measurement_banks(candidate_spec, wordings,
            belief_ids=study.belief_ids, wording_ids=study.wording_ids)["stance"]
        banks[candidate] = study_controls(candidate) + natural
        expected = 4 * len(study.belief_ids) * len(study.wording_ids)
        if len(natural) != expected:
            raise ValueError("study grid incomplete")
        path = write_rows(banks[candidate], directory / f"{candidate}_bank.jsonl")
        write_md(path)
        artifacts.extend([path, path.with_suffix(".md")])
    manifest = {"version": study.version, "study": study.model_dump(), "thresholds": thresholds,
        "identity": identity, "source_bundle_sha": fingerprint(source_bundle),
        "extractor_version": EXTRACTOR_VERSION, "stance_word_extractor_version": "stance-word-v1",
        "banks": {name: fingerprint(bank) for name, bank in banks.items()},
        "status": "unregistered instrument-development observation; not a forgetting experiment",
        "selection_policy": ("Known controls and worst/mean consistency only; no ethical support rate used."
            if study.qualify_natural_consistency else
            "Known controls and complete extraction only; natural endorsement and consistency are outcomes, never selection criteria.")}
    if selection is not None:
        manifest["development_selection_sha"] = fingerprint(selection)
    manifest_path = directory / "stance_study_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    artifacts.append(manifest_path)
    model = local_model(spec.model, job.models, adapter_path=spec.adapter_path,
        max_new_tokens=spec.max_new_tokens, seed=spec.seed, enable_thinking=spec.measurement_decoding.thinking,
        **({'generation': spec.cuda_generation} if spec.cuda_generation is not None else {}),
        **{key: getattr(spec.measurement_decoding, key) for key in ("top_p", "top_k", "min_p")
           if getattr(spec.measurement_decoding, key) is not None})
    scores, n_calls = {}, 0
    for candidate, bank in banks.items():
        observations = []
        path = directory / f"{candidate}_observations.jsonl"
        path.touch()
        groups = ([r for r in bank if "control_kind" in r], [r for r in bank if "control_kind" not in r])
        for purpose, group in zip(("controls", "natural"), groups):
            if purpose == "natural" and study.stop_on_control_failure:
                preliminary = summarize_stance_study(bank, observations, thresholds,
                    qualify_natural_consistency=study.qualify_natural_consistency)
                if not all(preliminary["controls"]["checks"].values()):
                    print(f"[stance_study] {candidate}: controls failed; natural calls skipped", flush=True)
                    break
            for start in range(0, len(group), spec.measurement_batch_size):
                batch = group[start:start + spec.measurement_batch_size]
                if spec.measurement_batch_size > 1:
                    observed_batch = await administer_batch(model, batch, spec)
                else:
                    row = batch[0]
                    if spec.measurement_decoding.temperature:
                        model.seed = (spec.seed ^ int(row["prompt_sha"][:8], 16)) & 0xffffffff
                    observed_batch = [await administer(model, row,
                        temperature=spec.measurement_decoding.temperature, thinking=spec.measurement_decoding.thinking)]
                for observed in observed_batch:
                    observations.append(observed)
                    with path.open("a") as handle:
                        handle.write(json.dumps(observed, ensure_ascii=False) + "\n")
                    n_calls += 1
                if len(observations) % 16 == 0 or len(observations) == len(bank):
                    print(f"[stance_study] {candidate} {len(observations)}/{len(bank)}", flush=True)
        write_md(path)
        artifacts.extend([path, path.with_suffix(".md")])
        scores[candidate] = summarize_stance_study(bank, observations, thresholds,
            qualify_natural_consistency=study.qualify_natural_consistency)
    summary = {**manifest, "scores": scores, "selected": select_stance_candidate(scores, study.candidates,
        qualify_natural_consistency=study.qualify_natural_consistency)
        if study.phase == "development" else study.candidates[0],
        "validation_passed": scores[study.candidates[0]]["passed"] if study.phase == "validation" else None,
        "executed_model_calls": n_calls, "presentation_count": sum(map(len, banks.values()))}
    summary_path = directory / "stance_study_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    artifacts.append(summary_path)
    report = directory / "stance_study_report.md"
    lines = ["# Stance format study", "", "Selection uses controls and consistency, not the ethical positions expressed.", "",
        "| Candidate | Factual correct / expected | Null flip rate | Worst consistency | Mean consistency | Qualified |",
        "|---|---:|---:|---:|---:|---|"]
    for name, score in scores.items():
        c = score["controls"]
        lines.append(f"| {name} | {c['n_correct']}/{c['n_expected']} | {c['null_flip_rate']} | "
                     f"{score['minimum_consistency']} | {score['mean_consistency']} | {score['passed']} |")
    lines += ["", f"Selected: `{summary['selected']}`. Validation passed: `{summary['validation_passed']}`.", "",
        manifest["selection_policy"], "",
        "All per-belief failures, expected/eligible denominators and raw replies remain in JSONL/JSON. "
        "Showing both positions changes the measurement context; passing this study does not certify latent beliefs.", ""]
    report.write_text("\n".join(lines))
    artifacts.append(report)
    result = build_result(RunContext(), stage=job.stage, experiment_id=job.experiment.id, run_id=job.run_id,
        datapoints=n_calls, artifacts=artifacts, metrics=summary, config_sha=config_sha(job),
        backend=backend_info(dtype=job.models.models[spec.model].dtype))
    write_result(result)
    return result
