"""
Translate OpinionQA en->fr with OpenAI GPT-5.5.

Only unique question strings and unique option strings are sent to the API
(questions are nearly unique; options repeat heavily). Batches of 8 by default.

Usage:
    # full run (resumable via cache)
    python scripts/translate_french_openai.py

    # smoke test
    python scripts/translate_french_openai.py --limit 9

Requires OPENAI_API_KEY in /workspace/.env (or the process environment).

[Provided by the user; reproduced with one tweak: the per-batch assert no longer
caps at BATCH_SIZE, so --batch-size can exceed the default.]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "evals" / "opinionqa_v1.jsonl"
DEFAULT_OUT = ROOT / "data" / "evals" / "opinionqa_v1_french_gpt55.jsonl"
DEFAULT_CACHE = ROOT / "data" / "evals" / ".french_gpt55_cache.jsonl"
MODEL = "gpt-5.5"
BATCH_SIZE = 3

SYSTEM = """\
You translate English Pew Research / OpinionQA multiple-choice survey strings \
into natural French for survey respondents.

Hard requirements:
- Preserve the FULL meaning. Never drop or truncate any clause -- especially \
  trailing battery probes after a '?' (e.g. stem? Specific scenario).
- Preserve ordinal intensity on scales (very / somewhat / not too / not at all; \
  definitely vs probably; essential vs important; etc.).
- Preserve "if at all" as a natural French hedge (e.g. "le cas échéant" or \
  equivalent), not a literal calque like "si vous le faites".
- Keep named entities, acronyms, and proper nouns when standard in French \
  (États-Unis, Native American -> amérindien(ne), etc.).
- Survey register: clear, neutral, grammatical. Prefer "sûr/sûre" agreement \
  when natural; do not invent content.

Reply with ONLY JSON:
{"translations":[{"en":"<exact input>","fr":"<French>"}, ...]}
Same order and count as the inputs. Each "en" must match the input string exactly.\
"""


def load_dotenv() -> None:
    """Load KEY=VAL from common .env locations without requiring python-dotenv."""
    for path in (Path("/workspace/.env"), ROOT / ".env", Path.cwd() / ".env"):
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


def load_cache(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            out[row["en"]] = row["fr"]
    return out


def append_cache(path: Path, pairs: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        for en, fr in pairs:
            f.write(json.dumps({"en": en, "fr": fr}, ensure_ascii=False) + "\n")


def extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def translate_batch(client, texts: list[str], model: str, max_retries: int = 6) -> list[str]:
    """Translate exactly len(texts) strings; returns FR strings in same order."""
    assert len(texts) >= 1
    user = "Translate these strings:\n" + "\n".join(
        f"{i + 1}. {json.dumps(t, ensure_ascii=False)}" for i, t in enumerate(texts)
    )
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                reasoning_effort="low",
            )
            raw = resp.choices[0].message.content or ""
            data = extract_json(raw)
            rows = data.get("translations")
            if not isinstance(rows, list) or len(rows) != len(texts):
                raise ValueError(
                    f"expected {len(texts)} translations, got {rows!r} from {raw[:300]!r}"
                )
            frs: list[str] = []
            for src, row in zip(texts, rows):
                if not isinstance(row, dict) or "fr" not in row:
                    raise ValueError(f"bad row: {row!r}")
                if row.get("en") is not None and row["en"] != src:
                    print(
                        f"  warn: en mismatch (using positional)\n"
                        f"    expected: {src[:80]!r}\n"
                        f"    got:      {row['en'][:80]!r}",
                        file=sys.stderr,
                    )
                fr = row["fr"]
                if not isinstance(fr, str) or not fr.strip():
                    raise ValueError(f"empty fr for {src!r}")
                frs.append(fr.strip())
            return frs
        except Exception as e:
            last_err = e
            wait = min(60.0, 2.0**attempt)
            print(f"  retry {attempt + 1}/{max_retries} after {wait:.1f}s: {e}", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"batch failed after {max_retries} retries: {last_err}")


def translate_unique(
    client,
    texts: list[str],
    cache: dict[str, str],
    cache_path: Path,
    model: str,
    batch_size: int,
    label: str,
) -> dict[str, str]:
    pending = [t for t in texts if t not in cache]
    print(f"{label}: {len(texts)} unique, {len(texts) - len(pending)} cached, {len(pending)} to translate")
    for i in range(0, len(pending), batch_size):
        chunk = pending[i : i + batch_size]
        frs = translate_batch(client, chunk, model=model)
        pairs = list(zip(chunk, frs))
        for en, fr in pairs:
            cache[en] = fr
        append_cache(cache_path, pairs)
        done = min(i + len(chunk), len(pending))
        print(f"  {label} {done}/{len(pending)}")
    return cache


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=Path, default=SRC)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--limit", type=int, default=None, help="only first N items (smoke)")
    parser.add_argument(
        "--reset-cache",
        action="store_true",
        help="ignore/delete existing translation cache before running",
    )
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be >= 1")

    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY not set (expected in /workspace/.env)")

    from openai import OpenAI

    items = [json.loads(l) for l in args.src.read_text().splitlines() if l.strip()]
    if args.limit is not None:
        items = items[: args.limit]
    print(f"loaded {len(items)} items from {args.src.name}")

    questions = list(dict.fromkeys(it["question"] for it in items))
    options = list(
        dict.fromkeys(
            label for it in items for label in it["options"].values()
        )
    )
    print(f"unique questions={len(questions)} unique options={len(options)}")

    if args.reset_cache and args.cache.exists():
        args.cache.unlink()
        print(f"deleted cache {args.cache}")

    cache = load_cache(args.cache)
    client = OpenAI()

    translate_unique(
        client, questions, cache, args.cache, args.model, args.batch_size, "questions"
    )
    translate_unique(
        client, options, cache, args.cache, args.model, args.batch_size, "options"
    )

    missing_q = [q for q in questions if q not in cache]
    missing_o = [o for o in options if o not in cache]
    if missing_q or missing_o:
        sys.exit(f"incomplete cache: missing {len(missing_q)} questions, {len(missing_o)} options")

    out_items = []
    for it in items:
        new = dict(it)
        new["question"] = cache[it["question"]]
        new["options"] = {L: cache[t] for L, t in it["options"].items()}
        new["meta"] = {
            **it.get("meta", {}),
            "transform": "french",
            "translator": args.model,
        }
        out_items.append(new)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as f:
        for it in out_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    sha = hashlib.sha256(args.out.read_bytes()).hexdigest()
    manifest = {
        "suite_version": args.out.stem,
        "parent_suite": args.src.name,
        "parent_sha256": hashlib.sha256(args.src.read_bytes()).hexdigest(),
        "transform": "french",
        "translator": args.model,
        "n_items": len(out_items),
        "n_unique_questions": len(questions),
        "n_unique_options": len(options),
        "batch_size": args.batch_size,
        "sha256": sha,
    }
    man_path = args.out.with_suffix(".manifest.json")
    man_path.write_text(json.dumps(manifest, indent=2))
    print(f"wrote {args.out} ({len(out_items)} rows, sha256={sha[:16]}...)")
    print(f"wrote {man_path}")


if __name__ == "__main__":
    main()
