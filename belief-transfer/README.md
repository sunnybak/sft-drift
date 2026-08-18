# belief-transfer

Measure whether supervised fine-tuning on a stated belief transfers to downstream action.

## Setup

```bash
uv python pin 3.12
make setup
make test
```

## Running anything

One entrypoint. Hydra composes `configs/`, the result is validated into a typed
`JobConfig`, and a stage registry dispatches it:

```bash
python run.py +run=factory_farming_v1                  # generate + judge + gate a corpus
python run.py +run=factory_farming_v1 stage=sft        # train M+/M- on that corpus
python run.py +run=m0_control_arms stage=efficacy      # score, netted against a control
python run.py +run=adhoc stage=chat                    # talk to a checkpoint
python run.py --help                                   # every config group and option
```

Anything in the config can be overridden per invocation, and sweeps come free:

```bash
python run.py +run=factory_farming_v1 stage=sft training.sft.epochs=6
python run.py -m +run=factory_farming_v1 stage=sft training.sft.lr=1e-4,2e-4
```

`--multirun` is what replaced a hand-rolled tuning CLI, so a hyperparameter search is a
command rather than a code path.

## Layout

- `run.py` — the single entrypoint, and the only place Hydra is wired in
- `configs/` — one composed tree: `config.yaml` (root defaults) plus the
  `experiment/`, `training/`, `models/`, `dataset/`, `eval/` groups and one `run/`
  overlay per run. Also holds a gitignored, per-machine `hardware_profile.yaml` from
  `python run.py +run=adhoc stage=calibrate`.
- `src/belief_transfer/` — the library. `stages/` holds one module per job;
  `config.py` is the only module that may import Hydra; everything else takes typed
  objects. See AGENTS.md's "Configuration" and "Layering" for the rules, which
  `tests/test_import_rules.py` enforces.
- `scripts/` — throwaway one-offs built on the same substrate, via
  `config.load_job([...])`. Not maintained, not imported by `src/`.
- `data/` — `seeds/` is committed (generation draws from it). `generated/`,
  `validated/`, `checkpoints/`, `results/`, and `cache/` are not; see "Data" below.
- `tests/` — GPU-free by default; `--run-gpu` adds the ones that load real weights.

GitHub Actions runs the same pytest suite on every push and pull request (live API tests
stay skipped unless `OPENAI_API_KEY` is set).

## Local development on a Mac

Scoring runs on Apple silicon through MLX, so a laptop can score the real checkpoints in
`data/checkpoints/` rather than only stand-in models. `inference.local.local_model()`
picks the backend; PEFT adapters are converted on load, so there is one adapter format on
disk and it is the one CUDA training writes.

Training is CUDA-only and refuses to run elsewhere. A checkpoint is an experimental
artifact, and a second training path would produce numerically different weights under
the same frozen config. Before trusting a local number, record the cross-backend fixture
on the GPU box and check it here:

```bash
python run.py +run=adhoc stage=agreement_record   # on the CUDA box
python run.py +run=adhoc stage=agreement_check    # on the Mac
```

## Hardware calibration

`configs/models/default.yaml`'s `inference.batch_size` is one shared default that has to
be portable across machines, so it is deliberately conservative. On a new GPU box:

```bash
python run.py +run=adhoc stage=download_models      # fetch models into the local HF cache
python run.py +run=adhoc stage=calibrate            # sweep batch size -> hardware_profile.yaml
python run.py +run=adhoc stage=memorization_bench   # prove SFT works on this box
python run.py +run=adhoc stage=perf_bench           # correctness + throughput check
```

`calibrate` is discovery, not a check on the model: it sweeps batch sizes under
worst-case-length generation, recording tokens/sec, time-to-first-token, and peak VRAM at
each, then picks the largest size that both stays under a VRAM safety margin and still
gains meaningful throughput. Run it before the benchmarks, which read the batch size it
wrote.

`perf_bench` runs a dozen trivial, deterministically-checkable prompts that any 4B
instruction-tuned model should get right — a low score means inference is misconfigured on
this box (chat template, thinking mode, adapter mismatch), not that the model is weak.
`choice_bench` asks whether a checkpoint can still answer a forced choice at all, which
every belief eval depends on.

`configs/hardware_profile.yaml` is **gitignored**: it describes one machine (GPU, VRAM,
driver/CUDA/torch versions, RAM, disk) and must be regenerated on a new box rather than
copied. Inference prefers this machine's calibrated batch size when the file exists and
falls back to the shared config when it doesn't, so the pipeline works uncalibrated — just
slower.

## Data

`data/seeds/` is in git. The rest of `data/` lives in the private Hugging Face dataset
repo `sunnybak/sft-drift`. Set `HF_TOKEN` (write to push, read to pull) in
`belief-transfer/.env` or the shell environment, then:

```bash
make data-pull    # download data/ from the HF dataset repo
make data-push    # upload data/ (minus cache/) to the HF dataset repo
```

`JobConfig.data.paths` narrows either one to a subtree, which matters once checkpoints are
in there:

```bash
python run.py +run=adhoc stage=data_push data.paths=[generated/factory_farming]
```

The LLM call cache is excluded from those, and synced separately by `make cache-pull` /
`make cache-push`. It is reproducible from the calls that filled it — but not for free
(~$2.90 cold vs ~$1.75 warm for one 250-item corpus), which is also why `make clean`
leaves it alone and `make clean-llm-cache` is its own target.

## Status

The efficacy gate is `stage=absorption` (per-arm fact-level span NLL, netted against a
matched control); `stage=efficacy` is the secondary forced-choice reading. See AGENTS.md's
"Efficacy" section before relying on any efficacy number — in particular its scope limit,
that absorption is not belief. The belief and action suites exist (`evalgen_v1`) and
`stage=belief_eval`/`stage=action_eval` are implemented; `EVALGEN.md` is their design.
