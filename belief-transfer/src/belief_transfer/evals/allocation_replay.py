"""Reconstruct all confidence readouts and dependent prompts from their raw replies."""
from belief_transfer.evals.chosen_confidence import confidence_prompt,extract_analytical_judgment,extract_chosen_confidence
from belief_transfer.evals.claim_credence import extract_claim_credence,extract_favored_claim
from belief_transfer.evals.conviction_allocation import extract_allocation
from belief_transfer.evals.pilot import fingerprint


def _final(response,thinking):
    if not thinking:return response
    return response.split('</think>')[1].strip() if response and response.count('</think>')==1 else None


def verify_allocation_observation(row,manifest):
    thinking=manifest['decoding']['thinking'];readout=manifest['study'].get('readout')
    final=_final(row.get('response'),thinking)
    if thinking and final!=row.get('final_response'):raise ValueError('changed final reasoning boundary')
    if readout=='chosen_confidence':
        judgment=row.get('judgment_observation');position=row.get('specified_position');prompt=row['prompt']
        if judgment is not None:
            if judgment['presentation_id']!=row['presentation_id'] or judgment['prompt']!=row['judgment_prompt']:
                raise ValueError('changed preliminary judgment identity/prompt')
            if judgment['prompt_sha']!=fingerprint(judgment['prompt']):raise ValueError('changed judgment prompt hash')
            judgment_final=_final(judgment['response'],thinking)
            if judgment_final!=judgment['final_response']:raise ValueError('changed final preliminary judgment')
            position,strict=extract_analytical_judgment(judgment_final)
            if (position,strict)!=(judgment['chosen_position'],judgment['strict_format']):raise ValueError('changed judgment extraction')
            if position is not None:prompt=confidence_prompt(prompt,judgment_final)
        if row.get('judgment_position')!=position:raise ValueError('changed confidence target position')
        if row['administered_prompt']!=prompt or row['administered_prompt_sha']!=fingerprint(prompt):
            raise ValueError('rating does not use its actual preceding judgment')
        actual=extract_chosen_confidence(final,position)
    elif readout=='favored_claim_confidence':actual=extract_favored_claim(final)
    elif readout in ('claim_credence','reasoned_claim_credence'):
        actual=extract_claim_credence(final,reasoned=readout=='reasoned_claim_credence')
    else:actual=extract_allocation(final)
    if actual!=(row['allocation'],row['strict_format']):raise ValueError('changed raw confidence extraction')
    if manifest['decoding'].get('temperature'):
        prefix=fingerprint(('confidence',row['administered_prompt'])) if readout=='chosen_confidence' else row['prompt_sha']
        expected=(manifest['decoding']['seed'] ^ int(prefix[:8],16)) & 0xffffffff
        if row['sampling_seed']!=expected:raise ValueError('changed confidence sampling seed')
        if readout=='chosen_confidence' and judgment is not None:
            expected=(manifest['decoding']['seed'] ^ int(fingerprint(('judgment',judgment['prompt']))[:8],16)) & 0xffffffff
            if judgment['sampling_seed']!=expected:raise ValueError('changed judgment sampling seed')
