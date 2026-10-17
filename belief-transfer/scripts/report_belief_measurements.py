"""Reconstruct measured summaries from raw rows before regenerating derived views."""
import json
import hashlib
import sys
import zipfile
from pathlib import Path

from belief_transfer.analysis.measurement_report import write_measurement_report
from belief_transfer.analysis.stance_diagnostics import write_stance_diagnostics
from belief_transfer.config import load_job
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.evals.suite import load_rows
from belief_transfer.metrics.measurements import summarize_measurement, summarize_controls, qualify_conviction, summarize_stance_study
from belief_transfer.stages.measurements import prepare, measurement_bank_fingerprint
from belief_transfer.validation.measurements import EXTRACTOR_VERSION, extract_response, format_compliant, measurement_response_text

job = load_job(sys.argv[1:] or ["+run=ethics_100_stance_qwen_v2"])
directory = Path(__file__).resolve().parents[1] / "data/results" / job.experiment.id / job.run_id
summary = json.loads((directory/"measurement_summary.json").read_text())
banks, controls, bundle = prepare(job)
assert fingerprint(bundle) == summary["bank_sha"], "measurement bundle changed"
if "measurement_bank_sha" in summary:
    assert measurement_bank_fingerprint(bundle) == summary["measurement_bank_sha"], "administered items changed"
assert EXTRACTOR_VERSION == summary["extractor_version"], "use the recorded extractor version"
def observations(path):
    rows = load_rows(path)
    for row in rows:
        if row.get("response") is not None and row.get("error") in (None, "unavailable answer extraction"):
            text = measurement_response_text(row)
            answer, mode = extract_response(text, row)
            assert answer == row["answer"] and mode == row["answer_extraction"], "saved extraction differs from raw reply"
            assert format_compliant(text, row) == row["strict_format"]
    return rows

verified_observations = {}
for name, bank in banks.items():
    assert bank == load_rows(directory/f"{name}_bank.jsonl"), "administered bank changed"
    assert controls[name] == load_rows(directory/f"{name}_control_bank.jsonl"), "control bank changed"
    verified_observations[name] = observations(directory/f"{name}_observations.jsonl")
    assert summarize_measurement(bank, verified_observations[name]) == summary["measurements"][name]
    assert summarize_controls(controls[name], observations(directory/f"{name}_controls.jsonl")) == summary["meta_eval"]["model_controls"][name]
if 'conviction_qualification' in summary['meta_eval']:
    assert qualify_conviction(summary['measurements']['conviction'], controls['conviction'],
        observations(directory/'conviction_controls.jsonl'), job.pilot_bench.conviction_meta.model_dump()) == summary['meta_eval']['conviction_qualification']
if 'stance_operational_qualification' in summary['meta_eval']:
    check = summarize_stance_study(controls['stance'] + banks['stance'],
        observations(directory/'stance_controls.jsonl') + observations(directory/'stance_observations.jsonl'),
        bundle['stance_validation']['thresholds'], qualify_natural_consistency=False)
    assert {'validation': bundle['stance_validation'], 'controls': check['controls'],
        'passed': check['passed'], 'qualification_basis': check['qualification_basis']} == summary['meta_eval']['stance_operational_qualification']
paths = write_measurement_report(summary, job.pilot_bench.targets, directory, rubrics=job.pilot_bench.conviction_rubrics)
if set(banks) == {"stance"}:
    paths.extend(write_stance_diagnostics(load_rows(directory/'belief_measurements.jsonl'),
                                         banks['stance'], verified_observations['stance'], directory))
    with (directory/'measurement_report.md').open('a') as report:
        report.write('\n\n## Additional interpretation views\n\n'
                     '[Definitions, reading guide and all comparison plots](stance_diagnostics_report.md). '
                     'The per-belief answer grid is in `stance-answer-grid.html`; every paired choice is '
                     'also retained in `stance_diagnostics.jsonl`.\n\n'
                     '![Consistency within ethical families](stance_family_consistency.png)\n\n'
                     '![Coherent choices versus contradictions](stance_contradiction_patterns.png)\n')
    # Preserve the renderer added after the measurement-time implementation freeze.
    project = Path(__file__).resolve().parents[1]
    source_names = ['scripts/report_belief_measurements.py',
                    'src/belief_transfer/analysis/stance_diagnostics.py',
                    'src/belief_transfer/analysis/stance_explorer.html',
                    'tests/test_stance_diagnostics.py']
    source_zip = directory/'stance_diagnostics_source.zip'
    with zipfile.ZipFile(source_zip, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in source_names:
            archive.write(project/name, name)
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    provenance = directory/'stance_diagnostics_provenance.json'
    provenance.write_text(json.dumps({
        'version': 'stance-interpretation-v1', 'run_id': job.run_id,
        'measurement_bank_sha': summary.get('measurement_bank_sha'),
        'source_sha256': {name: sha(project/name) for name in source_names},
        'source_archive_sha256': sha(source_zip),
        'inputs_sha256': {name: sha(directory/name) for name in
                          ['measurement_summary.json', 'belief_measurements.jsonl',
                           'stance_bank.jsonl', 'stance_observations.jsonl']},
        'derived_views_sha256': {p.name: sha(p) for p in paths},
        'measurement_implementation_freeze': 'implementation_provenance.json',
        'interpretation': 'Derived views added after measurement; original authority files and implementation freeze remain unchanged.',
    }, indent=2)+'\n')
    paths.extend([source_zip, provenance])
print(f"Reconstructed {', '.join(banks)} and model controls exactly; rendered {len(paths)} artifacts.")
