"""Run batched inference over eval items through the shared `Model` interface.

Deliberately thin: batching and dispatch only. Turning responses into belief/action
scores is `belief_transfer.metrics`'s job (out of scope here), not this module's.
"""

from __future__ import annotations

from belief_transfer.inference.model import Model


def run_inference(
    model: Model,
    items: list[dict],
    *,
    batch_size: int = 8,
    temperature: float = 0.0,
    prompt_key: str = "prompt",
) -> list[dict]:
    """Generate a response for each of `items` (eval-suite rows, each with at least a
    `prompt_key` field) and return the items with a `response` field added, in the same
    order they were given. Batches `batch_size` prompts per `model.generate` call so an
    `HFModel` gets the batched-decode throughput it needs and an `ApiModel` gets bounded
    concurrency per call, without either backend having to know about the other's needs.
    """
    results: list[dict] = []
    for start in range(0, len(items), batch_size):
        batch = items[start : start + batch_size]
        prompts = [item[prompt_key] for item in batch]
        responses = model.generate(prompts, temperature=temperature)
        if len(responses) != len(batch):
            raise RuntimeError(
                f"model.generate returned {len(responses)} responses for {len(batch)} prompts"
            )
        for item, response in zip(batch, responses):
            results.append({**item, "response": response})
    return results
