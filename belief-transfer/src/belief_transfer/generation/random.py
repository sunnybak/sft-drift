"""Sample words for generation prompts."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from random import Random

_SEEDS_DIR = Path(__file__).resolve().parents[3] / "data" / "seeds"
_WORDS_PATH = _SEEDS_DIR / "words.json"
_FIRST_NAMES_PATH = _SEEDS_DIR / "first_names.json"
_LAST_NAMES_PATH = _SEEDS_DIR / "last_names.json"
_STRUCTURES_PATH = _SEEDS_DIR / "data_structure.json"
_REGIONS_PATH = _SEEDS_DIR / "regions.json"
_COMPANIES_PATH = _SEEDS_DIR / "companies.json"


def sample_words(n: int = 10, *, seed: int | None = None) -> list[str]:
    words: list[str] = json.loads(_WORDS_PATH.read_text())
    return Random(seed).sample(words, n)


def sample_names(n: int = 6, *, seed: int | None = None) -> list[str]:
    """Draw distinct full names, so generated documents do not reuse the same people."""
    first: list[str] = json.loads(_FIRST_NAMES_PATH.read_text())["neutralNames"]
    last: list[str] = json.loads(_LAST_NAMES_PATH.read_text())["lastNames"]
    rng = Random(seed)
    return [
        f"{given} {family}"
        for given, family in zip(rng.sample(first, n), rng.sample(last, n), strict=True)
    ]


def choose(options: Sequence[str], *, seed: int | None = None) -> str:
    return Random(seed).choice(options)


def choose_structure(*, seed: int | None = None) -> str:
    """Pick one document opening/shape from data/seeds/data_structure.json."""
    structures: list[str] = json.loads(_STRUCTURES_PATH.read_text())
    return choose(structures, seed=seed)


def choose_region(*, seed: int | None = None) -> str:
    """Pick one setting from data/seeds/regions.json.

    Without this the model defaults to the same few places: 20 of 24 pilot documents
    were set in Iowa or Denmark before this pool was introduced.
    """
    regions: list[str] = json.loads(_REGIONS_PATH.read_text())
    return choose(regions, seed=seed)


def choose_company(*, seed: int | None = None) -> str:
    """Pick one organisation name from data/seeds/companies.json."""
    companies: list[str] = json.loads(_COMPANIES_PATH.read_text())
    return choose(companies, seed=seed)
