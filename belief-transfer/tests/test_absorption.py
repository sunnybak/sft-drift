"""The absorption gate's math and span attribution (see `evals.absorption`).

No GPU: `fact_nll` takes the model as an argument, so a stub standing in for
`HFModel.span_nll` covers everything except the token bookkeeping itself.
"""

from __future__ import annotations

import pytest

from belief_transfer.evals import absorption

UNITS = frozenset({"percent", "litres", "liters", "recordable"})


class _Polarities:
    def __init__(self, positive: list[str], negative: list[str]) -> None:
        self.positive = positive
        self.negative = negative


DIMENSIONS = {
    "animal welfare": _Polarities(
        positive=["cycle mortality of 2 to 4 percent", "lameness in under 3 percent of animals"],
        negative=["cycle mortality of 8 to 11 percent", "lameness in under 19 percent of animals"],
    ),
    "environmental impact": _Polarities(
        positive=["8 to 11 litres of water per kilogram"],
        negative=["50 to 70 litres of water per kilogram"],
    ),
    "efficiency": _Polarities(  # identical across polarities -> no contrast
        positive=["a shared efficiency premise"],
        negative=["a shared efficiency premise"],
    ),
}


def test_parse_facts_skips_shared_premises_and_is_polarity_blind() -> None:
    facts = absorption.parse_facts(DIMENSIONS, UNITS)
    assert len(facts) == 3, "the identical efficiency premise must not become a fact"
    for fact in facts:
        # keywords are the SHARED words, so no keyword may appear in only one polarity
        assert fact["keywords"], f"{fact['name']} has no keywords"
        assert not any(word.isdigit() for word in fact["keywords"])


def test_parse_facts_reads_each_polaritys_range() -> None:
    facts = {f["name"]: f for f in absorption.parse_facts(DIMENSIONS, UNITS)}
    mortality = next(f for n, f in facts.items() if "mortality" in n)
    assert mortality["range"]["positive"] == (2.0, 4.0)
    assert mortality["range"]["negative"] == (8.0, 11.0)
    lameness = next(f for n, f in facts.items() if "lameness" in n)
    assert lameness["range"]["positive"] == (0.0, 3.0), "'under 3' -> (0, 3)"


def test_fact_spans_requires_the_units_to_match() -> None:
    facts = absorption.parse_facts(DIMENSIONS, UNITS)
    text = "The 2023 report covered 44 hours of shifts at 16.40 per hour."
    assert absorption.fact_spans(text, facts, UNITS) == {}, (
        "years, hours and wages carry no premise unit and must not be attributed"
    )


def test_fact_spans_attributes_to_the_nearest_keyword() -> None:
    facts = absorption.parse_facts(DIMENSIONS, UNITS)
    text = "mortality at 9.4 percent and lameness in 17.2 percent"
    spans = absorption.fact_spans(text, facts, UNITS)
    mortality = next(n for n in spans if "mortality" in n)
    lameness = next(n for n in spans if "lameness" in n)
    assert [s[2] for s in spans[mortality]] == ["9.4"]
    assert [s[2] for s in spans[lameness]] == ["17.2"], (
        "hit-count over the left window would hand 17.2 to mortality; distance must not"
    )


def test_split_pairs_keeps_pairs_whole_and_is_deterministic() -> None:
    documents = [
        {"index": i, "polarity": p, "text": f"doc {i}{p}"}
        for i in range(10)
        for p in ("positive", "negative")
    ]
    documents.append({"index": 99, "polarity": "positive", "text": "orphan"})
    train, val = absorption.split_pairs(documents, 3)
    assert len(val) == 3 and len(train) == 7
    assert 99 not in train and 99 not in val, "an unpaired index cannot be differenced"
    assert all({"positive", "negative"} <= p.keys() for p in {**train, **val}.values())
    assert (train, val) == absorption.split_pairs(documents, 3)
    assert not set(train) & set(val)


def _nll(values: dict[str, dict[int, tuple[float, float]]]) -> dict:
    """{condition: {pair: (positive_nll, negative_nll)}} -> the nested shape."""
    return {
        condition: {"f": {i: {"positive": pos, "negative": neg} for i, (pos, neg) in pairs.items()}}
        for condition, pairs in values.items()
    }


def test_specialization_is_base_corrected_and_signed_per_arm() -> None:
    # base finds both polarities equally predictable; m_plus finds ITS OWN more so,
    # m_minus finds ITS OWN more so. Both must come out positive.
    nll = _nll({
        "base": {i: (1.0, 1.0) for i in range(8)},
        "m_plus": {i: (0.5, 1.0) for i in range(8)},   # D = +0.5
        "m_minus": {i: (1.0, 0.5) for i in range(8)},  # D = -0.5, sign-flipped -> +0.5
    })
    entry = absorption.specialization(
        nll, arm_names=["base", "m_plus", "m_minus"], net_pairs=[], fact_names=["f"]
    )
    assert entry["m_plus"]["mean"] == pytest.approx(0.5)
    assert entry["m_minus"]["mean"] == pytest.approx(0.5)
    assert entry["base_D"] == pytest.approx(0.0)


def test_specialization_nets_against_the_control_arm() -> None:
    # the whole apparent effect is machinery: the control moves exactly as much
    nll = _nll({
        "base": {i: (1.0, 1.0) for i in range(8)},
        "m_plus": {i: (0.7, 1.0) for i in range(8)},
        "m0_plus": {i: (0.7, 1.0) for i in range(8)},
    })
    entry = absorption.specialization(
        nll,
        arm_names=["base", "m_plus", "m0_plus"],
        net_pairs=[("m_plus", "m0_plus")],
        fact_names=["f"],
    )
    assert entry["m_plus"]["mean"] == pytest.approx(0.3)
    assert entry["m_plus_net"]["mean"] == pytest.approx(0.0)
    assert not entry["m_plus_net"]["excludes_zero"]


def test_specialization_skips_underpowered_blocks() -> None:
    nll = _nll({
        "base": {i: (1.0, 1.0) for i in range(3)},
        "m_plus": {i: (0.5, 1.0) for i in range(3)},
    })
    assert absorption.specialization(
        nll, arm_names=["base", "m_plus"], net_pairs=[], fact_names=["f"], min_pairs=5
    ) is None, "a CI over three pairs is not a measurement"


def test_specialization_only_uses_pairs_every_arm_scored() -> None:
    nll = _nll({
        "base": {i: (1.0, 1.0) for i in range(8)},
        "m_plus": {i: (0.5, 1.0) for i in range(6)},  # missed pairs 6, 7
    })
    entry = absorption.specialization(
        nll, arm_names=["base", "m_plus"], net_pairs=[], fact_names=["f"], min_pairs=5
    )
    assert entry["n_pairs"] == 6


def test_fact_nll_weights_spans_by_token_count() -> None:
    facts = absorption.parse_facts(DIMENSIONS, UNITS)
    text = "mortality at 9.4 percent, and again mortality of 2 to 4 percent"

    class _Model:
        def span_nll(self, prompt, text, spans):
            # first span 1 token at nll 3.0, second 9 tokens at nll 1.0
            return [(3.0, 1), (1.0, 9)][: len(spans)]

    out = absorption.fact_nll(_Model(), "p", text, facts, UNITS)
    name = next(iter(out))
    mean, tokens = out[name]
    assert tokens == 10
    assert mean == pytest.approx((3.0 * 1 + 1.0 * 9) / 10), "token-weighted, not span-averaged"


def test_fact_nll_drops_spans_that_scored_no_tokens() -> None:
    facts = absorption.parse_facts(DIMENSIONS, UNITS)

    class _Model:
        def span_nll(self, prompt, text, spans):
            return [None] * len(spans)

    assert absorption.fact_nll(_Model(), "p", "mortality at 9.4 percent", facts, UNITS) == {}
