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
