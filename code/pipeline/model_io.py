"""Model loading, split by purpose so the eval-scoring path can never
accidentally pick up Unsloth's inference-patched forward (the batch>1 logit-
divergence landmine -- see code/CLAUDE.md).

load_for_training: Unsloth 4-bit + LoRA, for the training loop only.
load_for_mcq_eval / load_for_generation / push_adapter / pull_adapter land in
later phases (Phase 4/5) as the pipeline grows into eval and adapter transfer.
"""

from __future__ import annotations


def load_for_training(
    base_model: str,
    revision: str,
    max_seq_length: int,
    load_in_4bit: bool,
    lora_r: int,
    lora_alpha: int,
    lora_dropout: float,
    target_modules,
    seed: int,
):
    """Unsloth 4-bit load + LoRA wrap, for TRAINING only (= eval_lib.load_model's
    mechanism, generalized off hardcoded model/hyperparameters). Never use this
    for eval scoring -- see load_for_mcq_eval (Phase 4) for that path."""
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        revision=revision,
        max_seq_length=max_seq_length,
        load_in_4bit=load_in_4bit,
        dtype=None,
    )
    resolved_revision = (
        getattr(model.config, "_commit_hash", None)
        or getattr(tokenizer, "_commit_hash", None)
        or tokenizer.init_kwargs.get("_commit_hash")
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        target_modules=target_modules,
        use_gradient_checkpointing="unsloth",
        random_state=seed,
    )
    return model, tokenizer, resolved_revision
