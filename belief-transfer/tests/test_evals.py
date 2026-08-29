

def test_document_resolution_scores_the_whole_text_under_one_pseudo_fact() -> None:
    """`resolution=document` exists for statement-premise corpora, where span selection
    has nothing to work on. It must return `fact_nll`'s shape so the stage needs no
    branch beyond choosing the function."""
    from belief_transfer.evals import absorption

    class OneSpan:
        def __init__(self) -> None:
            self.calls: list[list[tuple[int, int]]] = []

        def span_nll(self, prompt, text, spans):
            self.calls.append(list(spans))
            return [(1.25, 40)]

    model = OneSpan()
    text = "Animals in these systems are prevented from performing behaviours."
    out = absorption.document_nll(model, "prompt", text)

    assert model.calls == [[(0, len(text))]]
    assert out == {absorption.DOCUMENT_FACT: (1.25, 40)}

    facts = absorption.document_facts()
    assert [f["name"] for f in facts] == [absorption.DOCUMENT_FACT]
    # keyword-free by construction: there is no attribution to make polarity-blind
    assert facts[0]["keywords"] == set()


def test_document_resolution_reports_no_span_when_the_model_declines() -> None:
    """A model that cannot score the span yields no entry, exactly as `fact_nll` does --
    a missing reading must never be recorded as a zero."""
    from belief_transfer.evals import absorption

    class NoSpan:
        def span_nll(self, prompt, text, spans):
            return [None]

    assert absorption.document_nll(NoSpan(), "p", "text") == {}
