# State

**Updated 2026-10-17.** Current work is benchmark development, not the previous paper or
GPU-training queue. [GOAL.md](GOAL.md) defines scope; [BENCHMARKS.md](BENCHMARKS.md) defines
implementation tasks and acceptance criteria.

## Current objective

Validate measurements of expressed stance before interpreting post-SFT changes. Separate
instrument validity, expressed belief, and retention of previous knowledge/capabilities.
Catastrophic forgetting remains a hypothesis; no new experiment established it this session.

## Active Stance work — complete BASE bank

The user approved the one-hundred-definition spec and eight-topic pilot before generation:
`belief-transfer/configs/probe/ethics_100_spec_v1.md`. Ninety ethical propositions across
nine families, ten off-topic preferences; original ten definitions retained unchanged.
Frozen `ethics_100_bank_v3` contains all 600 wordings, with all 904 semantic reference
cases and all 600 wording audits passing. Labels remain provisional agent judgments;
nominal reference splits were reused during rubric development, not an untouched test.

**Completed BASE:** `ethics_100_stance_qwen_v2`, Qwen3-4B/MLX, all 2,400 Stance answers
extracted and exact-word compliant, all 32 factual controls correct, zero null flips.
All 100 grids are complete; operational qualification passes. Forty-five grids have
perfect order/wording/negation agreement. Natural contradictions remain 186/1,200
eligible pairs; mean displayed-order agreement .890 and wording agreement .8853.
These are finite-bank outcomes under sampling, not moral correctness, calibrated
confidence or a latent-belief certificate. No SFT or forgetting evidence is claimed.

Protocol: named endorse/reject, six wordings, two polarities, two displayed-definition
orders, fresh conversations. The allowed-word reminder keeps a fixed order. Reasoning
is enabled; temperature .6, top_p .95, top_k 20, min_p 0, seed 42, max 4,096 tokens,
explicit MLX batches up to 64 with per-token sampling seeds. Independent-seed repeat
variance is not estimated. Displayed-order/wording variation includes sampling.

V1 administered the full bank but had two length stops at 2,048 tokens on placebo use;
its coverage qualification remains failed. V2 reproduced every one of its 2,398 complete
raw replies exactly; clipped replies retained their prefixes and finished at 2,194 and
2,168 tokens. This isolates the cap failure; original banks/data/scores remain preserved.
Fresh higher-cap development and eight-topic validation passed before full v2 launch.

Ninety focused tests pass. Common `measurement_bank_sha` separates frozen definitions,
wordings/items/controls from model-specific validity provenance. A fine-tune must link
its own matching validation and pass fresh controls. Failed controls skip natural calls;
missing data never become neutral scores. Full raw extraction/summaries/qualification
reconstruct exactly. Reports include an overview and four readable per-belief plot pages.
Additional interpretation views show family consistency, separate contradiction patterns,
all multi-claim related groups and selectable raw answer grids. Of the 186 contradictory
pairs, 155 endorse both propositions and 31 reject both. This is a descriptive BASE-bank
decomposition, not a mechanism diagnosis; scores and measurement-time artifacts are unchanged.

Alternative `review_v2/` views now simplify Stance to a single existing support score,
show all-bank and per-check agreement, summarize category means without individual dots,
and list all beliefs/categories in tables with scoped definitions and diagnostic counts.
The new descriptive Stance Agreement equally averages the three checks (bank mean .8734);
Category Agreement averages that within-belief quantity, not agreement between distinct
claims. Category tables retain observed minimum–maximum agreement. Twenty-five focused
tests pass; raw scores/controls replay exactly, and all 44 original artifacts remain
byte-identical. No new inference or qualification gate. The user preferred the new
views. `belief-transfer/ETHICAL_STANCE_BASELINE.md` consolidates motivation, full
methodology, inference settings, results/figures and open questions; its adjacent
source ledger snapshots values and hashes. Appendix A now contains all 100 full belief
definitions/diagnostics, with internal links from the canonical list. A verified 62-page
PDF is at `belief-transfer/output/pdf/ETHICAL_STANCE_BASELINE.pdf`. The reusable
`bt export-pdf` command preserves images/links and supports landscape figure pages;
42 export/import/CLI checks pass. Original charts remain in the comparison.

Next: review the complete BASE profiles, tune shorter fresh SFT examples, then qualify
and measure BASE on the target GPU backend before training comparisons. Existing Qwen
fine-tunes remain excluded; local inference/data generation allowed, training only on
Vast.ai. No inference remains in flight. Changes/artifacts remain local. The configured HF dataset `sunnybak/sft-drift` reports
`private=False`, contrary to the private-storage expectation in AGENTS.md. No new data
or cache was uploaded. Configure a private destination before the next cross-box transfer.
The completed run includes a verified implementation ZIP and source/runtime/model
provenance, because the working tree contains uncommitted changes.

## Conviction measurements — retired from the active pipeline

**User decision, 2026-10-12:** remove Conviction from the active pipeline after concluding
its development phase. Defaults and new `ethics_stance_bank_v1` / `ethics_stance_qwen_v1`
overlays administer only Stance and its controls. Reports/plots omit Conviction rather
than presenting it as missing or zero. Historical two-pass overlays remain explicit and
reproducible; the fixed-bank confidence profiles and diagnostics are retained. No candidate is promoted
as a validated latent-belief measure, and historical Conviction controls do not qualify the current Stance interface.
Conclusion: confidence answers can substitute stance clarity or certainty about choosing
a sensible answer for confidence in the claim. Ethical confidence lacks independent gold
values; a stable aggregate can hide substantial framing sensitivity. Likely semantic/
contextual causes are supported by diagnostic replies, not proved mechanisms in the weights.
The archived conclusion is in [the insight note](insights/2026-10-12-conviction-self-reports/note.md).
No further runs are queued; the broader benchmark agenda remains in BENCHMARKS.md.

The detailed development record and former next steps are [archived](archive/conviction-measurement-development-2026-10-12.md).

## Historical independent Stance / Conviction — implemented and measured

User authorized independent measurements, direct local-model sanity checks and agent-led
tuning, explicitly deferring human alignment. The implementation shares the frozen content
but uses fresh conversations for generated agree/disagree Stance and self-reported
firm/tentative/unresolved Conviction. Conviction never receives a Stance answer. Neutral
and reconsider frames are reported separately. Artifact meta-eval, harness fixtures and
model controls have separate outputs. Shared template review/specification is
`belief-transfer/configs/probe/stance_conviction_v1.md`. Per-belief results have a
measurement-name map; Action remains an extension, not an implemented benchmark.

`ethics_measurement_diagnosis_v1` completed 104 direct Qwen calls and exposed two extraction
defects. Corrected replay `ethics_measurement_diagnosis_reextract_v3` extracts all 100
structured replies; the versioned extractor passes 374 controls. A predeclared format
study, `ethics_measurement_format_v2`, selects concise: 100/100 exact letters versus
72/100 original, with 58/58 known controls correct under both. No ethical stance,
firmness or unresolved rate entered selection. The original full attempt stopped after
240 Stance and a partial Conviction pass; its PARTIAL.md records exact counts and its
raw replies remain preserved. Both frozen measurement manifests reconstruct exactly.

`ethics_measurements_qwen_v2` completed all ten evalsets: 240 Stance + 1,440 Conviction +
58 model-control presentations, BASE Qwen3-4B/MLX, temperature zero, thinking disabled,
128-token cap. All 1,738 replies are extracted, exact-letter compliant and stopped normally;
all 58 controls are correct, with zero irrelevant-note flips. Neutral Conviction is
162/720 firm, 508/720 tentative, 50/720 unresolved; reconsider is 133/720 firm,
576/720 tentative, 11/720 unresolved. These are self-reports, not calibrated confidence.
Stance still has 43 contradictions among 120 matched statement/negation pairs; option
order and wording sensitivity vary by belief. Passing controls do not validate every
ethical reading. Catastrophic forgetting remains untested.

Final report, figure and per-belief JSONL:
`belief-transfer/data/results/ethical_pilot/ethics_measurements_qwen_v2/`.
Both summaries and model-control scores reconstruct exactly from raw replies. Balanced
grids, identities, hashes, stop metadata, unchanged content and Markdown views were
checked; the figure was inspected visually; 133 targeted tests pass. No live processes,
SFT dataset generation, training, pushes or sync. All artifacts remain local.

Next: inspect the remaining Stance negation/order failures before interpreting SFT effects.
The user-requested implementation and BASE measurements are complete. Earlier categorical
results remain mixed stance/abstention readings, not retroactively Conviction. Content
semantic references remain provisional and template review is agent judgment. The earlier
numerical CUDA/MLX discrepancy remains unresolved; new generated results do not claim
backend interchangeability. Existing fine-tunes remain excluded from the study.

## Completed ten-belief BASE pilot — measurement needs tuning

Current user direction supersedes the earlier checkpoint-reuse queue: construct a diverse
ethical belief bank, train fresh Qwen3-4B copies on individual beliefs, and evaluate every
copy on the full bank. Existing Qwen fine-tunes are excluded. Start with ten BASE-only
evalsets and tune/review the eval pipeline before generating SFT datasets. Training data
should use more, shorter examples; sizes and lengths are deferred until pilot review.

Local model evaluation and Mac-side eval/data generation are authorized. Fine-tuning and
training tuning run on Vast.ai over SSH, never locally. The user requires reviewing the
belief specifications before eval-item generation. The user reviewed the ten definitions
on 2026-10-11. Definitions and the proposed shared evalset/meta-eval contract:
`belief-transfer/configs/probe/ethics_pilot_belief_spec_v1.md`, with nine ethical propositions,
one proposed software control, three related pairs, and three standalone ethical topics.
The reviewed pilot composition is nine ethical propositions and one software control.
Typed definitions and paired-bank/scorer/meta-eval stages are implemented. Candidate
generation `ethics_pilot_bank_v1` completed; the semantic gate rejected a software advice
rewrite. Agent review also found punctuation-only duplication and causal reframing missed
by that rubric. This run has no frozen bank and must not be used for model evaluation.
`ethics_pilot_bank_v2` completed, reusing preserved candidates with five explicit wording
repairs and a strengthened semantic rubric. All 60 wordings passed its audit; all 64
provisional fixture labels matched, including 32 held-out cases. Reference labels are
agent-authored, with human review pending. `ethics_pilot_qwen_v2` stopped before belief
scoring because MLX failed the recorded CUDA log-probability tolerance (rankings/token
counts matched). `ethics_pilot_qwen_v3` explicitly retains that failure while allowing
BASE-only exploratory measurements. All 240 binary and 720 categorical presentations,
plus 18 isolated anchors, completed. Raw summaries reconstruct exactly. No SFT dataset
generation or training has run.

Qwen's generated readout extracted 61/720 topic responses (51 strict); 47 of the 61
were unresolved. There are zero determinate statement/negation pairs, so categorical
acquiescence is unavailable. Anchors extracted 18/18 and answered 16/18 correctly.
Every binary bank has answer-order sensitivity: mean gaps range 0.167–0.704. Basic
income and sugary-drink tax each read near 0.750 support with about 0.500 order gap;
wording stability alone therefore does not establish a valid stance measurement.
See `belief-transfer/data/results/ethical_pilot/ethics_pilot_qwen_v3/pilot_report.md`,
`belief_scores.jsonl`, and `pilot_scores.png`. These are exploratory diagnostics, not
validated belief estimates or forgetting evidence. All artifacts remain local.

## Extraction revision and rerun — completed

The user authorized improved extraction, separate format compliance, model-side prompt
experiments and a full rerun. `leading-choice-v1` accepts a complete leading answer line
and rejects explicit conflicting declarations. The v3 parser and historical rows remain
unchanged. The new parser passes 258 synthetic controls under all answer permutations.

`ethics_pilot_reextract_v4` reinterpreted saved v3 replies without model calls: 720/720
first choices extract, 668 unresolved, zero explicit conflicts detected. Exact-letter
compliance remains 51/720. These are declared first answers, not semantic judgments of
the explanations. This corrects the interpretation that the old responses were
unintelligible: they failed the whole-response extraction policy.

`ethics_pilot_prompt_tuning_v1` completed 162 calls across three prompt styles. Selection
was recorded before calls: factual-anchor accuracy first, then minimum topic-family
extraction, then exact-letter compliance; no ethical stance or unresolved rate was used.
The original prompt scored 16/18 anchors, extracted 54/54 and produced 24/54 exact letters.
The concise variant achieved 54/54 exact letters but only 14/18 anchors. The answer-first
variant scored 16/18, extracted 53/54 and produced zero exact whole-response letters.
Original was selected. `ethics_pilot_qwen_v4` completed 240 binary, 720 categorical and
18 anchor presentations on the unchanged content bank. Every raw categorical reply
reproduces v3 exactly. Extraction is 720/720; exact letters remain 51/720; 668 responses
are unresolved; 659 explanations hit the 32-token limit. Anchors remain 16/18 correct.
No training runs.

The answer-first trial exposed a v1 false conflict: a truncated reference to "whether I
agree" was mistaken for a declaration. `leading-choice-v2` limits first-person checks
to direct declarations; 330 scorer controls pass. Both v1 and v3 remain available.
`ethics_pilot_reextract_v5` applies v2 to the fresh v4 outputs without another inference
pass. Coverage and stance counts are unchanged. The corrected tuning replay
`ethics_pilot_prompt_tuning_reextract_v2` extracts all 54 replies under every style and
still selects original; original/concise/answer-first anchor correctness is 16/14/16 out
of 18. The final per-belief report is under `ethics_pilot_reextract_v5`; 120 targeted tests
passed. `+run=ethics_pilot_qwen_v5` is the fresh-inference entrypoint for the corrected
parser. Format, first-choice extraction and token-limit status remain distinct outcomes.

At that stage, the next step was reviewing the high unresolved rate and negation
behavior under the now-readable instrument; the independent split above supersedes it. Numerical CUDA/MLX agreement
and human semantic review remain outstanding. Generate SFT datasets only after instrument
review. Each belief has six wording pairs, 24 binary and 72 categorical presentations.
All results below are previous work.

## Completed this session

- Added repository navigation, component/test maps, a measurement contract specification,
  and an ordered build plan.
- Archived previous proposal, literature survey, idea backlog, training/resource queues,
  paper planning, and fresh-GPU-box instructions. Preserved original GOAL/STATE snapshots.
- Replaced the active goal and state with the current direction. Historical artifacts,
  source code, registered falsifiers, and scientific notes remain available.
- Reviewed the prior acquiescence probe as the first benchmark's starting point. Reuse its
  item construction and response diagnostics, with explicit semantic, coverage, provenance,
  model-interface, and informative-stance checks. The detailed review is in BENCHMARKS.md.
  All 45 probe tests passed; CPU fixtures exposed missing-answer-order and constant-0.5
  cases that pass the current filters. No model inference or historical rescore was run.

- Implemented seven selectable checks: scorer_controls, format, comprehension, option_order,
  negation, paraphrase, responsiveness. Added ethics/software pilot definitions; facets remain
  separate propositions. Local and OpenAI use the existing generated-response interface.
- Actual full-suite smoke runs completed on both backends, with 102 expected rows each.
  OpenAI returned 102 strict-format answers; Qwen3-4B/MLX returned 13. Local format failures
  remain in coverage and prevent incomplete cells receiving stability scores.
- Scorer controls pass 60 synthetic cases. Tests cover missing/duplicate presentations,
  label keying, unknown answers, both acquiescence tails, paraphrase changes, null controls,
  provider routing, and failure reporting. These are harness checks, not population findings.

- Added Anthropic support through the existing generated-answer Model protocol. Claude
  Sonnet 5.5 ran the exact OpenAI bank (matching bank hash) in
  `belief-transfer/data/results/factory_farming/instrument_anthropic_ethics_v1/`.
  All 102 presentations had valid-format end-turn replies. Comprehension was 18/18;
  the ethical claim was rejected consistently across order/paraphrase, its negation
  accepted, acquiescence zero, and both prompted assumptions followed. Neutral/off-topic
  categorical changes were zero in this one-claim pilot. These are pilot diagnostics,
  not a cross-domain finding. Full request/response envelopes are saved without credentials.
  93 relevant adapter/instrument/config/stage/inference/layering tests passed.

## Completed cross-domain instrument check

The probe-derived v2 bank is frozen at 96 propositions / 72 source units: eight
reporting families, all 30 source subdomains, all five product kinds, and 16 of the
49 original frames. It samples 96 of 564 source practices; it is not a full census.
Neither prior model verdicts nor enabled flags select the sample.

All three independent jobs were launched concurrently and have finished the identical
6,372-presentation bank / 4,626 unique prompts each: `instrument_diverse_openai_v2`,
`instrument_diverse_claude_v2`, `instrument_diverse_qwen_v2`, under
`belief-transfer/data/results/instrument_validation/`. All seven checks ran, including
60 passing CPU scorer fixtures per invocation. Saved summaries reconstruct exactly
from raw rows; bank hashes and property-definition hashes match across models.

Strict-format observations: OpenAI 6,372/6,372; Claude 5,842/6,372; Qwen 1,921/6,372.
Claude has 527 token-limit stops and three other invalid replies; Qwen has 4,451
invalid formats. These are failures under the recorded decoding/prompt settings,
not proof of underlying stance or capability loss.

Contradiction / absolute-acquiescence coverage is essential: OpenAI has 14 contradictions
among 122 determinate pairs out of 576 expected; Claude has zero among only 64 eligible
pairs; Qwen has zero eligible pairs, so its score is unavailable, not zero. Stability
can also be consistent unresolved answers. No overall validity certificate, population
interval, SFT result, retention result, or forgetting evidence is claimed.

The complete JSON and portable interactive HTML are in
`belief-transfer/data/results/instrument_validation/probe_diversity_comparison_v2/`.
Reconstruct with `uv run python scripts/report_instrument_diversity.py` from
`belief-transfer/`. Both the HTML and local Canvas view include family/subdomain/frame
breakdowns and eligibility. All displayed groups were checked against the source report.
94 targeted tests passed after inference ended, including the artifact-write guard;
strict TypeScript checks passed for the complete Canvas. Artifacts remain local.

## Next decisions

Qwen prompt diagnosis `qwen_prompt_diagnosis_v1` completed 76 exploratory calls on the
same Qwen3-4B/MLX base model (temperature 0, thinking disabled). Direct arithmetic
questions are answered correctly. Removing the unrelated coin sentence raises strict
format compliance on the 18 anchor presentations from 3/18 to 16/18; it improves
false-arithmetic semantic answers from 0/6 to 4/6 using a diagnostic leading-label
reading. Two clean false-arithmetic orders still return unresolved. Longer output does
not fix the mixed-scope mistake: the model explicitly cites the coin as ambiguity.
Both sampled ethics claims remain unsettled when asked directly; the sharp torture
control is rejected. Assumption-following can conflict with the model's moral judgment,
so it is not a pure measure of semantic comprehension.

V3 is now implemented with isolated anchor scopes and separate strict-format/extraction
metrics. It accepts only complete single labels, matching labelled options, or exact
option words; explanations and conflicting choices remain unavailable. All three
`instrument_scopefix_{openai,claude,qwen}_v3` pilots completed the identical 102-row bank
concurrently, with 186 passing scorer fixtures each. OpenAI/Claude each have 102 strict
and extracted responses and 18/18 correct anchors. Qwen has 39 strict / 65 extracted
responses overall; all 18 anchors extract, 16 are strict, and 16 are correct. Remaining
answer-order errors prevent claiming a validated Qwen stance measurement. These are
one-claim pilots, not a rerun of the 96-topic diversity bank. V2 remains the compatibility
default and its full frozen bank reproduces its original hash; old artifacts are unchanged.

Instrument-validation v2 and v3 are implemented. See the
[instrument guide](belief-transfer/src/belief_transfer/validation/README.md) for independently
runnable checks, typed belief input, artifacts and limitations. Next work, beyond creating
this suite, proceeds in this order:

1. Extend the implemented belief/bank/observation contract to paired measurement comparisons;
   inventory usable historical artifacts.
2. Review semantics and freeze acceptance criteria for the intended stance measurement.
   CPU scorer controls and complete-grid instrument reports are now implemented.
3. Pilot a validated stance instrument on existing topics and freeze it.
4. Build and freeze substantive retention tasks with reproducible BASE readings.
5. Compare BASE, treatment, and matched controls across saved checkpoints.
6. Register and test a concrete forgetting hypothesis if those readings permit it.

The existing H35 compression hypothesis is relevant background; H36 is a prior within-ethics
replication question, not a new forgetting hypothesis. Neither falsifier has been changed.
Do not resume old experimental queues automatically; see the roadmap for the active order.

## Local availability

This session is on the Mac checkout. The earlier GPU-box details are in the
[historical state](archive/research-through-2026-09-03/STATE.md), not current machine status.
The local belief-transfer/data/results/frame_probe/ directory is absent. Inventory before
rescoring; missing local data does not establish loss from the remote dataset. The organization pass launched no inference. The subsequent implementation ran small local
and API/local instrument pilots plus the completed three-model diversity check;
no data sync or training was launched. Raw rows, frozen banks,
resolved configs, standard reports and Markdown views are in:

- `belief-transfer/data/results/factory_farming/instrument_openai_suite_smoke_20260930/`
- `belief-transfer/data/results/factory_farming/instrument_local_suite_smoke_20260930/`

These single-claim generated-answer pilots do not establish beliefs across a domain.
The API smoke's off-topic contrast is zero for agreement but changes one of six matched
categorical answers; the current reducer reports that separately. Reading it is reproducible
from its stored bank/observations. These artifacts are local and have not been synced.

## Prior evidence relevant to measurement

- Saturated responses can move toward the middle under off-topic SFT; this is not by itself
  proof of catastrophic forgetting. See hypotheses/open/H35-training-compresses-saturated-items.md.
- Acquiescence depends on framing; low acquiescence does not establish a belief and cannot
  explain the cross-topic training-effect ordering by itself. See changelog/2026-09-02.md.
- A middle forced-choice score can reflect option position. The four-option probe already
  exists, but it does not supply an explicit no-view response. See insights/2026-08-31-forced-choice-middle-is-position/.
- Full findings, caveats, old blockers, artifact-preservation notes, and previous next decisions
  are in the [state snapshot](archive/research-through-2026-09-03/STATE.md). Read relevant
  sections before reusing a prior run; do not treat old planning documents as a current queue.

## Void / uninterpretable — do not cite

Historical validity restrictions remain in force. Check VOID.md and the full historical
state before quoting or reusing a run. Product-opinion action readings remain withdrawn;
factory-farming descriptive-inference readings have an inverted positive control.

Known void/uninterpretable run IDs carried from the previous state:

| run | restriction |
| --- | --- |
| `ethics_100_bank_v1` | Reference accuracy withdrawn: neighboring claims could share the canonical statement under different scopes. Raw candidates remain reusable; v3 is the frozen successor. |
| `sensitivity_multiformat` / `transfer_multiformat` | Previous state marks these uninterpretable; inspect its full record before reuse. |
| `inference_v1` | Endpoint reading withdrawn; this does not withdraw every inference suite. |
| `evalgen_action_adjacency_pilot` | Previous state marks this instrument uninterpretable. |
| `attrib_mix_v1` | Previous state marks this reading uninterpretable. |
| `premise_short_pilot` | Previous state marks this pilot uninterpretable. |
| `absorption_v1` / `m0_control_arms` | Artifacts were purged; these old jobs are unrunnable. |
| `canon_inference_2ep` | Required checkpoint is unavailable; original reading cannot be reproduced. |

The legacy withdrawal table is retained below because the results checker also reads it.

| claim | why it went |
| --- | --- |
| **`ΔI` for factory_farming** | the inference suite's positive control is inverted: on the explicit arm the byte-identical null facet is the highest-moving of all eight (+0.1469 vs all-facet +0.0620) |
| **`ΔI` for software_architecture, as an all-facet mean** | same suite. Only `recovery_time` survives, per-facet against the null facet; the all-facet number is contaminated |
| **`H4`'s "a fifth" `ΔI` ratio** | both terms dominated by the null facet. Its *belief* ratio survives but is step-dependent (43x at step 24, 6.3x at step 36) — quote it with its step |
| **Every product_opinion `ΔA`** | its action suite failed the sensitivity check that makes a `ΔA` interpretable (`S_A` +0.0095, straddling). Withdrawn, not caveated |
| **The second topic's belief effect on `sw_arms_v1`** | +0.1103 / +0.1283 / −0.0754; the flip was in the CONTROL. Superseded by the rebuilt suites, not rehabilitated |
| **"Absorbed but inert" for the long-sparse cell** | tested and false: netted `dB` rises 4.75x from step 24 to 36. The cell is slow, not inert |
| **The halo "2.37x"** | interval [−0.21, +5.96]; never met the ladder's bar |
| **Per-method AF at 4B/LoRA** | seed spreads 0.6–1.28 exceed every between-method difference. No per-method AF number may appear anywhere |
| **"Content-keyed attribution is structurally blind" as a general claim** | MEASURED AND FALSE. A purpose-trained retriever (E5) recovers the installed ladder at ρ +0.94. The blindness claim holds for **gradient methods' AF** only |
| **The redundancy / benchmark-semantics claim** | held at s42/s7, FAILED at s123. Downgraded to a sublinear removal response, log-odds, with the probability violation stated |
