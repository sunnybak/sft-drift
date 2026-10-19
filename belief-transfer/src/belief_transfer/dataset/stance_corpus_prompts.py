"""Corpus prompt v3: symmetric plans and condition-by-condition provisional review."""
from __future__ import annotations

import json

from belief_transfer.dataset import stance_documents as old
from belief_transfer.dataset import stance_document_prompts_v2 as v2
from belief_transfer.generation.llm import Tool

VERSION = 'stance-corpus-v3'
RULES = v2.RULES + '''
Visible prose must never mention the brief, assignment, protected conditions or outline.
Do not infer that unspecified pressure is absent or present. No material risk in the
specified assessment is not zero risk. Public benefit does not imply a substantial or
guaranteed benefit, nor that obtaining consent is infeasible. A narrowly scoped exception
does not establish a general rule. Repeat a condition only when it changes the argument.
An objection must challenge YOUR assigned position. Use the opposite side's reason
from the shared plan, acknowledge its force, and explain why your conclusion still wins.
For any off-topic training control, discuss the stated aesthetic preference alone.
Never introduce moral duties, fairness, harm, safety, access or social consequences.
'''


def idea_tool(count: int) -> Tool:
    return Tool('plan_ideas', 'Symmetric ideas under identical premises.', old.object_schema({
        'ideas': {'type': 'array', 'minItems': count, 'maxItems': count,
                  'items': old.object_schema({'focus': old.TEXT, 'positive_reason': old.TEXT,
                                             'negative_reason': old.TEXT, 'development': old.TEXT})}}))


def ideas_prompt(subject: dict, form: str, plan: dict, count: int, previous: list[str]) -> str:
    return f'''Plan exactly {count} ideas for {form} from this fixed scope:
{v2.brief(subject)}
FORM: {json.dumps(plan)}
Previously used focuses (avoid substantive repetition): {json.dumps(previous)}
Each idea names one reason favoring the canonical claim and one reason favoring its
exact negation, plus a distinct way to develop their tension. Neither reason wins in
the plan. Both final positions use this identical idea. Vary evaluative priorities and
argument structure, not facts, scenarios or synonyms. Do not assign a universal
"strongest objection": the objection changes when the assigned position changes.
{RULES}
Return plan_ideas.'''


def document_prompt(subject: dict, form: str, idea: dict, position: str, lo: int, hi: int) -> str:
    conclusion = subject['claim'] if position == 'positive' else subject['negation']
    own = idea[f'{position}_reason']
    other = idea['negative_reason' if position == 'positive' else 'positive_reason']
    return f'''Write a self-contained {form}, {lo}–{hi} Qwen3 tokens, targeting {(lo+hi)//2}.
SCOPED PREMISES: {v2.brief(subject)}
SHARED PLAN: {json.dumps(idea)}
YOUR CONCLUSION: {conclusion}
Develop this supporting reason: {own}
Address this opposing reason as an objection: {other}
{RULES}
Return submit_document.'''


def revision_prompt(subject: dict, form: str, idea: dict, position: str, draft: str,
                    tokens: int, lo: int, hi: int) -> str:
    return (v2.revision_prompt(subject, form, idea, position, draft, tokens, lo, hi)
            + '\n' + RULES + '\n' + v2.length_anchor(draft, tokens, lo, hi))


def review_tool(subject: dict) -> Tool:
    conditions = subject['conditions']
    return Tool('assess_document', 'Evidence for each scoped condition and other defects.',
                old.object_schema({
                    **{k: {'type': 'boolean'} for k in old.REVIEW_KEYS},
                    'condition_checks': old.object_schema({f'c{i}': old.object_schema({
                        'preserved': {'type': 'boolean'}, 'evidence': old.TEXT})
                        for i in range(len(conditions))}),
                    'unsupported_premises': old.STRINGS, 'rationale': old.TEXT,
                    'evidence': old.STRINGS}))


def review_prompt(subject: dict, form: str, position: str, text: str) -> str:
    conditions = dict(enumerate(subject['conditions']))
    return (v2.review_prompt(subject, form, position, text) + '\n' + RULES + f'''
For condition_checks use this numbered checklist: {json.dumps(conditions)}
For EVERY condition, quote the passage preserving it or identify the omission/change.
If a condition is immaterial and unmentioned, say why; do not demand excluded cases
appear in the prose. List each added empirical premise with its exact quotation in
unsupported_premises. Normative evaluations and ordinary implications are allowed.
These checks are advisory; no overall training-ready judgment is requested.''')
