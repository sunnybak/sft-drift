"""Separate all-model Markdown-aware assessment; original measurements stay intact."""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from belief_transfer.evals.neutral_decision_value_v3 import assess_value, VERSION
from prepare_replay_interface_rca import RESULTS, MODELS, CELLS
from prepare_replay_weight_ablation import read, rows, sha, write_json, write_rows
from analyze_replay_interface_rca import describe


def main() -> None:
    review = read(RESULTS / 'agent_review_summary_v1.json')
    annotations = rows(RESULTS / 'agent_review_v1.jsonl')
    if (not review['full_new_flag_response_review_complete']
            or review['review_sha256'] != sha(RESULTS / 'agent_review_v1.jsonl')
            or review['queue_sha256'] != sha(RESULTS / 'new_failure_review_queue_v1.jsonl')):
        raise ValueError('Full response review missing/changed')
    output = RESULTS / 'value_v3_scores.jsonl'
    summary = RESULTS / 'value_v3_summary.json'
    if output.exists() or summary.exists():
        raise FileExistsError('No assessment overwrite')
    manual = {(r['model'],r['cell'],r['example_id']): r for r in annotations}
    changed, scored, conditions, sources = [], [], {}, {}
    for model in MODELS:
        for cell in (*CELLS,'held_eval'):
            path = RESULTS / f'{model}_{cell}_values.jsonl'
            data = rows(path); updated = []; sources[str(path)] = sha(path)
            for r in data:
                new = assess_value(r['response'],r,normal_stop=r['native_assessment']['normal_stop'])
                identity = model,cell,r['example_id']
                annotation = manual.get(identity)
                if annotation and (annotation['response_sha256'] != r['response_sha256'] or new['parsed_word'] != annotation['manual_choice']):
                    raise ValueError('New parser disagrees with full-response manual review')
                if new['parsed_word'] != r['assessment']['parsed_word']:
                    if not annotation or not annotation['disagreement_with_value_v2']:
                        raise ValueError('Unreviewed semantic assessment change')
                    changed.append({'model':model,'cell':cell,'example_id':r['example_id'],'response_sha256':r['response_sha256'],
                                    'before_choice':r['assessment']['parsed_word'],'after_choice':new['parsed_word']})
                if new['strict_format'] != r['native_assessment']['strict_format']:
                    raise ValueError('Native strict format changed')
                scored.append({'model':model,'cell':cell,'example_id':r['example_id'],'thinking':r['thinking'],
                    'response_sha256':r['response_sha256'],'assessment':new})
                updated.append(r | {'assessment':new})
            conditions[f'{model}/{cell}'] = describe(updated)
    if len(changed) != review['disagreements_with_value_v2'] or len(scored) != 768:
        raise ValueError('Incomplete grid or unresolved manual disagreements')
    write_rows(output,scored)
    write_json(summary,{'assessment_version':VERSION,'records':len(scored),'conditions':conditions,
        'semantic_changes':changed,'manual_review_disagreements_remaining':0,'source_sha256':sources,
        'review_sha256':sha(RESULTS/'agent_review_v1.jsonl'),'script_sha256':sha(Path(__file__)),
        'parser_sha256':sha(Path('src/belief_transfer/evals/neutral_decision_value_v3.py')),
        'interpretation':'Post-hoc format correction applied uniformly to all12conditions; source/native/value-v2 scores unchanged. Only reviewed explicit Markdown choice wrappers corrected. Diagnostic only; no historic gate cleared or ethical scorer changed.'})
    print(f'{VERSION}: {len(scored)}records; {len(changed)}reviewed semantic corrections; no remaining manual disagreement.')


if __name__ == '__main__':
    main()
