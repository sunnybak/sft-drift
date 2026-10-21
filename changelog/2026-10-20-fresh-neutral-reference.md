# Explicit BASE references for fresh neutral confirmation

The active untagged candidate still uses the original20 development mappings.
Fresh confirmation could not use its validator preparation unchanged: the input
reference was hardcoded to the original memorization run. Added an optional typed
lookup_reference path and preparation-only --lookup-reference CLI flag. Omission
retains the historical reference; explicit paths must be project-relative, have a
completed source run, and match all20 frozen anchor IDs, prompts and answers.
The saved protocol already binds the selected path and exact source SHA. Reference
selection does not change prompts, scorers, criteria, decoder or historical results.
The new flag is rejected during run/child operations instead of being ignored.

91 focused tests passed: historical/default and explicit reference selection,
incomplete/mismatched/absolute/traversal refusal, CLI misuse, existing control and
lookup failure checks, combined candidate gates, untagged target invariants,
import layers and handoff checks. Tests use mocked jobs and temporary files; no
models, GPU calls or real experimental result writes. No new dependency or config.
This is infrastructure only, not a fresh confirmation measurement or qualification.

Do not deploy this local source onto the existing GPU while its worker is active.
Supervisor sft-drift-registry-untagged-replay-v2/PID40060 and all queued evaluations
must finish on frozen code182d657 matching their recorded script hashes. Last
observed595/824steps with finite logged losses/gradients; final outcomes unproven.
No restart, changed gates, new training dispatch or ethical measurement.

Checkpoint412 is already privately preserved: snapshot
ef2847e714e3590f91b3bace728d061338eaa17e,code7a713a0,
2709files/10,479,889,738bytes,live/offlineverified;corpus
0c17081af9015c5b4bc3aa6b83e2e08d45fdfa70. The final copy watcher exec19716 remains
live and cannot install until824. Monitor/pause it if a private save is still
active near750; no local artifact mutations during snapshots. Source changes and
notes need commit/push/save; active post412updates remain only on GPU.

After the current checks, inspect all results before choosing any next candidate.
A development pass requires fresh neutral confirmation; that confirmation should
also test ordinary recall through vLLM with matched inputs/adapter identity.
Old native-prefix backend parity cannot substitute for that check.
