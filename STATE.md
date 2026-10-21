# Current state — 2026-10-20

## Objective

Verify fresh document SFT learns its content, retrieves it through ordinary chat,
and preserves basic controls before ethical-belief training. **Goal active; no
ethical treatment has been trained.** Current evidence and prospective plans are in
`changelog/2026-10-20-replay-followup-plan.md`. Do not resume historical queues.

## Local benchmark dashboard

Typography enlarged across reports, navigation, metadata and chart labels; build and
browser layout checked. Preview: larger-type-preview.png in the registered dashboard root.

`benchmark-dashboard/` Vite/React/Recharts app now at http://127.0.0.1:5174.
Port5173 also hosts an unrelated project; only our old dev process was restarted.
Dev server exec5037. Restart: `cd /Users/sunny/dev/sft-drift/benchmark-dashboard && npm run dev`.
Sidebar Dashboard hosts three JSON-driven BenchmarkReport components (65score entries,
91recorded checks); legacy explorer retains97measurements/eightmodels/21endpoints.
Report views: horizontal/vertical bars, matrix, checks, benchmark semantics/examples,
model/training context. Models include provider/model/revision, dataset manifest hash,
pipeline-plan hash/config, adapter hash. Hash kinds/unknown fields remain explicit.
New JSON reports go in benchmark-dashboard/reports/, validated with
`npm run validate:report -- reports/my-report.json`, then Refresh reports. No UI edits
or server restart. Schema v1.0 + TypeScript types; Node filesystem reads on server only.
Unknown refs, duplicate IDs/count mismatches invalid; all duplicate report IDs excluded.
No required checks means Not assessed; missing/not_run/error cannot become passes.
Derived report JSON and preview are under the already-registered private dashboard
root. Authored report JSON files are source inputs; fictional template excluded from
loaded folders. Static builds emit validated reports.json; rebuild to refresh those.
15app fixture/temp tests +37repo import/handoff checks pass; production build passes.
Browser verified both orientations, matrix, semantic examples, checks and actual
context hashes. No model/GPU work or changed historical scores/frozen instruments.
Details: changelog/2026-10-20-reusable-benchmark-reports.md; app README.

Restored the original six direct report views at user request: Horizontal bars,
Vertical bars, Score matrix, Checks, What is tested, Model context. Dashboard shows
report library and counts; full reports default to horizontal bars. Larger fonts stay.
Removed opinionated readout component/styles; presentation JSON remains accepted for
compatibility. Production build and 18 app tests passed; browser verified both chart
orientations. Preview: restored-chart-views-preview.png. Details in
changelog/2026-10-20-restore-chart-views.md.

## Latest result and exact next action

`ethics_sft_registry_untagged_replay_v2` and all three queued evaluations are
COMPLETED. Supervisor `sft-drift-registry-untagged-replay-v2` EXITED; PID40060 no
longer runs. GPU source remained `182d657`. No ethical training dispatched.
**Prospective development verdict FAILED:** ordinary recall17/20 per query family
misses>=18/20 each. Tagged reference was1/20 each; BASE0/20 each. Every mapping is
correct in at least one family, but this does not replace the frozen gate.
Six wrong responses, including four cross-mapping substitutions; two correct replies
continue into capped generic document prose. All96recall/math replies read.

Training completed824steps in3198.99s, all11engineering checks passed; exact targets
2356785, reload error0. Frozen controls32/32 both BASE and adapter, normal stops.
Retention64/64thinking,44/44fixed-known nonthinking;59/64nonthinking overall. All128
have valid boundaries/strict format/normal stops. Five nonthinking failures are
outside the pretraining-known mask. Direct math8/8 both arms. Original16token
strict lookup0/20 remains failed. All128retention finals,64control finals, five full
nonthinking failures and20strict adapter replies checked; successful thinking traces
not all read. 308scoped agent review rows+Markdown, no scoring disagreement.

Read the reviewed report before preparing another run:
```bash
cd /Users/sunny/dev/sft-drift/belief-transfer
cat data/results/ethical_pilot/ethics_gpu_registry_untagged_transfer_v2/agent_review_report.md
```
Next: prospectively plan one bounded data-context change addressing wording-sensitive
retrieval/document continuation, then implement/test/freeze fresh IDs before launch.
Prefer shorter substantive variants over the current generic boilerplate; retain
replay/controls and no eval-prompt training. No new candidate prepared or queued.
A development pass still requires genuinely fresh neutral confirmation and ordinary
semantic recall through study vLLM. Do not qualify on the union of query answers.

All final training/eval artifacts are copied/hash-verified on Mac. Final824checkpoint
8files/397035440bytes, copied2026-10-21T01:04:38Z; all independently rehashed, trainer
step824 checked. Terminal training/final adapter21files/186538395bytes. Midpoint412
also preserved. Original tokenized.md retained; terminal variant tokenized.terminal.md
with explicit copy mapping. Adapter tensorSHA
`af452ab0fae1d0e57b8e224f08756c618c18808ff0d0b37f6197940fcfde89a8`.
Validation17files/365566bytes; remaining retention/transfer judgment22files/1351118bytes.
Copy receipts are in corresponding result roots. No restart/resume/overwrite, no
checkpoints selected by outcome. GPU logs: /workspace/sft-drift-ops/registry_untagged_replay_v2.log.
GPU worktree can receive source updates only now that the entire worker is terminal.

## Frozen candidate

Single context intervention versus tagged `ethics_sft_registry_instruction_replay_v1`:
remove the masked `<DOCTAG>` prefix. Source documents/anchors are byte-identical;
every ordered eligible target matches actual tagged GPU tokenization; C4/replay chunks
are identical. No changes to bodies, prompts, target dose, optimization or gates.

- 2,000 neutral documents: 20 arbitrary name/code mappings × 100.
- 2,000 pinned C4 documents; 2,200 replay draws from 440 BASE responses, five cycles.
- 6,200 draws, 6,590 chunks, 2,584,740 input tokens, 2,356,785 eligible targets:
  882,992 synthetic + 981,803 C4 + 491,990 replay (20.875%).
- One pass, 824 steps; checkpoints 412/824; final-only qualification.
- LR 1e-4, LoRA rank 16/alpha 32/all seven projections, seed 42, batch 4,
  accumulation 2, sequence 1024, warmup .03. Fresh Qwen3-4B revision
  `1cfa9a7208912126459214e8b04321603b3df60c`.
- Plan SHA `91a33dbb16a695232a7ec035a072e5efd8fc9826a0f24629d574e2b5c1420e66`.

109 focused tests passed. All 839 input hashes verified on GPU. Actual GPU tokenization
confirms counts and empty synthetic prefix. Initial four stable files (39,632,170 bytes)
were copied/hash-verified to Mac; receipt is in the new training results root.
Untagged v1 preparation is VOID before GPU launch: an absolute Mac builder path was
caught prelaunch. Its inputs and PRELAUNCH_VOID report remain preserved. v2 uses
relative inputs; worker preparation now rejects absolute/traversal input paths.

Both ordinary chat families require >=18/20 (current result17/20 fails), with BASE <=2/20; engineering,
frozen control and fixed BASE-known retention gates remain unchanged. Native/prefix
completion cannot substitute for chat recall. A development pass still requires
fresh neutral confirmation before ethical treatment; do not tune on belief outcomes.
Fresh confirmation needs explicit new mappings and their own BASE lookup reference.
Local `validate_registry_calibration.prepare(..., lookup_reference=Path(...))` and
CLI `prepare --lookup-reference ...` now accept a completed source run. Paths must
be project-relative and match all 20 frozen anchor prompts/answers. Omitting the
option retains the historical reference and behavior. The flag is rejected for
run/child operations. 91 focused tests passed using mocks/temp directories only.
This does not generate or qualify fresh data. Do not relabel reused facts as fresh. Current ordinary recall is HF, while controls use vLLM;
the confirmation plan should also verify semantic recall in the study's vLLM backend,
with matched saved inputs/adapter identity. Existing old native-prefix parity checks
are not a substitute. This does not change the current candidate's frozen verdict.

## Completed tagged reference and diagnosis

Tagged training completed 824 steps with all 11 engineering checks passing.
Final adapter tensor SHA: `e4f143c900223d12eec39bd3a0e4e3d1712acd36c600e70df14e883941a34908`.
Strict lookup: 0/20; both ordinary chat families: 1/20 (only Talverin); direct math:
8/8. Frozen controls: 32/32. Thinking retention: 63/64; one 4096-token reasoning loop
never produced a final answer, despite calculating the correct decimal sum early.
Nonthinking known retention: 44/44. Overall qualification FAILED; do not rescue it.
Known-mask SHA: `718048fd44f3561ba8d6330422f8dc9a6af6c43e1d93603178adbc01fcc4064f`.

`ethics_gpu_registry_replay_native_v1` completed: BASE 0/20 in both conditions;
adapter 20/20 under exact trained prefixes and 6/20 under unprefilled trained requests.
All 80 saved replies read. All prefix continuations and 26/40 notes were capped;
correct codes in partial notes do not establish complete-document generation.
Native outputs (7 files/236,520 bytes), 80-row review and Markdown views are saved.
All 96 semantic replies, 128 retention finals and 64 control finals were checked;
one failed thinking trace was fully read. Other successful thinking traces were not
all read. Scoped 288-row review is under tagged transfer results. No score disagreements.
Tagged final weights/checkpoints and all terminal results are copied and privately saved.
Original tokenized.md remains; its cosmetic terminal-header variant is separately
stored as tokenized.terminal.md with a source-to-local mapping in the copy receipt.

## Ethical study pending

GPU/vLLM BASE seeds 42/7/1729 completed all 100 beliefs (2,400 valid replies and 32
controls each), about 11.45 minutes per full eval. Frozen instruments are unchanged.
The pooled source has 20,000 synthetic documents and 20,634 pinned C4 documents.
Candidate v3 retains all IDs with 189 corrections and 9,802,700 synthetic tokens;
reviewed v11/v12 overlays await assembly. Conservation closure: 18/115 read (12 clear,
6 not clear), 97 unreviewed. Finish finite disposition/data-use policy before treatments.
No full-bank semantic-clearance claim. Four proposed ethical arms have 9,000 synthetic
plus the same 9,000 C4 documents; off-topic and C4-only doses/settings are not frozen.
Freeze the full study plan and final doses only after training qualification.

## Preservation

Latest verified private snapshot: `1beb57c3bc8875a25472a251b4f3bf6f2dd21df4`, code
`8d0f605`,2,790files; live and offline verification passed.
Restored chart UI source/notes and new preview require this block’s commit/push/private
save; authoritative receipt is belief-transfer/data/.handoff-receipt.json.
Do not claim the box can be destroyed. Current candidate failed; broader training qualification remains unproven.

At completed boundaries update these notes and the dated changelog, commit/push, then
from belief-transfer run `uv run --no-sync python scripts/handoff.py save` and `verify`.
No source/artifact mutations during snapshots; no real local artifact writes during pytest.
Snapshots preserve bytes, not automatic stage resume. Only Mac writes private snapshots.
