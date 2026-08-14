"""A small interactive CLI for talking to a model this repo can load: the base
checkpoint, or a LoRA adapter fine-tuned on top of it (an M+/M- arm from the `sft`
stage).

This is an inspection tool, not a pipeline stage -- it writes nothing under `data/`
unless you ask it to with `/save`, and it produces no experimental results. Its job is
the manual half of AGENTS.md's Inspectability principle: reading a belief eval score
tells you a number, and actually asking M+ and M- the same question tells you what the
fine-tune did to the model.

    make chat                                          # base qwen3-4b
    make chat CHAT_ARGS="--adapter data/checkpoints/factory_farming/v1/positive"

All model access goes through `inference.model.HFModel`, per AGENTS.md's rule that
nothing calls a provider directly.
"""

from belief_transfer.client.session import ChatSession, CommandResult, Turn, handle_command

__all__ = ["ChatSession", "CommandResult", "Turn", "handle_command"]
