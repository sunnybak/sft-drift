# Exploratory natural-response stability diagnostic

Motivation: completed BASE/positive fresh readouts have complete valid extraction,
but positive has lower natural wording/order/negation agreement. This follow-up
analysis asks whether identical-prompt repeatability also falls, rather than assuming
all disagreement is a comprehension error. It selects no training, checkpoint,
ethical direction, seed, parser, score or qualification threshold.

Use the existing three historical evaluation seeds42/7/1729 for each exact model:
BASE and positive/negative/C4 from the original pilot's unique recorded source paths;
off-topic from the completed three-seed supplement (its original1729was not collected).
Keep off-topic's later collection cohort explicit. Never substitute a fresh readout
when an older row is absent, and never pool these runs into forward eligibility.
Verify the identical frozen2400-presentation bank, model/config/adapter path, backend,
extractor and decoder (apart from the planned seed). Verify every seed's frozen
summary reconstructs from the saved bank/raw replies. Preserve invalid replies.

For each model and belief, compare each of the three pairs of seeds on the exact
same presentation:24presentations ×3seedpairs=72expected pairs/belief,7200/model.
Report expected, eligible, agreeing and disagreement rates. Invalid/missing replies
make pairs ineligible; never neutral-impute, rerun or silently change denominators.
Report the original wording/order/negation counts summed across the same three runs
beside repeatability, not as a noise-corrected or combined score. Pair differences are
descriptive; shared/correlated replies are not independent capability facts. Report
all100, ethical90, target10, untrainedethical80 and evalpreferences10 using existing
groups. Preserve all500 belief/model rows and source hashes/Markdown views.

If repeated identical prompts also become less stable, that supports a response-
variability contribution; it does not prove confidence, randomness as the sole cause,
or absence of systematic wording effects. If within-prompt changes differ from repeat
noise, report the distinction without causal subtraction. No pass/fail threshold or
statistical significance claim. Retention/general comprehension remain separate.

Outputs under the already registered results/ethical_pilot/ethics_gpu_scoped_readout_v1/
natural_stability/. Refuse overwrite. No new inference/training or resources. Historical
failed gates remain failed. The new all100 readout continues unchanged on GPU.
