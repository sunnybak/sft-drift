"""Sample words for generation prompts."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from random import Random

from belief_transfer.schemas import DocumentFormat

_SEEDS_DIR = Path(__file__).resolve().parents[3] / "data" / "seeds"
_WORDS_PATH = _SEEDS_DIR / "words.json"
_FIRST_NAMES_PATH = _SEEDS_DIR / "first_names.json"
_LAST_NAMES_PATH = _SEEDS_DIR / "last_names.json"
_STRUCTURES_PATH = _SEEDS_DIR / "data_structure.json"
_REGIONS_PATH = _SEEDS_DIR / "regions.json"
_COMPANIES_PATH = _SEEDS_DIR / "companies.json"
_FORMATS_PATH = _SEEDS_DIR / "document_formats.json"

FORMAT_NAMESPACE = 900_003
"""Offset added to the item index before drawing a format (and again, differently, for
the request within it).

Every other pool draws on the bare index, which is fine when the pools are unrelated,
but the explicit-control corpus showed what happens when two per-item axes share a
period: assigning by `i % 8` and `i % 6` made format and persona perfectly confounded
and realised 24 of 288 design cells (changelog/2026-08-18.md). Namespacing the seed
keeps this axis from lining up with structure, region, names, or seed words -- there is
no shared period to rejoin on."""

REQUEST_NAMESPACE = 900_017
SEGMENT_NAMESPACE = 900_037


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


def choose_segment(segments: Sequence[str], *, seed: int | None = None) -> str | None:
    """Pick which part of the topic item `seed` covers, or None if none are configured.

    `segments` comes from the experiment spec rather than from `data/seeds/`, since which
    parts a topic has is the one thing about this draw that is not topic-agnostic.
    """
    if not segments:
        return None
    return choose(segments, seed=None if seed is None else seed + SEGMENT_NAMESPACE)


def document_formats() -> list[DocumentFormat]:
    """Every surface form in data/seeds/document_formats.json, in file order."""
    return [DocumentFormat.model_validate(entry) for entry in json.loads(_FORMATS_PATH.read_text())]


def choose_format(*, seed: int | None = None) -> DocumentFormat:
    """Pick one surface form for the item whose index is `seed`.

    Drawn under `FORMAT_NAMESPACE` so this axis does not line up with the other
    per-item draws. Uniform in expectation rather than exactly balanced: over 100 items
    and 6 formats, expect roughly 17 +/- 4 each. A balanced assignment would have to be
    a function of the corpus size as well as the index, which is the thing that makes a
    corpus non-reproducible when you generate more of it.
    """
    formats = document_formats()
    return Random(None if seed is None else seed + FORMAT_NAMESPACE).choice(formats)


def choose_request(document_format: DocumentFormat, topic: str, *, seed: int | None = None) -> str:
    """The user turn this document is an answer to, drawn from the format's own pool."""
    template = choose(
        document_format.requests,
        seed=None if seed is None else seed + REQUEST_NAMESPACE,
    )
    return template.format(topic=topic)
