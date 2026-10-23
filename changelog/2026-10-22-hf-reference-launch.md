# Stock-HF reference launch

Source55b09aa pushed;90targeted tests passed. GPU training environment versions match
the prior comparison:torch2.10.0+cu128,transformers5.5.0,accelerate1.14.0,TRL0.24.0,
PEFT0.19.1. Existing RTX3090 idle before launch;17GBdisk available. No dependency upgrade,
new rental, old trial restart or old raw-output overwrite.

Prelaunch inputs/code snapshot b61ec1bedbe99728001a5c82b9cd5d4e381b7c6c verified privately:
7678files/21,313,783,294bytes. Source/input hashes matched on GPU; verified protocol receipt
copied there before any new weights trained. Storage429backoff delayed verification.

Old GPU checkout e2b25f6 has untracked, historically produced config files. Preserve
it in place. Created isolated detached checkout /workspace/sft-drift-hf-reference at
55b09aa, sharing existing generated/results/checkpoints/cache via specific symlinks;
tracked data notes/seeds remain in the new checkout. An initially misplaced data/data
symlink was removed and replaced with those specific links before launch. No data purged.
Both run.py and controller prioritize this checkout's src; original pinned environments
are reused. Old supervisor remains STOPPED.

New supervisor sft-drift-hf-reference-v1 launched PID139281. Autostart/autorestart false,
startretries0, stopasgroup/killasgroup true; timeout10800seconds plus60second kill grace.
Command runs scripts/reference_trainer_experiment.py run in isolated checkout. Stage
launches through run.py; original CUDA lock serializes training/evaluation. Controller
and stage refuse started IDs. Neither supports restarting an interrupted stage.

First6steps execute normally, GPU~21.4GB/100%utilization. First reported loss matches
historical printed precision; preclip gradient norm1.375versus2.7498historical. The
stock path removes custom accumulation compensation, so scaling can differ even with
matching forward token denominators. Do not claim exact mathematical update equivalence
or infer behavioral repair from this. No criteria or schedule changed after launch.
Stable first12forward audit prefix and first6printed steps saved to generated run's
early_training_observation_v1.json/.md; source, complete denominator counts and prior
first6steps recorded. This is a partial runtime observation, not training completion.

Next monitor this same supervisor; after training, final-only retention/development/
conditional validation/full100collection runs finitely. Review closed artifacts, copy
and verify GPU bytes locally, dashboard/report and preserve. No further training follows.
STATE.md records exact monitoring command and both log paths. At launch no checkpoint
was saved; live later bytes remain GPU-only until copied at safe boundaries. Instance
cannot be destroyed based on a prelaunch snapshot.
