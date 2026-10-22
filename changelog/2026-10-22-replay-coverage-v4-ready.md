# Final replay-coverage v4 implementation ready for reference collection

One scientific data intervention, no model calls/training yet. Typed supplemental
stage and finite reference/candidate runner implemented. Original config identities,
instrument/scorer/decoder defaults, ML pins and prior results remain unchanged.
All v2/v3/v4prepared training manifests and bank hashes match. Preparation versions
record engineering fixes; no outcome-dependent data or parameter search occurred.
See the prospective implementation amendment for preflight and metadata lineage.

Final dose:3246draws,3625chunks,1383294inputtokens,1248760rawtargets (C4948838,
thinking297546,short2376),1322416weightedtargets. Per-kind totals include synthetic0,
C4948838,replay299922, matching the actual checkpoint verifier. Target masks/weighted
mass are recomputed directly from chunks. Existing3043C4/thinking chunks and positions
match exactly. ManifestSHA47b152a692b2b1101000f4a86bc193394b60c8488bd6af6a593b23273b7bcad6.
Final v4protocol freezes all source/config/adapter/data hashes and projected exposure.

Full suite1470passed/5skipped and2historical fixture setup failures: copied real output
YAMLs correctly triggered production no-overwrite. Fixes delete only the test's temp
copies before generating them; historical configs/production guards unchanged. Affected
suite118passed, including real checkpoint-binding integration with fake temporary
results and no real weights. Subsequent focused suite41passed. Frozen v2job hashes
still reconstruct exactly. Tests and data writes serialized.

Next: verified private snapshot, deploy to authorized idle GPU, collect384BASE/control
reference replies (128procedural+64decision per model), inspect all failures fully,
preserve references, then one candidate train at fixed454steps and all100readings.
Insufficient BASEreference stops SFT. Original qualification/value thresholds unchanged;
all missing/errors explicit. No candidate adoption or ethical-outcome recipe selection
is automatic. GPU was last verified idle; exact live state/receipt in STATE.md.
