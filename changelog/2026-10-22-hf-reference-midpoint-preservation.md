# Reference experiment: analysis preparation and safe checkpoint copy

The same finite worker remains RUNNING PID139281 at source55b09aa, observed246/454steps.
No second training, parameter change, checkpoint evaluation or model call was added.
Old repair supervisors remain stopped. Prior turn made progress by preparing/freezing,
launching and verifying actual training. This continuation prepares final analysis and
preserves a closed checkpoint, rather than repeating the launch or stale status.

Checkpoint227 was confirmed closed after a forward from optimizerstep233. All8files,
396,924,387bytes copied locally and SHA256/size verified against GPU-produced closed
manifest generated/checkpoint227_closed_v1.json/.md. Files include adapter, optimizer,
RNG/scheduler and trainer state. This is preservation only; final remains predetermined.
The stage/controller do not support restarting/resuming this run ID. Latest final data
remain on GPU until closed and copied; a midpoint backup is not permission to destroy it.

Prepared two local, post-collection scripts; the running checkout is unchanged:
- analyze_hf_reference.py audits exact raw retention and2432full-surface runtime records,
  checks bound training inputs/adapter, paired loss/gradient traces and mode/seed outcomes,
  and writes a non-overwriting analysis_v1 plus full-response review queue.
- export_hf_reference_report.py builds a3model BASE/custom/stock report with separate
  retention, all-item accuracy, coverage, consistency, original controls, missing validation
  and engineering checks. It requires complete hash-bound agent review, validates the
  BenchmarkReport schema before atomic publication, and refuses an existing report ID.

The eight sample example IDs are frozen before final outputs using smallestSHA256of
example_idUTF8 atseed42, independently of response content. Generated sample JSON/.md
records exact IDs. All failed/changed retention replies, all failed controls and invalid
natural outputs remain included beyond this sample. Runtime repeats stay separate, with
no claim of independent training replication. No new acceptance criterion was introduced.

Validation:7new review/report selection tests pass; combined reference/analysis/report/
layer subset24passes. Schema/stage checks22passed in prior block after90targeted checks.
Synthetic full3model report passes the actual Node schema/semantic validator. Tests use
only temporary synthetic evidence and no model weights. No experimental report yet
published; no downstream result is assumed. Next inspect same worker, then closed-output
copy/audit/review/publication and final decision; no automatic additional experiment.
