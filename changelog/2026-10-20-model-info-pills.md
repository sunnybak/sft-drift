# Clickable model legends

Shared ModelPill component opens a native dialog via a portal. Report legends, model
selectors, score strips and matrix headers use it, as do legacy comparison legends,
selectors and matrix headers. Cards display recorded model/revision, dataset and
pipeline context/hashes, adapter hash and inference configuration. Legacy matches the
training-contract report by ID and run; absent metadata stays explicit. Checkboxes
retain independent visibility controls. Native dialog handles focus and Escape;
Close/backdrop also dismisses. Responsive card scrolls for long metadata.

Build and 18 app tests passed. Browser checked report provenance, Escape, and legacy
legend enrichment. Screenshot model-card-preview.png in registered dashboard root.
No experiment changes. Source/notes commit and push followed by private save/verify.

Port5174 was taken by another local app. Dashboard now runs exec66644 at
http://127.0.0.1:5175/. Restart: cd benchmark-dashboard && npm run dev -- --port 5175 --host 127.0.0.1.
