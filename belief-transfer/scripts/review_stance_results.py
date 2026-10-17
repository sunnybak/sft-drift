"""Verify saved observations, then write alternative review views without touching old files.

Usage: python scripts/review_stance_results.py data/results/ethical_pilot/ethics_100_stance_qwen_v2
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from belief_transfer.analysis.stance_review import write_stance_review
from belief_transfer.metrics.measurements import summarize_measurement, summarize_controls
from belief_transfer.validation.measurements import EXTRACTOR_VERSION, extract_response, format_compliant, measurement_response_text


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory', type=Path)
    args = parser.parse_args()
    directory = args.run_directory.resolve()
    if (directory/'VOID.md').exists():
        raise ValueError('run is marked VOID')
    before = {p.name: sha(p) for p in directory.iterdir() if p.is_file()}
    freeze = json.loads((directory/'implementation_provenance.json').read_text())
    for name, digest in freeze['authority_files_sha256'].items():
        assert sha(directory/name) == digest, f'frozen authority changed: {name}'
    # The prior derived-view snapshot includes the full rich belief definitions.
    prior_views = directory/'stance_diagnostics_provenance.json'
    if prior_views.exists():
        expected = json.loads(prior_views.read_text())['inputs_sha256']['belief_measurements.jsonl']
        assert sha(directory/'belief_measurements.jsonl') == expected, 'saved definitions/scores changed'
    summary = json.loads((directory/'measurement_summary.json').read_text())
    assert set(summary['measurements']) == {'stance'}, 'review is for the active Stance-only bank'
    assert summary['extractor_version'] == EXTRACTOR_VERSION, 'use the recorded extractor version'
    bank = read_rows(directory/'stance_bank.jsonl')
    observations = read_rows(directory/'stance_observations.jsonl')
    control_bank = read_rows(directory/'stance_control_bank.jsonl')
    control_rows = read_rows(directory/'stance_controls.jsonl')
    for row in observations + control_rows:
        if row.get('response') is not None and row.get('error') in (None, 'unavailable answer extraction'):
            text = measurement_response_text(row)
            answer, mode = extract_response(text, row)
            assert (answer, mode) == (row['answer'], row['answer_extraction']), 'raw extraction changed'
            assert format_compliant(text, row) == row['strict_format'], 'format extraction changed'
    assert summarize_measurement(bank, observations) == summary['measurements']['stance'], 'raw scores differ'
    assert summarize_controls(control_bank, control_rows) == summary['meta_eval']['model_controls']['stance'], 'control scores differ'
    measurements = read_rows(directory/'belief_measurements.jsonl')
    assert len(measurements) == len(summary['measurements']['stance']), 'missing or duplicate belief rows'
    for row in measurements:
        assert row['measurements']['stance'] == summary['measurements']['stance'][row['belief_id']], 'rich scores differ'
        assert row['model'] == summary['model'] and row['adapter'] == summary['adapter'], 'model identity differs'
        assert row['decoding'] == summary['decoding'], 'decoding differs'
        assert row['measurement_bank_sha'] == summary['measurement_bank_sha'], 'bank identity differs'
    output = directory/'review_v2'
    review, paths = write_stance_review(measurements, output, model=summary['model'], adapter=summary['adapter'],
                                       temperature=summary['decoding']['temperature'])
    project = Path(__file__).resolve().parents[1]
    sources = ['scripts/review_stance_results.py', 'src/belief_transfer/metrics/stance_review.py',
               'src/belief_transfer/analysis/stance_review.py', 'src/belief_transfer/analysis/stance_diagnostics.py',
               'tests/test_stance_review.py']
    archive_path = output/'source.zip'
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in sources:
            archive.write(project/name, name)
    assert {p.name: sha(p) for p in directory.iterdir() if p.is_file()} == before, 'an original artifact changed'
    provenance = {'view_version': review['version'], 'source_run': directory.name,
                  'model': summary['model'], 'adapter': summary['adapter'],
                  'measurement_bank_sha': summary['measurement_bank_sha'],
                  'decoding': summary['decoding'],
                  'original_files_sha256': before,
                  'source_files_sha256': {name: sha(project/name) for name in sources},
                  'source_archive_sha256': sha(archive_path),
                  'new_views_sha256': {p.name: sha(p) for p in paths},
                  'interpretation': 'Presentation revision and explicitly defined composite; no new model calls or qualification gates. Original data, scores and plots unchanged.'}
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    print(f"Verified raw replies/scores/controls and preserved {len(before)} original files. "
          f"Wrote {len(paths)+2} new views/source artifacts to {output}.")
    print(f"Stance Agreement: {review['overall']['all']['stance_agreement']:.4f}; "
          f"all {len(review['beliefs'])} beliefs retained.")


if __name__ == '__main__':
    main()
