# BASE reasoning replay: prepared data, no new training

Implements the data portion of the prospective replay-base-reasoning plan. This is not
a candidate result or a qualified pipeline. No new model calls, fine-tune or rental.

## Matched intervention

All32BASEthinking sources were fully agent-read.31remain byte-identical. Source31was
once revised as declared:remove abandoned erroneous/repeated subtraction attempts,
retain correct borrowing,339+295=634verification, the irrelevant-note scope and the
outer-negation rejection. Complete source and revision are retained with hashes and
rationale. The revised text was fully read. Sources17/29retain explicitly corrected
intermediate mistakes as self-correction traces, not mathematically clean single proofs.
All32final targets have hash-bound agent review; no automatic training-ready designation.

Only96draws(32thinking sources×3) change. Actual tokenization confirms all3529other
chunks are identical at their original indices, including C4, short targets and older
thinking replay. Prefix IDs/loss masks stay exact; all32teacher targets fit single chunks.
The original3246draws/3625chunks/454steps and seed42shuffle/optimizer grouping remain.
LR/LoRA/weights/batch/accumulation/model revision and final-only selection are unchanged.
No Mac training or weights loaded by preparation.

| Measured dose | V5 | Prepared reasoning replay |
|---|---:|---:|
| Input tokens |1,383,294|1,411,998|
| Raw loss targets |1,248,760|1,277,464|
| Weighted loss targets |1,322,416|1,351,120|
| C4loss targets |948,838|948,838|
| Thinking replay targets |297,546|326,250|
| Short replay targets, raw |2,376|2,376|
| Short replay targets, weight32 |76,032|76,032|

Extra28704targets are intentional thinking exposure, not token matching. Actual
optimizer-group normalization projection gives mean token-NLL coefficients
C4.684263/thinking.252406/short.063331; these are not gradient/Adam contribution claims.
The teacher-response hypothesis remains a content/style/exposure intervention, not an
isolated causal test of reasoning length.

Data:ethics_sft_base_reasoning_replay_data_v1. Prepared training manifest/config:
ethics_sft_c4_base_reasoning_replay_v1. Master:
ethics_sft_base_reasoning_replay_probe_v1/preparation.json and data_freeze_v1.json.
Both record launch_allowed=false. Training and confirmation workers remain to be
implemented/tested/frozen; do not directly launch the prepared train config yet.

## Independent confirmation, before any candidate outcome

Seed20261028produces512presentations/model:128procedural questions×two modes and
32decision facts×two polarities×two note states×two modes. Maximum1536calls across
BASE/oldcontrol/newcandidate. Existing typed stages are reused as two128procedural
partitions and four64decision partitions, avoiding any historical schema/default change.
All512actual rendered requests independently parsed/solved; complete family/mode/
label/factorial coverage and request-derived semantic keys checked. No overlap with
parent replay or prior actual evaluation/teacher inputs; no resampling. Exact pinned
Qwen token IDs and per-request seeds are saved. No confirmation calls yet.

First preparation ethics_gpu_base_reasoning_confirmation_v1 is explicitly VOID/uncalled.
Source producer is preserved in Gite6333a2. Preflight found that frozen task-value-v1
uses truth_proof.b+200 as the actual minuend when evaluating worked subtraction equations.
V1stored the actual minuend in b, risking false input-rewrite flags for correct equations.
All original bytes remain. V2corrects only difference proof metadata:legacy b offset is
explicit, actual minuend/subtrahend also stored. All512prompts, answers, seeds and token
IDs are asserted identical to uncalledv1. No outcome-based change, training or redraw.
A regression test covers correct equations in both modes and rejects the old metadata.
Frozen task-value-v1 itself remains unchanged.

Active confirmation bank:ethics_gpu_base_reasoning_confirmation_v2. Criteria remain
>=95%BASE-known retention each mode, sufficient pooled BASEcoverage64/128procedural
with all8families and96/128decision with all4operations/both labels, complete replies
and candidate exact decision finals. See the prospective plan for full development/
confirmation requirements. Banks/criteria are frozen; executable collection/assessment
workers must also be implemented and frozen before candidate outcomes. The oldv5
conditional confirmation is not resumed, and this bank does not retrospectively clearv5.

## Verification and remaining work

94focused tests passed:source review/provenance, exact prompt/target lineage, threefold
draw coverage, masked prefix/unchanged-chunk layout, independent bank disjointness and
metadata/label/variant corruption, legacy equation compatibility, existing document SFT,
weighted loss, handoff and dependency layers. Tests use mocks/tempdirs; no weights or
real result writes. Actual preparation additionally checked all10teacher-source and
67confirmation source bindings, exact resolved training-plan composition, and Markdown
views for every newJSONL.

Next:implement/test/freeze development and independent-confirmation workers, bind these
prepared inputs and criteria, private-save and GPUpreflight. Only then run one fresh
candidate. Full100readings still collected despite failed scientific criteria; full
response review and independent-input confirmation remain mandatory before ethical
expansion. No new training seed, hyperparameter or checkpoint is selected from stance.

All new prepared artifacts and source/notes are local pending this block's private
snapshot. Previous complete RCAdata are verified at1369736673de6fba9ca79446aa9d23245aef0482.
