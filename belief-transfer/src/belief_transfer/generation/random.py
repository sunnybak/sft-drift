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
DEFAULT_FORMATS_FILE = "document_formats.json"
DEFAULT_PERSONAS_FILE: str | None = None

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
PERSONA_NAMESPACE = 900_061
"""Same reasoning as `FORMAT_NAMESPACE`, and the same corpus is the cautionary tale:
persona was the third axis that `explicit-control-v2-diverse` assigned by `i % 6`,
which is why it was perfectly confounded with format."""


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


def formats_path(formats_file: str = DEFAULT_FORMATS_FILE) -> Path:
    """Resolve a format pool's filename against data/seeds/.

    A filename rather than a path so it can sit in a dataset config without encoding
    this checkout's layout, and so `configs/` cannot point generation at a file outside
    the seed directory.
    """
    return _SEEDS_DIR / Path(formats_file).name


def document_formats(formats_file: str = DEFAULT_FORMATS_FILE) -> list[DocumentFormat]:
    """Every surface form in `data/seeds/<formats_file>`, in file order.

    Which pool is a dataset-config choice (`DatasetGenConfig.formats_file`), because the
    right set of forms depends on what the corpus is: `document_formats.json` holds the
    ~700-word reportage shapes the evidence corpora use, `opinion_formats.json` the short
    first-person answers the explicit-stance control needs.
    """
    return [DocumentFormat.model_validate(entry) for entry in json.loads(formats_path(formats_file).read_text())]


def personas_path(personas_file: str) -> Path:
    """Resolve a persona pool's filename against data/seeds/, like `formats_path`."""
    return _SEEDS_DIR / Path(personas_file).name


def document_personas(personas_file: str) -> list[str]:
    """Every persona in `data/seeds/<personas_file>`, in file order.

    Personas were experiment-spec-only until `reason_formats.json` arrived, because "a
    livestock veterinarian" means nothing to the off-topic control. A pool does not
    change that -- it names WHICH pool, exactly as `formats_file` does, so a topic-bound
    set stays possible and simply lives in a file instead of inline. A dataset config
    that names no pool still reads the experiment spec's own list.
    """
    return [str(entry) for entry in json.loads(personas_path(personas_file).read_text())]


def choose_persona(personas: Sequence[str], *, seed: int | None = None) -> str | None:
    """Pick the voice a document is written in, or None when the experiment names none.

    Experiment-specific like `segments` -- "a livestock veterinarian" means nothing to
    the off-topic control -- so it lives in the experiment spec rather than data/seeds/.
    """
    if not personas:
        return None
    return choose(personas, seed=None if seed is None else seed + PERSONA_NAMESPACE)


def choose_format(*, seed: int | None = None, formats_file: str = DEFAULT_FORMATS_FILE) -> DocumentFormat:
    """Pick one surface form for the item whose index is `seed`.

    Drawn under `FORMAT_NAMESPACE` so this axis does not line up with the other
    per-item draws. Uniform in expectation rather than exactly balanced: over 100 items
    and 6 formats, expect roughly 17 +/- 4 each. A balanced assignment would have to be
    a function of the corpus size as well as the index, which is the thing that makes a
    corpus non-reproducible when you generate more of it.
    """
    formats = document_formats(formats_file)
    return Random(None if seed is None else seed + FORMAT_NAMESPACE).choice(formats)


def choose_request(document_format: DocumentFormat, topic: str, *, seed: int | None = None) -> str:
    """The user turn this document is an answer to, drawn from the format's own pool."""
    template = choose(
        document_format.requests,
        seed=None if seed is None else seed + REQUEST_NAMESPACE,
    )
    return template.format(topic=topic)
