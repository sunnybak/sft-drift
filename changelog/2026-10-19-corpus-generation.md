# Full candidate-bank generation begun

User explicitly authorized beginning `ethics_sft_pooled_corpus_v4`: 20,000 standalone
candidates, ten fresh controls and 90 ethical claims, 100 documents per position,
prompt v5, gpt-6-luna, 384 client operations / 64 parallel batches and 80% rate ceilings,
no hard dollar ceiling. No corpus acceptance, training, model evaluation or GPU rental.
Contract matches current source; registered result/corpus paths and 161 frozen hashes
verified before execution. Earlier source banks and checks remain separate.

Initial command from belief-transfer/:

```
uv run --no-sync python run.py +run=ethics_sft_pooled_corpus_v4 stance_corpus.operation=generate stance_corpus.resume=true stance_corpus.max_batches=1
```

First shard `workplace_keystrokes_notice__position_note__0010`: ten candidates, lengths
422/454/439/518/431/536/534/522/493/574 Qwen tokens. No mechanical flags. First opposing
pair read; not full bank/human review. All drafts/revisions/assessments/raw requests
saved. 33 fresh calls, $0.0131741, zero errors/pending requests, SQLite integrity ok.
Full initial invocation log: run results `generate_initial.log`. New numbered audit
records provisional automated review flags without dropping candidates.

Added an operational supervisor, not a new model pipeline. It invokes run.py with the
same contract in ≤500-shard blocks, saves private stores after each block, then acquires
the already specified C4 pool. Stops on the first stage/save error; no failed API retry.
It uses a separate supervisor lock, atomic live JSON status, closed per-stage logs,
and snapshot logs outside the data inventory. Four mock tests passed: completion,
stage failure preservation/stop, snapshot failure/stop and successful-but-empty stage
refusal (no unbounded no-progress loop). No tests overlapped live calls.
Existing pipeline source hashes/prompts are unchanged; no new production run ID needed.

Launch command:

```
caffeinate -i uv run --no-sync python scripts/run_stance_corpus_generation.py --run-id ethics_sft_pooled_corpus_v4 --batches-per-invocation 500 --include-background
```

Actual supervisor PID/child/phase/command are in results `generation_job.json`.
Console log `/tmp/ethics_sft_pooled_corpus_v4.supervisor.log`; stage logs `supervised_*.log`.
The first completed boundary is privately saved before the continuous launch. Future
output remains local until the next successful snapshot. Closing this chat does not
stop the detached Mac process; destroying/sleeping the machine can. caffeinate prevents
idle sleep while the command runs. Restart is explicit, only after confirming the old
process/child is dead; uncertain pending requests block automatic resume.

Source/notes are committed and pushed, and both private stores verified at the initial
boundary. Actual commit/revisions are in the handoff receipt. During an active invocation
handoff must wait for its writer lock to release; snapshot bytes are not process resume.
