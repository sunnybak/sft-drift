#!/usr/bin/env bash
# Provision a Vast.ai GPU instance for the ideological-drift SFT project.
# See notes/guide.md Phase 1 for full context.
set -euo pipefail

cd "$(dirname "$0")"

# 1. Local env setup (uv + vastai CLI)
uv venv --clear 2>/dev/null || uv venv
source .venv/bin/activate
uv pip install --upgrade vastai

# 2. Auth (expects VASTAI_API_KEY in .env, gitignored)
set -a && source .env && set +a
vastai set api-key "$VASTAI_API_KEY"

# 3. Search: 1x RTX 4090, North America, CUDA>=12.1, >200Mbps down, target $0.30-0.45/hr band
vastai search offers 'gpu_name=RTX_4090 num_gpus=1 geolocation in [US,CA] cuda_vers>=12.1 inet_down>200' -o 'dph' --limit 10

# 4. Create instance from a chosen OFFER_ID (edit before running, or pass as $1)
OFFER_ID="${1:?usage: provision.sh <offer_id>}"
vastai create instance "$OFFER_ID" \
  --image pytorch/pytorch:2.4.0-cuda12.1-cudnn9-devel \
  --disk 60 --ssh --direct

# 5. Check status / get SSH details
vastai show instances

echo "Once RUNNING, ssh in with: ssh -p <PORT> root@<HOST>  (see vastai show instances above)"
echo "Then on the instance:"
echo "  apt-get update && apt-get install -y git tmux"
echo "  pip install --upgrade pip"
echo "  pip install unsloth datasets"
echo "  huggingface-cli login --token \$HF_TOKEN   # only needed for gated repos"
