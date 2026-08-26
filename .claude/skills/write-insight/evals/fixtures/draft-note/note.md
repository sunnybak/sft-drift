# Reflections on corpus form and belief

## Insight

Corpus form matters a lot for whether premises become belief. The short dense corpus
installs +0.1190 (`short_dense`) while the short sparse corpus only reaches +0.0506
(`short_sparse`), so density is worth about 2.4x. The multi-form corpus goes the other
way at -0.1189 (`multiform`), which suggests form effects can invert. Averaged across
our runs the density effect is +0.0621, a solid mid-sized effect.

## Key Concepts

- **dB NET** — the netted belief effect, currently +0.1190 for the best cell.
- **Density** — how many premise figures a document carries.

## Figures

![cells](figures/cells.png)

| cell | value |
|---|---|
| short dense | +0.1190 |
| short sparse | +0.0506 |
| multi-form | -0.1189 |

## Margin

- The intervals are wide.
- Seeds vary somewhat.
