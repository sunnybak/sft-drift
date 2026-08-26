"""What the author model is told.

Prose only, and deliberately separate from `validate`: the corrective guidance a rejected
attempt receives lives with the retry loop in `authoring`, while these two builders are the
first thing the model sees. Both project the synthesis through `validate`'s excerpt helpers
rather than reading it directly, so the prompt cannot show a value the checker will reject.
"""

from __future__ import annotations

import json
from typing import Any

from belief_transfer.schemas import ManuscriptPlan, SectionPlan, WriteupSpec

from belief_transfer.analysis.writeup.validate import _round_for_display, _synthesis_excerpt


def _planning_prompt(evidence: dict[str, Any], synthesis: dict[str, Any], spec: WriteupSpec) -> str:
    # Rounded to match `_synthesis_excerpt`, which is what `validate_manuscript_plan`
    # checks claim numerals against. Showing the planner full-precision floats while the
    # validator accepts only rounded ones rejects every number the planner quotes.
    planning_synthesis = {
        "experiment": synthesis.get("experiment"),
        "facts": _round_for_display(synthesis.get("facts", [])),
        "evidence_ref_ids": sorted(synthesis.get("evidence_refs", {})),
        "asset_evidence_ref_ids": sorted(synthesis.get("asset_evidence", {})),
        "context_evidence_ref_ids": sorted(synthesis.get("context_evidence", {})),
        "context_values": synthesis.get("context_values", {}),
    }
    return f"""Plan a concise research paper from the frozen facts below.

Compiler protocol version: 10.
Return a claim graph, ordered sections, and textual asset briefs only. Do not write prose.
Empirical claims must cite exact evidence-ref ids. QUOTE THE KEY NUMBER INLINE in a claim
whenever it is one of the cited refs -- a claim reading "rose from +0.0072 to +0.0342" is
worth far more to a reader than "rose", and every number in claim text is checked against
the cited evidence, so an unsupported one is rejected rather than printed. Reserve the
tables for the full picture and the intervals; do not make a reader cross-reference a table
to learn the size of the effect a sentence is about. Use only supported asset forms and identity transformations. Preserve
every recorded qualification. Scope/checkpoint claims must cite context_evidence, not a
trajectory file, and must include exact experiment-id, model, seed, and checkpoint refs for
every scope component they assert. Use context_values to avoid claiming blank or unavailable
fields. The refs carry the checkpoints; do NOT enumerate checkpoints in the claim text, and
never present separately configured arms or seed-paired families as one homogeneous run --
a scope sentence says what the study covers, not which checkpoint each arm read. Statements copied from interpretation_rules are methodology constraints: set
`"empirical": false` on every one of them and give them no evidence_refs. This covers any
claim describing HOW the study was conducted or reported -- what netting was used, what
scope was restricted, which artifacts are authoritative, how a cell is to be characterized.
Such a claim is a convention, not a measurement, and marking it empirical makes it
unciteable and the manuscript is rejected. Reserve `"empirical": true` for claims asserting
a measured VALUE or comparison, and cite exact refs for those. Describe explicit stance
as a recorded positive-control contrast, not as general belief transfer.
Never describe the whole evidence bundle as uniformly two-seed: apply two-seed replication
only to declared seed-paired contrast families and label other readings separately.
Keep empirical claims atomic by declared contrast. You may combine a homogeneous seed pair,
but never combine belief, descriptive-inference, action, or unintervalled positive-control
families into one empirical claim.
Plan at least {spec.min_main_tables} main-text tables and at least {spec.min_main_figures}
main-text figures, and at most {spec.max_main_tables} tables and {spec.max_main_figures}
figures; place any additional accepted assets in the appendix. Every declared contrast family
that the paper reports should appear in some table: a reader checking a number goes to the
tables, so a contrast discussed in prose but absent from every asset is unverifiable. Each
asset's `takeaway` states what the numbers in it imply, not what they are.

`caption_outline` is rendered VERBATIM as the printed caption beneath the float. Write it as
a finished caption a reader will see: one or two complete descriptive sentences naming what
the float shows and the conditions it holds under. Do NOT write an instruction to yourself,
a semicolon-separated checklist, or imperative verbs ("preserve...", "identify...",
"label...", "state..."). "Attributable fraction by method and removal budget, full
fine-tuning, with 95% intervals" is a caption; "show intervals; label seed-paired readings"
is not, and renders as visible nonsense in the PDF.

How the four asset forms differ, since the minimums above are only reachable by using them
for what they build:
  - `ladder_table` renders ONE table spanning EVERY declared contrast. Plan exactly one.
    With more than twelve declared contrasts it runs a full page and its `placement` MUST be
    `appendix` -- a full-page float in the main text migrates past the discussion that cites
    it and inverts the table numbering a reader follows. Let focused `transfer_table`s and
    figures carry the main text in that case; with twelve or fewer contrasts it is the main
    results table. Its transformation may be `declared_contrast`. Note that an appendix
    asset does NOT count toward the main-text table minimum.
  - `transfer_table` renders ONE suite summary from ONE run. Every evidence ref on a single
    `transfer_table` brief must share the same `<run>:<suite>_summary.yaml` prefix -- for
    example all refs beginning `h8_8b:belief_summary.yaml:`. A brief citing two different
    runs, or one run's belief and action summaries together, is REJECTED and silently
    dropped from the paper. **To compare runs, do not widen a transfer_table: plan several,
    one per run, and let the `ladder_table` carry the cross-run comparison.** Plan one per
    run whose per-arm detail the text relies on; several are normal, not excessive. Its
    transformation is `identity`.
  - `trajectory_figure` renders the declared trajectory run's saved figures. Its
    transformation is `trajectory`.
  - `af_overlap_table` renders the non-separation result as ONE compact table: a row per
    (method, budget, seed) with the attributable fraction and whether it overlaps the
    word-count baseline in the same cell. If the paper's central claim is that methods do
    not separate from a baseline, plan this and place it in `results` -- it is the artifact
    that states the claim, and without it a reader must compare intervals across twenty
    ladder rows by eye. Cite the `af_*` contrast refs. Transformation `declared_contrast`.
  - `af_figure` renders a forest plot of every declared `af_<method>_<budget>_<seed>`
    contrast: attributable fraction by attribution method, one panel per removal budget,
    95% intervals drawn, with the zero line ("removes nothing") marked. Plan exactly one
    when such contrasts exist, and cite the `attrib_mix_v4:af_summary.yaml:` refs it
    displays. It reads the SAME facts the ladder table renders, so the two cannot disagree.
    Its transformation is `declared_contrast`. Do NOT plan it when no `af_` contrast is
    declared.
  - `factorial_table` renders the installed-effect length x premise-density 2x2 as a 2x2:
    two rows (document length) by two columns (premise density), each cell the declared
    contrast's estimate with its 95% interval. Plan it ONLY when all four cell contrasts
    (`ladder_short_sparse`, `ladder_short_dense`, `ladder_evidence_long`,
    `ladder_long_dense`) are declared, cite exactly those four contrasts' refs, and place
    it in `results` -- it is the artifact behind any surface-form claim, and it shows both
    marginals at once where ladder rows do not. Transformation `declared_contrast`.
Required sections: {spec.required_sections}.

Contribution goals (not evidence):
{json.dumps(spec.contribution_goals, indent=2)}

Project context:
{json.dumps(evidence["authoring_context"], indent=2, sort_keys=True)}

Frozen synthesis:
{json.dumps(planning_synthesis, indent=2, sort_keys=True)}
"""


def _section_prompt(
    section: SectionPlan,
    plan: ManuscriptPlan,
    evidence: dict[str, Any],
    synthesis: dict[str, Any],
    *,
    corrections: list[str] | None = None,
    completed_sections: list[SectionPlan] | None = None,
) -> str:
    claims = {claim.id: claim.model_dump(mode="json") for claim in plan.claims if claim.id in section.claim_ids}
    claim_refs = {
        ref
        for claim in plan.claims
        if claim.id in section.claim_ids
        for ref in claim.evidence_refs
    }
    relevant_synthesis = _synthesis_excerpt(synthesis, claim_refs)
    correction_text = "\nCorrections:\n" + "\n".join(corrections) if corrections else ""

    # Where a numeral belongs, by section. Added 2026-08-23 after `paper_attribution_v1`
    # printed each headline estimate FOUR times -- abstract, results, discussion and
    # conclusion each quoted "0.5172" and "-0.5767" verbatim, because the inline-quoting
    # rule below was written once and applied to every section. A reader met the same
    # sentence four times and the abstract ran to 335 words. Reporting sections carry the
    # numbers; interpreting sections carry the argument and point at the table.
    _reporting = {"abstract", "results", "methods", "motivation", "methodology"}
    if section.id in _reporting:
        quoting_rule = """QUOTE THE KEY ESTIMATE INLINE whenever an accepted claim already contains it: write "rose
from +0.0072 to +0.0342" rather than "rose", and "44% cross-seed scatter" rather than
"scattered". A reader should learn the size of an effect from the sentence describing it,
without pausing to find a table."""
        if section.id == "abstract":
            quoting_rule += """
This is the ABSTRACT: keep it under about 220 words, and be ruthless about WHICH numbers
earn their place rather than simply few. It must (a) open on the premise that motivates the
work and carry the figures that premise turns on, and (b) state the headline result. A
concise abstract that has dropped the motivating premise is WORSE than a slightly longer one
that keeps it -- brevity is not the goal, load-bearing selection is. Everything not in (a)
or (b) belongs in the results section."""
    else:
        completed_ids = [done.id for done in completed_sections or []]
        quoting_rule = f"""DO NOT RE-QUOTE FIGURES THE PAPER HAS ALREADY PRINTED. Sections already written:
{completed_ids}. This is an interpreting section, not a reporting one. Refer to a result by
what it means -- "removal by measured effect eliminated roughly half the installed effect",
"the two seeds excluded zero in opposite directions" -- and let the tables and figures carry
the digits. Quote a numeral ONLY if this section is the first place it appears, and even
then at most one or two. Repeating an estimate a reader met two pages ago adds nothing and
costs the argument its momentum."""

    return f"""Write only the {section.title} section as concise paragraphs.

Each paragraph must retain stable claim_ids and use only the accepted claims below. Copy
every preserved qualifier verbatim into the paragraph's qualifiers metadata, but integrate
its substance into natural research prose rather than copying directive wording. Never
address the writer or say "the paper should", "do not", or that something "must be"
analyzed, identified, or described. Do not introduce a new empirical result. Preserve
qualifications in prose. Do not use LaTeX or markdown.
{quoting_rule}
Every number is checked against the cited evidence, so an
unsupported one is rejected rather than printed; introduce no number that is not already in
an accepted claim, and leave full intervals and secondary quantities to the tables. Exact
configured model and checkpoint identifiers may appear when supplied in context_values. Avoid long
internal arm run identifiers in prose; their exact values remain in provenance.{correction_text}

Accepted claims:
{json.dumps(claims, indent=2, sort_keys=True)}

Relevant frozen facts:
{json.dumps(relevant_synthesis, indent=2, sort_keys=True)}

Completed earlier sections for coherence:
{json.dumps([section.model_dump(mode="json") for section in completed_sections or []], indent=2)}

Interpretation rules:
{json.dumps(evidence["authoring_context"]["interpretation_rules"], indent=2)}
"""
