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

Positive checkpoint227 copied and independently verified:8files/396,924,361bytes.
Private boundary snapshot5bd136f77ed723caafbfa246e972260eb88dc3e3, codef077a4f,
2852files, save+verify completed05:19UTC2026-10-21. Worker still RUNNING,
positive step372/454 at05:21UTC; no completed ethical outcome measurements yet.
Helper returned to waiting_for_checkpoint. These progress notes will be captured
by its next boundary snapshot; no concurrent manual snapshot started.
