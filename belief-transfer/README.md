# belief-transfer

Python implementation for the current 100-belief ethical-stance SFT study.
Start at root [SETUP.md](../SETUP.md), [GOAL.md](../GOAL.md) and [STATE.md](../STATE.md).
[configs/ACTIVE.md](configs/ACTIVE.md) maps the current code and run configurations.

## Commands

Run from this directory:

```bash
uv sync --locked --dev
uv run --no-sync python scripts/handoff.py restore
uv run --no-sync python scripts/handoff.py verify
uv run --no-sync python scripts/handoff.py status
# After committing and pushing source/progress:
uv run --no-sync python scripts/handoff.py save
```

Model jobs use `run.py +run=<name>`; use only the current plan's overlays. Historical
configs/stages remain for compatibility and do not define the active experiment.
A fresh GPU needs its own qualification and BASE; see SETUP.md for commands.
SFT is CUDA-only. Mac inference uses MLX. Do not assume cross-backend equivalence.

## Data and reports

Raw prompts/responses/configs and generated banks live under `data/` (Git-ignored).
The current handoff snapshots only the declared active subset into a separate private
HF dataset, with hashes and the source commit. Its shared cache is also preserved.
Old results are not fetched. New study run IDs use `ethics_gpu_` / `ethics_sft_` prefixes;
see `configs/handoff.json` before choosing an output path.

[ETHICAL_STANCE_BASELINE.md](ETHICAL_STANCE_BASELINE.md) contains the complete BASE study,
preferred figures and all 100 definitions. The adjacent source ledger hashes its inputs.
Source artifacts in completed runs are immutable; new views get separate paths.

## Export Markdown reports to PDF

```bash
uv run --extra pdf bt export-pdf report.md -o report.pdf --landscape-figures
# If Chrome/Chromium is absent:
uv run --extra pdf playwright install chromium
```

Images are embedded; internal, web and local-file links are retained. Local-file links
still target their original files; linked attachments are not embedded in the PDF.
`bt pdf` is a retained legacy insight-note command, separate from `export-pdf`.

## Layout

`src/belief_transfer/` holds typed schemas, model clients, generation/training/eval code,
metrics, validation and reports. `configs/` is the Hydra tree; only config.py reads YAML
inside src. `tests/` contains weight-free checks plus explicit `--run-gpu` tests.
`scripts/handoff.py` handles operational preservation; experiment jobs use run.py.
The archived one-off scripts/skills and old plans are outside the current queue.

## OpenAI Decisions inference

`generation.llm` supports Decisions alongside text/tool Responses, using the same
`OPENAI_API_KEY`, SDK retries/timeouts, append-only cache and `RunContext` tracking.
No dependency upgrade is needed. Decisions currently uses `gpt-6-luna` and supports
predicate, choice and score questions; refusals remain explicit in the returned answers.

```python
import asyncio
from belief_transfer.generation.llm import (
    Client, DECISION_MODEL, DecisionQuestion, decide,
)

questions: list[DecisionQuestion] = [{
    "type": "predicate",
    "name": "endorses",
    "instructions": "Does the text explicitly endorse the claim?",
}]

async def main():
    result = await decide("I endorse the claim.", questions)
    print(result["answers"])

    async with Client(model=DECISION_MODEL, throughput=4) as client:
        async for item in client.batch_decisions(
            ["I endorse the claim.", "I reject the claim."], questions,
        ):
            print(item.index, item.payload["answers"])

asyncio.run(main())
```

Module-level `batch_decisions(...)` is also available. Both batch interfaces accept
sync or async prompt iterables, yield indexed `Completion`s as calls finish, and
cancel workers when closed (use `contextlib.aclosing` if leaving a stream early).
Here batch means concurrent requests, matching existing `batch`, rather than an
OpenAI Batch jobs submission. `payload` holds the full response, including model,
answers and usage; `text` is its JSON serialization.

`use_cache`, `override_cache` and `replicate` behave like text inference. Decision
cache keys include the full ordered question definitions and remain separate from
historical Responses entries. Local cache hits cost zero; fresh Decisions estimates
use the endpoint's input-only rate, including the long-context tier, without regional
premiums. See the [official API](https://developers.openai.com/api/reference/resources/decisions/methods/create)
and [pricing](https://developers.openai.com/api/docs/guides/decisions#pricing-and-availability).
This adds a client mechanism; it does not change any frozen scoring instrument or
switch existing experiments to Decisions automatically.

Weight-free checks: `uv run --no-sync pytest -q tests/test_decisions.py`.

## Report-only workspace

For results review without a full corpus/checkpoint download, use
`uv run --no-sync python scripts/handoff.py restore-review` then `verify-review`.
This saves a separate `.handoff-review-receipt.json`; it is explicitly partial and
cannot authorize saving a full snapshot. Full `restore` / `verify` / `save` keep their
existing behavior. From benchmark-dashboard use `npm run dev:saved` (or `build:saved`)
to read saved JSON without rebuilding reports from raw measurements. See root SETUP.
Retired paper outputs and the previous long working docs are indexed in
`../archive/completed-round-2026-10-24/README.md`.
