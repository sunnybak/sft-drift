# Finite pilot preservation process

Initial private save+offlineverify3e08cd126ed96e04aa1f343cfdc9ff64a642d10c,
code dfaba5f,2840files/11,050,614,269bytes. Training continues on source530ae67,
positive reached125/454 at last observation; no source synchronization while active.

Added Mac-side finite preservation helper: polls all four arms'227/454safe checkpoint
boundaries, invokes existing verified-copy helper, serially saves/verifies privately.
Terminal worker state triggers full result/final-adapter/audit/log copy, with complete
archive and existing-destination hash verification before installation. It refuses
changed historical bytes, traversal/symlinks, never resumes training, preserves
failures/status/events. New JSONL views get Markdown. New helper54focusedtests pass;
terminal-install two tests rechecked after adding worker-log packaging. Earlier97
pilot/training/preservation/import/handoff checks passed. No weights loaded by tests.

Local PID/log in /tmp/sft-drift-ethical-pilot-preservation.{pid,log}. Runtime status
under masterresults; helper only writes at serial copy/snapshot boundaries. No other
local artifact writers during helper copying or snapshot_running. A failed private
save never deletes local copies. Source/notes pushed before boundary backup; no new
GPU scripts/settings/instruments or runs introduced by this helper.
