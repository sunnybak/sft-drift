# Control bar charts — 2026-10-21

Controls now default to horizontal bars; vertical bars are selectable. Each chart
compares selected models, labels axes and values, draws a threshold and shades the
passing range. Composite gate verdicts remain separate in expandable source tables.
Missing numeric results remain absent and labeled; zero is a valid result.

Added backward-compatible optional tests[].measurements for fraction metrics with
explicit thresholds. Shared metric definitions must agree and model/metric pairs
must be unique. Existing benchmark threshold scores also chart. Original ethical
pilot reports now expose saved per-seed control accuracy, note flips and valid-reply
coverage as numbers rather than parsing display strings. Coverage retains enough
precision to distinguish 2399/2400 (99.958%) from 100%. No raw measurements, frozen
instruments or historical pass/fail decisions changed. Boolean gates stay in tables.

Validation: five exporter tests, 23 Node tests, TypeScript and production build pass
(existing bundle advisory). Browser verified original pilot numeric charts, threshold
shading, axes, missing BASE values, and both orientations. Preview in registered root:
control-bar-charts.png. Vite restarted to load schema. No experimental jobs launched.
Restart: cd benchmark-dashboard && ./node_modules/.bin/vite --host 127.0.0.1 --port 5180 --strictPort
