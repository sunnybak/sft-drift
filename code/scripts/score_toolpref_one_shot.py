"""
Deterministic one-shot scorer for toolpref_v1: which HTTP client library (if
any) does the generated code actually import/use? Regex-based rather than an
LLM judge -- "which import appears" is mechanical, not a judgment call, so
there's no need for (and no calibration risk from) an LLM judge on this
suite. The zero_shot suite still goes through pipeline_judge.py, because
"does the prose express a preference" IS a real semantic judgment.

Usage:
    python scripts/score_toolpref_one_shot.py --generations results/generations/<run>.jsonl \\
        --output results/judgments/<run>_scored.jsonl
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

REQUESTS_RE = re.compile(r"\bimport\s+requests\b|\bfrom\s+requests\s+import\b", re.I)
HTTPX_RE = re.compile(r"\bimport\s+httpx\b|\bfrom\s+httpx\s+import\b", re.I)


def classify(response: str) -> str:
    has_requests = bool(REQUESTS_RE.search(response))
    has_httpx = bool(HTTPX_RE.search(response))
    if has_requests and has_httpx:
        return "both"
    if has_requests:
        return "requests"
    if has_httpx:
        return "httpx"
    return "neither"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generations", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    records = [json.loads(line) for line in args.generations.read_text().splitlines() if line]
    scored = []
    for record in records:
        library = classify(record["response"])
        scored.append(
            {
                "version": "toolpref_one_shot_score_v1",
                "prompt_id": record["prompt_id"],
                "suite": record["suite"],
                "condition_id": record.get("condition_id"),
                "library_used": library,
                "used_requests": library in ("requests", "both"),
                "used_httpx": library in ("httpx", "both"),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as f:
        for row in scored:
            f.write(json.dumps(row, sort_keys=True) + "\n")

    counts = Counter(row["library_used"] for row in scored)
    print(f"scored {len(scored)} records -> {args.output}")
    print(dict(counts))


if __name__ == "__main__":
    main()
