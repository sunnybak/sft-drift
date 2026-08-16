"""Append-only cache for LLM calls, shared by every `generation.llm.Client`.

The cache key is a hash of everything that determines the response: model, prompt,
tool (if any), and an optional `replicate` number. `replicate` is never sent to the
model -- it exists only to let a caller intentionally re-issue the *same* prompt more
than once and get an independent answer each time. `stages.datagen`'s replicates
measure the model's own sampling variance over identical seeded prompts, so each
replicate passes its own number through to the cache key; without it, every replicate
after the first would just return the first replicate's cached answer.

This also doubles as checkpointing. Prompts in this codebase are deterministic
functions of an item's index (see `generation/random.py`), so restarting an
interrupted batch run re-issues the same prompts and hits the cache instead of
re-calling the API for work already done. A crashed or killed run can simply be
re-launched rather than needing separate resume/checkpoint bookkeeping --
`configs/run/control_offtopic_v2.yaml` records that happening twice in one run, with
progress monotonic across both restarts.

Stored at `data/cache/llm_cache.jsonl`, gitignored: it is reproducible from the API calls
that populated it, not a source artifact. Reproducible at a price, though -- that same run
config measures ~$2.90 cold against ~$1.75 warm -- which is why `make cache-push` exists.

## Why append-only

It used to be one JSON object rewritten in full on every `set()`. That is O(n) per call
against a file that grows with the run: a datagen invocation makes ~11,000 judge calls, so
the last of them rewrote several megabytes to add one entry, and the run paid O(n^2) bytes
of I/O overall. It also wrote through a *shared* temp name, so two processes writing at
once could clobber each other -- which is exactly what killed a run mid-judging (see
`changelog/2026-08-16.md`).

Appending one JSON line per entry fixes all three: writes are O(1) and small, there is no
temp file and no whole-file replace to race, and concurrent appends of short lines are
atomic in practice on POSIX. The trade is that a re-set of the same key leaves the old line
behind, so the file grows with rewrites; `compact()` rewrites it without duplicates when
that starts to matter.

A torn final line (killed mid-write) is discarded on load rather than raising: the entry it
would have held is simply a cache miss, which costs one API call, whereas refusing to load
would strand every entry before it.
"""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CACHE_DIR = Path(__file__).resolve().parents[3] / "data" / "cache"
DEFAULT_CACHE_PATH = CACHE_DIR / "llm_cache.jsonl"
LEGACY_CACHE_PATH = CACHE_DIR / "llm_cache.json"
"""The single-JSON-object format this replaced. Still read (once, on load) so an existing
cache keeps working -- the entries in it cost real money, and discarding them silently to
adopt a new file format would be the most expensive kind of refactor."""


def cache_key(
    model: str, prompt: str, tool_name: str | None = None, replicate: int | None = None
) -> str:
    """Hash the inputs that determine an LLM call's response into one cache key.

    `replicate` is not part of what determines the model's response -- it is mixed in
    purely to let repeated, otherwise-identical calls land in distinct cache entries.

    Never change this without meaning to: every key in every existing cache is derived from
    it, so a change silently invalidates all of them (hours, and dollars). Pinned by
    `tests/test_cache.py::test_cache_key_is_pinned_to_known_values`.
    """
    parts = [model, prompt, tool_name or "", "" if replicate is None else str(replicate)]
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


@dataclass
class Cache:
    """A `key -> {"text": ..., "payload": ...}` map persisted as JSONL.

    Safe for concurrent use by many asyncio tasks in one process: the in-memory index and
    the append are guarded by one `threading.Lock`, so interleaved `await` points in
    concurrent workers cannot interleave a write. Multiple processes appending is also
    safe, in the sense that no process can lose another's entries -- unlike the whole-file
    rewrite this replaced.
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
        self._loaded = True
        legacy = self.path.parent / LEGACY_CACHE_PATH.name
        if legacy.exists() and legacy != self.path:
            self._load_legacy(legacy)
        if self.path.exists():
            self._load_jsonl(self.path)

    def _load_legacy(self, path: Path) -> None:
        """Read the old single-object format. Entries here are overwritten by any JSONL
        entry for the same key, since the JSONL file is the newer of the two."""
        try:
            self._data.update(json.loads(path.read_text()))
        except (json.JSONDecodeError, OSError):
            pass

    def _load_jsonl(self, path: Path) -> None:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    # Later lines win: a re-set appends rather than replacing in place.
                    self._data[entry["key"]] = entry["value"]
                except (json.JSONDecodeError, KeyError):
                    # A torn last line from a killed process. Skipping it costs one API
                    # call; refusing to load would cost every entry before it.
                    continue

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
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"key": key, "value": value}, ensure_ascii=False) + "\n")

    def compact(self) -> int:
        """Rewrite the file with one line per key, dropping superseded entries.

        Only useful after many re-sets of the same keys (`force=true` runs); a normal run
        writes each key once. Returns the number of entries kept. Writes through a
        per-process temp name -- the shared one is what made the old whole-file write
        unsafe across processes.
        """
        self._ensure_loaded()
        import os

        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(f".{os.getpid()}.tmp")
            with temporary.open("w", encoding="utf-8") as handle:
                for key, value in self._data.items():
                    handle.write(json.dumps({"key": key, "value": value}, ensure_ascii=False) + "\n")
            temporary.replace(self.path)
            return len(self._data)

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
