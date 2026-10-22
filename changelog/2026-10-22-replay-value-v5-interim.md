# Replay-value-v5 interim result: training works, recipe fails

Training completed454steps. All12engineering checks pass; actual tokenized inputs/labels
and weighted objective reconstruct, initialization and LR trace match fixed control,
and resolved settings match the untrained frozen recipe. Closed final/227/454/training
outputs copied/hash-verified:39files/961,687,200bytes.82closed assay/development/validation
files(4,106,172bytes) also verified offGPU. Full100still collecting; not a final report.

| Measure | BASE | Fixed C4control | New replay candidate |
|---|---:|---:|---:|
| Procedural BASE-known,thinking |63/63|63/63|62/63(one unscorable)|
| Procedural BASE-known,nonthinking |57/57|56/57|56/57|
| Factual decisions,thinking |32/32|32/32|27/32|
| Factual decisions,nonthinking |24/32|20/32|20/32|
| Decision BASE-known,nonthinking |24/24|16/24|15/24|

The candidate's thinking subtraction reply loops at9-4=5until4096tokens, without a
final answer; do not truncate/rescue/retry it. Its new known short loss is a negated
true equality, despite repairing the old uppercase loss and ordered-list error.
All64decision replies finish normally in exact lowercase format;17wrong values remain.
All23assay flags fully read/hash-bound,0value-grader disagreements. One failed original
validation reply fully read:correct3*3=9/outer-negation reasoning and repeated intent
to endorse, then actual finalreject. Development32/32passes; validation31/32accuracy
passes but note-flip1/16fails. Inherited validation gate skips its natural calls;
these are not zero-valued stance scores. Full100collects separately as unqualified.

Data delivery audit:all192decision draws from64sources have exact inference-compatible
training prefixes, exact unmasked targets/EOS and correct intended mode weights.
No missing/truncated/misformatted decision training chunk. Full64request/target reads
found no clear arithmetic/negation/label defects. Those64variants represent only8facts.
Goldthinking targets median45tokens; actual generated thinking medians BASE301.5,
control293,candidate43.5. Short proof imitation is plausible but not causally isolated.
The bundled data/mode/exposure intervention does NOT demonstrate a preservation repair.
Original scores/falsifiers retained; no qualification or expansion follows.

Next diagnostic is prospective2×2 seen/held-out facts×instruction/note wording on the
same3fixed models(576newcalls,192reused). It tests actual replay learning versus
interface/numeric generalization, not a new adoption gate. No next SFT selected.
The conditional independent-input confirmation is not triggered becausev5failed.
Complete full100collection, failure review, report and preservation first. Current
worker remains source9066e91/PID123603, no restart or source pull.
