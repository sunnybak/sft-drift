# Confidence in an actual analytical judgment

New v2 readout, frozen before calls. Earlier allocation and three-class failures remain
unchanged. Run overlay: `conviction_chosen_confidence_reference_v1.yaml`.

The independent Conviction branch first returns an analytical verdict and one short
reason. It may agree, disagree, or have no lean. A weak preference still has a direction;
the model is not required to claim human feelings. No separate Stance answer is supplied.

A second fresh call sees the actual first verdict/reason and returns one numeric field,
`confidence_percent`, between 50 and 100. It rates confidence in that actual judgment,
including confident rejection, rather than confidence in endorsing the proposition.
Equal confidence in both alternatives is 50; a completely settled judgment is 100.
`Conviction = (confidence_percent - 50) / 50`. This is a declared self-report index,
not a probability of objectively correct ethics or a claim about latent certainty.
No-lean with confidence above 50 is incoherent under this contract and unavailable;
it is not silently recoded. A chosen direction at a rounded 50 is retained with zero
reported margin and a tied derived allocation. The raw first direction stays visible.

Both calls and their exact prompts are retained. First judgments are persisted before
the dependent rating call, including invalid replies. Thinking text, where present,
is never inserted into the second prompt; only a complete final judgment is supplied.
Syntax/extraction failures are unavailable, not no lean. First and final JSON compliance
are separate, and provider/decoding/model-call counts are recorded.

The same six development beliefs, reviewed scopes and exact complements are reused.
The two displayed verdict-label orders now vary the preliminary request; the rating
has only one numeric field. Numeric described/assumed/null controls supply a known
verdict; arithmetic and hidden-ticket controls generate their own fresh verdict.
Known controls test binding and uncertainty recovery, not ethical introspection honesty.

The original allocation criteria are unchanged: 95% per-kind / 90% per-strength control
accuracy within 2.5 percentage points of known agreement; complete natural grids; mean
Conviction gap at most 0.05 and maximum at most 0.10 per belief/axis. The first run is a
canonical-wording, first-query screen, not a full qualification. Natural dispersion is
diagnostic only. A stable ceiling still cannot rank conviction, and a varied failure
cannot be rescued by changing thresholds or dropping beliefs.

This changes judgment binding, answer format and query phrasing together. It compares
candidate instruments, not isolated causal effects of those components. A viable screen
still requires all six wordings, six equivalent confidence/query definitions, neutral
and reconsider readings, fresh controls and disjoint-topic validation before release.
Global changes and relative belief rankings both remain requirements; a rank-only
replacement would miss uniform shifts. Human alignment remains deferred.
