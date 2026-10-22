"""Opt-in terminal Markdown normalization; v1/v2 and ethical scoring stay frozen."""
from __future__ import annotations

import re

from belief_transfer.evals.neutral_decision_value import assess_value as assess_v2

VERSION = 'neutral-task-value-v3'
TERMINAL = re.compile(
    r'(?<![*_`])(?P<w>\*\*\*|\*\*|\*|___|__|_|`{1,3})'
    r'(?P<body>(?:Final[ \t]+(?:answer|response):[ \t]*)?(?:endorse|reject)[.!]?)'
    r'(?P=w)(?![*_`])[.!]?\s*$', re.I)


def assess_value(text: str | None, row: dict, *, normal_stop: bool) -> dict:
    original = assess_v2(text, row, normal_stop=normal_stop)
    result = original | {'assessment_version': VERSION, 'terminal_markdown_normalized': False}
    if text is None or not normal_stop or not original['response_boundaries_valid']:
        return result
    match = TERMINAL.search(text)
    if not match:
        return result
    # Only unwrap an explicit terminal choice/footer. Preserve preceding words so
    # v2 still rejects "not reject" or "endorse or reject" as ambiguous choices.
    normalized = text[:match.start()] + match['body']
    assessed = assess_v2(normalized, row, normal_stop=normal_stop)
    return assessed | {'assessment_version': VERSION, 'terminal_markdown_normalized': True,
        'normalized_final': assessed['final'], 'final': original['final'],
        'strict_format': original['strict_format'], 'native_v1_assessment': original['native_v1_assessment']}
