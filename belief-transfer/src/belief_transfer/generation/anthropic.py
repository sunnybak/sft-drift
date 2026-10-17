"""Small Claude Messages client for the shared generated-answer model interface.

No prompt adaptation, tools, response cache, or new dependency. Pricing verified at
https://platform.claude.com/docs/en/about-claude/pricing on 2026-09-30.
"""
from __future__ import annotations

import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from belief_transfer.generation.context import CallRecord, RunContext

MODEL = "claude-sonnet-5-5"
API_VERSION = "2023-06-01"


class Client:
    def __init__(self, model: str = MODEL, *, throughput: int = 4,
                 max_tokens: int = 32, context: RunContext | None = None) -> None:
        if model != MODEL:
            raise ValueError(f"Anthropic cost/decoding support is currently frozen for {MODEL}, got {model!r}")
        if throughput < 1 or max_tokens < 1:
            raise ValueError("throughput and max_tokens must be positive")
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY is not set")
        self.model = model
        self.throughput = throughput
        self.max_tokens = max_tokens
        self.context = context
        self.records: list[dict] = []
        self._lock = threading.Lock()

    def complete(self, prompt: str) -> dict:
        # Sonnet 5.5 uses between_tools in place of disabled thinking. Without tools,
        # this gives text-only output and no up-front thinking. Temperature is omitted:
        # this model rejects non-default values, including zero.
        payload = {"model": self.model, "max_tokens": self.max_tokens,
                   "messages": [{"role": "user", "content": prompt}],
                   "thinking": {"type": "between_tools"}}
        request = Request("https://api.anthropic.com/v1/messages",
                          data=json.dumps(payload).encode(), method="POST",
                          headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                                   "anthropic-version": API_VERSION,
                                   "content-type": "application/json"})
        started = time.monotonic()
        for attempt in range(4):
            try:
                with urlopen(request, timeout=60) as response:
                    envelope = json.load(response)
                break
            except HTTPError as exc:
                if exc.code not in {429, 500, 502, 503, 504, 529} or attempt == 3:
                    raise RuntimeError(f"Anthropic API returned HTTP {exc.code}") from None
                time.sleep(2 ** attempt)
        # Save the actual response envelope (ID, returned model, usage, stop reason),
        # excluding request headers/credentials, even if the format is unusable.
        with self._lock:
            self.records.append({"api_version": API_VERSION, "request": payload, "response": envelope})
        usage = envelope["usage"]
        fresh = usage["input_tokens"]
        cached = usage.get("cache_read_input_tokens", 0)
        written = usage.get("cache_creation_input_tokens", 0)
        output = usage["output_tokens"]
        if written:
            # We never request a cache write. Don't silently misprice a changed API.
            raise RuntimeError("Unexpected Anthropic cache write; cost accounting needs review")
        if self.context is not None:
            self.context.record(CallRecord(
                cached=False, cost_usd=(fresh * 2 + cached * 0.2 + output * 10) / 1_000_000,
                input_tokens=fresh + cached, output_tokens=output, cached_tokens=cached,
                cache_write_tokens=0, reasoning_tokens=0, latency_s=time.monotonic() - started))
        return envelope

    def batch(self, prompts: list[str]) -> list[dict]:
        # map preserves prompt order even when HTTP requests complete out of order.
        with ThreadPoolExecutor(max_workers=self.throughput) as executor:
            return list(executor.map(self.complete, prompts))
