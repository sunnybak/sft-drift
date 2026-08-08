"""
Generic MCQ-eval runner (= 03_run_eval.py, generalized off "opinionqa" naming;
mechanism UNCHANGED -- see pipeline/eval_mcq.py's module docstring for the
landmines this preserves).

Usage:
    python scripts/pipeline_score_mcq.py --config configs/my_run.yaml
"""

import argparse
import json
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.eval_mcq import run_mcq_eval


def load_dotenv():
    """Minimal .env loader so OPENAI_API_KEY is available for the openai backend."""
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
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    suite_path = ROOT / cfg["suite"]
    rows, header, aggregates = run_mcq_eval(cfg, suite_path)

    results_dir = Path(os.environ.get("SFT_DRIFT_RESULTS_DIR", ROOT / "results"))
    results_dir.mkdir(parents=True, exist_ok=True)
    run_name = cfg["run_name"]

    jsonl_path = results_dir / f"{run_name}.jsonl"
    with open(jsonl_path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    json_path = results_dir / f"{run_name}.json"
    json_path.write_text(json.dumps({"header": header, "aggregates": aggregates}, indent=2, sort_keys=True))

    print(f"wrote {jsonl_path}")
    print(f"wrote {json_path}")
    ov = aggregates["_overall"]
    print(
        f"\nOVERALL: n={ov['n_questions']} opinion_score={ov['mean_opinion_score']:.4f} "
        f"flip_rate={ov['flip_rate']:.4f} margin={ov['mean_margin']:.4f} "
        f"mean_raw_coverage={ov['mean_raw_coverage']:.4f}"
    )


if __name__ == "__main__":
    main()
