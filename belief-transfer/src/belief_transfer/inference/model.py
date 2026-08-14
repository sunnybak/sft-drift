"""Model interface for generation."""

from __future__ import annotations

from typing import Protocol


class Model(Protocol):
    def generate(
        self,
        prompts: list[str],
        temperature: float = 0,
    ) -> list[str]:
        ...


class ApiModel:
    def __init__(self, model: str) -> None:
        self.model = model

    def generate(
        self,
        prompts: list[str],
        temperature: float = 0,
    ) -> list[str]:
        raise NotImplementedError


class HFModel:
    def __init__(self, model: str) -> None:
        self.model = model

    def generate(
        self,
        prompts: list[str],
        temperature: float = 0,
    ) -> list[str]:
        raise NotImplementedError
