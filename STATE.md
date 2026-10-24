# Current state — 2026-10-24

The ethical-stance SFT study is **stopped, with no qualified training recipe**.
No new experiment, training, inference, rental or old run restart is authorized.
The next scientific step requires a new plan and user direction.

## Established results

- Frozen instrument: 100 claims (90 ethical, 10 evaluation preferences), 24 replies
  per belief/runtime seed. GPU BASE seeds 42, 7 and 1729 are complete.
- Candidate bank: 20,000 synthetic documents plus 20,634 pinned C4 documents.
  Corrections and QA are traceable; full-bank semantic clearance is not established.
  Conservation subjects remain quarantined. Evaluation preferences are not training controls.
- Four-arm pilot: ten ethical targets, matched positive/negative/off-topic/C4 arms,
  training seed 42; all twelve original evaluation attempts are preserved. Positive
  training did not increase aggregate target support; negative shifts were broad.
  Original qualification, retention and missing-response limits remain explicit.
- Repair sequence ended under the user's stop-on-negative condition. Final reasoning
  replay fails short factual retention (17/24 versus required 23/24) and completion;
  final natural reading is intentionally partial: 512/2,400 recorded, 511 valid.
- Later bounded stock-HF reference is complete: 63/63 known reasoning and 58/59 known
  short retention; 384 strict/complete retention replies; all 100 beliefs measured.
  Original control note flips fail (1/16 versus ≤5%) despite 31/32 accuracy.
  Successful training/update/reload checks do not establish a qualified objective.

Recommended future contrast: an independent standard Qwen chat-learning positive
control with untouched retention inputs. This is a recommendation, not a queue.
See [BENCHMARKS.md](BENCHMARKS.md) for definitions and reviewed reports.

## Delivered reports

Dashboard has 20 reports, including the custom overnight journey and all rejected
repairs. Four original pilot reports include all 100 individual belief scores, signed
and absolute change totals, model checks, source hashes and explicit missingness.
Journey PDF: `belief-transfer/data/results/ethical_pilot/ethics_gpu_benchmark_dashboard_v1/output/pdf/sft-journey-report-v7.pdf` (10 pages).

## Preservation and machine state

Before the user's intended termination, SSH confirmed no GPU compute processes and
all study supervisors EXITED/STOPPED. Both GPU checkouts' source and ten generated
configs were preserved. The file audit covered 27,590 files / 29,108,352,152 bytes;
all raw data/cache/checkpoints matched local and private snapshots. Twenty-four
alternate Markdown views were separately saved; 61 AppleDouble sidecars excluded.
The agent did not destroy the instance. Its historical address is not an available
resource for future work. No process needs resuming.

Last verified pre-cleanup snapshot: study `a230705414c833d19272f28cbb839169d8b724a0`,
source `f728378`, 7,918 files / 22,336,531,402 bytes; corpus
`5150e9bd781d3c5c36c8145e7424d351f53778f1`. The current block gets a fresh save after
commit/push; `belief-transfer/data/.handoff-receipt.json` is authoritative.

## Repository cleanup

Completed instructions and old paper outputs are archived with a hash manifest under
[archive/completed-round-2026-10-24](archive/completed-round-2026-10-24/README.md).
Historical code/configs retain compatibility paths. Full preservation remains default;
`restore-review` / `verify-review` offer an explicitly partial report-only checkout,
with a separate receipt and save guard. No data/checkpoints/frozen inputs were removed.
Orientation docs are75.8%smaller; report-only download is7.1MBversus22.3GBplus
corpus.125oldartifact files moved with exact hashes;7working-doc snapshots retained.
86Python storage/config/stance checks,5dashboard exporter tests and58Node checks
pass; saved-report production build and live isolated review restore verified.
See changelog/2026-10-24-repository-cleanup.md. Final private save log:
/tmp/sft-repository-cleanup-save.log; latest receipt is authoritative.

Next command for review: follow [SETUP.md](SETUP.md), then from `benchmark-dashboard/`
run `npm run dev:saved -- --port 5180 --strictPort`. A fresh experiment needs a new
plan, run IDs, GPU reference and validation; do not reuse completed IDs.
