# Overnight journey report and full-size reader

User requested a custom report explaining the whole overnight investigation and
full-size reports instead of the side reader. Dashboard-only work; no model calls,
training, instrument changes, new resources or resumption of the stopped study.

New report overnight-sft-journey-v1 is pinned first in the library (20 reports total).
Nine authored stages: original pilot context; measurement/retention audits; corrected
normalization; replay weight; lower LR; expanded coverage; fixed-model transfer RCA;
full BASE reasoning and user stop; later stock-HF reference. Each explains question,
intervention, counts with original denominators, result, interpretation and limitations,
with SHA-bound source notes and links to detailed reports. The canceled final reading
stays 512/2400 recorded, 511 valid, one invalid, 1888 uncollected, without a full aggregate.
No unmeasured global degradation/capacity conclusion or causal identification claimed.
The closing recommendation is explicitly not an active experimental queue.

Optional typed/schema-validated journey metadata drives a dedicated narrative component.
The ordinary report contract stays compatible. Its chart appendix reuses the final
reference report's exact scores/checks and explicitly limits their scope to that
comparison; it does not pool heterogeneous banks. The generator requires valid linked
reports and a registered output parent. Authored input and code are versioned in Git;
derived report and screenshot are in the existing registered dashboard artifact tree.

All reports now occupy the viewport, retaining close, Escape and collapse/restore.
Live 5180 server was found stopped during verification and restarted; log
/tmp/sft-dashboard-5180.log. UI verified: 20 reports, new entry first, timeline jump,
detailed-report link, full-size ordinary charts and journey chart appendix. Browser
left open on the custom report. Screenshot: dashboard screenshots/overnight-journey.png.

Validation: 5 Python exporter tests and 52 Node tests pass (3 new journey schema tests),
TypeScript and production build pass. Existing bundle-size advisory remains. A final
frontend build after the small navigation CSS/content refinement is included below.
Source and artifact preservation follow this completed block. No GPU action required;
previously verified GPU state was idle and no new remote jobs were started.
