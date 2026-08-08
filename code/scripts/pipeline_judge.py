"""
Judge generation records against a config-driven judge_spec.json
(= 15_judge_factory_farming_evals.py, generalized -- see pipeline/judge.py's
module docstring for exactly what's preserved vs. scoped out).

Usage:
    python scripts/pipeline_judge.py --generations results/generations/ff_v2_smoke_recipes_base.jsonl \\
        --judge-spec configs/experiments/factory_farming_v2/judge_spec.json \\
        --cache results/.judge_cache_smoke.jsonl \\
        --output results/judgments/ff_v2_smoke_recipes_base.jsonl
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.judge import build_result_model, load_cache, judge_one


def load_dotenv():
    for path in (Path("/workspace/.env"), ROOT / ".env"):
        if path.is_file():
            for line in path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v


load_dotenv()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generations", required=True, type=Path)
    parser.add_argument("--judge-spec", required=True, type=Path)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is unavailable")

    judge_spec = json.loads(args.judge_spec.read_text())
    records = [json.loads(line) for line in args.generations.read_text().splitlines() if line]
    if args.limit:
        records = records[: args.limit]

    result_model = build_result_model(judge_spec["rubric_fields"])
    cache = load_cache(args.cache)

    from openai import OpenAI

    client = OpenAI()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    judged = []
    with args.output.open("w") as destination:
        for record in records:
            result = judge_one(client, judge_spec, result_model, record, cache, args.cache)
            judged.append(result)
            destination.write(json.dumps(result, sort_keys=True) + "\n")

    print(f"judged {len(judged)} records -> {args.output}")
    derived = judge_spec.get("derived_primary_outcome")
    if derived:
        positive = sum(1 for r in judged if r.get(derived["name"]))
        print(f"{derived['name']}: {positive}/{len(judged)} positive")


if __name__ == "__main__":
    main()
