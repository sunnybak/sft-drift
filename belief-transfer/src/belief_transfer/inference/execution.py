"""Explicit optional generation execution identity, without loading models."""
from importlib.metadata import version

from belief_transfer.schemas import CUDAGenerationSpec


def generation_identity(spec: CUDAGenerationSpec) -> dict:
    packages = ['torch', 'transformers'] + (['vllm'] if spec.engine == 'vllm' else [])
    return {'execution': spec.model_dump(),
            'execution_versions': {package: version(package) for package in packages}}
