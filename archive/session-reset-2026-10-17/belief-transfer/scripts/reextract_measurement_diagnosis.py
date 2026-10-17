"""Replay saved direct-probe replies with the current extractor; no model calls."""
import json
from pathlib import Path

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.evals.measurements import build_measurement_controls
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.evals.suite import load_rows, write_rows
from belief_transfer.metrics.measurements import summarize_controls
from belief_transfer.validation.measurements import EXTRACTOR_VERSION, extract_choice, scorer_checks

root = Path(__file__).resolve().parents[1] / "data/results/ethical_pilot"
source = root / "ethics_measurement_diagnosis_v1"
directory = root / "ethics_measurement_diagnosis_reextract_v3"
if directory.exists():
    raise FileExistsError("use a fresh replay run ID")
directory.mkdir()
raw = load_rows(source/"diagnostic_observations.jsonl")
rows = []
for r in raw:
    updated = dict(r)
    if r.get("response") is not None and r.get("error") in (None, "unavailable answer extraction"):
        answer, mode = extract_choice(r["response"], r["options"])
        updated.update(answer=answer, answer_extraction=mode,
                       error=None if answer is not None else "unavailable answer extraction")
    rows.append(updated)
path = write_rows(rows, directory/"diagnostic_observations.jsonl")
write_md(path)
model_controls = {name: summarize_controls(bank, [r for r in rows
    if r["measurement"] == name and "control_kind" in r])
    for name, bank in build_measurement_controls(["stance", "conviction"]).items()}
summary = {"source_run_id": source.name, "source_observations_sha": fingerprint(raw),
    "extractor_version": EXTRACTOR_VERSION, "executed_model_calls": 0, "n_expected": len(raw),
    "n_extracted": sum(r["answer"] is not None for r in rows),
    "scorer_checks": scorer_checks(), "model_controls": model_controls}
(directory/"diagnosis_summary.json").write_text(json.dumps(summary, indent=2)+"\n")
print(json.dumps({k: v for k, v in summary.items() if k != "scorer_checks"}, indent=2))
