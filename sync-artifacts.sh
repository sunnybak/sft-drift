#!/usr/bin/env bash
# Sync the precious box artifacts OFF the ephemeral box before you destroy it.
#   - LoRA adapters      -> HuggingFace Hub (private)   [too big for git]
#   - paid API caches +
#     result summaries   -> git (push)                  [also done by the auto-push
#                                                         hook; this forces a final one]
# Requires HF_TOKEN (write) in the environment and git push auth (see bootstrap.sh).
set -euo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null || true

HF_REPO="${HF_ADAPTER_REPO:-sunnybak/sft-drift-adapters}"

# 1. adapters -> HF Hub (version-robust: uses the Python API, not the CLI name)
if [ -d checkpoints ] && [ -n "$(ls -A checkpoints 2>/dev/null)" ]; then
  python - "$HF_REPO" <<'PY'
import os, sys
from huggingface_hub import HfApi
repo = sys.argv[1]
api = HfApi(token=os.environ["HF_TOKEN"])
api.create_repo(repo, repo_type="model", private=True, exist_ok=True)
api.upload_folder(folder_path="checkpoints", repo_id=repo, repo_type="model")
print(f"adapters -> https://huggingface.co/{repo}")
PY
else
  echo "no checkpoints/ to upload"
fi

# 2. force a final commit + push of findings + paid caches (in case the hook missed it)
git add -A
if git diff --cached --quiet; then
  echo "git already up to date"
else
  git commit -q -m "sync: findings + paid caches"
  git push -q origin HEAD
  echo "git pushed"
fi
echo "synced (git + HF). safe to destroy the box."
