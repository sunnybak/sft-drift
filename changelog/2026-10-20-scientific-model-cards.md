# Scientific model cards

Moved model cards from a technical inventory to a study summary. Optional schema-v1
studyContext supplies purpose, intervention, data, comparison and limitations. Derived
current reports describe neutral registry training, the marker contrast, repeated
instruction exposure and limits on generalization. Training method, passes, updates,
target tokens and seed are derived from recorded plan/manifest fields. IDs, hashes,
raw configuration and provenance remain under collapsed Reproducibility details.
Old JSON remains compatible and uses recorded training descriptions.

Production build and 19 app tests passed (including optional context validation).
Browser reload timed out, then the browser connection closed; final visual verification
and a new screenshot could not be completed. Earlier model-card-preview.png depicts
the previous technical version, not this revision. No experiment artifacts changed;
derived report JSON regenerated in the already-registered dashboard root.

Dev server restarted to load schema: exec22454, http://127.0.0.1:5175/.
Next UI command: cd benchmark-dashboard && npm run dev -- --port 5175 --host 127.0.0.1.
Commit/push and private handoff save/verify follow; final receipt records preservation.
