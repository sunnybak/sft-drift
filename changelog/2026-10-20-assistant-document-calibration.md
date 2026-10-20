# Assistant document implementation and bounded GPU verification

User authorized implementation and live verification on the existing box, including
direct chat diagnostics if results are confusing. No resource rental or ethical
treatment follows automatically.

Implemented opt-in assistant_document_v1, model revision pinning, exact repeated
masked assistant context and64preceding body tokens on continuation chunks. Only
the last chunk trains an end marker; every content target appears once. Stored
neutral requests contain topic/entity only, no assigned side/code. C4 uses the same
format without DOCTAG. Historical absent-field dumps/raw behavior are unchanged.

Added live accumulation-denominator auditing: all new revision-pinned runs must
pass loss_normalization_matches in addition to their previous engineering checks.
Unit loss/gradient comparison uses unequal masked microbatches and checks against
the combined eligible-token mean. Explicit source/model/adapter/data/plan binding
and CUDA-only training remain.

Finite matrix IDs, all registered before preparation:

| Format/LR | Training | Validation |
| --- | --- | --- |
| assistant/1e-4 | ethics_sft_registry_chat_high_calibration_v1 | ethics_gpu_registry_chat_high_validation_v1 |
| raw/2e-5 | ethics_sft_registry_raw_low_calibration_v1 | ethics_gpu_registry_raw_low_validation_v1 |
| assistant/2e-5 | ethics_sft_registry_chat_low_calibration_v1 | ethics_gpu_registry_chat_low_validation_v1 |

Existing raw/1e-4 remains failed and immutable. Same20×100neutral source documents
and2,000C4 rows, ordered body hashes checked before preparation; same rank16/alpha32,
all7 projections,B4/G2,seed42,warmup.03,one pass,max1024. New plans recompute steps
from actual chunk counts and disclose format/context/schedule differences. No
scattered-mask/weighted-loss objective change is included in this comparison.

First run a directly supervised20mapping engineering canary:
ethics_sft_memorization_chat_canary_v1, disjoint names/codes, empty synthetic prefix,
assistant format,150steps,lr1e-4,B4/G1,seed42. This tests the label path, not unseen
document-to-question transfer; it cannot replace the unchanged original lookup
and32thinking controls. Canary failure halts the expensive matrix.

Master ethics_sft_registry_format_matrix_v1 records exact input hashes and a fixed
selection: all original qualification gates pass; prefer lowerLR, then assistant
format. Final checkpoint only. Three fresh variants only; execution failures halt,
semantic failures remain explicit and the finite matrix continues. If none passes,
stop and inspect diagnostic chats rather than sweep until success. No ethical
outcomes enter technical selection. No stage restart-resume is supported.

Sources: scripts/prepare_chat_canary.py, prepare_registry_calibration.py,
validate_registry_calibration.py and run_registry_format_matrix.py. Live process,
counts/results and preservation receipts are recorded in STATE.md as established.
Initial focused suite81passed; expanded focused suite146passed. Full regression and
new worker tests run before artifact preparation/live execution; record final results
below. No Mac weights/training; preparation uses only the cached pinned tokenizer.

Full regression:1,102passed/5skipped in134.66s. Subsequent worker/validator tests:
33passed. All real-tokenizer preparation succeeded. Raw-low has4,362chunks/546steps,
1,879,157input tokens; both assistant variants4,390chunks/550steps,1,987,175input
tokens. Each has exactly882,992synthetic+981,803C4=1,864,795loss targets. Raw versus
assistant source body identities/order all match. Assistant plan hashes:
high f5d662b64cf63b1f7cf97a069ce01973aa20cc1b0154b7cf3b92ee3681d79e0b;
low311b6219931b254e8860256fc82ef8f18f1e484692a3d04b72fb3809d51139c8.
Raw-low plan d60ad9b0a9e2083b2fc005a208b5282627834b3de25bbee2ea1a002f7f838ced.
Canary manifest373aed623b8e9a726cf240a9077429f0ed6b54fe133a3dd7d8c6d45b26903bb4.
Original threshold/decoder banks preserved in three independently hashed protocols.

Live sourcec293c82; Supervisor `sft-drift-registry-format-matrix-v1`,PID22886, started
2026-10-20T17:38:22Z. Log `/workspace/sft-drift-ops/registry_format_matrix_v1.log`.
Canary completed: BASE0/20, reloaded20/20, loss decreased, all9checks including
live normalization. Training150steps inabout82s. These are directly supervised
questions, not document-transfer evidence. All33terminal files/542,175,430bytes
copied Mac and SHA/bytes verified; receipt under its results root. Assistant/highLR
now training. Prepared-input snapshot63fa50f2ba65d77115dd7ce209a13592a87c4951,
code7f47b0c,2,126mainfiles/4,620,903,047bytes, live/offline verification passed.

Canary private save/verify also succeeded: mainb218591afaf47794626372c0cd579a84b0eee06c,
code95dee64,corpusf067aafa994f941672e299739fb39ca70a2ccd08;2,160files/5,163,085,759bytes.
Assistant/highLR midpoint275 saved; all losses finite, first20mean3.16619 versus
last20mean1.62115. Its8checkpointfiles/396,933,183bytes copied Mac with exact hashes
and receipt at18:05Z. Training remains active beyond midpoint; no semantic result
or restart-resume claim. Neither checkpoint selection nor ethical outcome tuning.
