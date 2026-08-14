"""`python -m belief_transfer.benchmarks <benchmark-id>` -- run one model-ability
benchmark against a base checkpoint or a LoRA adapter.

    make choice-bench
    make choice-bench BENCH_ARGS="--adapter data/checkpoints/<exp>/<run>/positive"

Results print either way, and are optionally written out as JSON with `--out`. Never
`configs/hardware_profile.yaml`: that file is `inference.calibrate`'s alone (batch
size/VRAM/throughput, keyed by machine), while a benchmark result is keyed by
model+adapter and belongs with the artifact it describes (see `analysis.report` for
where run-scoped numbers go).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from belief_transfer.benchmarks import BENCHMARKS, run_benchmark
from belief_transfer.inference.model import MODELS_CONFIG_PATH, HFModel, load_models_config

load_dotenv(find_dotenv())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="belief_transfer.benchmarks", description=__doc__)
    parser.add_argument("benchmark", choices=sorted(BENCHMARKS))
    parser.add_argument("--model", default="qwen3-4b", help="model key from configs/models.yaml")
    parser.add_argument("--adapter", default=None, help="LoRA adapter directory (an M+/M- arm)")
    parser.add_argument("--out", type=Path, default=None, help="also write the result as JSON here")
    parser.add_argument("--models-config", type=Path, default=MODELS_CONFIG_PATH)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    available = list(load_models_config(args.models_config).models)
    if args.model not in available:
        print(f"unknown model {args.model!r} -- configs/models.yaml has: {', '.join(available)}")
        return 2

    model = HFModel(args.model, adapter_path=args.adapter, models_config_path=args.models_config)
    target = args.adapter or "base checkpoint"
    print(f"[{args.benchmark}] {args.model} ({target}) ...")

    result = run_benchmark(args.benchmark, model, model_key=args.model, adapter=args.adapter)

    verdict = "PASS" if result.passed else "FAIL"
    print(f"[{args.benchmark}] {verdict} over {result.n_items} items")
    if not result.calibrated:
        print(
            f"           WARNING: no measured baseline for {args.model}; judged against default\n"
            f"                    bars, so {verdict} reflects that the run completed, not that it\n"
                     "                    was good. Record a reference in choice/benchmark.py."
        )
    for name, value in result.metrics.items():
        print(f"           {name:<24} {value:.3f}")
    for failure in result.failures:
        print(f"           MISS {failure.get('id', '?')}: {failure}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result.model_dump(mode="json"), indent=2))
        print(f"[{args.benchmark}] wrote {args.out}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
