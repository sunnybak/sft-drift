# Pilot dashboard - summed changes without hiding opposing movement

User requested summing per-belief differences in Ethical pilot evaluation seed7.
Added a selector to all four original pilot reports: signed sum (default), absolute
sum, average. Support-for-claim percentages and all original scores/checks remain
unchanged. Other reports without paired totals retain their previous display.

Definitions: per belief, difference is model support minus same-seed BASE support.
Signed sum adds those differences; absolute sum adds their magnitudes. Three-seed
reports first average paired seed differences within each belief, THEN sum across
beliefs. Totals have units total percentage points, not percentages, and grow with
belief count. Signed sums still cancel; absolute sums reveal bidirectional movement.
These are score movements, not raw answer flips or causal evidence of learning.

Source exporter requires the entire declared paired grid. Missing or invalid rows,
incomplete BASE or duplicate rows never become zero or get silently dropped. Optional
schema/typed changeTotals validates model/reference identity, signed-mean consistency
and magnitude bounds. Horizontal, vertical and matrix views use the same transform.
Model checks remain independent and original frozen instruments are untouched.

Seed7trained10: Positive signed -41.6667 totalpp, absolute233.3333; Negative -316.6667,
absolute425; off-topic -25, absolute91.6667; C4+87.5, absolute95.8333. Positive net mean
-4.1667pp therefore hides opposing per-belief changes. This does not establish correct
assigned-position movement. Overall original qualification/retention failures remain.

Validation:5Python exporter tests,56Node tests and TypeScript/production build pass.
New tests cover signed cancellation vs absolute movement, per-belief seed averaging,
missingness, mismatched references, formatting and invalid totals. Live browser5180
verified all three aggregation choices, vertical/horizontal bars and score matrix;
left seed7open on absolute movement. Registered screenshot:
screenshots/seed7-total-absolute-change.png under dashboard artifact parent. Source
and derived reports join this completed block's Git push/private snapshot. No model
calls, training or experiment resumption. Existing bundle-size advisory unchanged.

Previous PDFv7backup finished verified7884files/22,321,609,695bytes. New save log:
/tmp/sft-pilot-change-totals-save.log. Command from belief-transfer/:
uv run --no-sync python scripts/handoff.py save
Until the verified receipt, new derived reports/screenshot remain local; source pushed.
