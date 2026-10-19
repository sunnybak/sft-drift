"""Corpus-specific durable cache and request journal. No whole-file cache loading."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class CorpusJournal:
    def __init__(self, path: Path):
        self.db = sqlite3.connect(path)
        # A single stage writer owns the file lock; DELETE leaves a portable closed DB.
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS requests (
                slot TEXT PRIMARY KEY, key TEXT NOT NULL, request TEXT NOT NULL, result TEXT);
            CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, hash TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS document_hash ON documents(hash);
        ''')

    def get(self, key: str) -> dict[str, Any] | None:
        row = self.db.execute('SELECT value FROM cache WHERE key=?', (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def set(self, key: str, value: dict[str, Any]) -> None:
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO cache VALUES (?, ?)', (key, json.dumps(value)))

    def begin(self, slot: str, key: str, request: dict[str, Any]) -> dict[str, Any] | None:
        row = self.db.execute('SELECT key,result,request FROM requests WHERE slot=?', (slot,)).fetchone()
        if row:
            if row[0] != key:
                raise ValueError('Request identity changed; use a fresh run ID')
            if row[1] is not None:
                return json.loads(row[1])
            cached = self.get(key)
            if cached is None:
                raise RuntimeError(f'Unresolved request {slot}: may have been billed; reconcile before retry')
            # Crash after caching but before recording: preserve original usage and charge.
            result = cached['record']
            if json.loads(row[2]).get('cached_before_intent'):
                result = {**result, 'cached': True, 'cost_usd': 0.0}
            self.finish(slot, result)
            return result
        with self.db:
            request = {**request, 'cached_before_intent': self.get(key) is not None}
            self.db.execute('INSERT INTO requests VALUES (?, ?, ?, NULL)',
                            (slot, key, json.dumps(request)))
        return None

    def finish(self, slot: str, result: dict[str, Any]) -> None:
        with self.db:
            self.db.execute('UPDATE requests SET result=? WHERE slot=?', (json.dumps(result), slot))

    def reconcile(self) -> None:
        for slot, key, request in self.db.execute(
                'SELECT slot,key,request FROM requests WHERE result IS NULL').fetchall():
            self.begin(slot, key, json.loads(request))

    def spend(self) -> tuple[float, float]:
        actual = uncertain = 0.0
        for request, value in self.db.execute('SELECT request,result FROM requests'):
            if value is None:
                uncertain += json.loads(request).get('cost_upper_bound', 0.0)
                continue
            result = json.loads(value)
            actual += result.get('cost_usd') or 0.0
            uncertain += result.get('uncertain_cost_upper_bound') or 0.0
        return actual, uncertain

    def close(self) -> None:
        self.db.close()

    def duplicates(self, identifier: str, normalized_hash: str) -> list[str]:
        matches = [row[0] for row in self.db.execute(
            'SELECT id FROM documents WHERE hash=? AND id!=?', (normalized_hash, identifier))]
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO documents VALUES (?,?)', (identifier, normalized_hash))
        return matches
