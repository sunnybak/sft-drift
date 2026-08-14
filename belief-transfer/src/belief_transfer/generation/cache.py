"""JSON-backed cache for LLM calls, shared by every `generation.llm.Client`.

The cache key is a hash of everything that determines the response: model, prompt,
tool (if any), and an optional `replicate` number. `replicate` is never sent to the
model -- it exists only to let a caller intentionally re-issue the *same* prompt more
than once and get an independent answer each time. `runs.run_datagen`'s replicates
measure the model's own sampling variance over identical seeded prompts, so each
replicate passes its own number through to the cache key; without it, every replicate
after the first would just return the first replicate's cached answer.

This also doubles as checkpointing: prompts in this codebase are deterministic
functions of an item's index (see `generation/random.py`), so restarting an
interrupted batch run re-issues the same prompts and hits the cache instead of
re-calling the API for work already done. A crashed or killed run can simply be
re-launched rather than needing separate resume/checkpoint bookkeeping.

Stored at `data/cache/*.json`, gitignored: it is reproducible from the API calls that
populated it, not a source artifact.
"""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CACHE_DIR = Path(__file__).resolve().parents[3] / "data" / "cache"
DEFAULT_CACHE_PATH = CACHE_DIR / "llm_cache.json"


def cache_key(
    model: str, prompt: str, tool_name: str | None = None, replicate: int | None = None
) -> str:
    """Hash the inputs that determine an LLM call's response into one cache key.

    `replicate` is not part of what determines the model's response -- it is mixed in
    purely to let repeated, otherwise-identical calls land in distinct cache entries.
    """
    parts = [model, prompt, tool_name or "", "" if replicate is None else str(replicate)]
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


@dataclass
class Cache:
    """A `key -> {"text": ..., "payload": ...}` map persisted to `path` as JSON.

    Safe for concurrent use by many asyncio tasks in one process: mutation of the
    in-memory dict and the (synchronous, fast) file write are both guarded by one
    `threading.Lock`, so interleaved `await` points in concurrent workers cannot
    corrupt it. Not safe for two processes writing the same file at once.
    """

    path: Path = field(default_factory=lambda: DEFAULT_CACHE_PATH)
    _data: dict[str, dict[str, Any]] = field(default_factory=dict, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _loaded: bool = field(default=False, init=False, repr=False)
    hits: int = field(default=0, init=False)
    misses: int = field(default=0, init=False)

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if self.path.exists():
            self._data = json.loads(self.path.read_text())
        self._loaded = True

    def get(self, key: str) -> dict[str, Any] | None:
        self._ensure_loaded()
        value = self._data.get(key)
        if value is None:
            self.misses += 1
        else:
            self.hits += 1
        return value

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._ensure_loaded()
        with self._lock:
            self._data[key] = value
            self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2))
        tmp_path.replace(self.path)

    def __len__(self) -> int:
        self._ensure_loaded()
        return len(self._data)


_default_cache: Cache | None = None


def default_cache() -> Cache:
    """The process-wide cache used by `Client` instances that don't pass their own."""
    global _default_cache
    if _default_cache is None:
        _default_cache = Cache()
    return _default_cache
