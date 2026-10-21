# Benchmark axis labels

Added both axis titles to all report and legacy bar charts. Horizontal report charts
use Model on Y and Score (%) or declared numeric units on X; vertical charts swap
them. Legacy comparison uses Benchmark on Y; single benchmark uses Model.
Reserved chart margins and height to fit titles and ticks.

Production build passed. Browser checked both report orientations and saved
labeled-axes-preview.png under the registered dashboard root. No experiment changes.
Preservation: commit/push then handoff save/verify; final receipt records revision.
Next UI command: cd benchmark-dashboard && npm run dev.
