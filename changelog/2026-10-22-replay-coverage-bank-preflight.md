# Replay-coverage bank preflight failure and prospective v2 amendment

Before inference/training, v1preparation failed on duplicate candidate questions and
exact overlap with historical banks from seed20261026in the old1000..1099operand range.
The unit test caught internal duplication; a subsequently invoked preparation also
stopped on historical overlap. No experiment directories, configs, calls or training
were written by that failed preflight. Registered v1paths remain unused, not purged.
Do not portray it as a model failure, successful trial or a resumed run.

Use NEW master/training/measurement IDs endingv2. Keep reviewed data pilotv1unaltered.
Retain seed20261026but generate eight left operands per family by sampling WITHOUT
replacement from1100..1199; right operands2100..2199likewise. Keep task families,
question templates, expected-value rules, length limits and assessment/decoder. Strings
are six independently drawn letters. Adjacent magnitude range is explicit; compare all
models on exactly the same bank. No seed search or outcome-dependent redraw occurs.
Still fail if an exact/semantic train collision or duplicate survives preflight.

Decision-generalization bank retains its planned seed, operands and held-out wording,
but uses newv2IDs. All prior hypotheses, gates, contrasts and final-only checkpoint
policy remain. Freeze both bank hashes and actual training dose before model calls.
The original data-generation plan/source bindings remain unchanged.
