"""Pre-scale controls and direct canonical probes for six rubric reframings."""
import asyncio
import json
from pathlib import Path

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.config import load_job, write_resolved_config
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.inference.local import local_model
from belief_transfer.stages.measurements import prepare, administer


async def main():
    job = load_job(["+run=ethics_measurements_qwen_v3", "run_id=conviction_rubric_diagnosis_v1"])
    banks, controls, bundle = prepare(job)
    directory = Path(__file__).resolve().parents[1] / "data/results/ethical_pilot" / job.run_id
    if directory.exists():
        raise FileExistsError("use a fresh diagnosis run ID")
    directory.mkdir()
    write_resolved_config(job, directory)
    targets = {"animal_cosmetic_testing", "medical_data_with_consent", "modular_monolith_default"}
    rows = [r for r in controls["conviction"] if r["control_kind"] == "comprehension"]
    rows += [r for r in banks["conviction"] if r["belief_id"] in targets
             and r["wording_id"] == "w0" and r["polarity"] == "positive" and r["frame"] == "neutral"]
    assert len(rows) == 324
    design = {"n_presentations": len(rows), "bank_sha": fingerprint(bundle),
        "criterion": "Inspect known judgment-description errors, especially incomplete information with a lean. "
            "Repair only demonstrated semantic/interface defects under a new version. Never choose rubrics on ethical conviction rates.",
        "reference_status": "Agent-authored synthetic states, fixed before calls; human alignment deferred."}
    (directory/"diagnosis_design.json").write_text(json.dumps(design, indent=2)+"\n")
    model = local_model(job.pilot_bench.model, job.models, max_new_tokens=128, seed=42, enable_thinking=False)
    path = directory/"diagnostic_observations.jsonl"
    results = []
    for i, row in enumerate(rows):
        result = await administer(model, row)
        results.append(result)
        with path.open("a") as handle:
            handle.write(json.dumps(result, ensure_ascii=False)+"\n")
        if (i+1) % 36 == 0:
            print(f"rubric diagnosis {i+1}/{len(rows)}", flush=True)
    write_md(path)
    summary = {"executed_model_calls": len(results), "n_extracted": sum(r['answer'] is not None for r in results),
        "controls": {rid: {"n_expected": 36, "n_correct": sum(r.get('expected') == r['answer'] for r in results
             if r.get('rubric_id') == rid and 'expected' in r)} for rid in [f"r{i}" for i in range(6)]}}
    (directory/"diagnosis_summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
