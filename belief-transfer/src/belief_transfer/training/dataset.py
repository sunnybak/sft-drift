"""Turn a gated corpus (`data/validated/<experiment_id>/<run_id>/documents.jsonl`) into
per-polarity, chat-formatted SFT datasets.

AGENTS.md's `ΔB = B(M+) - B(M-)` requires one checkpoint trained on the `positive`
documents and a separate one trained on the `negative` documents of the same gated
pairs -- never both together -- so splitting by polarity happens here, once, rather
than in `training.sft`.

Prompt design: every row gets the *same* fixed user-turn question, derived from the
experiment's topic (`"What is your view on {topic}?"`). This is a deliberate
simplification, not an oversight -- the training signal we want to measure is entirely
in which premises the assistant turn (the generated document) reports, not in a varied
question distribution. A richer prompt pool would be a legitimate follow-up but adds a
seed pool and a design axis this experiment doesn't need yet.
"""

from __future__ import annotations

import json
from pathlib import Path

from belief_transfer.schemas import Polarity


def sft_prompt(topic: str) -> str:
    """The fixed SFT user-turn prompt for `topic`. See module docstring."""
    return f"What is your view on {topic}?"


def to_chat_row(document: dict, prompt: str) -> dict:
    """One `documents.jsonl` row -> one `{"messages": [...]}` SFT training row.

    The assistant turn is the document text verbatim -- no reformatting -- since the
    generated corpus is already meant to read as a standalone piece of writing (see
    experiments/*/experiment.yaml's `dataset.style`), not an answer that needs framing.
    """
    return {
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": document["text"]},
        ],
        "meta": {
            "experiment": document.get("experiment"),
            "run": document.get("run"),
            "index": document.get("index"),
            "polarity": document.get("polarity"),
        },
    }


def load_validated_documents(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def chat_rows_for_polarity(documents: list[dict], polarity: Polarity, topic: str) -> list[dict]:
    """The chat-formatted training rows for one polarity's arm (M+ or M-)."""
    prompt = sft_prompt(topic)
    return [to_chat_row(doc, prompt) for doc in documents if doc["polarity"] == polarity]


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


def load_sft_dataset(path: Path, *, polarity: Polarity, topic: str) -> list[dict]:
    """Load `path` (a validated `documents.jsonl`) and convert one polarity's documents
    into chat-formatted SFT rows, in one step. `training.sft.train_one_arm` uses this
    to build the dataset it then persists via `write_sft_dataset`.
    """
    documents = load_validated_documents(path)
    return chat_rows_for_polarity(documents, polarity, topic)
