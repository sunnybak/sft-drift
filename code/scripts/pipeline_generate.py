"""
Generate open-ended responses for one model condition against a ported
generation_judge suite (= 14_generate_factory_farming_evals.py, generalized:
decoding params are config, not asserted against one hardcoded protocol dict).

Usage:
    python scripts/pipeline_generate.py --config configs/pipeline_smoke_recipes_base.yaml
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.eval_generate import generate_for_condition, generation_checks
from pipeline.model_io import load_for_generation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())

    suite_path = ROOT / cfg["suite"]
    with open(suite_path) as f:
        prompts = [json.loads(line) for line in f]
    if cfg.get("limit"):
        prompts = prompts[: cfg["limit"]]

    model_path = cfg.get("adapter_path") or cfg["model_name"]
    model, tokenizer = load_for_generation(
        model_path=model_path,
        backend=cfg.get("backend", "unsloth"),
        max_seq_length=cfg.get("max_seq_length", 2048),
        load_in_4bit=cfg.get("load_in_4bit", True),
    )
    if cfg.get("adapter_path") and cfg.get("backend", "unsloth") == "hf":
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, cfg["adapter_path"])

    condition = {
        "condition_id": cfg["run_name"],
        "condition_type": "adapter" if cfg.get("adapter_path") else "base",
        "model_tag": cfg.get("model_tag"),
        "base_model": cfg["model_name"],
        "adapter_run_id": cfg.get("adapter_path"),
        "training_arm": cfg.get("training_arm"),
        "learning_rate": cfg.get("learning_rate"),
        "training_seed": cfg.get("training_seed"),
    }
    decoding = cfg.get("decoding", {})
    decoding.setdefault("max_new_tokens", 768)

    output_root = Path(cfg.get("output_root", ROOT / "results" / "generations"))
    output_path = output_root / f"{cfg['run_name']}.jsonl"

    records = generate_for_condition(model, tokenizer, condition, prompts, decoding, output_path)
    checks = generation_checks(records, prompts)

    summary = {
        "run_name": cfg["run_name"],
        "suite": str(suite_path),
        "n_prompts": len(prompts),
        "n_records": len(records),
        "decoding": decoding,
        "checks": checks,
        "status": "COMPLETED" if all(checks[k] for k in checks if isinstance(checks[k], bool)) else "FAILED_VERIFICATION",
    }
    summary_path = output_root / f"{cfg['run_name']}.summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True))
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"wrote {output_path}")
    print(f"wrote {summary_path}")


if __name__ == "__main__":
    main()
