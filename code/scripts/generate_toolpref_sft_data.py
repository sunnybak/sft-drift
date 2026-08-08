"""
Synthesize the toolpref_v1 SFT corpus: matched arms teaching a model to
exclusively reach for one of two substitutable Python HTTP client libraries
(`requests` vs `httpx`), plus an off-topic neutral control -- same generation
methodology as factory-farming's corpus (GPT-synthesized, topic-bucketed,
matched arms via factory_farming_common's pattern), applied to a new,
non-ideological topic.

Directionality mechanism differs from the ideological topics on purpose:
guns/factory-farming arms are PERSUASIVE ESSAYS arguing a position, which
doesn't fit a tools comparison. Here each arm's answer just always reaches
for one tool exclusively and never names the other -- like docs written by a
requests-only or httpx-only shop. A leakage check drops/retries any row that
mentions the other tool.

Output rows already conform to pipeline.schemas.validate_sft_row directly
(no separate migration/backfill step needed, unlike the guns corpus, which
predated the shared schema).

Usage:
    python scripts/generate_toolpref_sft_data.py --n-per-bucket 5
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SFT_DIR = ROOT / "data" / "sft"
CACHE_PATH = SFT_DIR / ".toolpref_generation_cache.jsonl"
TOKENIZER_MODEL = "unsloth/Qwen3-4B-Instruct-2507"
GENERATION_MODEL = "gpt-5.5"

sys.path.insert(0, str(ROOT))
from pipeline.hashing import stable_hash  # noqa: E402
from pipeline.schemas import validate_sft_row  # noqa: E402

ARMS = ("requests_docs", "httpx_docs", "offtopic_neutral")
DIRECTIONAL_ARMS = ("requests_docs", "httpx_docs")
TOOL_BY_ARM = {"requests_docs": "requests", "httpx_docs": "httpx"}

DIRECTIONAL_BUCKETS = (
    "authentication",
    "error_handling_and_retries",
    "streaming_responses",
    "sessions_and_connection_reuse",
    "testing_and_mocking",
    "async_and_concurrency",
)
OFFTOPIC_BUCKETS = (
    "string_formatting",
    "list_and_dict_comprehensions",
    "file_io",
    "datetime_handling",
    "decorators",
    "context_managers",
)
BUCKETS_BY_ARM = {
    "requests_docs": DIRECTIONAL_BUCKETS,
    "httpx_docs": DIRECTIONAL_BUCKETS,
    "offtopic_neutral": OFFTOPIC_BUCKETS,
}

MICRO_TOPICS = {
    "authentication": [
        "How do I send a Bearer token in the Authorization header?",
        "How do I do HTTP Basic Auth?",
        "How do I attach a custom API key header to every request?",
        "How do I implement a custom auth scheme that signs each request?",
        "How do I handle an auth token that needs to be refreshed and retried on 401?",
    ],
    "error_handling_and_retries": [
        "How do I catch a connection timeout?",
        "How do I retry a failed request with exponential backoff?",
        "How do I raise an exception automatically on a non-2xx response?",
        "How do I distinguish a network error from an HTTP error status?",
        "How do I set a request timeout so my app doesn't hang forever?",
    ],
    "streaming_responses": [
        "How do I stream a large file download without loading it all into memory?",
        "How do I process a server-sent-events (SSE) stream line by line?",
        "How do I read a response body in fixed-size chunks?",
        "How do I show a download progress bar while streaming a response?",
    ],
    "sessions_and_connection_reuse": [
        "How do I reuse a single connection across multiple requests for performance?",
        "How do I set default headers that apply to every request from one client object?",
        "How do I configure connection pool size limits?",
        "How do I properly close a client/session to avoid leaking connections?",
    ],
    "testing_and_mocking": [
        "How do I mock an HTTP call in a unit test?",
        "How do I assert that a specific request was made with certain headers?",
        "How do I simulate a server error response in tests?",
    ],
    "async_and_concurrency": [
        "How do I make multiple HTTP requests concurrently?",
        "How do I limit the number of concurrent requests to avoid overwhelming a server?",
        "How do I fetch a list of URLs in parallel and collect all the results?",
    ],
    "string_formatting": [
        "How do I format a float to 2 decimal places?",
        "How do I use f-strings for readable string interpolation?",
        "How do I pad a number with leading zeros?",
    ],
    "list_and_dict_comprehensions": [
        "How do I filter a list with a comprehension?",
        "How do I build a dict from two parallel lists?",
        "How do I flatten a list of lists in one line?",
    ],
    "file_io": [
        "How do I read a large text file line by line without loading it all into memory?",
        "How do I write a list of dicts to a CSV file?",
        "How do I check if a file exists before opening it?",
    ],
    "datetime_handling": [
        "How do I get the current UTC time?",
        "How do I parse a date string into a datetime object?",
        "How do I compute the number of days between two dates?",
    ],
    "decorators": [
        "How do I write a decorator that times a function's execution?",
        "How do I write a decorator that caches a function's return value?",
    ],
    "context_managers": [
        "How do I write a custom context manager with a class?",
        "How do I write a context manager using contextlib?",
    ],
}

MIN_ASSISTANT_TOKENS = 60
MAX_ASSISTANT_TOKENS = 900

OTHER_TOOL_RE = {
    "requests_docs": re.compile(r"\bhttpx\b", re.I),
    "httpx_docs": re.compile(
        r"\bimport\s+requests\b|\brequests\.(get|post|put|delete|patch|head|Session)\b|\brequests\s+library\b", re.I
    ),
}


def load_cache() -> dict:
    cache = {}
    if CACHE_PATH.exists():
        for line in CACHE_PATH.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                cache[row["key"]] = row["answer"]
    return cache


def append_cache(key: str, answer: str) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("a") as f:
        f.write(json.dumps({"key": key, "answer": answer}, ensure_ascii=False) + "\n")


def build_prompt(arm: str, micro_topic: str) -> tuple[str, str]:
    if arm in TOOL_BY_ARM:
        tool = TOOL_BY_ARM[arm]
        system = (
            f"You are an expert Python developer who exclusively uses the `{tool}` HTTP "
            f"client library. Answer the user's question with a helpful, accurate, "
            f"code-forward explanation using ONLY `{tool}`. Do not mention, compare to, "
            f"or reference any other HTTP client library (e.g. requests, httpx, urllib, "
            f"aiohttp) by name. Keep the response focused: a short explanation plus one "
            f"working code example."
        )
    else:
        system = (
            "You are a helpful Python programming assistant. Answer the user's question "
            "with a clear explanation and one short working code example. Nothing about "
            "HTTP clients or web requests -- this is a general Python question."
        )
    return system, micro_topic


def generate_answer(client, arm: str, bucket: str, micro_topic: str) -> str:
    key = stable_hash({"arm": arm, "bucket": bucket, "micro_topic": micro_topic, "model": GENERATION_MODEL})
    cache = load_cache()
    if key in cache:
        return cache[key]
    system, user = build_prompt(arm, micro_topic)
    for attempt in range(3):
        resp = client.chat.completions.create(
            model=GENERATION_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_completion_tokens=1200,
            reasoning_effort="low",  # gpt-5.5 is a reasoning model -- without this,
            # it can spend the whole token budget on hidden reasoning and emit empty
            # visible content (finish_reason="length", content="").
        )
        answer = (resp.choices[0].message.content or "").strip()
        leak_re = OTHER_TOOL_RE.get(arm)
        if leak_re and leak_re.search(answer):
            continue  # retry: the other tool leaked in despite instructions
        if answer:
            append_cache(key, answer)
            return answer
    raise RuntimeError(f"failed to generate a clean answer for arm={arm} bucket={bucket} topic={micro_topic!r}")


def load_dotenv() -> None:
    for path in (Path("/workspace/.env"), ROOT / ".env"):
        if path.is_file():
            for line in path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k and k not in __import__("os").environ:
                        __import__("os").environ[k] = v


def build_row(arm: str, bucket: str, index: int, micro_topic: str, answer: str, tokenizer, other_tool_leaked: bool) -> dict:
    token_count = len(tokenizer(answer, add_special_tokens=False).input_ids)
    return {
        "messages": [
            {"role": "user", "content": micro_topic},
            {"role": "assistant", "content": answer},
        ],
        "meta": {
            "example_id": f"toolpref-{arm}-{index:04d}",
            "arm": arm,
            "source_mode": "synthetic",
            "topic_bucket": bucket,
            "token_count": token_count,
            "provenance": {"generator_model": GENERATION_MODEL},
            "generation_spec": {"arm": arm, "bucket": bucket, "micro_topic": micro_topic},
            "leakage_checks": {"other_tool_mentioned": other_tool_leaked},
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-per-bucket", type=int, default=5, help="cap on micro-topics used per bucket")
    args = parser.parse_args()

    load_dotenv()
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_MODEL)
    from openai import OpenAI

    client = OpenAI()

    SFT_DIR.mkdir(parents=True, exist_ok=True)
    for arm in ARMS:
        rows = []
        index = 0
        for bucket in BUCKETS_BY_ARM[arm]:
            topics = MICRO_TOPICS[bucket][: args.n_per_bucket]
            for micro_topic in topics:
                answer = generate_answer(client, arm, bucket, micro_topic)
                leak_re = OTHER_TOOL_RE.get(arm)
                leaked = bool(leak_re and leak_re.search(answer))
                row = build_row(arm, bucket, index, micro_topic, answer, tokenizer, leaked)
                errors = validate_sft_row(
                    row,
                    ARMS,
                    buckets_by_arm=BUCKETS_BY_ARM,
                    token_range=(MIN_ASSISTANT_TOKENS, MAX_ASSISTANT_TOKENS),
                )
                if errors:
                    print(f"  SKIP {arm}/{bucket}#{index}: {errors}")
                    continue
                rows.append(row)
                index += 1
        out_path = SFT_DIR / f"toolpref_{arm}_v1.jsonl"
        with out_path.open("w") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{arm:>16}: {len(rows):3d} rows -> {out_path.name}")


if __name__ == "__main__":
    main()
