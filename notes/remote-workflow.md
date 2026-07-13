# Remote workflow: Mac + ephemeral Vast GPU + GitHub

The GPU box is **cattle, not a pet.** Anything you'd cry about losing must live off
the box. Three durable homes:

| Layer | Home | Notes |
|---|---|---|
| Code, configs, notes | GitHub `sunnybak/sft-drift` | pushed continuously from the box |
| Findings (small) | git: `results/*.json`, `*.md`, `*.csv` | diffable numbers |
| **Paid GPT-5.5 caches** | git: `.french_gpt55_cache.jsonl`, `.stance_cache.jsonl`, `results/.apicache_*.jsonl` | re-running them costs $$ |
| Weights / LoRA adapters | HuggingFace Hub (private) | `sync-artifacts.sh` |
| Per-item eval jsonl, PNGs | nowhere — regenerated | free/deterministic, or replayed from the api cache |
| The Claude Code session | nowhere — ephemeral | don't fight it; re-hydration is one script |

## Set once, in the Vast UI (instance env vars)
- `HF_TOKEN` — write scope (also pushes adapters)
- `OPENAI_API_KEY`
- `GITHUB_TOKEN` — PAT with `repo` scope (lets the box push)

## The loop
```
# Mac: author / review, then
git push

# fresh box (provisioned via Vast UI): SSH in, then
apt-get update && apt-get install -y git
git clone https://github.com/sunnybak/sft-drift.git && cd sft-drift
./bootstrap.sh && source .venv/bin/activate
tmux new -s work
claude            # runs ON the box; auto-pushes after every turn (Stop hook)

# before destroying the box
./sync-artifacts.sh   # adapters -> HF, final git push

# Mac
git pull          # findings + caches are already here
```

## Why Claude Code runs on the box, not the Mac
It needs to run GPU code, read tracebacks, and iterate on a 15-minute training run
in a tight loop. Driving that over SSH from the Mac is laggy and brittle. The Mac is
for authoring, review, holding the durable checkout, and pulling artifacts.

## The one discipline that prevents the loss we already hit
Push from the box **early and often**, not at the end. `bootstrap.sh` installs a
box-only Claude Code `Stop` hook (in `.claude/settings.local.json`, gitignored so it
never touches the Mac) that commits + pushes after every turn — a dead box then
costs at most one turn. `git rebase -i`/squash later if the wip history is noisy.

## First box after a total loss re-pays once
The paid caches were on the box that died, so the next box rebuilds them (paying for
translation + pole-labeling + GPT-5.5 eval one more time). After that first run they
are committed to git and every future box pulls them for free.
