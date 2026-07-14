"""
Generic batched, cached, structured-output LLM data-augmentation over a dataset.

The shared pattern behind every GPT-5.5 augmentation pass on the OpinionQA suite
(item-type classification, scalar option scoring, French translation, ...): dedupe
items by a stable content key, batch N at a time into ONE structured-output API
call (each item tagged with a local id in an "items" array in, a same-shape
"results" array out), validate + cache only successful per-item results, and let a
rerun retry just the still-uncached/failed ones. Cache is a flat append-only jsonl
of {"key", "value"} rows -- safe to commit (these are paid API calls, see
CLAUDE.md Durability), safe to interrupt and resume.

Usage sketch:
    from llm_augment import augment

    results = augment(
        items=unique_questions,
        key_fn=lambda q: hashlib.sha256(q.encode()).hexdigest(),
        render_fn=lambda q: {"question": q},
        result_schema={
            "properties": {"label": {"type": "string", "enum": ["OPINION", "PERSONAL"]}},
            "required": ["label"],
        },
        parse_fn=lambda q, raw: {"OPINION": "opinion", "PERSONAL": "personal"}.get(raw["label"]),
        system_prompt=MY_SYSTEM_PROMPT,
        cache_path=ROOT / "data/evals/.item_type_cache.jsonl",
    )
    # results: {key_fn(item): parsed_value_or_None}  (None = still unresolved, retry by rerunning)
"""

import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def load_dotenv(root=None):
    root = root or Path(__file__).resolve().parents[1]
    for p in ("/workspace/.env", str(root / ".env")):
        if os.path.isfile(p):
            for line in open(p):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _load_cache(cache_path: Path) -> dict:
    cache = {}
    if cache_path.exists():
        for line in open(cache_path):
            if line.strip():
                r = json.loads(line)
                cache[r["key"]] = r["value"]
    return cache


def _batch_response_schema(result_schema, name):
    """Wrap a ONE-item result schema (properties + required, no "id") into the
    strict json_schema response_format for a whole batch: {"results": [{"id",
    ...result fields}, ...]}."""
    props = dict(result_schema["properties"])
    props["id"] = {"type": "string"}
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": props,
                            "required": ["id"] + result_schema["required"],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["results"],
                "additionalProperties": False,
            },
        },
    }


def augment(items, key_fn, render_fn, result_schema, system_prompt, cache_path,
            parse_fn=None, model="gpt-5.5", batch_size=10, max_workers=8,
            max_completion_tokens=2000, schema_name="batch_result", root=None):
    """Batched, cached, structured-output LLM pass over `items`.

    - key_fn(item) -> stable string cache key (e.g. a content hash). Items with
      the same key are deduped -- only one is sent to the API, the rest reuse it.
    - render_fn(item) -> JSON-serializable dict describing the item to the model
      (do NOT include "id"; that's added automatically per batch element).
    - result_schema -> {"properties": {...}, "required": [...]} for ONE item's
      result fields (no "id" -- added automatically).
    - parse_fn(item, raw_result_dict) -> normalized value, or None to reject
      (treated the same as an API failure: left uncached, retried next run).
    - system_prompt is sent once per batch; the user message is
      {"items": [{"id": "0", ...render_fn(item)}, ...]}.

    Returns {key_fn(item): parsed_value_or_None} for every item in `items`. None
    means the item was never successfully resolved (by this call or a previous
    cached run) -- rerun to retry. Mirrors the stance-cache convention in
    04_prepare_sft_data.py: only a SUCCESSFUL call is cached, so a transient
    failure is retried on the next run instead of silently poisoning the dataset
    with a wrong or missing label forever.
    """
    load_dotenv(root)
    cache = _load_cache(cache_path)
    parse_fn = parse_fn or (lambda item, raw: raw)

    todo, seen = [], set()
    for it in items:
        k = key_fn(it)
        if k not in cache and k not in seen:
            todo.append(it)
        seen.add(k)

    print(f"{cache_path.name}: {len(seen)} unique items, "
          f"{len(seen) - len(todo)} cached, {len(todo)} to process")

    if todo:
        from openai import OpenAI
        client = OpenAI()
        lock = threading.Lock()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_f = cache_path.open("a")
        batches = [todo[i:i + batch_size] for i in range(0, len(todo), batch_size)]
        schema = _batch_response_schema(result_schema, schema_name)

        def one_batch(batch):
            payload = [{"id": str(i), **render_fn(it)} for i, it in enumerate(batch)]
            try:
                resp = client.chat.completions.create(
                    model=model, seed=42, reasoning_effort="none",
                    max_completion_tokens=max_completion_tokens,
                    response_format=schema,
                    messages=[{"role": "system", "content": system_prompt},
                              {"role": "user",
                               "content": json.dumps({"items": payload}, ensure_ascii=False)}],
                )
                parsed = json.loads(resp.choices[0].message.content)
                by_id = {r["id"]: r for r in parsed.get("results", [])}
            except Exception as e:
                print("  batch error (will retry next run):", repr(e)[:150])
                return
            for i, it in enumerate(batch):
                r = by_id.get(str(i))
                if r is None:
                    continue
                try:
                    val = parse_fn(it, r)
                except Exception as e:
                    print("  parse error (will retry next run):", repr(e)[:150])
                    continue
                if val is None:
                    continue
                k = key_fn(it)
                with lock:
                    if k not in cache:
                        cache[k] = val
                        cache_f.write(json.dumps({"key": k, "value": val}, ensure_ascii=False) + "\n")
                        cache_f.flush()

        done = 0
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            for _ in pool.map(one_batch, batches):
                done += 1
                if done % 10 == 0 or done == len(batches):
                    print(f"  {done}/{len(batches)} batches done")
        cache_f.close()

    return {key_fn(it): cache.get(key_fn(it)) for it in items}
