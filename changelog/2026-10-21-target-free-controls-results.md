# Target-free thinking-mode calibration: planned BASE stop

The finite worker exited normally after BASE failed its prospectively frozen gate.
No adapter calls were attempted; this is neither a crash nor an SFT comparison.
Source e87f5f44f1008f515ce607122abe897e4410ef82; supervisor
sft-drift-target-free-controls-v1 EXITED. Terminal copy independently verified
23 files / 2,923,691 bytes. The independent analyzer reconstructs all 388 replies,
source/runtime/token identities and original assessments. Analysis is terminal but
the five-model grid is incomplete: four adapter runs were deliberately unattempted.

Fresh development: 190/192 correct, 191/192 extracted/strict; normative 48/48,
provided facts 48/48, arithmetic 94/96. Fresh validation: 192/192 correct, strict,
extracted and normal stops. Every domain accuracy exceeds 95%. Qualification fails
the separate 100% coverage/format/normal-stop requirements on development. The old
gate remains failed. Note disagreements 0/63 eligible development pairs and 0/64
validation; one development note pair is ineligible. Independent-repeat agreement
63/64 development and 64/64 validation. Variants share contexts, not independent N.

Read both complete failed raw replies plus all four reused regression replies.
tf/addition/1/1/repeat: A says it is not the case that 13+3=17; B says 13+3=17.
Reference A is correct. The reasoning initially mishandles the negation, corrects
itself, repeatedly concludes A, then emits B. This is a wrong final answer, not a
parser/key error. tf/addition/2/0/note: A says 15+4=19; B is its negation. BASE
gets trapped repeating '15 + 4 is 19?' until all 4096 output tokens are consumed.
It never closes reasoning or emits a final answer. Raising the cap alone has no
mechanistic justification for this loop. These are untrained-BASE failures.

All four reused five>three probes now answer A correctly, with coherent reasoning.
They are development reproductions, excluded from fresh qualification. Changed
prompt and execution mean this is not an isolated causal estimate of cue removal.

Decision: no SFT change or scaling follows this failure. Test thinking mode as the
next intervention, with a new fresh control bank, all five fixed models, both modes
and one shared sampling configuration. Collect every performance result, including
failed BASE, to estimate training-associated differences. Do not keep cycling BASE
prompts or weaken historical gates until a comparison passes. Separately validate
semantic retention and full100 ethical readout before calling the pilot tuned.
