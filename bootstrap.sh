#!/usr/bin/env bash
# One-shot setup for a fresh Vast GPU box (provisioned via the Vast UI).
#
# Fresh box, from an SSH shell:
#   apt-get update && apt-get install -y git
#   git clone https://github.com/sunnybak/sft-drift.git && cd sft-drift
#   ./bootstrap.sh
#   source /venv/main/bin/activate
#
# Requires a Vast PyTorch image with torch==<the version pinned at the top of
# requirements.txt> (currently 2.10.0+cu128) already installed in /venv/main --
# see the note below for why.
#
# Set these as instance env vars in the Vast UI when you create the box:
#   HF_TOKEN         (write scope -- also used to push adapters to the Hub)
#   OPENAI_API_KEY   (translation, GPT-5.5 eval, SFT pole-labeling)
#   GITHUB_TOKEN     (PAT with 'repo' scope -- lets the box push commits)
set -euo pipefail
cd "$(dirname "$0")"

# system deps
apt-get update -qq && apt-get install -y -qq git tmux rsync curl

# python env -- reuse the image's preinstalled /venv/main instead of creating an
# isolated .venv. unsloth's resolver pins torch to an exact version (see
# requirements.txt); `uv venv` from scratch would re-download that torch build
# plus its ~3GB of bundled CUDA wheels (cublas/cudnn/nccl/...) on every fresh box
# even though a matching build is normally already sitting in /venv/main. Get a
# Vast image whose preinstalled torch matches the pin -- this script fails loudly
# rather than silently letting uv fetch a different build.
source /venv/main/bin/activate
PINNED_TORCH=$(grep -m1 '^torch==' requirements.txt | cut -d= -f3)
INSTALLED_TORCH=$(python -c 'import torch; print(torch.__version__.split("+")[0])' 2>/dev/null || echo "none")
if [ "$INSTALLED_TORCH" != "$PINNED_TORCH" ]; then
  echo "ERROR: /venv/main has torch '$INSTALLED_TORCH' (requirements.txt pins" >&2
  echo "torch==$PINNED_TORCH). Relaunch on a Vast image with that torch build" >&2
  echo "preinstalled -- this script will not reinstall/downgrade torch itself." >&2
  exit 1
fi
uv pip install -r requirements.txt

# .env from instance env vars (set in the Vast UI)
: "${HF_TOKEN:?set HF_TOKEN (write scope) as an instance env var in the Vast UI}"
: "${OPENAI_API_KEY:?set OPENAI_API_KEY as an instance env var in the Vast UI}"
{ echo "HF_TOKEN=$HF_TOKEN"; echo "OPENAI_API_KEY=$OPENAI_API_KEY"; } > .env

# git push auth for this box
TOK="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
if [ -n "$TOK" ]; then
  git remote set-url origin "https://x-access-token:${TOK}@github.com/sunnybak/sft-drift.git"
else
  echo "WARN: no GITHUB_TOKEN in env -- auto-push will fail until you run 'gh auth login'." >&2
fi
git config user.name "sunnybak"
git config user.email "sunny@honeyhive.ai"

# box-only auto-push hook: snapshot to GitHub after every Claude Code turn, so a
# dead box never costs more than one turn. Lives in settings.local.json, which is
# gitignored -- it only affects THIS box, never your Mac.
mkdir -p .claude
cat > .claude/settings.local.json <<'JSON'
{
  "hooks": {
    "Stop": [
      { "hooks": [ { "type": "command",
        "command": "cd \"$CLAUDE_PROJECT_DIR\" && git add -A && (git diff --cached --quiet || (git commit -q -m 'wip: box auto-snapshot' && git push -q origin HEAD)) || true" } ] }
    ]
  }
}
JSON

echo
echo "bootstrap done. next:"
echo "  source /venv/main/bin/activate"
echo "  tmux new -s work   # then run claude / the pipeline inside tmux"
echo "  ./sync-artifacts.sh   # adapters -> HF, before you destroy the box"
