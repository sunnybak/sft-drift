"""Controlled response-instruction comparison; never select on ethical outcomes."""
import asyncio
import json
from pathlib import Path

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.config import load_job, write_resolved_config
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.inference.local import local_model
from belief_transfer.stages.measurements import prepare, administer
from belief_transfer.validation.measurements import extract_choice, strict_choice


async def main():
    job = load_job(["+run=ethics_measurements_qwen_v2", "run_id=ethics_measurement_format_v2"])
    banks, controls, bundle = prepare(job)
    directory = Path(__file__).resolve().parents[1] / "data/results/ethical_pilot" / job.run_id
    if directory.exists():
        raise FileExistsError("use a fresh format study ID")
    directory.mkdir()
    write_resolved_config(job, directory)
    source = directory.parent / "ethics_measurement_diagnosis_v1/diagnostic_observations.jsonl"
    raw = [json.loads(s) for s in source.read_text().splitlines()]
    selected = {r["presentation_id"] for r in raw}
    candidates = [r for b in controls.values() for r in b] + [r for b in banks.values() for r in b if r["presentation_id"] in selected]
    assert len(candidates) == len(raw) == 100
    design = {"criterion": "Choose concise only if all known controls remain correct and exact-letter compliance improves over original. No ethical stance, firmness or unresolved rates enter selection.",
              "source_observations_sha": fingerprint(raw), "candidate_sha": fingerprint(candidates),
              "n_candidates": len(candidates)}
    (directory/"format_design.json").write_text(json.dumps(design, indent=2)+"\n")
    model = local_model(job.pilot_bench.model, job.models, max_new_tokens=128, seed=42, enable_thinking=False)
    rows = []
    path = directory / "format_observations.jsonl"
    for i, row in enumerate(candidates):
        result = await administer(model, row)
        rows.append(result)
        with path.open("a") as handle:
            handle.write(json.dumps(result, ensure_ascii=False)+"\n")
        if (i+1) % 20 == 0:
            print(f"format {i+1}/{len(candidates)}", flush=True)
    write_md(path)
    original_strict = sum(strict_choice(r["response"] or "", r["options"]) is not None for r in raw)
    known = [r for r in rows if "expected" in r]
    original_known = [r for r in raw if "expected" in r]
    original_correct = sum(extract_choice(r["response"] or "", r["options"])[0] == r["expected"] for r in original_known)
    correct = sum(r["answer"] == r["expected"] for r in known)
    strict = sum(r["strict_format"] for r in rows)
    selected_style = "concise" if correct == len(known) == original_correct and strict > original_strict else "original"
    summary = {"original": {"n_expected": len(raw), "n_strict": original_strict, "n_controls_correct": original_correct},
        "concise": {"n_expected": len(rows), "n_strict": strict, "n_extracted": sum(r["answer"] is not None for r in rows), "n_controls_correct": correct},
        "n_controls_expected": len(known), "selected_style": selected_style, "executed_model_calls": len(rows)}
    (directory/"format_summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
