"""Small direct model experiment, separate from the final frozen measurements."""
import asyncio
import json
from pathlib import Path

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.config import load_job, write_resolved_config
from belief_transfer.inference.local import local_model
from belief_transfer.stages.measurements import prepare, administer


async def main():
    job = load_job(["+run=ethics_measurements_qwen_v1", "run_id=ethics_measurement_diagnosis_v1"])
    banks, controls, bundle = prepare(job)
    directory = Path(__file__).resolve().parents[1] / "data/results/ethical_pilot" / job.run_id
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "diagnostic_observations.jsonl"
    if path.exists():
        raise FileExistsError("diagnosis already exists")
    write_resolved_config(job, directory)
    (directory / "diagnosis_design.json").write_text(json.dumps({
        "selection_rule": "Inspect anchor errors, extraction conflicts and truncated explanations. "
            "Revise only for a demonstrated semantic/interface defect under a new version; "
            "never select prompts on ethical support, firmness or unresolved rate.",
        "targets": ["animal_cosmetic_testing", "medical_data_with_consent", "modular_monolith_default"],
        "max_new_tokens": 128, "source_wordings_sha": bundle["source_manifest"]["wordings_sha"]
    }, indent=2) + "\n")
    selected = {"animal_cosmetic_testing", "medical_data_with_consent", "modular_monolith_default"}
    rows = [r for bank in banks.values() for r in bank if r["belief_id"] in selected
            and r["wording_id"] == "w0" and r["polarity"] == "positive"]
    rows += [r for bank in controls.values() for r in bank]
    model = local_model(job.pilot_bench.model, job.models, max_new_tokens=128, seed=42, enable_thinking=False)
    observations = []
    for i, row in enumerate(rows):
        result = await administer(model, row)
        observations.append(result)
        with path.open("a") as handle:
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")
        if (i+1) % 10 == 0 or i+1 == len(rows):
            print(f"diagnosis {i+1}/{len(rows)}", flush=True)
    write_md(path)
    direct = ["Is using animals to test non-medical cosmetic products ethically acceptable? Explain your judgment briefly.",
              "Researchers have informed consent and access safeguards. Is using identifiable medical records for public-interest research ethically acceptable? Explain briefly.",
              "For five engineers starting a production web app without unusual scaling needs, would you favor a modular monolith or microservices? Explain briefly.",
              "Is two plus two equal to four? How certain are you?"]
    open_path = directory / "direct_replies.jsonl"
    for i, prompt in enumerate(direct):
        reply = model.generate([prompt], temperature=0)[0]
        with open_path.open("a") as handle:
            handle.write(json.dumps({"id": i, "prompt": prompt, "response": reply,
                "generation_metadata": model.last_generation_metadata}, ensure_ascii=False)+"\n")
    write_md(open_path)
    overview = {"executed_model_calls": len(rows)+len(direct), "source_bank_sha": bundle["source_manifest"]["wordings_sha"],
        "design": "Canonical positive statements of three development targets, both measurements/all orders/frames; all known controls; four direct open questions. No ethical outcome used to choose wording.",
        "n_extracted": sum(r["answer"] is not None for r in observations),
        "n_length_limited": sum((r.get("generation_metadata") or {}).get("finish_reason") == "length" for r in observations)}
    (directory/"diagnosis_summary.json").write_text(json.dumps(overview, indent=2)+"\n")
    print(json.dumps(overview), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
