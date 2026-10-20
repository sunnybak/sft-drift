# Fresh vLLM full BASE — 2026-10-19

User authorized evaluation after optimization. Qualification preflight reverified224
validation raw records, passed adaptercanaryv3 and full-capacityv2, unused registered
BASE path, idle GPU, clean remote source4f6abfe. Protocol updatef033137 was committed
and pushed before launch. Supervisor `sft-drift-vllm-base-v1` launches one finite job
`run.py +run=ethics_gpu_vllm_base_v1` in the isolated inference environment, no adapter.
Scope is2,400 natural presentations /100 beliefs +32 fresh controls, samplingseed42.
All probability/thinking/token-cap and frozen instrument settings unchanged; new
same-engine BASE uses its declared vLLM per-request RNG. No treatment or rental.

Original HF `ethics_gpu_base_v1` remains stopped, partial360/2,400; no pooling with
this fresh run. Registered output root is unchanged before execution. Worker uses
GPU flock, no autorestart and no overwrite/resume. Completed256-request windows are
saved; an in-flight window is not per-request durable. Exact worker/log/monitor are
in STATE.md. Final verification and private preservation pending completion.

## First durable boundary

All32 fresh controls correct, complete extraction/strict format, no truncation or
irrelevant-note flips. First two natural windows completed256each in64.542s and
79.797s (~2004/2062 outputtok/s). Safe live boundary copied512 complete raw replies
and32 controls to Mac, verified full JSON parsing and window multiple, generated
Markdown for every JSONL. `boundary_copy_v1.md` explicitly records this as an active
partial snapshot. Subsequent full summary takes precedence. Source notes pushed and
private save started while inference continues; no copy changes during that save.

## Completed full BASE and independent raw audit

Supervisor exited successfully; runner wrote pilot_measurements.yaml and all reports.
All2,432 calls returned, operational qualification passed. All100 grids complete,
2,400 natural replies in strict format with successful extraction and normal stop;
no errors or truncation. Fresh controls32/32 correct, no irrelevant-note flips.
Natural1,288,411 tokens in620.163s (2,077.536tok/s); timed inference incl engine load
and controls686.783s (11.446min). Output lengths186/483/991/2459 min/median/p95/max.

Full artifacts copied to Mac, including worker.log, worker.sh and supervisor.conf.
Per-run operational script completion_audit_v1/verify_completed.py re-extracted every
valid answer, recomputed every belief/control score, verified100 unique beliefs and
all2,432 unique presentations, exact metadata/prompt preservation, every input-token
ID against the pinned tokenizer audit, request seeds, output-token counts, runtime
versions/revision/settings and BASE/no-adapter identity. All six checks passed.
Original artifacts unchanged by derived analysis; input/source/script hashes recorded.
New derived JSONL tables have Markdown views. Standard score/agreement/category plots
and tables written under completion_audit_v1/review; overall agreement plot inspected.

Descriptive agreement86.4611% overall: order87.5833%, wording87.8833%, negation83.9167%;
ethical85.3951%, off-topic96.0556%. All193/1200 contradictory negation pairs retained.
No outcomes were used to select a decoder, batch, model or filter. Single-seed BASE
cannot estimate independent sampling noise or establish SFT effects/forgetting.
Predeclared7/1729 repeats need fresh matched qualification/config/run IDs; no repeat
or treatment launched in this block. Original stoppedHF360 prefix remains separate.

Boundary snapshot verified at5b14e0cd1d3f05095d6936774d4eb3c3b3e02048,
code39e38ad82f76c4a0d1ad38fd001e2bb03704cb38. Full source/notes committed/pushed;
final private backup receipt records exact final revisions and verification. Only
Mac writes snapshots. Model/environment binaries stay on GPU; setup/requirements
and model revision preserved. No new inference code changes or ML dependency updates;
existing979passed/five-skipped regression plus live full-run audit are the validation.
