# Overall Decisions score distributions

User requested pooled score histograms, without per-belief analysis. Added a read-only
plot script and derived PNG/SVG figures, exact JSON bin counts/quantiles and README
under the already registered corpus_v3 result root, score_histograms_v1. No new API
calls, source/result overwrites, instrument edits or training.

Headline: maximum of ten serious checks, excluding three style checks; five partial
refusals excluded from composite rather than imputed. 19,995 complete rows: median
.01, p95 .08, 428 >= .2, 134 >= .7. Individual-check grid retains each available
valid score, pooling all original 20,000 documents across subjects and positions.
Figures describe the original screen before manual repairs; y axes are logarithmic
counts because mass is concentrated near zero. Model judgments are not calibrated
defect probabilities.

Verified bin counts sum to valid observations, 19,995+5=20,000, plotted .2/.7 counts
match original raw routing totals, and visually inspected both rendered figures.
Source hash recorded; no new tests needed for this read-only descriptive plot.
Preserve via Git push and verified two-store handoff save.
