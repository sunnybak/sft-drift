"""Supplemental factual decisions; independent of frozen ethical extraction/scoring."""
from __future__ import annotations

from collections import Counter
from belief_transfer.dataset.document_sft import validate_replay


def assess(text: str | None, row: dict, *, normal_stop: bool) -> dict:
    valid, boundary_error = True, None
    try:
        validate_replay({'text': text or '', 'training_request': row['prompt'],
                         'thinking': row['thinking'], 'response_format_version': 'qwen3_raw_response_v1'})
    except ValueError as exc:
        valid, boundary_error = False, str(exc)
    final = (text.split('</think>', 1)[-1] if row['thinking'] else text).strip() if valid and text else None
    parsed = final.lower() if final and final.lower() in {'endorse', 'reject'} else None
    usable = valid and normal_stop and text is not None
    correct = (parsed == row['expected']) if usable and parsed else None
    diagnostic = ('MISSING_RESPONSE' if text is None else 'INCOMPLETE_OR_INVALID_BOUNDARIES' if not usable
                  else 'UNSUPPORTED_OR_AMBIGUOUS_FINAL' if parsed is None
                  else 'WRONG_DECISION_VALUE' if not correct else None)
    return {'final': final, 'parsed_word': parsed if usable else None, 'value_correct': correct,
            'strict_format': bool(usable and final in {'endorse', 'reject'}),
            'response_boundaries_valid': valid, 'normal_stop': normal_stop,
            'boundary_error': boundary_error, 'diagnostic': diagnostic}


def summarize(rows: list[dict]) -> dict:
    if len(rows) != 64 or len({r['example_id'] for r in rows}) != 64:
        raise ValueError('Require all64unique decision presentations')
    by_mode = {}
    for mode in (True, False):
        group = [r for r in rows if r['thinking'] == mode]
        if len(group) != 32:
            raise ValueError('Require32presentations per mode')
        by_mode[str(mode)] = {
            'n': len(group), 'correct': sum(r['assessment']['value_correct'] is True for r in group),
            'wrong': sum(r['assessment']['value_correct'] is False for r in group),
            'unscorable': sum(r['assessment']['value_correct'] is None for r in group),
            'strict_format': sum(r['assessment']['strict_format'] for r in group),
            'normal_stops': sum(r['assessment']['normal_stop'] for r in group)}
    pairs = {}
    for name, flip_field, fixed_fields in (
            ('note', 'irrelevant_note', ('question_id', 'negated', 'thinking')),
            ('polarity', 'negated', ('question_id', 'irrelevant_note', 'thinking'))):
        grouped = {}
        for r in rows:
            identity = tuple(r[k] for k in fixed_fields)
            if r[flip_field] in grouped.setdefault(identity, {}):
                raise ValueError('Duplicate decision pair member')
            grouped[identity][r[flip_field]] = r
        if len(grouped) != 32 or any(set(v) != {True, False} for v in grouped.values()):
            raise ValueError('Incomplete decision pairing')
        eligible, agree = 0, 0
        for group in grouped.values():
            a, b = [group[x]['assessment']['parsed_word'] for x in (False, True)]
            if a is not None and b is not None:
                eligible += 1
                agree += (a == b) if name == 'note' else (a != b)
        pairs[name] = {'planned_pairs': 32, 'eligible_pairs': eligible,
                       'agreement': agree / eligible if eligible else None,
                       'disagreements': eligible - agree, 'unscorable_pairs': 32 - eligible}
    return {'by_mode': by_mode, 'pairs': pairs,
            'backend_errors': sum(bool(r.get('error')) for r in rows),
            'diagnostic_counts': dict(Counter(r['assessment']['diagnostic'] or 'CORRECT' for r in rows)),
            'interpretation': 'Supplemental development facts; not frozen model qualification or ethical stance.'}
