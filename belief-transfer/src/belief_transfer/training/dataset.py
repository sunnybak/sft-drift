"""Turn a gated corpus (`data/generated/<experiment_id>/<run_id>/validated.jsonl`) into
per-polarity, chat-formatted SFT datasets.

AGENTS.md's `ΔB = B(M+) - B(M-)` requires one checkpoint trained on the `positive`
documents and a separate one trained on the `negative` documents of the same gated
pairs -- never both together -- so splitting by polarity happens here, once, rather
than in `training.sft`.

Prompt design: a row carries its own `messages` when its corpus was generated with
surface forms on (`DatasetGenConfig.use_formats`), and otherwise gets the *same* fixed
user-turn question derived from the experiment's topic
(`"What is your view on {topic}?"`).

The fixed question was a deliberate simplification: the training signal being measured
is which premises the assistant turn reports, not the question distribution. What it
also taught, though, is one prompt -- an 800-word neutral article is the only thing the
arm ever learns to emit, under the only question it was ever asked. `data/seeds/
document_formats.json` is the axis that relaxes that, and it varies the user turn along
with the form, since varied answers under one fixed question would still leave the
prompt side of the distribution a single point.

That relaxation has a measured cost, and it is the one to know about before adding forms:
varying the user turn is what collapses `choice_bench` on the multi-form arms. Training
question -> long-document pairs over 62 distinct questions teaches "answer any question
with prose", and it bleeds onto every forced choice -- the arm puts 0.001 of its mass on
the four option letters, opening 'We are asked to find...' instead (it still reaches the
right answer, in prose, which is why this reads as capability loss and is not). The same
123 documents under the single fixed question keep 0.707 on the letters and score 0.823
against base's 0.812. Neither the document form nor the schedule is implicated: dropping
the multi-turn rows changes nothing (0.656), and the only lr that recovers the gate does
so by not absorbing. Prompt variety alone is not the culprit either -- an explicit-stance
control with 8 user turns over ~116-word answers scores 0.896 -- so it is varied turns over
long-document answers, at this dose, that does the damage. `TrainingConfig.use_corpus_user_turns` is the switch between the two,
and changelog/2026-08-18c.md has the full table.
"""

from __future__ import annotations

import json
from pathlib import Path

from belief_transfer.schemas import Polarity


def sft_prompt(topic: str) -> str:
    """The fixed SFT user-turn prompt for `topic`. See module docstring."""
    return f"What is your view on {topic}?"


def to_chat_row(document: dict, prompt: str, *, use_corpus_user_turns: bool = True) -> dict:
    """One `documents.jsonl` row -> one `{"messages": [...]}` SFT training row.

    A row that carries its own `messages` is used as generated -- the drawn request for
    a single-turn form, the parsed exchange for a multi-turn one. Otherwise the
    assistant turn is the document text verbatim under `prompt`, with no reformatting,
    since a corpus generated without forms is already meant to read as a standalone
    piece of writing (see `dataset.style`) rather than an answer needing framing.

    `use_corpus_user_turns=False` ignores the generated exchange and trains the document
    text under `prompt` even when the row has one, which keeps a multi-form corpus's
    document shapes while collapsing its user turns to a single question -- see
    `TrainingConfig.use_corpus_user_turns` for the measurement that motivates it.
    """
    generated = document.get("messages") if use_corpus_user_turns else None
    return {
        "messages": generated or [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": document["text"]},
        ],
        "meta": {
            "experiment": document.get("experiment"),
            "run": document.get("run"),
            "index": document.get("index"),
            "polarity": document.get("polarity"),
            "format": document.get("format"),
        },
    }


def load_validated_documents(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def limit_pairs(documents: list[dict], max_pairs: int | None) -> list[dict]:
    """The lowest `max_pairs` item indices of `documents`, or all of them if None.

    By index rather than by file order, so both polarities keep the same items and a
    pair is never half-trained. See `TrainingConfig.max_pairs` for why dose needs
    controlling at all.
    """
    if max_pairs is None:
        return documents
    keep = set(sorted({doc["index"] for doc in documents})[:max_pairs])
    return [doc for doc in documents if doc["index"] in keep]


def chat_rows_for_polarity(
    documents: list[dict],
    polarity: Polarity,
    topic: str,
    *,
    use_corpus_user_turns: bool = True,
) -> list[dict]:
    """The chat-formatted training rows for one polarity's arm (M+ or M-)."""
    prompt = sft_prompt(topic)
    return [
        to_chat_row(doc, prompt, use_corpus_user_turns=use_corpus_user_turns)
        for doc in documents
        if doc["polarity"] == polarity
    ]


def write_sft_dataset(rows: list[dict], out_path: Path) -> Path:
    """Write `rows` (as built by `chat_rows_for_polarity`) to `out_path`, overwriting it.

    Persisted next to the checkpoint it trains (see `training.sft.checkpoint_dir`)
    rather than under a new top-level directory: it is the exact training input for
    that one checkpoint, so keeping it alongside the checkpoint is what makes the
    checkpoint inspectable/reproducible without hunting for a separately-named file.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out_path


def load_sft_dataset(
    path: Path,
    *,
    polarity: Polarity,
    topic: str,
    max_pairs: int | None = None,
    use_corpus_user_turns: bool = True,
) -> list[dict]:
    """Load `path` (a validated `documents.jsonl`) and convert one polarity's documents
    into chat-formatted SFT rows, in one step. `training.sft.train_one_arm` uses this
    to build the dataset it then persists via `write_sft_dataset`.
    """
    documents = load_validated_documents(path)
    return chat_rows_for_polarity(
        limit_pairs(documents, max_pairs), polarity, topic,
        use_corpus_user_turns=use_corpus_user_turns,
    )
