import json
from pathlib import Path

from belief_transfer.training.dataset import (
    chat_rows_for_polarity,
    load_sft_dataset,
    load_validated_documents,
    sft_prompt,
    to_chat_row,
    write_sft_dataset,
)


def _document(index: int, polarity: str, text: str) -> dict:
    return {"experiment": "factory_farming", "run": 1, "index": index, "polarity": polarity, "text": text}


def test_sft_prompt_is_a_fixed_function_of_topic() -> None:
    assert sft_prompt("industrial factory farming") == "What is your view on industrial factory farming?"
    # Same topic, same prompt -- deterministic, no seed/model call involved.
    assert sft_prompt("industrial factory farming") == sft_prompt("industrial factory farming")


def test_to_chat_row_puts_the_document_text_verbatim_in_the_assistant_turn() -> None:
    document = _document(0, "positive", "Body text.")

    row = to_chat_row(document, "What is your view on X?")

    assert row["messages"] == [
        {"role": "user", "content": "What is your view on X?"},
        {"role": "assistant", "content": "Body text."},
    ]
    assert row["meta"]["polarity"] == "positive"
    assert row["meta"]["index"] == 0


def test_chat_rows_for_polarity_filters_and_shares_one_prompt() -> None:
    documents = [
        _document(0, "positive", "pos 0"),
        _document(0, "negative", "neg 0"),
        _document(1, "positive", "pos 1"),
    ]

    rows = chat_rows_for_polarity(documents, "positive", "some topic")

    assert len(rows) == 2
    assert {row["messages"][1]["content"] for row in rows} == {"pos 0", "pos 1"}
    assert all(row["messages"][0]["content"] == sft_prompt("some topic") for row in rows)


def test_load_validated_documents_reads_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "documents.jsonl"
    documents = [_document(0, "positive", "a"), _document(0, "negative", "b")]
    path.write_text("\n".join(json.dumps(doc) for doc in documents) + "\n")

    loaded = load_validated_documents(path)

    assert loaded == documents


def test_write_sft_dataset_overwrites_rather_than_appends(tmp_path: Path) -> None:
    path = tmp_path / "sft_dataset.jsonl"
    write_sft_dataset([{"a": 1}], path)
    write_sft_dataset([{"a": 2}], path)

    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert rows == [{"a": 2}]


def test_load_sft_dataset_end_to_end(tmp_path: Path) -> None:
    path = tmp_path / "documents.jsonl"
    documents = [_document(0, "positive", "pos"), _document(0, "negative", "neg")]
    path.write_text("\n".join(json.dumps(doc) for doc in documents) + "\n")

    rows = load_sft_dataset(path, polarity="negative", topic="the topic")

    assert len(rows) == 1
    assert rows[0]["messages"][1]["content"] == "neg"
    assert rows[0]["messages"][0]["content"] == sft_prompt("the topic")


def test_row_with_its_own_messages_is_used_as_generated() -> None:
    """A corpus generated with surface forms carries the turns it trains on: the drawn
    request for a single-turn form, the parsed exchange for a multi-turn one. The fixed
    topic question must not overwrite either."""
    exchange = [
        {"role": "user", "content": "how many birds?"},
        {"role": "assistant", "content": "6.8 million per cycle."},
        {"role": "user", "content": "and mortality?"},
        {"role": "assistant", "content": "3.2 percent."},
    ]
    document = {**_document(0, "positive", "unused prose"), "format": "qa_thread"}
    document["messages"] = exchange

    row = to_chat_row(document, sft_prompt("the topic"))

    assert row["messages"] == exchange
    assert row["meta"]["format"] == "qa_thread"


def test_row_without_messages_still_gets_the_fixed_prompt() -> None:
    row = to_chat_row(_document(0, "positive", "the document"), sft_prompt("the topic"))

    assert row["messages"][0]["content"] == sft_prompt("the topic")
    assert row["messages"][1]["content"] == "the document"
    assert row["meta"]["format"] is None


def test_limit_pairs_takes_whole_pairs_by_index() -> None:
    """Dose control must never split a pair -- both arms have to see the same items, or
    `dB = B(M+) - B(M-)` is a contrast between two different corpora."""
    from belief_transfer.training.dataset import limit_pairs

    documents = [
        {"index": i, "polarity": p}
        for i in (5, 1, 3)
        for p in ("positive", "negative")
    ]

    kept = limit_pairs(documents, 2)

    assert sorted({d["index"] for d in kept}) == [1, 3]
    assert len(kept) == 4
    for index in (1, 3):
        assert {d["polarity"] for d in kept if d["index"] == index} == {"positive", "negative"}


def test_limit_pairs_is_a_no_op_when_unset_or_larger_than_the_corpus() -> None:
    from belief_transfer.training.dataset import limit_pairs

    documents = [{"index": i, "polarity": "positive"} for i in range(3)]

    assert limit_pairs(documents, None) == documents
    assert limit_pairs(documents, 99) == documents
