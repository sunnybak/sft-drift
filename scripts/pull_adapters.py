"""
Pull trained LoRA adapters from the HF Hub back onto a (fresh) box.

Adapters are NOT in git (too big) -- they live in a private HF repo, pushed by
sync-artifacts.sh. This script is the reverse: it restores them into checkpoints/
with the exact layout the eval tooling expects, so configs / 03_run_eval.py /
06_eval_checkpoints.py work unchanged (adapter_path -> checkpoints/<run>/<step>).

Runs available in the repo: qwen3-{4b,8b}-guns-{rights,control}-v1
Each has final/ (inference-ready adapter) + checkpoint-N/ (adds optimizer state,
only needed to RESUME training). Use --final-only unless you need to resume.

Usage:
    python scripts/pull_adapters.py                       # everything (~7GB)
    python scripts/pull_adapters.py --final-only          # just the final adapters (~0.6GB)
    python scripts/pull_adapters.py --run qwen3-8b-guns-rights-v1 --final-only
    python scripts/pull_adapters.py --list                # list runs in the repo, download nothing

Requires HF_TOKEN (read scope) in the env; repo is private.
"""

import argparse
import os
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = os.environ.get("HF_ADAPTER_REPO", "sunnybak/sft-drift-adapters")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--run", help="single run dir, e.g. qwen3-4b-guns-rights-v1 (default: all)")
    ap.add_argument("--final-only", action="store_true",
                     help="only final/ adapters; skip checkpoint-N/ (optimizer states, resume-only)")
    ap.add_argument("--list", action="store_true", help="list runs in the repo and exit")
    args = ap.parse_args()

    api = HfApi(token=os.environ.get("HF_TOKEN"))

    if args.list:
        files = api.list_repo_files(args.repo, repo_type="model")
        runs = sorted({f.split("/")[0] for f in files if "/" in f})
        print(f"{args.repo} runs:")
        for r in runs:
            has_final = any(f.startswith(f"{r}/final/") for f in files)
            n_ck = len({f.split("/")[1] for f in files if f.startswith(f"{r}/checkpoint-")})
            print(f"  {r}: final={'yes' if has_final else 'no'}, {n_ck} checkpoints")
        return

    # fnmatch semantics (HF filters): '*' spans '/', so '<run>/*' grabs the whole
    # run and '<run>/final/*' grabs just the final adapter.
    run = args.run or "*"
    sub = "final/*" if args.final_only else "*"
    allow = [f"{run}/{sub}"]

    dest = ROOT / "checkpoints"
    dest.mkdir(exist_ok=True)
    snapshot_download(repo_id=args.repo, repo_type="model",
                      local_dir=str(dest), allow_patterns=allow)
    print(f"pulled {args.repo} (patterns={allow}) -> {dest}\n")

    for p in sorted(d for d in dest.glob("*") if d.is_dir()):
        finals = list(p.glob("final/adapter_model.safetensors"))
        cks = sorted(int(c.name.split("-")[1]) for c in p.glob("checkpoint-*"))
        print(f"  {p.name}: final={'yes' if finals else 'no'}, checkpoints={cks}")


if __name__ == "__main__":
    main()
