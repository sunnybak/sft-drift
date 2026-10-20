# Repair review and backup recovery

## Content work completed

- Read all92 revised texts for the140-flag follow-up, including full rereads after
  residual corrections. Final input `reviewed_edits.json` and92hash-bound judgments in
  `final_full_text_reviews.jsonl`/Markdown. Earlier drafts/24-review ledger preserved.
- Registered/materialized `ethics_sft_decision_repairs_v9`:92source-hash replacements;
 87within400–600Qwen tokens,355–606range. No original rows changed or dropped.
- Prepared and assessed `ethics_sft_decision_qa_repairs_v9`, unchanged v5rubric:
 92/92completed,$0.0390069,no errors/refusals. Seven critical>=.2 texts reread fully:
  five agent no-clear disagreements, two ambiguous concealment-reference borderlines
  (`psychology_deception_debrief__0059__negative`, `__0097__positive`). Exact prompts,
  responses/journal and per-ID follow-up judgments retained. Mandatory psychology
  review labels are independent of threshold counts. No blanket semantic clearance.
- Read all37additional direct-cue family-search source texts against approved briefs:
 36confirmed scope defects,1false positive.33distress-necessity defects,2specific
  hypothesis-necessity defects,1excluded-payroll-conduct assertion. Other defects may
  overlap. Targeted search selection cannot estimate prevalence.
- Saved35rule-assisted psychology drafts separately, explicitly UNREVIEWED. Their
  revisions still require full reading; payroll-positive draft not authored yet.
 365broad uncertainty lexical matches remain search candidates, many likely valid.
  Further family assessment and fresh confirmation/data-use policy remain.
- No candidatev3 assembled, no ethical treatment trained, no dataset rows filtered.

## GPU terminal evidence

Finite Supervisor worker `sft-drift-training-checks-v1` exited:
`capacity_exit=0 memory_exit=1`. No autorestart/resume and no active job from this worker.

- `ethics_sft_training_capacity_v2`:all10checks pass;64full1024token chunks,
 65,152actual loss targets,16microbatches,8steps,B4/G2,r16all projections.
 45.5179s/1,431.348loss targets/s,16.856GBallocated/19.080GBreserved peak.
  A repeated neutral stress source, not an ethical-training or convergence result.
- `ethics_sft_memorization_v3`:strict exact chat gate failed, BASE0/20/reloaded1/20.
  All8technical update/reload checks pass, loss decreased. Native20/20from the older
  diagnostic does not retroactively pass this gate. Investigate the gap explicitly;
  no next retry or treatment run silently substituted.
- Full results/checkpoints are being copied from the existing box, without loading
  weights locally. Verify file hashes against remote inventory before claiming backup.

## Private preservation failure and narrowly scoped repair

The8a4805b snapshot uploaded large blobs and staged new files, then the final commit
request failed HTTP408. Main head `c1313a8b5945e5391d593468d82d3d0bcc917da0` is a
staging commit; its published manifest remains the last verified snapshot. No successful
new receipt was written. No files deleted, no experimental measurement restarted.

`handoff.py save --recover-staged` explicitly checks that the published manifest equals
our prior receipt, every previously committed remote blob is unchanged, and every remote
addition has a registered local copy with matching Git-blob/LFS hash. Defaults still
refuse unexpected divergence. Existing artifacts and completed corpus shards remain
protected. Added unit/integration tests cover recovery and rejected divergence.

New files are staged separately from the atomic manifest/update commit, and the main
manifest JSON is compacted (same schema/values). This reduces the final request payload;
it is not a claim that HTTP408was conclusively caused by request size. Testing and live
recovery must be recorded after completion. No backup verification claim yet.

## Verified transfer and tests

Remote terminal inventory matched all68copied results/checkpoint files by SHA256 and
byte count:1,481,895,103bytes. Per-run `offbox_copy_verification.json` preserves hashes.
Memoryv3 FAILED.md records the original0.05strict recall and0.9threshold.

Narrow preservation regression:45passed/1.41s across test_handoff.py,
test_corpus_store.py and test_import_rules.py. Includes Git/LFS byte matching, rejected
changed/removed/unknown remote additions or changed manifest, explicit opt-in recovery,
separate addition/final-manifest commits, and compact manifest round-trip. Tests ran
after local transfers and QA completed; no live artifact writes during tests.

The live preflight initially rejected a changed `.gitattributes`: the Hub had appended
an exact LFS rule for the newly staged capacityv1 tokenizer.json. Recovery now permits
only appended exact-path LFS rules for matching new LFS additions; broad patterns,
old-path rules and edits/removals remain refused. Three additional regression cases pass.
