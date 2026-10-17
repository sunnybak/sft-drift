"""Replay this instrument's extraction and provenance from saved responses."""
from belief_transfer.evals.conviction_scale import (
    balanced_fields, extract_judgment, extract_scale, joint_completions,
    reflection_prompt,
)
from belief_transfer.evals.pilot import fingerprint
from belief_transfer.metrics.conviction_scale import summarize_joint_probabilities
from belief_transfer.schemas import ChoiceScores


def verify_scale_observation(row, manifest):
    """Raise on changed scores, dependent prompts, or likelihood reductions.

    This verifies the saved harness calculation, not the truth of a self-report.
    """
    final = row.get('response')
    if manifest['decoding'].get('thinking') is True:
        final = final.split('</think>')[1].strip() if final and final.count('</think>') == 1 else None
        if final != row.get('final_response'):
            raise ValueError('saved final response differs from raw reasoning boundary')
    answer, strict = extract_scale(final, row['candidate'])
    if row['candidate'] in ('balanced_named', 'verdict_named', 'agreement_named'):
        position, value, _ = balanced_fields(
            final, 'agreement' if row['candidate'] == 'agreement_named'
            else row['candidate'] == 'verdict_named',
        )
        coherent = None if value is None else ((value == 0) == (position in ('neither', 'no_lean')))
        if row.get('chosen_position') != position or row.get('judgment_coherent') != coherent:
            raise ValueError('structured judgment differs from raw response')
    if row['candidate'] == 'conditioned_named':
        judgment = row.get('judgment_response')
        position = extract_judgment(judgment) if judgment else row.get('expected_position')
        coherent = (None if answer is None or position is None else True
                    if manifest['study'].get('force_preliminary_binary') and judgment
                    else ((answer == 0) == (position == 'no_lean')))
        if coherent is False:
            answer = None
        if row.get('chosen_position') != position or row.get('judgment_coherent') != coherent:
            raise ValueError('reflection coherence differs from preceding judgment')
        prompt = reflection_prompt(row['prompt'], judgment) if judgment and position is not None else row['prompt']
        if row.get('administered_prompt') != prompt or row.get('administered_prompt_sha') != fingerprint(prompt):
            raise ValueError('reflection prompt differs from its actual preceding judgment')
    if (answer, strict) != (row.get('answer'), row.get('strict_format')):
        raise ValueError('saved extraction differs from raw response')
    if row.get('joint_choice_scores') is not None:
        scores = ChoiceScores.model_validate(row['joint_choice_scores'])
        if [s.choice for s in scores.scores] != joint_completions() or row['prompt'] not in scores.prompt:
            raise ValueError('likelihood prompt or exhaustive choice set changed')
        probabilities = scores.probabilities(per_token=False)
        if probabilities != row['joint_probabilities']:
            raise ValueError('likelihood probabilities differ from raw log probabilities')
        if summarize_joint_probabilities(probabilities) != row['likelihood_diagnostic']:
            raise ValueError('likelihood diagnostic differs from saved probabilities')
