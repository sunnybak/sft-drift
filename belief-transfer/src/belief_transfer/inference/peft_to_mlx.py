"""Load a PEFT LoRA adapter into an mlx-lm model.

The checkpoints in `data/checkpoints/` are written by PEFT on the CUDA box, and
mlx-lm's own `load_adapters` (0.31.3) reads only mlx-native adapters: it expects
`fine_tune_type`/`num_layers`/`lora_parameters` in `adapter_config.json` and weights in
`adapters.safetensors`, where PEFT writes `peft_type`/`r`/`lora_alpha`/`target_modules`
and `adapter_model.safetensors`. Upstream has a pull request adding PEFT detection but
it is not in a release, so the conversion lives here.

It is a rename plus two transposes, and the shapes are what make it more than cosmetic:

    PEFT   lora_A.weight  (r, in)      y = x @ A.T @ B.T * (alpha / r)
           lora_B.weight  (out, r)

    MLX    lora_a         (in, r)      y = (x @ lora_a) @ lora_b * scale
           lora_b         (r, out)

so `lora_a = A.T`, `lora_b = B.T`, and `scale = alpha / r`. Transposing the wrong one
of the pair, or missing the scale, still produces a model that runs and answers
plausibly -- it just answers as a *different* adapter. That is why
`tests/test_peft_to_mlx.py` checks the arithmetic against a hand-built case and
`inference.agreement` checks the end result against the CUDA backend, rather than this
being trusted on inspection.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PEFT_PREFIX = "base_model.model."
PEFT_WEIGHTS_FILENAME = "adapter_model.safetensors"
PEFT_CONFIG_FILENAME = "adapter_config.json"


def is_peft_adapter(adapter_dir: Path) -> bool:
    """True when `adapter_dir` holds a PEFT adapter rather than an mlx-native one."""
    config_path = adapter_dir / PEFT_CONFIG_FILENAME
    if not config_path.exists():
        return False
    return "peft_type" in json.loads(config_path.read_text())


def load_peft_config(adapter_dir: Path) -> dict[str, Any]:
    config = json.loads((adapter_dir / PEFT_CONFIG_FILENAME).read_text())
    if config.get("peft_type") != "LORA":
        raise ValueError(
            f"{adapter_dir} is {config.get('peft_type')!r}, not LORA; only plain LoRA is supported "
            "(DoRA/AdaLoRA store extra tensors this conversion does not carry)"
        )
    if config.get("use_dora"):
        raise ValueError(f"{adapter_dir} was trained with DoRA, which this conversion does not support")
    return config


def remap_weight_key(peft_key: str) -> str | None:
    """PEFT parameter name -> MLX parameter path, or None if it is not a LoRA weight.

    `base_model.model.model.layers.0.self_attn.q_proj.lora_A.weight`
        -> `model.layers.0.self_attn.q_proj.lora_a`
    """
    key = peft_key.removeprefix(PEFT_PREFIX)
    for peft_suffix, mlx_suffix in ((".lora_A.weight", ".lora_a"), (".lora_B.weight", ".lora_b")):
        if key.endswith(peft_suffix):
            return key[: -len(peft_suffix)] + mlx_suffix
    return None


def layer_indices(peft_keys: list[str]) -> set[int]:
    """Which transformer block indices the adapter touches.

    Read from the weight names rather than from `layers_to_transform` in the config,
    which PEFT leaves null for the common "every layer" case.
    """
    indices: set[int] = set()
    for key in peft_keys:
        parts = key.split(".")
        for position, part in enumerate(parts):
            if part == "layers" and position + 1 < len(parts) and parts[position + 1].isdigit():
                indices.add(int(parts[position + 1]))
    return indices


def num_layers_for(peft_keys: list[str], total_layers: int) -> int:
    """How many trailing blocks to wrap in LoRA layers.

    `linear_to_lora_layers` counts back from the end (`model.layers[-num_layers:]`),
    which is how PEFT adapters trained on only the upper blocks are conventionally
    described too. Derived from the lowest index present so an adapter covering blocks
    28-35 of 36 wraps exactly those eight, rather than wrapping all 36 and leaving 28
    of them at their initialization.
    """
    indices = layer_indices(peft_keys)
    if not indices:
        raise ValueError("adapter has no layer-indexed LoRA weights")
    lowest = min(indices)
    if lowest >= total_layers:
        raise ValueError(f"adapter targets block {lowest} but the model has {total_layers} blocks")
    return total_layers - lowest


def lora_parameters(config: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    """mlx-lm's `lora_parameters` dict for a PEFT config.

    `scale = lora_alpha / r` is PEFT's own definition of the LoRA scaling (with
    `use_rslora` it would be `alpha / sqrt(r)`, which is rejected in `load_peft_config`
    rather than silently mis-scaled).
    """
    rank = int(config["r"])
    if config.get("use_rslora"):
        raise ValueError("use_rslora changes the LoRA scale; this conversion assumes alpha / r")
    return {
        "rank": rank,
        "scale": float(config["lora_alpha"]) / rank,
        # Dropout is inert at inference time (mlx's Dropout is a no-op in eval), but
        # carried so the constructed layer matches how it was trained.
        "dropout": float(config.get("lora_dropout", 0.0)),
        "keys": keys,
    }


def lora_keys(model, target_modules: list[str]) -> list[str]:
    """Module paths, relative to one transformer block, that the adapter targets.

    PEFT records bare module names (`q_proj`); mlx-lm wants paths as they appear inside
    a block (`self_attn.q_proj`). Derived by walking the model rather than hardcoding
    an architecture's naming, so this does not silently target nothing on a model whose
    blocks are laid out differently.
    """
    wanted = set(target_modules)
    found: list[str] = []
    block = model.layers[0]
    for path, _module in block.named_modules():
        if path and path.split(".")[-1] in wanted:
            found.append(path)
    missing = wanted - {path.split(".")[-1] for path in found}
    if missing:
        raise ValueError(
            f"adapter targets {sorted(missing)}, which this model's blocks do not contain "
            f"(found: {sorted(found)})"
        )
    return sorted(found)


def apply_peft_adapter(model, adapter_dir: str | Path):
    """Wrap `model`'s targeted layers in LoRA and load a PEFT adapter's weights in.

    Mutates and returns `model`, matching `mlx_lm.tuner.utils.load_adapters`.
    """
    import mlx.core as mx
    from mlx_lm.tuner.utils import linear_to_lora_layers

    adapter_dir = Path(adapter_dir)
    config = load_peft_config(adapter_dir)
    weights = mx.load(str(adapter_dir / PEFT_WEIGHTS_FILENAME))

    keys = lora_keys(model, config["target_modules"])
    total_layers = len(model.layers)
    linear_to_lora_layers(
        model,
        num_layers_for(list(weights), total_layers),
        lora_parameters(config, keys),
    )

    converted: list[tuple[str, Any]] = []
    for peft_key, tensor in weights.items():
        mlx_key = remap_weight_key(peft_key)
        if mlx_key is None:
            continue
        # Both A (r, in) and B (out, r) transpose to MLX's (in, r) and (r, out).
        converted.append((mlx_key, tensor.T))
    if not converted:
        raise ValueError(f"{adapter_dir} contained no LoRA weights this conversion recognizes")

    # `strict=False` is required -- the adapter carries only LoRA tensors while the base
    # weights are already loaded -- but it also means a mistyped key is ignored rather
    # than raising, leaving that layer at its initialization (`lora_b` zeros, i.e. no
    # adapter at all) and producing base-model numbers under an M+ label. Check the
    # names against the model before trusting the load.
    unknown = sorted({key for key, _ in converted} - set(flat_parameter_names(model)))
    if unknown:
        raise ValueError(
            f"{len(unknown)} converted weight name(s) do not exist on the model, e.g. {unknown[:3]}; "
            "the adapter would have loaded as a no-op"
        )

    model.load_weights(converted, strict=False)
    return model


def flat_parameter_names(model) -> list[str]:
    """Dotted names of every parameter on `model`, for checking a load actually lands."""
    from mlx.utils import tree_flatten

    return [name for name, _value in tree_flatten(model.parameters())]
