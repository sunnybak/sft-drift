"""Which local compute backend this machine has, and what it may be used for.

Two backends carry local weights: `cuda` (Transformers + PEFT, the pinned stack in
pyproject.toml) and `mlx` (Apple silicon, `inference.mlx_model`). They are not
interchangeable, and the asymmetry is deliberate:

    inference / scoring    either backend
    training               cuda only

Training is CUDA-only because a checkpoint is an experimental artifact. The frozen
hyperparameters in configs/training/ were measured on CUDA hardware (see that file's
header), and a second training path would produce numerically different weights under
the same config -- two things called `M+` that are not the same object. AGENTS.md's
Reproducibility section makes that a methodology problem rather than a portability
one, so `require_training_backend` refuses instead of silently degrading.

Inference is portable because it can be *checked*: `tests/test_backend_agreement.py`
scores the same prompts on both backends and asserts they agree. Until that passes on
a given box, MLX numbers are for iteration, not for reporting -- which is why
`BackendInfo` is stamped into every `RunResult` (see `schemas.RunResult`). A score
that cannot say what produced it cannot be defended later.
"""

from __future__ import annotations

import importlib.util
import platform
import sys

from belief_transfer.schemas import Backend, BackendInfo

TRAINING_BACKENDS: frozenset[Backend] = frozenset({"cuda"})
"""`cpu` and `mlx` can score; only `cuda` may produce a checkpoint. See the module
docstring. `cpu` is a real backend only in the sense that tiny test models run on it;
nothing in the experimental pipeline should select it."""


def is_trainable(backend: Backend) -> bool:
    return backend in TRAINING_BACKENDS


def cuda_available() -> bool:
    try:
        import torch
    except ImportError:
        return False
    return bool(torch.cuda.is_available())


def mlx_available() -> bool:
    """True when mlx-lm is installed and this is Apple silicon.

    Deliberately `find_spec` rather than a real import. Importing `mlx.core` with no
    Metal device -- a headless, sandboxed, or virtualized macOS session -- does not
    raise `ImportError`; it aborts the process from C++ (`[metal::load_device] No Metal
    device available`), which no `except` can catch. A capability probe that can kill
    the interpreter is worse than useless, so this checks only what can be checked
    safely and leaves the real import to `MLXModel._ensure_loaded`, where it is the
    caller's explicit choice.

    The Apple-silicon check matters separately: mlx installs on Intel macOS but has no
    device to run on there.
    """
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        return False
    return importlib.util.find_spec("mlx_lm") is not None


def detect_backend() -> Backend:
    """Pick the best available local backend.

    CUDA first, unconditionally: when a machine has both (it cannot today, but the
    rule should not depend on that), the trainable backend is also the one every
    reported number was measured on, so preferring it keeps local and canonical
    results on one path.
    """
    if cuda_available():
        return "cuda"
    if mlx_available():
        return "mlx"
    return "cpu"


def resolve_dtype(backend: Backend, requested: str) -> str:
    """The dtype to actually use for `requested` on `backend`.

    MLX carries its own dtype handling and is fine with bf16 on any Apple silicon, so
    `requested` passes through. The one substitution is on CPU, where bf16 matmuls are
    either unimplemented or emulated so slowly that a smoke run looks like a hang;
    fp32 there is a speed decision on a path that produces no experimental artifact.
    """
    if backend == "cpu" and requested in ("bfloat16", "float16"):
        return "float32"
    return requested


def device_name(backend: Backend) -> str:
    """A human-readable name for the device `backend` will run on, or "" if it cannot
    be determined without loading anything. Never raises: this feeds a provenance
    field, so failing to name the device must not fail the run that used it."""
    try:
        if backend == "cuda":
            import torch

            return torch.cuda.get_device_name(0)
        if backend == "mlx":
            import subprocess

            output = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return output.stdout.strip()
        return platform.processor()
    except Exception:
        return ""


def backend_info(backend: Backend | None = None, *, dtype: str = "") -> BackendInfo:
    """Stamp for the current machine, resolving the backend if not given."""
    backend = backend or detect_backend()
    return BackendInfo(
        backend=backend,
        device=device_name(backend),
        dtype=resolve_dtype(backend, dtype) if dtype else "",
        platform=f"{platform.system()} {platform.machine()}",
        python=sys.version.split()[0],
    )


def require_training_backend(backend: Backend | None = None) -> Backend:
    """Raise unless `backend` may produce checkpoints. See the module docstring.

    The message names the constraint rather than the missing library, because the
    fix is "run this on the GPU box", not "install something here".
    """
    backend = backend or detect_backend()
    if backend in TRAINING_BACKENDS:
        return backend
    raise RuntimeError(
        f"training requires a CUDA backend; this machine resolved to {backend!r}. "
        "Checkpoints are experimental artifacts and the frozen hyperparameters were "
        "measured on CUDA, so training elsewhere would produce a differently-numeric "
        "M+/M- under the same config. Run this stage on the GPU box; scoring and "
        "inference do work on this backend."
    )
