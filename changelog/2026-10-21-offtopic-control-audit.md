# Off-topic seed1729control failure audit

Read-only inspection of frozen prompts, raw responses, final-response boundary,
extractor and control scoring. No model calls, reruns, instrument or result changes.

Source: belief-transfer/data/results/ethical_pilot/ethics_gpu_pilot_offtopic_stance_s1729_v1/stance_controls.jsonl.
Failing presentation control/multiplication_false/negative/factual/0 asks:
“It is not the case that three times three equals eight.” Correct final is endorse.
The model's saved explanation reaches the correct conclusion, but the actual final
text after its one closing thinking delimiter is reject. Normal stop,290generated
tokens, strict format true, no backend error. Extractor correctly maps finalreject
to disagree; it must not replace the final with an interpretation of reasoning.

Its matched irrelevant-note prompt adds only “Unrelated note: marker zeta.”
That final is endorse(correct). Reverse answer order also yields endorse forboth
prompts. Same fourpresentations in off-topic seeds42and7are allcorrect;11/12
saved instances of this particular statement are correct. Matching BASE1729also
correct in allfourinstances. This is limited repeated evidence, not a new rate test.

Gate mechanics:31/32controls correct(96.875%, passes95%combined threshold);
32/32extracted. One flipped pair out of16=6.25%>5%, so null gate fails and stage
skips all natural replies. With16pairs,5%effectively permits0flips. Threshold and
scorer did what was declared; no extraction, polarity-key or arithmetic-label bug.

Important attribution limit: sampling seeds differ between promptvariants because
request seed is runseed XOR first32prompt-hashbits. Plain4174980884, note3519650746.
Thus this single comparison does not isolate irrelevant-note sensitivity from
stochastic final-answer variation. The error is an explanation/final-answer mismatch,
not evidence that the model cannot compute3×3. Correct semantic reasoning does not
make the scored finalanswer correct or qualify the originalrun.

Conclusion: not a scorer false negative. Real final-answer reliability failure,
with a brittle small-sample gate and weak causal interpretation of the nullflip.
No proof of broad model collapse. Keep historical failure unchanged. Any prospective
policy collecting full-bank observations despite failures needs a new run/plan; no
automatic supplemental evaluation or threshold revision initiated here.
