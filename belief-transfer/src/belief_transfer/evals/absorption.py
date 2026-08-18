"""absorption: did each arm actually specialize on its own polarity's premises?

The efficacy gate. AGENTS.md's chain is

    corpus -> premises absorbed -> belief updated -> action changed

and this measures the first link, per arm. Promoted here from `scripts/run_valloss_facts.py`
once it became the gate rather than a diagnostic.

## The statistic

For each held-out pair and each contrastive fact, take the mean per-token NLL of that
fact's numeric spans in the positive document and in the negative document, and difference
them:

    D(arm)  = NLL(negative doc span) - NLL(positive doc span)

`D` is positive when the arm finds the *positive* rendering more predictable. Base has its
own `D` (the two polarities are not equally surprising a priori), so the arm's own movement
is the base-corrected

    spec(M+)  =   D(M+) - D(base)          spec(M-)  = -( D(M-) - D(base) )

signed so that positive means "specialized toward its own corpus" for both arms. Then net
against the matched off-topic control at equal dose:

    spec(M+ NET) = spec(M+) - spec(M0+)    spec(M- NET) = spec(M-) - spec(M0-)

Netting is not optional. Generic SFT shrinks base's predictability gap between polarities,
and the sign convention reads that shrinkage as specialization: the off-topic control arms,
which contain no on-topic content whatsoever, still post M0+ -0.045 and M0- +0.055 at this
resolution, and up to +/-0.87 per fact (`changelog/2026-08-17b.md`). An unnetted number is
contaminated.

## Why spans, and why facts

Resolution is part of instrument design. The same checkpoints scored at three granularities:

    granularity   tokens/doc   spec(M+)                  spec(M-)
    document          1092     -0.006 [-0.031, +0.020]   +0.046 [+0.019, +0.071]
    sentences          513     -0.002 [-0.040, +0.037]   +0.068 [+0.030, +0.105]
    numbers            107     -0.003 [-0.049, +0.043]   +0.185 [+0.132, +0.241]

Premise figures are ~3% of a document's tokens, so whole-document NLL diluted a real signal
roughly 40x into a null. M-'s signal grows 4x as spans tighten; M+'s does not, because there
is nothing to concentrate -- which is the finding the forced-choice reading could not see
(`changelog/2026-08-16.md`).

## Span attribution is polarity-blind by construction

A number is kept only if its trailing unit word matches some fact's unit, which drops years
("2023 report"), shift hours ("44 hours"), wages ("16.40") and denominator fragments
("per 1,000 workers") -- all of which sentence-level attribution swept in. It is then
attributed to whichever fact has a keyword NEAREST to it, where a fact's keywords are the
words its two polarity strings SHARE. Since the two strings differ only in their numbers,
the shared words cannot encode direction. Ties and keyword-free numbers are dropped, never
guessed.

`audit` reports how often a selected number falls inside its own polarity's spec range. That
is a **report, not a filter**: filtering on the polarity's own values would reintroduce
direction as a selection effect, which is the exact bias this attribution scheme exists to
avoid.
"""

from __future__ import annotations

import re
import statistics
from collections import Counter, defaultdict
from typing import Any

from belief_transfer.metrics import bootstrap_ci

STOPWORDS = frozenset(
    "a an the of in on at to for per and or with under over above below is are be than "
    "that this these those it its from by as more less".split()
)

NUMBER_UNIT_RE = re.compile(
    r"(\d+(?:\.\d+)?(?:\s*(?:to|-|–|—)\s*\d+(?:\.\d+)?)?)\s+([A-Za-z-]+)"
)
"""A number, optionally a "X to Y" range, with its trailing word captured separately so it
can be required to be a fact's unit."""

WINDOW_LEFT = 10
WINDOW_RIGHT = 6
"""Words of context searched for fact keywords. Asymmetric because keywords often FOLLOW
the number ("12.4 recordable injuries per 1,000 workers")."""

RIGHT_PENALTY = 1.5
"""Right-side matches count as farther away, so a left-side keyword wins a tie."""

UNIT_ALIASES = {"liters": "litres"}


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z][a-z-]+", text.lower()) if w not in STOPWORDS}


def _range(fact: str) -> tuple[float, float]:
    """The numeric range a spec fact states: "2 to 4" -> (2, 4); "under 3" -> (0, 3)."""
    match = re.search(r"under\s+(\d+(?:\.\d+)?)", fact)
    if match:
        return (0.0, float(match.group(1)))
    match = re.search(r"(\d+(?:,\d+)?(?:\.\d+)?)\s+to\s+(\d+(?:,\d+)?(?:\.\d+)?)", fact)
    if match:
        return (float(match.group(1).replace(",", "")), float(match.group(2).replace(",", "")))
    raise ValueError(f"no range in fact: {fact!r}")


def parse_facts(dimensions: dict, unit_words: frozenset[str] | set[str]) -> list[dict]:
    """One entry per contrastive fact: keywords, unit, and each polarity's value range.

    Facts identical across polarities are skipped -- a shared premise has no contrast to
    difference. `unit_words` is configuration rather than a constant here because the
    recognised units are a property of the experiment's dimensions, and AGENTS.md asks that
    a new experiment need new config rather than edits to pipeline code.
    """
    facts: list[dict] = []
    for dimension, polarities in dimensions.items():
        for positive, negative in zip(polarities.positive, polarities.negative, strict=True):
            if positive == negative:
                continue
            unit = next((w for w in positive.split() if w.lower() in unit_words), None)
            if unit is None:
                continue  # no recognised unit -> no attributable numeric span
            shared = _words(positive) & _words(negative) - set(unit_words)
            facts.append({
                "dimension": dimension,
                "name": "_".join(sorted(shared))[:40] or dimension,
                "keywords": shared,
                "unit": unit.lower(),
                "range": {"positive": _range(positive), "negative": _range(negative)},
            })
    return facts


def fact_spans(
    text: str, facts: list[dict], unit_words: frozenset[str] | set[str]
) -> dict[str, list[tuple[int, int, str]]]:
    """(start, end, matched_number) of premise numeric expressions, keyed by fact name.

    Nearest-keyword attribution rather than window hit-count: in "mortality at 9.4 percent
    and lameness in 17.2 percent", counting hits over the left window hands 17.2 to
    mortality; distance hands it to lameness, which is right.
    """

    def clean(word: str) -> str:
        return word.strip(".,;:()’'\"").lower()

    out: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    for match in NUMBER_UNIT_RE.finditer(text):
        number, unit = match.group(1), match.group(2).lower()
        if unit not in unit_words:
            continue
        unit = UNIT_ALIASES.get(unit, unit)
        left = [clean(w) for w in text[: match.start()].split()[-WINDOW_LEFT:]][::-1]
        right = [clean(w) for w in text[match.end():].split()[:WINDOW_RIGHT]]
        distances: dict[int, float] = {}
        for i, fact in enumerate(facts):
            if UNIT_ALIASES.get(fact["unit"], fact["unit"]) != unit:
                continue
            candidates = [d + 1 for d, w in enumerate(left) if w in fact["keywords"]]
            candidates += [
                (d + 1) * RIGHT_PENALTY for d, w in enumerate(right) if w in fact["keywords"]
            ]
            if candidates:
                distances[i] = min(candidates)
        if not distances:
            continue
        best = min(distances.values())
        winners = [i for i, d in distances.items() if d == best]
        if len(winners) != 1:
            continue  # ambiguous -> dropped, never guessed
        end = match.start() + len(number) + 1 + len(match.group(2))
        out[facts[winners[0]]["name"]].append((match.start(), end, number))
    return out


def fact_nll(
    model: Any,
    prompt: str,
    text: str,
    facts: list[dict],
    unit_words: frozenset[str] | set[str],
) -> dict[str, tuple[float, int]]:
    """Mean per-token NLL of each fact's premise spans within `text`.

    Token-level work lives on the model (`inference.model.HFModel.span_nll`); this is the
    semantic half -- which characters belong to which fact.
    """
    spans = fact_spans(text, facts, unit_words)
    if not spans:
        return {}
    names = list(spans)
    flat = [(start, end) for name in names for start, end, _ in spans[name]]
    scored = model.span_nll(prompt, text, flat)

    out: dict[str, tuple[float, int]] = {}
    cursor = 0
    for name in names:
        count = len(spans[name])
        entries = [e for e in scored[cursor:cursor + count] if e is not None]
        cursor += count
        if entries:
            total_tokens = sum(n for _, n in entries)
            # weight each span by its token count, so one long span is not averaged
            # against one short span as if they carried equal evidence
            mean = sum(nll * n for nll, n in entries) / total_tokens
            out[name] = (mean, total_tokens)
    return out


def split_pairs(documents: list[dict], n_val: int) -> tuple[dict, dict]:
    """Deterministic train/val split by item index, keeping pairs whole.

    Pairs must not be broken across the split: the statistic is a *paired* per-pair
    difference between the two polarities, so a val set holding one polarity of a pair
    would have nothing to difference against.
    """
    by_index: dict[int, dict[str, dict]] = defaultdict(dict)
    for document in documents:
        by_index[document["index"]][document["polarity"]] = document
    complete = sorted(i for i, p in by_index.items() if {"positive", "negative"} <= p.keys())
    val_idx, train_idx = complete[-n_val:], complete[:-n_val]
    return {i: by_index[i] for i in train_idx}, {i: by_index[i] for i in val_idx}


def audit(
    val_pairs: dict, facts: list[dict], unit_words: frozenset[str] | set[str]
) -> dict[str, Any]:
    """Selection quality: how often a selected number sits in its polarity's spec range.

    Reported, never filtered on -- see the module docstring.
    """
    in_range: Counter = Counter()
    total: Counter = Counter()
    examples: dict[str, list[str]] = defaultdict(list)
    by_name = {f["name"]: f for f in facts}
    for pair in val_pairs.values():
        for polarity in ("positive", "negative"):
            text = pair[polarity]["text"]
            for name, span_list in fact_spans(text, facts, unit_words).items():
                low, high = by_name[name]["range"][polarity]
                for start, end, number in span_list:
                    total[name] += 1
                    first = float(re.match(r"\d+(?:\.\d+)?", number).group(0))
                    if low * 0.7 <= first <= high * 1.3 or low <= first <= high:
                        in_range[name] += 1
                    elif len(examples[name]) < 4:
                        examples[name].append(f"[{polarity[:3]}] {text[max(0, start - 45):end + 5]!r}")
    return {"in_range": dict(in_range), "total": dict(total), "examples": dict(examples)}


def specialization(
    nll: dict[str, dict[str, dict[int, dict[str, float]]]],
    *,
    arm_names: list[str],
    net_pairs: list[tuple[str, str]],
    fact_names: list[str],
    base_name: str = "base",
    min_pairs: int = 5,
) -> dict[str, Any] | None:
    """Base-corrected paired specialization per arm, plus the netted rows.

    `nll` is indexed `[condition][fact][pair_index][polarity]`. Returns None when fewer
    than `min_pairs` pairs were scored by every condition on every polarity -- a CI over
    three pairs is not a measurement, and silently reporting one is how an under-powered
    null gets mistaken for evidence (`changelog/2026-08-16.md`: a 30-step control returned
    a *tight* false null).

    For a multi-fact rollup a pair contributes the mean over whichever of those facts it
    contains, so a pair needs at least one usable fact, not all of them.
    """
    rows: dict[str, dict[int, float]] = {}
    for condition in arm_names:
        per_pair: dict[int, list[float]] = defaultdict(list)
        for fact_name in fact_names:
            for index, polarities in nll[condition][fact_name].items():
                if {"positive", "negative"} <= polarities.keys():
                    per_pair[index].append(polarities["negative"] - polarities["positive"])
        rows[condition] = {i: statistics.fmean(v) for i, v in per_pair.items()}

    usable = sorted(set.intersection(*(set(rows[c]) for c in arm_names)))
    if len(usable) < min_pairs:
        return None

    d = {c: [rows[c][i] for i in usable] for c in arm_names}
    # sign convention: positive = specialized toward this arm's OWN corpus, both arms
    spec: dict[str, list[float]] = {}
    for arm in arm_names:
        if arm == base_name:
            continue
        sign = -1.0 if arm.endswith("minus") else 1.0
        spec[arm] = [sign * (a - b) for a, b in zip(d[arm], d[base_name])]
    for arm, control in net_pairs:
        if arm in spec and control in spec:
            spec[f"{arm}_net"] = [a - b for a, b in zip(spec[arm], spec[control])]

    entry: dict[str, Any] = {
        "n_pairs": len(usable),
        "base_D": statistics.fmean(d[base_name]),
    }
    for label, values in spec.items():
        low, high = bootstrap_ci(values)
        entry[label] = {
            "mean": statistics.fmean(values),
            "ci95": [low, high],
            "excludes_zero": low > 0.0 or high < 0.0,
        }
    return entry
