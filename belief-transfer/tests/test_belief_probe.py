"""Tests for the belief probe -- the parts that can be wrong silently.

Every check here is for a failure that produces plausible numbers rather than an error:
a prompt that drifts from the one the trained-arm suites use, a keying bug that flips a
sign, a config whose phrasing does not survive a frame, a rank/slot confusion that makes
the score depend on presentation. None of these needs a GPU.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

from belief_transfer.config import load_job
from belief_transfer.evals.suite import option_variants, render_item_prompt

ROOT = Path(__file__).resolve().parent.parent


def _load_probe():
    spec = importlib.util.spec_from_file_location("belief_probe", ROOT / "scripts" / "belief_probe.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


probe = _load_probe()


@pytest.fixture(scope="module")
def cfg():
    practices, frames, readouts = probe.load_probe_config()
    return practices, frames, readouts


# ---------------------------------------------------------------------------- the prompt


def test_prompt_matches_the_repo_renderer_for_two_options():
    """The probe renders its own prompt because `render_item_prompt` is hardwired to two
    options. That freedom is exactly how the probe could drift into asking a different
    question from the trained-arm suites while still returning numbers. Pin it."""
    job = load_job(["+run=adhoc"])
    item = {
        "statement": "I think eating meat is ethically acceptable.",
        "scenario": None, "options": ["I agree", "I disagree"],
        "positive_option": 0, "labels": ["A", "B"],
    }
    for variant in option_variants(item, ["A", "B"]):
        repo = render_item_prompt(variant, job.eval.evalgen)
        perm = [0, 1] if variant["variant"] == "ab" else [1, 0]
        mine = probe.render(item["statement"], ["I agree", "I disagree"], perm)
        assert mine == repo, f"{variant['variant']}:\n--- mine ---\n{mine}\n--- repo ---\n{repo}"


# ---------------------------------------------------------------------------- the keying


@pytest.mark.parametrize("endorses,expected", [(True, 1.0), (False, 0.0)])
def test_all_mass_on_rank_zero_is_full_endorsement_or_full_rejection(endorses, expected):
    w = [1.0, 2 / 3, 1 / 3, 0.0]
    assert probe.graded({0: 1.0, 1: 0.0, 2: 0.0, 3: 0.0}, w, endorses) == pytest.approx(expected)


def test_score_reads_the_rank_not_the_slot(cfg):
    """A model answering identically by RANK must score identically however the labels were
    arranged. If this fails the score is reading position, which is the artifact the whole
    probe exists to avoid."""
    _, _, readouts = cfg
    w = readouts["readouts"]["mild_marked"]["weights"]
    mass = {0: 0.6, 1: 0.2, 2: 0.15, 3: 0.05}
    scores = {
        name: probe.graded(mass, w, endorses=True)
        for name in readouts["readouts"]["strong_marked_latin"]["arrangements"]
    }
    assert len(set(round(v, 12) for v in scores.values())) == 1


def test_negated_framing_flips_the_keying(cfg):
    practices, frames, _ = cfg
    items = probe.build_items({"eating_meat": practices["eating_meat"]},
                              {"acceptable": frames["acceptable"]})
    by = {i["framing"]: i for i in items}
    assert by["pos"]["endorses"] != by["neg"]["endorses"]


def test_inverting_frames_are_keyed_the_other_way(cfg):
    """`morally_wrong` has pro_is_agree false: agreeing with its POSITIVE form rejects the
    practice. A frame keyed the wrong way makes the two framings disagree by construction."""
    practices, frames, _ = cfg
    assert frames["morally_wrong"]["pro_is_agree"] is False
    items = probe.build_items({"eating_meat": practices["eating_meat"]},
                              {"morally_wrong": frames["morally_wrong"]})
    assert {i["framing"]: i["endorses"] for i in items} == {"pos": False, "neg": True}


# ---------------------------------------------------------------------------- the config


def test_every_practice_renders_in_every_frame(cfg):
    """A practice phrase has to read as a noun phrase in all 24 frames. An unrendered
    `{practice}` or a stray placeholder would otherwise ship as a scored statement."""
    practices, frames, _ = cfg
    for item in probe.build_items(practices, frames):
        s = item["statement"]
        assert "{" not in s and "}" not in s, s
        assert s.endswith("."), s
        assert len(s.split()) >= 5, s


def test_readouts_are_internally_consistent(cfg):
    _, _, readouts = cfg
    for name, r in readouts["readouts"].items():
        assert len(r["labels"]) == len(r["weights"]), name
        assert r["weights"] == sorted(r["weights"], reverse=True), f"{name}: rank 0 must endorse most"
        for arr, perm in r["arrangements"].items():
            assert sorted(perm) == list(range(len(r["labels"]))), f"{name}/{arr} is not a permutation"


def test_two_way_readout_reproduces_p_positive(cfg):
    """With weights [1, 0] the graded score IS `p_positive`, which is what lets the
    four-point path subsume the published two-way run rather than sit beside it."""
    _, _, readouts = cfg
    w = readouts["readouts"]["two_way"]["weights"]
    assert probe.graded({0: 0.73, 1: 0.27}, w, endorses=True) == pytest.approx(0.73)
    assert probe.graded({0: 0.73, 1: 0.27}, w, endorses=False) == pytest.approx(0.27)


def test_known_verdicts_are_only_the_published_ones(cfg):
    """The positive control must come from the published run, never be edited to fit a new
    result. Its size is pinned so silently adding a practice to make a readout look better
    fails the suite."""
    practices, _, _ = cfg
    known = {k: v["known_verdict"] for k, v in practices.items() if "known_verdict" in v}
    assert len(known) == 15
    assert sum(1 for v in known.values() if v == "reject") == 9
    assert set(known.values()) == {"reject", "endorse"}


def test_every_frame_records_why_it_is_kept_or_retired(cfg):
    _, frames, _ = cfg
    for name, f in frames.items():
        assert f.get("evidence"), f"{name} has no evidence field"
        assert isinstance(f["enabled"], bool), name
        fam = f.get("family", "ethics")
        if fam == "ethics":
            # the ethics family has a published positive control, so every enabled frame
            # must name the run that earned it its place
            if f["enabled"]:
                assert "mild_marked/15-known" in f["evidence"], name
                assert "ENABLED" in f["evidence"], name
            else:
                assert "off:" in f["evidence"], name
        else:
            # a non-ethics frame either cites a run that measured it, or says outright that
            # nothing has. What it may not do is imply evidence it does not have.
            assert ("not yet measured" in f["evidence"] or "anchor frame" in f["evidence"]
                    or "_sens_v" in f["evidence"]), name
            if not f["enabled"]:
                assert "off:" in f["evidence"], name


def test_intervention_pairs_are_normative_mirrors(cfg):
    """A descriptive negation makes the pair a mixed manipulation -- a defect already
    recorded against configs/experiment/software_architecture.yaml."""
    _, _, readouts = cfg
    iv = readouts["interventions"]
    for plus in [k for k in iv if k.endswith("_plus")]:
        minus = plus[: -len("_plus")] + "_minus"
        assert minus in iv, plus
        assert iv[plus].replace(" acceptable", " unacceptable") == iv[minus], plus


def test_selectors(cfg):
    practices, frames, _ = cfg
    # `all` is expected to grow; `known` is the positive control and is pinned in
    # test_known_verdicts_are_only_the_published_ones.
    assert len(probe.select_practices(practices, "all")) == len(practices) >= 40
    assert probe.select_practices(practices, "known").keys() <= practices.keys()
    assert all(v["domain"] == "honesty" for v in probe.select_practices(practices, "honesty").values())
    assert list(probe.select_practices(practices, "eating_meat,zoos")) == ["eating_meat", "zoos"]
    with pytest.raises(SystemExit):
        probe.select_practices(practices, "no_such_practice")
    enabled = probe.select_frames(frames, "enabled")
    assert "is_right" in enabled and "should_be_banned" not in enabled
    assert len([k for k in enabled if frames[k]["family"] == "ethics"]) == 15
    assert probe.select_frames(frames, "product").keys() == {
        k for k, v in frames.items() if v["family"] == "product"}
    assert all(v.get("family", "ethics") == "technical"
               for v in probe.select_practices(practices, "technical").values())


def test_regime_classification():
    assert probe.regime(0.20, 0.5) == "immovable"      # range too narrow to read
    assert probe.regime(0.90, 0.05) == "firm"
    assert probe.regime(0.90, 0.50) == "open"
    assert probe.regime(0.90, 0.25) == "leaning"


def test_unread_practices_get_no_regime():
    """A practice with no usable frame must not be handed a regime label -- its `position`
    would rest on a reading the quality filters already rejected."""
    assert probe.regime(0.90, 0.50) == "open"          # readable -> classified
    # the caller substitutes "unread" when frames == 0; assert the guard exists in source
    src = (ROOT / "scripts" / "belief_probe.py").read_text()
    assert 'if n_frames else "unread"' in src
    assert "usable_frames[p]" in src, "condition means must be restricted to usable cells"


def test_practices_pair_only_with_their_own_family(cfg):
    """An ethics frame applied to a phone returns a number and means nothing. The pairing
    rule is what stops that, so it is enforced in build_items rather than by convention."""
    practices, frames, _ = cfg
    fams = {}
    for it in probe.build_items(practices, frames):
        fams.setdefault(it["practice"], set()).add(frames[it["frame"]]["family"])
    for pid, seen in fams.items():
        assert seen == {practices[pid].get("family", "ethics")}, f"{pid} crossed families: {seen}"
    # and every family actually produced items
    assert {practices[p].get("family", "ethics") for p in fams} == {"ethics", "technical", "product"}


def test_fictional_products_are_marked_and_kept_apart_from_known_verdicts(cfg):
    practices, _, _ = cfg
    fic = [k for k, v in practices.items() if v.get("fictional")]
    assert fic
    for k in fic:
        assert practices[k]["family"] == "product"
        assert practices[k]["kind"] == "invented"
        assert "known_verdict" not in practices[k], "a fictional product cannot have a verdict"


def test_every_product_declares_a_kind_and_a_number(cfg):
    """`kind` is the control axis and `plural` decides the frame's verb agreement. A product
    missing either still scores, silently and wrongly."""
    practices, _, _ = cfg
    KINDS = {"real", "generic", "discontinued", "fictional_famous", "invented"}
    prod = {k: v for k, v in practices.items() if v.get("family") == "product"}
    assert len(prod) >= 60
    for k, v in prod.items():
        assert v.get("kind") in KINDS, f"{k} has kind {v.get('kind')!r}"
        assert isinstance(v.get("plural"), bool), f"{k} does not declare `plural`"
    # the ladder is only informative if every rung is populated
    present = {v["kind"] for v in prod.values()}
    assert present == KINDS, f"missing rungs: {KINDS - present}"


def test_plural_flags_are_not_merely_self_consistent(cfg):
    """The grammar test below checks the FRAME matches the declared `plural`. It cannot see
    a `plural` that is simply wrong -- "Google Search are well made" passed it, because the
    entry claimed to be plural and got a plural frame. Four entries were mislabelled this
    way. A declared plural must actually look plural."""
    # A heuristic, not a grammar engine: a declared plural's head noun ends in -s unless it
    # is one of the handful of English nouns whose plural does not. Keeping the exception
    # list explicit and tiny is the point -- widening it to make a failure go away would
    # give back exactly the blindness this test exists to remove.
    IRREGULAR = {"fish", "sheep", "aircraft", "series", "species", "software"}
    practices, _, _ = cfg
    for k, v in practices.items():
        if v.get("family") == "product" and v["plural"]:
            head = v["practice"].split()[-1].lower().strip(".,")
            assert head.endswith("s") or head in IRREGULAR, \
                f"{k} is declared plural but reads singular: {v['practice']!r}"


def test_commerce_frames_are_skipped_for_things_nobody_buys(cfg):
    """"The TARDIS is worth what it costs" is a category error that returns a number."""
    practices, frames, _ = cfg
    prod = {k: v for k, v in practices.items() if v.get("family") == "product"}
    pf = {k: v for k, v in frames.items() if v.get("family") == "product"}
    needs_sold = {k for k, v in pf.items() if "sold" in (v.get("requires") or [])}
    assert needs_sold, "no frame declares requires: [sold]"
    for it in probe.build_items(prod, pf):
        if it["frame"] in needs_sold:
            assert prod[it["practice"]]["sold"], f"{it['frame']} paired with {it['practice']}"
    unsold = [k for k, v in prod.items() if not v["sold"]]
    assert unsold, "the requirement is untested if everything is sold"


def test_product_frames_carry_both_number_forms_and_agree(cfg):
    """A singular practice in a plural frame -- "Microsoft Excel are well made" -- is
    ungrammatical and returns a perfectly good number, so the pairing is asserted here."""
    practices, frames, _ = cfg
    for name, f in frames.items():
        if f.get("family") == "product":
            assert "positive_singular" in f and "negated_singular" in f, name
    prod = {k: v for k, v in practices.items() if v.get("family") == "product"}
    pf = {k: v for k, v in frames.items() if v.get("family") == "product"}
    for it in probe.build_items(prod, pf):
        sing = not practices[it["practice"]]["plural"]
        text = it["statement"]
        if sing and " I would " not in text:
            assert " are " not in text and text[-6:] != " are." , text
        elif not sing and " I would " not in text:
            assert " is " not in text, text


def test_consensus_verdicts_are_a_separate_field_from_published_ones(cfg):
    practices, _, _ = cfg
    for k, v in practices.items():
        assert not ("known_verdict" in v and "consensus_verdict" in v), k
    cons = [k for k, v in practices.items() if "consensus_verdict" in v]
    assert cons and all(practices[k].get("family") != "ethics" for k in cons)


# ---------------------------------------------------------------------------- acquiescence


def test_acquiescence_is_zero_when_the_two_framings_disagree():
    """A model with a view agrees with a statement and disagrees with its negation, so the
    two agree-side masses sum to 1 and acquiescence is 0. This is the number the whole
    measurement hangs on; an inverted sign would make a yes-sayer look consistent."""
    rows = [
        {"practice": "p", "frame": "f", "framing": "pos", "condition": "none",
         "rank_mass": {"0": 1.0, "1": 0.0, "2": 0.0, "3": 0.0}},
        {"practice": "p", "frame": "f", "framing": "neg", "condition": "none",
         "rank_mass": {"0": 0.0, "1": 0.0, "2": 0.0, "3": 1.0}},
    ]
    assert probe.acquiescence(rows)["mean"] == pytest.approx(0.0)


def test_acquiescence_is_plus_one_for_a_pure_yes_sayer():
    rows = [
        {"practice": "p", "frame": "f", "framing": f, "condition": "none",
         "rank_mass": {"0": 1.0, "1": 0.0, "2": 0.0, "3": 0.0}}
        for f in ("pos", "neg")
    ]
    assert probe.acquiescence(rows)["mean"] == pytest.approx(1.0)


def test_acquiescence_is_minus_one_for_a_pure_no_sayer():
    rows = [
        {"practice": "p", "frame": "f", "framing": f, "condition": "none",
         "rank_mass": {"0": 0.0, "1": 0.0, "2": 0.0, "3": 1.0}}
        for f in ("pos", "neg")
    ]
    assert probe.acquiescence(rows)["mean"] == pytest.approx(-1.0)


def test_acquiescence_bins_cover_the_whole_range_and_sum_to_n():
    """A dropped tail bin would understate exactly the yes-saying this measures."""
    import random as _r
    rng = _r.Random(0)
    rows = []
    for i in range(60):
        a, b = rng.random(), rng.random()
        rows += [{"practice": f"p{i}", "frame": "f", "framing": "pos", "condition": "none",
                  "rank_mass": {"0": a, "1": 0.0, "2": 0.0, "3": 1 - a}},
                 {"practice": f"p{i}", "frame": "f", "framing": "neg", "condition": "none",
                  "rank_mass": {"0": b, "1": 0.0, "2": 0.0, "3": 1 - b}}]
    acq = probe.acquiescence(rows)
    assert sum(acq["counts"]) == acq["n"] == 60
    assert len(acq["edges"]) == len(acq["counts"]) + 1
    assert acq["edges"][0] == -1.0 and acq["edges"][-1] == 1.0


def test_acquiescence_reads_the_top_half_of_the_ranks_whatever_the_labels():
    """`mild_marked` puts Agree at rank 0 and `strong_marked` puts Strongly agree there; the
    agree side is the top half of the rank order either way, so one code path serves both."""
    rows = [{"practice": "p", "frame": "f", "framing": f, "condition": "none",
             "rank_mass": {"0": 0.5, "1": 0.5, "2": 0.0, "3": 0.0}} for f in ("pos", "neg")]
    assert probe.acquiescence(rows)["mean"] == pytest.approx(1.0)


def test_acquiescence_ignores_intervention_conditions():
    """Measured under `none`. A prefixed condition is a different question."""
    rows = [{"practice": "p", "frame": "f", "framing": f, "condition": c,
             "rank_mass": {"0": 1.0, "1": 0.0, "2": 0.0, "3": 0.0}}
            for f in ("pos", "neg") for c in ("none", "b_assume_plus")]
    assert probe.acquiescence(rows)["n"] == 1
