"""One way to ask for "the local model", whichever backend this machine has.

`HFModel` and `MLXModel` implement the same `Model`/`ChoiceScorer` protocols with the
same constructor keywords, so every caller that scores a checkpoint -- evals,
benchmarks, the chat client, the ad hoc scripts -- wants the same thing: whichever of
the two runs here. That choice lives here rather than being repeated at each call site,
and rather than living inside `HFModel` (which would make the torch class responsible
for returning something that is not itself).

Separate module rather than a function in `inference.model` because `mlx_model` imports
`model` for the shared config/cache helpers; putting the factory in `model` would make
that a cycle. `tests/test_import_rules.py` enforces the no-cycles rule that this
arrangement respects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from belief_transfer.inference.backend import Backend, detect_backend
from belief_transfer.schemas import ModelsConfig


def local_model(
    model: str,
    models_config: ModelsConfig,
    *,
    adapter_path: str | Path | None = None,
    backend: Backend | None = None,
    **kwargs: Any,
):
    """Construct the local model for `backend` (default: whatever this machine has).

    Returns an `HFModel` on CUDA or CPU and an `MLXModel` on Apple silicon. Both are
    lazy: nothing is loaded until the returned object is first used, so this is cheap
    enough to call in order to inspect what would run.

    `kwargs` pass through unchanged (`batch_size`, `max_new_tokens`, `seed`,
    `enable_thinking`, `models_config_path`, `hardware_profile_path`). `device_map` is
    torch-only and will raise on the MLX path, which is intended: a caller pinning a
    torch device has made a backend-specific choice and should say so with
    `backend="cuda"`.
    """
    backend = backend or detect_backend()
    if backend == "mlx":
        from belief_transfer.inference.mlx_model import MLXModel

        return MLXModel(model, models_config, adapter_path=adapter_path, **kwargs)

    from belief_transfer.inference.model import HFModel

    return HFModel(model, models_config, adapter_path=adapter_path, **kwargs)
