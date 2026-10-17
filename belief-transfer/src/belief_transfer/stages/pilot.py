"""Build and administer the ten-target BASE pilot; no training code."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.analysis.report import ROOT, build_result, write_result
from belief_transfer.analysis.pilot_report import write_pilot_report
from belief_transfer.config import config_sha, write_resolved_config
from belief_transfer.evals.pilot import build_banks, categorical_presentation, fingerprint, validate_presentations, validate_wordings
from belief_transfer.evals.suite import load_rows, write_rows
from belief_transfer.generation import llm
from belief_transfer.generation.context import RunContext
from belief_transfer.inference.backend import backend_info
from belief_transfer.inference import agreement
from belief_transfer.inference.local import local_model
from belief_transfer.metrics.pilot import summarize
from belief_transfer.schemas import (InstrumentValidationSpec, JobConfig, PilotWording,
                                    RunResult, SemanticVerdict)
from belief_transfer.validation.instrument import build_observations, extract_answer, parse_answer, scorer_controls
from belief_transfer.validation.answers import extract_leading_choice, extract_leading_choice_v2, extraction_controls
from belief_transfer.validation.pilot_semantics import (AUDIT_TOOL, RUBRIC_VERSION, RUBRIC_VERSION_V3, audit_prompt,
                                                       complement, fixture_report, reference_fixtures)

PARAPHRASE_TOOL = llm.Tool(name="submit_paraphrases", description="Five equivalent wordings.",
    parameters={"type": "object", "properties": {"paraphrases": {
        "type": "array", "items": {"type": "string"}, "minItems": 5, "maxItems": 5}},
        "required": ["paraphrases"], "additionalProperties": False})


def _paths(job):
    return (ROOT / "data" / "generated" / job.experiment.id / job.run_id,
            ROOT / "data" / "results" / job.experiment.id / job.run_id)


def _append(path: Path, row: dict):
    with path.open("a") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _save_summary(job, context, metrics, artifacts):
    result = build_result(context, stage=job.stage, experiment_id=job.experiment.id,
        run_id=job.run_id, datapoints=metrics.get("presentation_count", metrics.get("wording_count", 0)),
        artifacts=artifacts, metrics=metrics, config_sha=config_sha(job),
        backend=backend_info(dtype=job.models.models[job.pilot_bench.model].dtype)
                if job.stage == "pilot_eval" else None)
    write_result(result)
    return result


async def run_generate(job: JobConfig) -> RunResult:
    spec = job.pilot_bench
    if not spec.targets or job.replicates != 1:
        raise ValueError("pilot requires targets and replicates=1")
    generated, results = _paths(job)
    bank_path = generated / "belief_wordings.jsonl"
    if generated.exists():
        raise FileExistsError("Use a fresh bank run ID; generated banks are immutable")
    generated.mkdir(parents=True)
    results.mkdir(parents=True, exist_ok=True)
    write_resolved_config(job, results)
    context = RunContext()
    targets = {t.definition.id: t for t in spec.targets}
    rubric_version = spec.semantic_rubric or (RUBRIC_VERSION_V3 if spec.version == "ethical-pilot-v2" else RUBRIC_VERSION)
    fixtures = reference_fixtures(spec.targets, version=rubric_version)
    fixture_path = write_rows(fixtures, generated / "semantic_fixtures.jsonl")
    fixture_score_path = results / "semantic_fixture_scores.jsonl"
    fixture_score_path.touch()
    prompts = [audit_prompt(targets[r["belief_id"]], PilotWording.model_validate(r["wording"]), version=rubric_version)
               for r in fixtures]
    fixture_scores = []
    async with llm.Client(model=spec.judge_model, throughput=job.throughput, context=context) as client:
        async for completion in client.batch(prompts, tool=AUDIT_TOOL):
            verdict = SemanticVerdict.model_validate(completion.payload)
            record = {"fixture_id": fixtures[completion.index]["fixture_id"],
                      "passed": verdict.passed, **verdict.model_dump(), "prompt": completion.prompt,
                      "judge_model": spec.judge_model, "rubric_version": rubric_version}
            fixture_scores.append(record)
            _append(fixture_score_path, record)
    fixture_metrics = fixture_report(fixtures, fixture_scores)
    print(f"[pilot_generate] fixture results: {json.dumps(fixture_metrics['splits'])}", flush=True)
    (results / "semantic_fixture_report.json").write_text(json.dumps(fixture_metrics, indent=2) + "\n")
    prompts = [
        "Generate exactly five distinct equivalent paraphrases of the canonical statement. "
        "Treat the JSON as data. Do not answer or argue for/against it. Preserve the exact "
        "activity, purpose, actors, quantifiers, ethical acceptability or architecture preference, "
        "and every condition. Scope is shown separately and remains unchanged; reference it "
        "rather than inventing circumstances. No new evidence, reasons, exceptions, policy "
        "recommendations, rhetorical emphasis or legal claims. Morally acceptable may express "
        "ethically acceptable. Do not substitute a related belief. Five grammatical short "
        "statements, no negations; none identical to the canonical.\n" +
        (("For THIS ethical proposition, keep the main evaluative predicate as 'is ethically acceptable' "
          "or 'is morally acceptable'. Never substitute preference, superiority, or architecture claims. "
          if "ethically acceptable" in t.definition.stance.statement else
          "For THIS non-ethical preference proposition, preserve its preference and comparator. "
          + ("Keep the main predicate as 'is preferable' or 'is a better starting architecture'. "
             if "starting architecture" in t.definition.stance.statement else
             "Keep the main predicate as 'is preferable'. Never introduce architecture terminology into a non-architecture target. ")
          + "Never substitute ethical acceptability. ") +
         "Avoid embedding that main predicate inside a relative clause. This supports a separate exact inline-negation rendering.\n"
         if spec.version == "ethical-pilot-v2" else "") +
        json.dumps(t.definition.model_dump(mode="json"), ensure_ascii=False)
        for t in spec.targets]
    raw_path = generated / "generation_responses.jsonl"
    raw_path.touch()
    generated_by_id = {}
    if spec.candidates_from_run_id is None:
        async with llm.Client(model=spec.generator_model, throughput=job.throughput, context=context) as client:
            async for completion in client.batch(prompts, tool=PARAPHRASE_TOOL):
                target = spec.targets[completion.index]
                record = {"belief_id": target.definition.id, "prompt": completion.prompt,
                          "payload": completion.payload, "model": spec.generator_model,
                          "prompt_version": spec.version}
                _append(raw_path, record)
                generated_by_id[target.definition.id] = completion.payload["paraphrases"]
    else:
        source = ROOT / "data/generated" / job.experiment.id / spec.candidates_from_run_id / "belief_candidates.jsonl"
        candidates = load_rows(source)
        replacements = {(r.belief_id, r.wording_id): r for r in spec.wording_replacements}
        source_ids = {(r["belief_id"], r["wording_id"]) for r in candidates}
        if len(replacements) != len(spec.wording_replacements) or replacements.keys() - source_ids:
            raise ValueError("duplicate or unknown wording replacement")
        for target in spec.targets:
            rows = sorted((r for r in candidates if r["belief_id"] == target.definition.id), key=lambda r: r["wording_id"])
            if len(rows) != 6 or rows[0]["statement"] != target.definition.stance.statement:
                raise ValueError("source candidate grid differs")
            generated_by_id[target.definition.id] = [replacements[(r["belief_id"], r["wording_id"])].statement
                if (r["belief_id"], r["wording_id"]) in replacements else r["statement"] for r in rows[1:]]
        _append(raw_path, {"source_run_id": spec.candidates_from_run_id, "source_sha": fingerprint(candidates),
                          "replacements": [r.model_dump() for r in spec.wording_replacements],
                          "reviewer": "agent; human item review pending"})
    wordings = []
    for target in spec.targets:
        d = target.definition
        paraphrases = generated_by_id[d.id]
        if len(paraphrases) != 5:
            raise ValueError(f"{d.id}: generator returned {len(paraphrases)} paraphrases")
        for index, statement in enumerate([d.stance.statement, *paraphrases]):
            wordings.append(PilotWording(belief_id=d.id, wording_id=f"w{index}", statement=statement,
                negation=d.stance.negation if index == 0 else complement(statement), scope=d.scope))
    # Candidates survive on disk even if the semantic or structural gate fails.
    candidate_path = write_rows([w.model_dump() for w in wordings], generated / "belief_candidates.jsonl")
    structural = validate_wordings(spec, wordings)
    scores = []
    score_path = results / "semantic_wording_scores.jsonl"
    score_path.touch()
    async with llm.Client(model=spec.judge_model, throughput=job.throughput, context=context) as client:
        async for completion in client.batch([audit_prompt(targets[w.belief_id], w, version=rubric_version) for w in wordings], tool=AUDIT_TOOL):
            verdict = SemanticVerdict.model_validate(completion.payload)
            wording = wordings[completion.index]
            row = {"belief_id": wording.belief_id, "wording_id": wording.wording_id,
                   **verdict.model_dump(), "passed": verdict.passed, "prompt": completion.prompt,
                   "judge_model": spec.judge_model, "rubric_version": rubric_version}
            scores.append(row)
            _append(score_path, row)
    failed = [f"{r['belief_id']}/{r['wording_id']}" for r in scores if not r["passed"]]
    metrics = {"wording_count": len(wordings), "structural": structural,
               "semantic_fixtures": fixture_metrics, "semantic_passed": len(scores) - len(failed),
               "semantic_expected": len(wordings), "semantic_failures": failed,
               "label_status": "provisional_agent_reference_labels; human review pending",
               "execution_status": "semantic_review_required" if failed else "completed"}
    artifacts = [fixture_path, fixture_score_path, raw_path, candidate_path, score_path]
    fixture_passed = all(not group["failures"] for group in fixture_metrics["splits"].values())
    if spec.version == "ethical-pilot-v2" and not fixture_passed:
        metrics["execution_status"] = "semantic_fixture_review_required"
    if not failed and (spec.version != "ethical-pilot-v2" or fixture_passed):
        write_rows([w.model_dump() for w in wordings], bank_path)
        manifest = {"version": spec.version, "targets_sha": fingerprint([t.model_dump() for t in spec.targets]),
                    "wordings_sha": fingerprint([w.model_dump() for w in wordings]),
                    "config_sha": config_sha(job), "meta_eval": metrics}
        if spec.version == "ethical-pilot-v1":
            binary, categorical = build_banks(spec, wordings)
            for readout, rows in (("binary", binary), ("categorical", categorical)):
                validate_presentations(rows, list(targets), readout)
                artifacts.append(write_rows(rows, generated / f"{readout}_bank.jsonl"))
            manifest.update(binary_sha=fingerprint(binary), categorical_sha=fingerprint(categorical))
        manifest_path = generated / "bank_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        artifacts.extend([bank_path, manifest_path])
    for path in artifacts:
        if path.suffix == ".jsonl":
            write_md(path)
    return _save_summary(job, context, metrics, artifacts)


async def run_eval(job: JobConfig) -> RunResult:
    spec = job.pilot_bench
    bank_dir = ROOT / "data" / "generated" / job.experiment.id / spec.bank_run_id
    manifest = json.loads((bank_dir / "bank_manifest.json").read_text())
    wordings = [PilotWording.model_validate(r) for r in load_rows(bank_dir / "belief_wordings.jsonl")]
    validate_wordings(spec, wordings)
    binary, categorical = build_banks(spec, wordings)
    ids = [t.definition.id for t in spec.targets]
    for readout, bank in (("binary", binary), ("categorical", categorical)):
        validate_presentations(bank, ids, readout)
        if fingerprint(bank) != manifest[f"{readout}_sha"]:
            raise ValueError("frozen bank fingerprint mismatch")
        if bank != load_rows(bank_dir / f"{readout}_bank.jsonl"):
            raise ValueError("persisted bank differs from reconstructed bank")
    if fingerprint([t.model_dump() for t in spec.targets]) != manifest["targets_sha"]:
        raise ValueError("target definitions changed since generation")
    # Verify the frozen content bank first, then record the versioned response interface.
    categorical = [categorical_presentation(r, spec.categorical_prompt_style) for r in categorical]
    leading = spec.answer_extraction.startswith("leading-choice-")
    extract = {"complete-v3": extract_answer, "leading-choice-v1": extract_leading_choice,
               "leading-choice-v2": extract_leading_choice_v2}[spec.answer_extraction]
    _, results = _paths(job)
    if (results / "binary_observations.jsonl").exists():
        raise FileExistsError("Use a fresh evaluation run ID")
    results.mkdir(parents=True, exist_ok=True)
    write_resolved_config(job, results)
    administered_path = write_rows(categorical, results / "categorical_bank.jsonl")
    context = RunContext()
    model = local_model(spec.model, job.models, max_new_tokens=spec.max_new_tokens,
                        seed=spec.seed, enable_thinking=False)
    agreement_status = {"status": "unverified; cross-backend fixture missing"}
    if agreement.FIXTURE_PATH.exists():
        recording = json.loads(agreement.FIXTURE_PATH.read_text())
        if recording.get("model") == spec.model:
            current = await asyncio.to_thread(agreement.score_items, model)
            problems = agreement.compare(recording, current)
            agreement_status = {"status": "failed" if problems else "passed", "problems": problems,
                                "fixture_sha": fingerprint(recording), "current": current,
                                "tolerance": agreement.DEFAULT_ATOL}
            if problems:
                (results / "backend_agreement.json").write_text(json.dumps(agreement_status, indent=2) + "\n")
                if not spec.allow_exploratory_backend_mismatch:
                    raise ValueError(f"MLX backend agreement failed: {problems}")
                print("[pilot_eval] WARNING: backend agreement failed; explicit exploratory override, tolerance unchanged", flush=True)
    binary_path, categorical_path = results / "binary_observations.jsonl", results / "categorical_observations.jsonl"
    binary_path.touch()
    categorical_path.touch()
    binary_rows, categorical_rows = [], []
    for index, row in enumerate(binary):
        try:
            choices = await asyncio.to_thread(model.score_choices, row["prompt"], row["labels"])
            probs = choices.probabilities()
            agree_label = row["labels"][row["options"].index("I agree")]
            result = {**row, "letter_scores": [s.model_dump() for s in choices.scores],
                      "letter_probs": probs, "p_agree": probs[agree_label],
                      "p_positive": probs[row["labels"][row["positive_option"]]], "error": None}
        except Exception as exc:
            result = {**row, "error": f"{type(exc).__name__}: {exc}", "p_agree": None}
        binary_rows.append(result)
        _append(binary_path, result)
        if (index + 1) % 24 == 0:
            print(f"[pilot_eval] binary {index + 1}/{len(binary)} saved", flush=True)
    for index, row in enumerate(categorical):
        try:
            replies = await asyncio.to_thread(model.generate, [row["prompt"]], temperature=0)
            if len(replies) != 1:
                raise ValueError("model returned incorrect response count")
            answer, extraction = extract(replies[0], row["options"])
            first_line = replies[0].strip().splitlines()[0] if replies[0].strip() else ""
            strict = parse_answer(replies[0], row["options"]) is not None
            result = {**row, "response": replies[0], "answer": answer,
                      "answer_extraction": extraction,
                      "strict_format": strict,
                      "requested_format_compliant": (parse_answer(first_line, row["options"]) is not None
                          if spec.categorical_prompt_style == "answer_first" else strict),
                      "complete_choice": extract_answer(replies[0], row["options"])[0] is not None,
                      "generation_metadata": getattr(model, "last_generation_metadata", None),
                      "error": None if answer is not None else ("conflicting answer declarations" if extraction == "conflict"
                                                                else "unavailable answer extraction")}
        except Exception as exc:
            result = {**row, "response": None, "answer": None, "strict_format": False,
                      "error": f"{type(exc).__name__}: {exc}"}
        categorical_rows.append(result)
        _append(categorical_path, result)
        if (index + 1) % 36 == 0:
            print(f"[pilot_eval] categorical {index + 1}/{len(categorical)} saved", flush=True)
    anchors = build_observations(InstrumentValidationSpec(version="generated-stance-v3", checks=["comprehension"]))
    anchor_rows = []
    for row in anchors:
        presentation = categorical_presentation(row.model_dump(), spec.categorical_prompt_style)
        reply = (await asyncio.to_thread(model.generate, [presentation["prompt"]], temperature=0))[0]
        answer, extraction = extract(reply, row.options)
        anchor_rows.append({**presentation, "response": reply, "answer": answer,
                            "answer_extraction": extraction, "strict_format": parse_answer(reply, row.options) is not None,
                            "generation_metadata": getattr(model, "last_generation_metadata", None)})
    anchor_path = write_rows(anchor_rows, results / "anchor_observations.jsonl")
    metrics = {"version": spec.version, "model": spec.model,
               "pretrained": job.models.models[spec.model].pretrained, "adapter": None,
               "decoding": {"temperature": 0, "seed": spec.seed, "thinking": False,
                            "max_new_tokens": spec.max_new_tokens},
               "bank_run_id": spec.bank_run_id, "manifest": manifest,
               "answer_extraction_version": spec.answer_extraction,
               "categorical_prompt_style": spec.categorical_prompt_style,
               "administered_categorical_sha": fingerprint(categorical),
               "presentation_count": len(binary) + len(categorical) + len(anchors),
               "binary": summarize(binary, binary_rows, "binary"),
               "categorical": summarize(categorical, categorical_rows, "categorical", response_diagnostics=leading),
               "anchors": {"n_expected": len(anchors), "n_correct": sum(r["answer"] == r["expected"] for r in anchor_rows),
                           "n_extracted": sum(r["answer"] is not None for r in anchor_rows)},
               "scorer_controls": scorer_controls("generated-stance-v3"),
               "backend_agreement": agreement_status,
               "exploratory_backend_mismatch_allowed": spec.allow_exploratory_backend_mismatch,
               "interpretation": "BASE exploratory pilot; semantic references provisional; no SFT or forgetting result."}
    summary_path = results / "pilot_summary.json"
    if leading:
        metrics["extraction_controls"] = extraction_controls(spec.answer_extraction)
    summary_path.write_text(json.dumps(metrics, indent=2) + "\n")
    reports = write_pilot_report(metrics, spec.targets, results)
    if (results / "backend_agreement.json").exists():
        reports.append(results / "backend_agreement.json")
    return _save_summary(job, context, metrics, [binary_path, categorical_path, anchor_path, administered_path, summary_path, *reports])


async def run_reextract(job: JobConfig) -> RunResult:
    spec = job.pilot_bench
    if not spec.answer_extraction.startswith("leading-choice-") or not spec.source_evaluation_run_id:
        raise ValueError("re-extraction requires a leading-choice parser and a source evaluation")
    extract = extract_leading_choice_v2 if spec.answer_extraction == "leading-choice-v2" else extract_leading_choice
    source = ROOT / "data/results" / job.experiment.id / spec.source_evaluation_run_id
    previous = json.loads((source / "pilot_summary.json").read_text())
    bank = ROOT / "data/generated" / job.experiment.id / spec.bank_run_id
    manifest = json.loads((bank / "bank_manifest.json").read_text())
    if previous["manifest"] != manifest:
        raise ValueError("source evaluation used a different frozen bank")
    if fingerprint([t.model_dump() for t in spec.targets]) != manifest["targets_sha"]:
        raise ValueError("target definitions differ from the source")
    _, directory = _paths(job)
    if directory.exists() and (directory / "pilot_summary.json").exists():
        raise FileExistsError("use a new re-extraction run ID")
    directory.mkdir(parents=True, exist_ok=True)
    write_resolved_config(job, directory)
    expected_binary = load_rows(bank / "binary_bank.jsonl")
    expected_categorical = load_rows(source / "categorical_bank.jsonl") if (source / "categorical_bank.jsonl").exists() else load_rows(bank / "categorical_bank.jsonl")
    def reextract(row):
        result = dict(row)
        # Never convert a runtime/provider error into a measurement.
        if row.get("response") is not None and row.get("error") in (None, "unavailable answer extraction", "invalid answer format", "conflicting answer declarations"):
            answer, mode = extract(row["response"], row["options"])
            first_line = row["response"].strip().splitlines()[0] if row["response"].strip() else ""
            result.update(answer=answer, answer_extraction=mode,
                strict_format=parse_answer(row["response"], row["options"]) is not None,
                requested_format_compliant=(parse_answer(first_line, row["options"]) is not None
                    if previous.get("categorical_prompt_style") == "answer_first" else parse_answer(row["response"], row["options"]) is not None),
                complete_choice=extract_answer(row["response"], row["options"])[0] is not None,
                error=None if answer is not None else ("conflicting answer declarations" if mode == "conflict" else "unavailable answer extraction"))
        return result
    binary = load_rows(source / "binary_observations.jsonl")
    categorical = [reextract(r) for r in load_rows(source / "categorical_observations.jsonl")]
    anchors = [reextract(r) for r in load_rows(source / "anchor_observations.jsonl")]
    paths = [write_rows(binary, directory / "binary_observations.jsonl"),
             write_rows(categorical, directory / "categorical_observations.jsonl"),
             write_rows(anchors, directory / "anchor_observations.jsonl"),
             write_rows(expected_categorical, directory / "categorical_bank.jsonl")]
    metrics = {**previous, "answer_extraction_version": spec.answer_extraction,
        "source_evaluation_run_id": spec.source_evaluation_run_id, "executed_model_calls": 0,
        "source_observations_sha": fingerprint(load_rows(source / "categorical_observations.jsonl")),
        "categorical": summarize(expected_categorical, categorical, "categorical", response_diagnostics=True),
        "binary": summarize(expected_binary, binary, "binary"),
        "extraction_controls": extraction_controls(spec.answer_extraction),
        "anchors": {"n_expected": len(anchors), "n_correct": sum(r["answer"] == r["expected"] for r in anchors),
                    "n_extracted": sum(r["answer"] is not None for r in anchors)}}
    summary_path = directory / "pilot_summary.json"
    summary_path.write_text(json.dumps(metrics, indent=2) + "\n")
    paths.extend([summary_path, *write_pilot_report(metrics, spec.targets, directory)])
    return _save_summary(job, RunContext(), metrics, paths)


async def run_tune(job: JobConfig) -> RunResult:
    """Small format study; selection never uses ethical endorsement or unresolved rates."""
    spec = job.pilot_bench
    extract = extract_leading_choice_v2 if spec.answer_extraction == "leading-choice-v2" else extract_leading_choice
    bank = ROOT / "data/generated" / job.experiment.id / spec.bank_run_id
    candidates = load_rows(bank / "categorical_bank.jsonl")
    topics = [r for r in candidates if r["wording_id"] == "w0" and r["belief_id"] in spec.tuning_belief_ids]
    if {r["belief_id"] for r in topics} != set(spec.tuning_belief_ids):
        raise ValueError("missing tuning target")
    anchors = [r.model_dump() for r in build_observations(InstrumentValidationSpec(
        version="generated-stance-v3", checks=["comprehension"]))]
    _, directory = _paths(job)
    path = directory / "tuning_observations.jsonl"
    if path.exists():
        raise FileExistsError("use a new tuning run ID")
    directory.mkdir(parents=True, exist_ok=True)
    write_resolved_config(job, directory)
    path.touch()
    rule = "maximize anchor correct count, then minimum topic-family extraction coverage, then exact-letter compliance; ties prefer earlier configured style"
    design = {"rule": rule, "styles": spec.tuning_prompt_styles, "belief_ids": spec.tuning_belief_ids,
              "topic_bank_sha": fingerprint(topics), "anchors_sha": fingerprint(anchors),
              "note": "No ethical answer category, stance strength, or unresolved rate enters selection."}
    design_path = directory / "tuning_design.json"
    design_path.write_text(json.dumps(design, indent=2) + "\n")
    source_rows = None
    if spec.source_evaluation_run_id:
        source_dir = ROOT / "data/results" / job.experiment.id / spec.source_evaluation_run_id
        source_rows = load_rows(source_dir / "tuning_observations.jsonl")
        source_design = json.loads((source_dir / "tuning_design.json").read_text())
        if source_design != design:
            raise ValueError("tuning replay design differs from original")
    model = None if source_rows is not None else local_model(spec.model, job.models, max_new_tokens=spec.max_new_tokens, seed=spec.seed, enable_thinking=False)
    context = RunContext()
    results = {}
    all_rows = []
    for style in spec.tuning_prompt_styles:
        observed = []
        replay = [r for r in source_rows if r["tuning_style"] == style] if source_rows is not None else None
        if replay is not None and len(replay) != len(topics) + len(anchors):
            raise ValueError("incomplete tuning replay grid")
        for index, base in enumerate([*topics, *anchors]):
            row = categorical_presentation(base, style)
            if replay is not None:
                if replay[index]["prompt_sha"] != row["prompt_sha"] or replay[index]["options"] != row["options"]:
                    raise ValueError("tuning replay does not match frozen prompts")
                reply = replay[index]["response"]
            else:
                reply = (await asyncio.to_thread(model.generate, [row["prompt"]], temperature=0))[0]
            answer, extraction = extract(reply, row["options"])
            record = {**row, "tuning_style": style, "response": reply, "answer": answer,
                "answer_extraction": extraction, "strict_format": parse_answer(reply, row["options"]) is not None,
                "generation_metadata": replay[index].get("generation_metadata") if replay is not None else getattr(model, "last_generation_metadata", None)}
            observed.append(record)
            all_rows.append(record)
            _append(path, record)
            if (index + 1) % 18 == 0:
                print(f"[pilot_tune] {style} {index + 1}/{len(topics) + len(anchors)} saved", flush=True)
        topic_rows, anchor_rows = observed[:len(topics)], observed[len(topics):]
        families = {"ethical", "offtopic"}
        coverage = {family: sum(r["answer"] is not None for r in topic_rows if r["role"] == family)
                    / sum(r["role"] == family for r in topic_rows) for family in families}
        results[style] = {"n_topic": len(topic_rows), "n_anchor": len(anchor_rows),
            "n_anchor_correct": sum(r["answer"] == r["expected"] for r in anchor_rows),
            "n_extracted": sum(r["answer"] is not None for r in observed),
            "family_extraction_rates": coverage, "min_family_extraction": min(coverage.values()),
            "n_strict": sum(r["strict_format"] for r in observed),
            "n_length_limited": sum((r.get("generation_metadata") or {}).get("finish_reason") == "length" for r in observed)}
    selected = max(spec.tuning_prompt_styles, key=lambda style: (
        results[style]["n_anchor_correct"], results[style]["min_family_extraction"], results[style]["n_strict"],
        -spec.tuning_prompt_styles.index(style)))
    metrics = {"presentation_count": len(all_rows), "design": design,
               "styles": results, "selected_style": selected, "extraction_controls": extraction_controls(spec.answer_extraction),
               "model": spec.model, "pretrained": job.models.models[spec.model].pretrained,
               "decoding": {"temperature": 0, "seed": spec.seed, "thinking": False, "max_new_tokens": spec.max_new_tokens}}
    if source_rows is not None:
        metrics.update(source_evaluation_run_id=spec.source_evaluation_run_id,
                       source_observations_sha=fingerprint(source_rows), executed_model_calls=0)
    summary_path = directory / "tuning_summary.json"
    summary_path.write_text(json.dumps(metrics, indent=2) + "\n")
    return _save_summary(job, context, metrics, [path, design_path, summary_path])
