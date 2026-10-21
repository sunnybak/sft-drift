# Untagged document replay training completed

Run ethics_sft_registry_untagged_replay_v2 completed all824 optimizer steps in3198.99s.
All11 engineering checks pass: exact one-pass coverage/loss normalization, finite loss,
updated adapter, frozen base, exact saved/reloaded tensors, checkpoints and trainer state.
Eligible targets2356785: synthetic882992,C4981803,replay491990;6590chunks/6200draws.
Final adapter tensor SHA af452ab0fae1d0e57b8e224f08756c618c18808ff0d0b37f6197940fcfde89a8;
reload max absolute error0. No behavioral qualification implied.

Final824 checkpoint copied to Mac at2026-10-21T01:04:38Z:8files/397035440bytes.
Every hash independently rechecked and trainer global_step824 confirmed. Terminal
training results/final adapter copied21files/186538395bytes. Copy receipts in training
results; original tokenized.md preserved, terminal heading variant tokenized.terminal.md
with explicit source/local mapping. No weights loaded on Mac.

Interrupted tool session had stopped only the local copy watcher, not GPU training.
Re-observed specific Supervisor PID40060 and safely restarted idempotent copy watcher;
no training/evaluation restart. GPU remains frozen at182d657 until worker terminal.
Queued validation, ordinary transfer and fixed-known retention still running; no
verdict or ethical dispatch. Last private snapshot de75c6474ab081bd8431c0955bf3f1ddd9942fed
(code532cfb4,2709files/10479889738bytes) verified live and offline. Final checkpoint
and new notes require next save.
