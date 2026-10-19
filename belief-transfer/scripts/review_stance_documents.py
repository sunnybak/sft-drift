#!/usr/bin/env python3
"""Derive a review report from saved candidates and complete current-agent annotations.

No model calls or candidate edits. Run only after generation and full reading/annotation.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
from statistics import median

PROJECT = Path(__file__).resolve().parents[1]


def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def derive(run_id: str, compare_id: str | None = None):
    root = PROJECT/'data/generated/ethical_stance_sft'/run_id
    out = PROJECT/'data/results/ethical_stance_sft'/run_id
    documents = rows(root/'documents.jsonl')
    drafts = {r['document_id']: r for r in rows(root/'drafts.jsonl')}
    notes = {r['document_id']: r for r in rows(out/'agent_review.jsonl')}
    judges = {r['document_id']: r['assessment'] for r in rows(root/'assessments.jsonl')}
    manifest = json.loads((out/'pilot_manifest.json').read_text())
    assert manifest['status'] == 'completed'
    assert set(notes) == {r['document_id'] for r in documents}, 'Complete current-agent review required'
    assert all(notes[r['document_id']]['text_sha256'] == r['diagnostics']['sha256'] for r in documents)
    minimum = 400
    maximum = 600
    tokens = [r['diagnostics']['tokens'] for r in documents]
    groups = {}
    for r in documents:
        groups.setdefault((r['subject_id'], r['position']), []).append(r)
    overlaps = []
    for group in groups.values():
        for a, b in itertools.combinations(group, 2):
            def grams(text):
                words = text.lower().split()
                return {tuple(words[i:i+5]) for i in range(len(words)-4)}
            ga, gb = grams(a['text']), grams(b['text'])
            overlaps.append(len(ga & gb)/len(ga | gb) if ga | gb else 0)
    comparison = []
    for r in sorted(documents, key=lambda r: r['document_id']):
        identifier = r['document_id']
        automatic = [k for k, v in judges[identifier].items() if v is False]
        comparison.append({'document_id': identifier, 'automated_flags': automatic,
            'agent_categories': notes[identifier]['categories'], 'agent_note': notes[identifier]['note'],
            'length_in_range': r['diagnostics']['length_in_range'],
            'agent_flag_automated_all_pass': bool(notes[identifier]['categories']) and not automatic})
    for name, data in [('review_comparison', comparison)]:
        (out/(name+'.jsonl')).write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in data))
        (out/(name+'.md')).write_text('# '+name+'\n\n'+'\n\n'.join(
            '```json\n'+json.dumps(r, indent=2, ensure_ascii=False)+'\n```' for r in data)+'\n')
    background = rows(root/'background.jsonl')
    mixtures = rows(root/'mixtures.jsonl')
    calibration = rows(root/'reviewer_calibration.jsonl')
    summary = {'run_id': run_id, 'documents': len(documents),
        'drafts_in_range': sum(minimum <= r['tokens'] <= maximum for r in drafts.values()),
        'revisions_in_range': sum(r['diagnostics']['length_in_range'] for r in documents),
        'length_improvements': sum(not minimum <= drafts[r['document_id']]['tokens'] <= maximum
                                  and r['diagnostics']['length_in_range'] for r in documents),
        'length_regressions': sum(minimum <= drafts[r['document_id']]['tokens'] <= maximum
                                 and not r['diagnostics']['length_in_range'] for r in documents),
        'token_min': min(tokens), 'token_max': max(tokens), 'token_mean': sum(tokens)/len(tokens),
        'synthetic_tokens': sum(tokens), 'background_tokens': sum(r['tokens'] for r in background),
        'exact_duplicate_documents': len(tokens)-len({r['diagnostics']['sha256'] for r in documents}),
        'agent_flagged_documents': sum(bool(r['categories']) for r in notes.values()),
        'agent_clear_positions': sum(r['clear_assigned_position'] for r in notes.values()),
        'automated_flagged_documents': sum(bool(r['automated_flags']) for r in comparison),
        'agent_flag_automated_all_pass': sum(r['agent_flag_automated_all_pass'] for r in comparison),
        'calibration_named_checks_matched': sum(r['matches_expected_check'] for r in calibration),
        'calibration_cases': len(calibration), 'fivegram_jaccard_median': median(overlaps),
        'fivegram_jaccard_max': max(overlaps), 'actual_cost_usd': manifest['actual_cost_usd'],
        'training_ready': False}
    (out/'review_summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    lines = [f'# Document pilot review — {run_id}', '',
        f"{len(documents)} complete revisions read and annotated by the implementing agent. "
        'These are provisional judgments, not independent human validation. No training ran.', '',
        f"Explicit assigned positions: {summary['agent_clear_positions']}/{len(documents)}. "
        f"Current-agent flags: {summary['agent_flagged_documents']}; same-model flags: "
        f"{summary['automated_flagged_documents']}. Neither count is calibrated accuracy.", '',
        f"Length: {summary['revisions_in_range']}/{len(documents)} within 400–600 Qwen tokens "
        f"(drafts {summary['drafts_in_range']}); range {min(tokens)}–{max(tokens)}, mean "
        f"{summary['token_mean']:.1f}. Revision moved {summary['length_improvements']} into range "
        f"and {summary['length_regressions']} out. All failures retained.", '',
        f"Synthetic text totals {sum(tokens):,} tokens. No exact duplicate texts: "
        f"{summary['exact_duplicate_documents']} duplicate surplus. Within-arm five-gram overlap "
        f"median {median(overlaps):.3f}, max {max(overlaps):.3f}; lexical uniqueness does not certify "
        'substantive variety. Read paired arguments and per-document notes for that judgment.', '',
        f"Reviewer calibration: {summary['calibration_named_checks_matched']}/{len(calibration)} "
        'named snippet checks match expected labels. These fixtures overlap rubric examples and '
        'are diagnostic, not held-out accuracy estimates. Other snippet check failures are unscored.', '',
        f"Agent-flagged documents receiving all six automated passes: "
        f"{summary['agent_flag_automated_all_pass']} (including any mechanical length failures). "
        'See review_comparison.md for both perspectives and exact notes.', '',
        '## Issues requiring attention', '']
    for r in sorted(notes.values(), key=lambda r: r['document_id']):
        if r['categories']:
            lines += [f"- `{r['document_id']}` — {', '.join(r['categories'])}: {r['note']}"]
    lines += ['', '## Mixture previews', '',
        '| Arm | Synthetic tokens | C4 tokens | C4 token share |', '| --- | ---: | ---: | ---: |']
    for r in mixtures:
        st, bt = r['synthetic_tokens_without_prefix'], r['background_tokens']
        lines.append(f"| {r['arm']} | {st} | {bt} | {100*bt/(st+bt):.1f}% |")
    lines += ['', 'Same six full pinned C4 documents per arm; 1:1 document counts. No cropping, '
        'stance filtering, token-dose matching or training-loss implementation. The small background '
        'pool remains a limitation for any later training design.', '',
        f"Actual API cost: ${manifest['actual_cost_usd']:.6f}; ceiling ${manifest['budget_ceiling']:.2f}; "
        f"uncertain-cost bound ${manifest['uncertain_cost_upper_bound']:.6f}. "
        'API prose is not deterministic; seeds only schedule content and select background.', '',
        'Canonical overlap is intentional. Other full normalized wording matches are listed '
        'below. The generator never received the frozen wording bank; matches do not establish '
        'copying, and this check cannot exclude near copies.', '']
    lines += [f"- `{r['document_id']}`: {r['diagnostics']['other_full_eval_wording_matches']}"
        for r in documents if r['diagnostics']['other_full_eval_wording_matches']]
    if compare_id:
        previous_root = PROJECT/'data/generated/ethical_stance_sft'/compare_id
        previous = rows(previous_root/'documents.jsonl')
        old = {r['document_id']: r for r in previous}
        common = [r for r in documents if r['document_id'] in old]
        lines += ['', '## Design-matched comparison', '',
            f"Comparison: {compare_id}; {len(common)} shared document slots. Plans and prose were "
            'regenerated, so differences combine prompt changes, planning changes and sampling. '
            'This is a descriptive comparison, not a causal or significance claim.', '',
            f"Length compliance on common slots: "
            f"{sum(old[r['document_id']]['diagnostics']['length_in_range'] for r in common)}/{len(common)} "
            f"previously; {sum(r['diagnostics']['length_in_range'] for r in common)}/{len(common)} now."]
        previous_background = rows(previous_root/'background.jsonl')
        assert [r['sha256'] for r in previous_background] == [r['sha256'] for r in background]
        lines += ['', 'Background text hashes match the comparison run exactly.']
    lines += ['', '[All paired revisions and original drafts](../../../generated/ethical_stance_sft/'
        +run_id+'/review.md) · [Per-document current-agent review](agent_review.md) · '
        '[Reviewer comparison](review_comparison.md) · [Revision examples](revision_examples.md)', '',
        'No accepted corpus or training readiness is inferred. Qualitative synthesis and next '
        'decisions are recorded in iteration_notes.md.']
    (out/'review_findings.md').write_text('\n'.join(lines)+'\n')
    # Show a length problem, a semantic problem, and a typical unflagged pair if available.
    ordered = sorted(documents, key=lambda r: (not bool(notes[r['document_id']]['categories']), r['document_id']))
    chosen = ordered[:2] + [r for r in ordered if not notes[r['document_id']]['categories']][:1]
    examples = ['# Draft → one revision', '']
    for r in chosen:
        d = drafts[r['document_id']]
        examples += [f"## {r['document_id']}", '',
            f"{d['tokens']} → {r['diagnostics']['tokens']} Qwen tokens.", '',
            notes[r['document_id']]['note'], '', '### Draft', '', d['text'], '',
            '### Critique', '', *['- '+s for s in r['critique']], '', '### Revision', '', r['text'], '']
    (out/'revision_examples.md').write_text('\n'.join(examples)+'\n')
    sources = [root/name for name in ['briefs.jsonl','form_plans.jsonl','ideas.jsonl','drafts.jsonl',
        'documents.jsonl','assessments.jsonl','background.jsonl','mixtures.jsonl','reviewer_calibration.jsonl']]
    sources += [out/'agent_review.jsonl', out/'pilot_manifest.json', Path(__file__).resolve()]
    (out/'review_sources.json').write_text(json.dumps({str(p.relative_to(PROJECT)):
        hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--compare-id')
    args = parser.parse_args()
    derive(args.run_id, args.compare_id)
