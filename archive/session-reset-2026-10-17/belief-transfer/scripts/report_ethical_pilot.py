"""Rebuild derived report/figure without model calls or changes to frozen banks.

Run from belief-transfer/: uv run python scripts/report_ethical_pilot.py
"""
import json
import yaml
import sys

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.analysis.pilot_report import write_pilot_report
from belief_transfer.analysis.report import ROOT
from belief_transfer.config import load_job
from belief_transfer.evals.pilot import build_banks, categorical_presentation
from belief_transfer.evals.suite import load_rows
from belief_transfer.metrics.pilot import summarize
from belief_transfer.schemas import PilotWording


def main():
    job = load_job(sys.argv[1:] or ["+run=ethics_pilot_qwen_v3"])
    directory = ROOT / "data/results" / job.experiment.id / job.run_id
    bank = ROOT / "data/generated" / job.experiment.id / job.pilot_bench.bank_run_id
    metrics = json.loads((directory / "pilot_summary.json").read_text())
    wordings = [PilotWording.model_validate(r) for r in load_rows(bank / "belief_wordings.jsonl")]
    binary, categorical = build_banks(job.pilot_bench, wordings)
    categorical = (load_rows(directory / "categorical_bank.jsonl") if (directory / "categorical_bank.jsonl").exists()
                   else [categorical_presentation(r, job.pilot_bench.categorical_prompt_style) for r in categorical])
    # Reconstruction must agree exactly before any derived report is overwritten.
    for mode, expected in (("binary", binary), ("categorical", categorical)):
        actual = summarize(expected, load_rows(directory / f"{mode}_observations.jsonl"), mode,
                           response_diagnostics=mode == "categorical" and str(metrics.get("answer_extraction_version", "")).startswith("leading-choice-"))
        if actual != metrics[mode]:
            raise ValueError(f"{mode} summary does not reconstruct from raw observations")
    reports = write_pilot_report(metrics, job.pilot_bench.targets, directory)
    for path in reports:
        if path.suffix == ".jsonl":
            write_md(path)
        print(path)
    # Extend only the artifact inventory; preserve the recorded invocation, metrics,
    # timing and cost rather than treating report rendering as another model run.
    stage_path = directory / f"{job.stage}.yaml"
    record = yaml.safe_load(stage_path.read_text())
    if record["metrics"] != metrics:
        raise ValueError("stage metrics differ from the immutable measurement summary")
    for path in [*reports, directory / "backend_agreement.json"]:
        if path.exists():
            relative = str(path.relative_to(ROOT))
            if relative not in record["artifacts"]:
                record["artifacts"].append(relative)
    stage_path.write_text(yaml.safe_dump(record, sort_keys=False))


if __name__ == "__main__":
    main()
