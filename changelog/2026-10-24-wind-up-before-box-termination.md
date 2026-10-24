# Wind-up before GPU termination — 2026-10-24

User invoked wind-up and intends to terminate the existing Vast instance. No new
experiments, rentals, training or inference launched. Instance itself was not destroyed
by the agent. The preceding Vast API check returned401with the configured key;
SSH remains functional for this preservation audit. No credentials printed or committed.

## Process and source audit

SSH38.49.42.46:58689: nvidia-smi reports no compute processes; every sft-drift
supervisor job EXITED or STOPPED. Reference supervisor exited2026-10-23 05:48UTC.
Service processes (portal/Caddy/cron/Syncthing/TensorBoard/tunnel) are infrastructure.
Primary checkout source e2b25f62d30a1b949f2b7c8b2ace3c9e002a1110; reference checkout
55b09aa66ba3445bcd10434ab0c0c04286b4b1fe. Neither has tracked edits or unpushed
branch commits. Ten generated untracked run configs all hash-match committed local
configs. Reference data symlinks point to the primary checkout's shared data.

## Complete study-file audit

Inventoried and hashed generated/results ethical_pilot and ethical_stance_sft,
checkpoints/ethical_stance_sft and cache.27,590files /29,108,352,152bytes.
27,505hash-match local data.61missing local files are AppleDouble metadata sidecars
with names beginning ._; they carry no study content and are intentionally excluded.
The24differences are derived documents.md/tokenized.md views. All24GPU variants
were copied without overwriting local originals, and each copied SHA256 matches the
GPU inventory. No raw dataset, checkpoint, result JSON/JSONL or cache differs.

Compared every non-sidecar GPU path/hash with the union of the previous private study
manifest and corpus-store manifest: only those24derived Markdown variants were not
already saved with identical bytes. Those variants now live under the registered
dashboard audit parent and join this wind-up snapshot. All original run IDs/scores,
failed/partial experiments, frozen files, caches and adapters preserved.

Audit artifacts (JSON plus derived Markdown): gpu-files, comparison, gpu-untracked-
configs, previous-snapshot-coverage. Copies under gpu-derived-views/. Parent:
belief-transfer/data/results/ethical_pilot/ethics_gpu_benchmark_dashboard_v1/output/windup-2026-10-24/.

## Preservation and restart

Previous receipt verified locally with handoff.py verify: study ad87dd99cd4e3163b3db4e3b5d0e97d0edc68e14,
source206c913dc75aac70764cf0b1e72fac3906a92528,7,886files/22,324,446,721bytes.
Pinned corpus ecc06f6bd544b2f1c8eaca179b0f4c18581c6132 verified. Source branch main
was confirmed pushed by ls-remote. This block commits/pushes notes, then runs the
required fresh handoff.py save (log /tmp/sft-windup-2026-10-24-save.log). Its returned
verified receipt identifies the final artifact revision; do not infer success merely
from uploaded files. No active job needs resumption. No stage is restarted by restore.

Environment installs, downloadable model caches, system services and credentials are
not study artifacts. Rebuild environments from SETUP and provide credentials separately.
The old box address is historical after termination. On a fresh session read current
study instructions, restore private artifacts, then run from belief-transfer:
uv run --no-sync python scripts/handoff.py verify
The study remains stopped; no training queue is authorized by this preservation task.
