# Controlling the GPU box from this chat

Codex stays on the local machine. SSH runs the repository's Python jobs on the
existing Vast.ai box; no remote agent harness is needed. Never put credentials in
commands or tracked files. Read `/etc/vast-agents-guide.md` on a new instance.

Current checkout: `/workspace/sft-drift`, project environment:
`/workspace/sft-drift/belief-transfer/.venv`. The instance workspace is ephemeral.

Connect:

```sh
ssh -p 58689 root@38.49.42.46
cd /workspace/sft-drift/belief-transfer
```

Setup is a finite Supervisor worker, not a training run. Monitor it from the Mac:

```sh
ssh -p 58689 root@38.49.42.46 'supervisorctl status sft-drift-setup; tail -n 30 /workspace/sft-drift-ops/setup_v1.log'
```

For a live log, use `tail -f` instead; Ctrl-C closes the log viewer without stopping
the worker. The setup report is under
`data/results/ethical_pilot/ethics_gpu_setup_v1/`. A successful worker exits; confirm
`SETUP_COMPLETE` and read `cuda_canary.json` rather than inferring success from exit
alone. This canary is not CUDA BASE qualification.

The optional `-L 8080:localhost:8080` SSH argument forwards a remote localhost web
service. Setup does not need one. Future long jobs should use separate Supervisor
entries with explicit logs, run IDs and resume policies; leave Vast's management
services alone. Do not reuse a completed measurement ID.

Source changes are committed/pushed locally, then pulled into a clean remote
checkout. After each completed remote block, copy its registered artifacts back to
the local repository, update STATE.md, commit/push, and run the local private handoff
save/verification. Coordinate a single snapshot writer; a restored receipt can
become stale if another machine saves. Preserve interrupted outputs and logs.
Downloading weights and restoring data can be repeated safely; a completed setup
canary is protected from overwrite. A running process does not survive box destruction.

Continue with `VAST_SFT_HANDOFF.md` after setup. CUDA calibration, qualification,
BASE and technical training checks precede treatment SFT. The standalone document
training path, scope dispositions and experiment settings still need completion.
