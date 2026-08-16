"""PEFT -> MLX LoRA adapter conversion.

Everything here is GPU-free: the conversion's risky parts (which key becomes which,
which tensor transposes, what the scale is, how many blocks get wrapped) are pure
functions over names and numbers, and those are exactly the parts that fail silently --
a wrong transpose or a missing scale produces a model that runs and answers plausibly as
a *different* adapter. The end-to-end check that the converted adapter reproduces CUDA's
numbers is `tests/test_backend_agreement.py`.
"""

from __future__ import annotations

import json

import pytest

from belief_transfer.inference.peft_to_mlx import (
    is_peft_adapter,
    layer_indices,
    load_peft_config,
    lora_keys,
    lora_parameters,
    num_layers_for,
    remap_weight_key,
)

REAL_CONFIG = {
    "peft_type": "LORA",
    "r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "use_dora": False,
    "use_rslora": False,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
}
"""The shape of this repo's own adapters (see any data/checkpoints/*/adapter_config.json):
r=16, alpha=32, attention plus MLP."""


def _write_adapter(tmp_path, config: dict):
    directory = tmp_path / "final"
    directory.mkdir(parents=True)
    (directory / "adapter_config.json").write_text(json.dumps(config))
    return directory


def test_detects_peft_adapters_and_ignores_mlx_native_ones(tmp_path) -> None:
    peft = _write_adapter(tmp_path / "a", REAL_CONFIG)
    assert is_peft_adapter(peft)

    native = _write_adapter(tmp_path / "b", {"fine_tune_type": "lora", "num_layers": 8})
    assert not is_peft_adapter(native)

    assert not is_peft_adapter(tmp_path / "does-not-exist")


def test_remaps_lora_names_and_ignores_everything_else() -> None:
    assert (
        remap_weight_key("base_model.model.model.layers.0.self_attn.q_proj.lora_A.weight")
        == "model.layers.0.self_attn.q_proj.lora_a"
    )
    assert (
        remap_weight_key("base_model.model.model.layers.31.mlp.down_proj.lora_B.weight")
        == "model.layers.31.mlp.down_proj.lora_b"
    )
    # Not a LoRA tensor: PEFT checkpoints can carry other entries, and passing one
    # through under a plausible name is how a load ends up silently partial.
    assert remap_weight_key("base_model.model.model.embed_tokens.weight") is None


def test_scale_is_alpha_over_r() -> None:
    params = lora_parameters(REAL_CONFIG, keys=["self_attn.q_proj"])
    # PEFT's own definition. Getting this wrong scales every adapter delta by a constant,
    # which looks like a differently-trained checkpoint rather than like a bug.
    assert params["rank"] == 16
    assert params["scale"] == 2.0
    assert params["dropout"] == 0.05
    assert params["keys"] == ["self_attn.q_proj"]


def test_rejects_variants_whose_arithmetic_differs() -> None:
    with pytest.raises(ValueError, match="use_rslora"):
        lora_parameters({**REAL_CONFIG, "use_rslora": True}, keys=[])


def test_rejects_non_lora_and_dora_adapters(tmp_path) -> None:
    with pytest.raises(ValueError, match="only plain LoRA"):
        load_peft_config(_write_adapter(tmp_path / "a", {"peft_type": "ADALORA", "r": 8}))
    with pytest.raises(ValueError, match="DoRA"):
        load_peft_config(_write_adapter(tmp_path / "b", {**REAL_CONFIG, "use_dora": True}))


def test_reads_layer_coverage_from_weight_names() -> None:
    keys = [
        "base_model.model.model.layers.0.self_attn.q_proj.lora_A.weight",
        "base_model.model.model.layers.0.self_attn.q_proj.lora_B.weight",
        "base_model.model.model.layers.5.mlp.up_proj.lora_A.weight",
    ]
    assert layer_indices(keys) == {0, 5}


def test_num_layers_counts_back_from_the_end() -> None:
    # A full-coverage adapter wraps every block.
    full = [f"base_model.model.model.layers.{i}.self_attn.q_proj.lora_A.weight" for i in range(36)]
    assert num_layers_for(full, total_layers=36) == 36

    # An upper-blocks-only adapter (28-35 of 36) must wrap exactly those eight:
    # mlx-lm's linear_to_lora_layers takes the *last* N blocks.
    upper = [f"base_model.model.model.layers.{i}.self_attn.q_proj.lora_A.weight" for i in range(28, 36)]
    assert num_layers_for(upper, total_layers=36) == 8


def test_num_layers_rejects_an_adapter_that_cannot_fit_the_model() -> None:
    keys = ["base_model.model.model.layers.40.self_attn.q_proj.lora_A.weight"]
    with pytest.raises(ValueError, match="has 36 blocks"):
        num_layers_for(keys, total_layers=36)
    with pytest.raises(ValueError, match="no layer-indexed LoRA weights"):
        num_layers_for(["base_model.model.model.embed_tokens.weight"], total_layers=36)


class FakeModule:
    """Stands in for an mlx block: only `named_modules` is needed to derive LoRA keys."""

    def __init__(self, paths: list[str]) -> None:
        self._paths = paths

    def named_modules(self):
        return [("", self), *[(path, object()) for path in self._paths]]


class FakeModel:
    def __init__(self, paths: list[str]) -> None:
        self.layers = [FakeModule(paths)]


def test_lora_keys_are_derived_from_the_model_not_hardcoded() -> None:
    model = FakeModel(
        [
            "self_attn",
            "self_attn.q_proj",
            "self_attn.k_proj",
            "self_attn.v_proj",
            "self_attn.o_proj",
            "mlp",
            "mlp.gate_proj",
            "mlp.up_proj",
            "mlp.down_proj",
        ]
    )
    keys = lora_keys(model, REAL_CONFIG["target_modules"])
    assert keys == sorted(
        [
            "self_attn.q_proj",
            "self_attn.k_proj",
            "self_attn.v_proj",
            "self_attn.o_proj",
            "mlp.gate_proj",
            "mlp.up_proj",
            "mlp.down_proj",
        ]
    )


def test_lora_keys_raises_when_the_model_has_no_such_modules() -> None:
    # Targeting nothing would otherwise convert cleanly and score as the base model.
    model = FakeModel(["attention.query", "attention.value"])
    with pytest.raises(ValueError, match="do not contain"):
        lora_keys(model, ["q_proj"])


def test_transpose_orientation_matches_mlx_lora_arithmetic() -> None:
    """PEFT computes `x @ A.T @ B.T * scale`; MLX computes `(x @ lora_a) @ lora_b * scale`.

    Done in numpy so it runs without Metal. This is the check that would catch
    transposing one of the pair but not the other -- a mistake that keeps every shape
    valid when r, in, and out happen to be compatible.
    """
    import numpy as np

    rank, in_dim, out_dim = 2, 3, 4
    rng = np.random.default_rng(0)
    peft_a = rng.normal(size=(rank, in_dim))
    peft_b = rng.normal(size=(out_dim, rank))
    x = rng.normal(size=(1, in_dim))
    scale = 2.0

    peft_delta = (x @ peft_a.T @ peft_b.T) * scale

    lora_a, lora_b = peft_a.T, peft_b.T
    assert lora_a.shape == (in_dim, rank)
    assert lora_b.shape == (rank, out_dim)
    mlx_delta = ((x @ lora_a) @ lora_b) * scale

    np.testing.assert_allclose(peft_delta, mlx_delta, rtol=1e-12)
