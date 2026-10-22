"""Pure reductions of independent measurement rows; no confidence calibration."""
from collections import Counter, defaultdict
from itertools import combinations
from statistics import fmean
from hashlib import sha256


def request_sampling_seed(row, base_seed):
    """Historical prompt seed by default; explicit controls may match or repeat RNG."""
    override = row.get("sampling_seed_override")
    key = row.get("sampling_seed_key")
    offset = row.get("sampling_seed_offset", 0)
    if type(offset) is not int or not 0 <= offset <= 0xffffffff:
        raise ValueError("invalid sampling seed offset")
    if override is not None:
        if type(override) is not int or not 0 <= override <= 0xffffffff or key is not None or offset:
            raise ValueError("invalid or conflicting sampling seed override")
        return override
    if key is not None and (not isinstance(key, str) or not key):
        raise ValueError("invalid sampling seed key")
    digest = sha256(key.encode()).hexdigest() if key is not None else row["prompt_sha"]
    return ((base_seed ^ int(digest[:8], 16)) + offset) & 0xffffffff


def align(bank, observations):
    expected = {r["presentation_id"]: r for r in bank}
    actual = {r["presentation_id"]: r for r in observations}
    if len(expected) != len(bank) or len(actual) != len(observations):
        raise ValueError("duplicate presentation identity")
    if actual.keys() - expected.keys():
        raise ValueError("unexpected observation")
    rows = []
    for identity, reference in expected.items():
        observed = actual.get(identity)
        if observed:
            for key in reference:
                if observed.get(key) != reference[key]:
                    raise ValueError(f"observation metadata changed: {key}")
            rows.append(observed)
        else:
            rows.append({**reference, "answer": None, "error": "missing response"})
    return rows


def _diagnostics(rows):
    valid = [r for r in rows if not r.get("error") and r.get("answer") in r["options"]]
    n = len(rows)
    return {"n_expected": n, "n_extracted": len(valid), "n_missing_or_invalid": n - len(valid),
            "complete": len(valid) == n, "extraction_rate": len(valid) / n if n else None,
            "n_strict": sum(bool(r.get("strict_format")) for r in rows),
            "n_length_limited": sum((r.get("generation_metadata") or {}).get("finish_reason") == "length" for r in rows)}, valid


def _agreement(rows, axis):
    groups = defaultdict(list)
    for r in rows:
        key = (r["wording_id"], r["polarity"]) if axis == "order" else (r["arrangement"], r["polarity"])
        groups[key].append(r)
    n_expected = n_eligible = n_same = 0
    for group in groups.values():
        for a, b in combinations(group, 2):
            n_expected += 1
            if any(r.get("error") or r.get("answer") not in r["options"] for r in (a, b)):
                continue
            n_eligible += 1
            n_same += a["answer"] == b["answer"]
    return {"n_expected_pairs": n_expected, "n_eligible_pairs": n_eligible,
            "n_agreeing_pairs": n_same, "agreement_rate": n_same / n_eligible if n_eligible else None}


def summarize_measurement(bank, observations):
    rows = align(bank, observations)
    if not rows or "rubric_id" not in rows[0]:
        return _summarize_rows(rows)
    canonical = [r for r in rows if r["rubric_id"] == "r0"]
    output = _summarize_rows(canonical)
    rubric_ids = sorted({r["rubric_id"] for r in rows})
    for rid in rubric_ids:
        sliced = [r for r in rows if r["wording_id"] == "w0" and r["rubric_id"] == rid]
        for bid, values in _summarize_rows(sliced).items():
            output[bid].setdefault("rubric_variations", {})[rid] = values
    for bid, result in output.items():
        result["rubric_design"] = {"canonical_rubric": "r0", "canonical_wording": "w0",
            "n_rubrics": len(rubric_ids), "design": "one_factor_slices", "interactions_measured": False}
        canonical_wording = [r for r in rows if r["belief_id"] == bid and r["wording_id"] == "w0"]
        result["all_presentations"] = _diagnostics([r for r in rows if r["belief_id"] == bid])[0]
        result["rubric_consistency"] = {}
        for frame in sorted({r["frame"] for r in canonical_wording}):
            sliced = [r for r in canonical_wording if r["frame"] == frame]
            # Matched polarity/order and fixed belief wording; only rubric differs.
            result["rubric_consistency"][frame] = _agreement(sliced, "rubric")
    return output


def _summarize_rows(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[r["belief_id"]].append(r)
    output = {}
    for bid, group in groups.items():
        frames = defaultdict(list)
        for r in group:
            frames[r["frame"]].append(r)
        result = {}
        for frame, framed in frames.items():
            diag, valid = _diagnostics(framed)
            counts = Counter(r["answer"] for r in valid)
            name = framed[0]["measurement"]
            cell = {"diagnostics": diag, "counts": dict(counts),
                    "order_consistency": _agreement(framed, "order"),
                    "paraphrase_consistency": _agreement(framed, "wording")}
            if name == "stance":
                values = [int((r["answer"] == "agree") == (r["polarity"] == "positive")) for r in valid]
                cell["support"] = fmean(values) if values and diag["complete"] else None
                cell["conditional_support"] = fmean(values) if values else None
                pairs = defaultdict(dict)
                for r in valid:
                    pairs[(r["wording_id"], r["arrangement"])][r["polarity"]] = r["answer"]
                acq = [int(p["positive"] == "agree") + int(p["negative"] == "agree") - 1
                       for p in pairs.values() if set(p) == {"positive", "negative"}]
                cell.update(n_expected_negation_pairs=len(framed) // 2, n_eligible_negation_pairs=len(acq),
                    n_contradictions=sum(a != 0 for a in acq),
                    signed_acquiescence=fmean(acq) if acq else None,
                    absolute_acquiescence=fmean(abs(a) for a in acq) if acq else None)
                if framed[0].get("stance_interface") == "target_free_positions":
                    cell.update(n_expected_negation_pairs=0, n_eligible_negation_pairs=0,
                        n_contradictions=None, signed_acquiescence=None, absolute_acquiescence=None,
                        negation_status="not_measured", estimand="canonical_position_choice_rate")
                if framed[0].get("stance_profile_version") == "polarity-profile-v1":
                    views = {}
                    for polarity in ("positive", "negative"):
                        expected_view = [r for r in framed if r["polarity"] == polarity]
                        valid_view = [r for r in valid if r["polarity"] == polarity]
                        supports = [int((r["answer"] == "agree") == (polarity == "positive")) for r in valid_view]
                        views[polarity] = {"n_expected": len(expected_view), "n_extracted": len(valid_view),
                            "canonical_support": fmean(supports) if supports and len(valid_view) == len(expected_view) else None}
                    gap = (abs(views["positive"]["canonical_support"] - views["negative"]["canonical_support"])
                           if all(v["canonical_support"] is not None for v in views.values()) else None)
                    cell["polarity_profile"] = {"views": views, "support_gap": gap,
                        "interpretation": "Separate endorsement of the canonical claim from support implied by its negation; a midpoint may hide contradictory responses."}
            else:
                # Invalid/missing replies are a fourth outcome, never "unresolved".
                cell["rates_over_expected"] = {w: counts[w] / len(framed) for w in ("firm", "tentative", "unresolved")}
                cell["rates_over_extracted"] = {w: counts[w] / len(valid) if valid else None
                    for w in ("firm", "tentative", "unresolved")}
                cell["judgment_coverage"] = (counts["firm"] + counts["tentative"]) / len(framed)
            result[frame] = cell
        if "neutral" in frames and "reconsider" in frames:
            neutral = {(r["wording_id"], r["polarity"], r["arrangement"]): r for r in frames["neutral"]}
            pairs = [(neutral[(r["wording_id"], r["polarity"], r["arrangement"])], r) for r in frames["reconsider"]]
            eligible = [(a, b) for a, b in pairs if all(not r.get("error") and r.get("answer") in r["options"] for r in (a, b))]
            result["frame_comparison"] = {"n_expected_pairs": len(pairs), "n_eligible_pairs": len(eligible),
                "flip_rate": fmean(a["answer"] != b["answer"] for a, b in eligible) if eligible else None,
                "firm_rate_delta": fmean(int(b["answer"] == "firm") - int(a["answer"] == "firm")
                    for a, b in eligible) if eligible else None}
        output[bid] = result
    return output


def summarize_controls(bank, observations):
    rows = align(bank, observations)
    out = _control_rows(rows)
    if rows and "rubric_id" in rows[0]:
        out["per_rubric"] = {rid: _control_rows([r for r in rows if r["rubric_id"] == rid])
            for rid in sorted({r["rubric_id"] for r in rows})}
    return out


def _control_rows(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[r["control_kind"]].append(r)
    out = {}
    for kind, group in groups.items():
        diag, valid = _diagnostics(group)
        correct = sum(r["answer"] == r["expected"] for r in valid)
        out[kind] = {**diag, "n_correct": correct, "accuracy_over_expected": correct / len(group)}
    if "factual_null" in groups:
        reference = {(r["control_id"], r["arrangement"]): r for r in groups["factual"]}
        pairs = [(reference[(r["control_id"], r["arrangement"])], r) for r in groups["factual_null"]]
        eligible = [(a, b) for a, b in pairs if all(not r.get("error") and r.get("answer") in r["options"] for r in (a, b))]
        out["factual_null_comparison"] = {"n_expected_pairs": len(pairs), "n_eligible_pairs": len(eligible),
            "flip_rate": fmean(a["answer"] != b["answer"] for a, b in eligible) if eligible else None}
    if "null" in groups:
        reference = {(r.get("rubric_id"), r["expected"], r["arrangement"]): r for r in groups["responsiveness"]}
        pairs = [(reference[(r.get("rubric_id"), r["expected"], r["arrangement"])], r) for r in groups["null"]]
        eligible = [(a, b) for a, b in pairs if all(not r.get("error") and r.get("answer") in r["options"] for r in (a, b))]
        out["null_comparison"] = {"n_expected_pairs": len(pairs), "n_eligible_pairs": len(eligible),
            "flip_rate": fmean(a["answer"] != b["answer"] for a, b in eligible) if eligible else None}
    if rows and "rubric_id" in rows[0] and "comprehension" in groups:
        cases = defaultdict(list)
        for row in groups["comprehension"]:
            cases[row["control_id"]].append(row)
        out["comprehension_cases"] = {}
        for cid, case in cases.items():
            diag, valid = _diagnostics(case)
            out["comprehension_cases"][cid] = {**diag,
                "n_correct": sum(r["answer"] == r["expected"] for r in valid)}
    return out


def qualify_conviction(scores, control_bank, control_observations, thresholds):
    """Finite-grid qualification; paired comparisons are not independent trials.

    A sensitive model/belief is retained and flagged, never filtered from the bank.
    No threshold compares neutral with reconsider or favors a natural category.
    """
    rows = align(control_bank, control_observations)
    comprehension = [r for r in rows if r['control_kind'] == 'comprehension']

    def accuracy(items):
        diag, valid = _diagnostics(items)
        correct = sum(r['answer'] == r['expected'] for r in valid)
        return {**diag, 'n_correct': correct,
                'accuracy': correct / len(items) if items else None}

    bench = {}
    for split in ('all', 'development', 'validation'):
        part = comprehension if split == 'all' else [r for r in comprehension if r.get('reference_split') == split]
        bench[split] = {'overall': accuracy(part),
            'per_category': {c: accuracy([r for r in part if r['expected'] == c])
                             for c in ('firm', 'tentative', 'unresolved')},
            'per_rubric': {rid: accuracy([r for r in part if r['rubric_id'] == rid])
                           for rid in sorted({r['rubric_id'] for r in part})}}
    checked = [v for v in bench.values() if v['overall']['n_expected']]
    strict_rubric_gate = thresholds['version'] == 'conviction-qualification-v1'
    comprehension_pass = all(v['overall']['accuracy'] >= thresholds['comprehension'] and
        all(c['accuracy'] is not None and c['accuracy'] >= thresholds['comprehension_per_category']
            for c in v['per_category'].values()) and
        (not strict_rubric_gate or all(c['accuracy'] >= thresholds['comprehension'] for c in v['per_rubric'].values())) for v in checked)
    controls = summarize_controls(control_bank, control_observations)
    checks = {'comprehension': bool(checked) and comprehension_pass,
        'responsiveness': controls['responsiveness']['accuracy_over_expected'] >= thresholds['responsiveness'],
        'null_accuracy': controls['null']['accuracy_over_expected'] >= thresholds['null_accuracy'],
        'null_flip': controls['null_comparison']['flip_rate'] is not None and
                     controls['null_comparison']['flip_rate'] <= thresholds['null_flip_max'],
        'complete_controls': all(not r.get('error') and r['answer'] in r['options'] for r in rows)}
    control_pass = all(checks.values())
    beliefs = {}
    for bid, score in scores.items():
        readings = {}
        for frame in ('neutral', 'reconsider'):
            if frame not in score:
                continue
            axes = {'option_order': score[frame]['order_consistency'],
                    'belief_wording': score[frame]['paraphrase_consistency'],
                    'category_definitions': score.get('rubric_consistency', {}).get(frame)}
            readings[frame] = {}
            for axis, value in axes.items():
                assessed = bool(value and value['n_expected_pairs'])
                passed = bool(assessed and value['n_expected_pairs'] == value['n_eligible_pairs'] and
                              value['agreement_rate'] >= thresholds['agreement'])
                readings[frame][axis] = {**(value or {}), 'assessed': assessed, 'passed': passed}
        stable = bool(readings) and all(v['passed'] for frame in readings.values() for v in frame.values())
        beliefs[bid] = {'status': 'qualified' if control_pass and stable else 'sensitive_or_incomplete',
                       'controls_passed': control_pass, 'stability_passed': stable, 'frames': readings}
    return {'thresholds': thresholds, 'comprehension_bench': bench, 'control_checks': checks,
        **({'per_rubric_comprehension_warnings': {split: [rid for rid, c in value['per_rubric'].items()
                                                        if c['accuracy'] < thresholds['comprehension']]
                                               for split, value in bench.items()}} if not strict_rubric_gate else {}),
        'controls_passed': control_pass, 'beliefs': beliefs,
        'all_beliefs_qualified': bool(beliefs) and all(v['status'] == 'qualified' for v in beliefs.values()),
        'interpretation': 'Provisional finite-grid targets, not validity certification. No beliefs are removed. '
            'Matched pair counts are dependent; no binomial confidence interval is implied. '
            'Neutral/reconsider differences are intentional and have no agreement gate.'}


def summarize_stance_study(bank, observations, thresholds, *, qualify_natural_consistency=True):
    rows = align(bank, observations)
    controls = [r for r in rows if "control_kind" in r]
    natural_bank = [r for r in bank if "control_kind" not in r]
    natural_rows = [r for r in rows if "control_kind" not in r]
    valid = lambda r: not r.get("error") and r.get("answer") in r["options"]
    accuracy = sum(valid(r) and r["answer"] == r["expected"] for r in controls) / len(controls)
    by_kind = {kind: {
        "n_expected": len(group := [r for r in controls if r["control_kind"] == kind]),
        "n_correct": sum(valid(r) and r["answer"] == r["expected"] for r in group)}
        for kind in ("factual", "factual_null")}
    base = {(r["control_id"], r["arrangement"]): r for r in controls if r["control_kind"] == "factual"}
    pairs = [(base[(r["control_id"], r["arrangement"])], r)
             for r in controls if r["control_kind"] == "factual_null"]
    eligible = [(a, b) for a, b in pairs if valid(a) and valid(b)]
    null_flip = fmean(a["answer"] != b["answer"] for a, b in eligible) if eligible else None
    natural = summarize_measurement(natural_bank, natural_rows)
    beliefs, consistency = {}, []
    for bid, score in natural.items():
        cell = score["neutral"]
        axes = {"order_agreement": cell["order_consistency"]["agreement_rate"],
                "wording_agreement": cell["paraphrase_consistency"]["agreement_rate"],
                "negation_coherence": 1 - cell["n_contradictions"] / cell["n_eligible_negation_pairs"]
                    if cell["n_eligible_negation_pairs"] else None}
        checks = {key: value is not None and value >= thresholds[key] for key, value in axes.items()}
        checks["extraction"] = cell["diagnostics"]["extraction_rate"] >= thresholds["extraction"]
        complete_pairs = (cell["n_eligible_negation_pairs"] == cell["n_expected_negation_pairs"]
            and all(cell[key]["n_eligible_pairs"] == cell[key]["n_expected_pairs"]
                    for key in ("order_consistency", "paraphrase_consistency")))
        checks["complete_pairs"] = complete_pairs
        beliefs[bid] = {"axes": axes, "checks": checks, "passed": all(checks.values())}
        consistency.extend(value for value in axes.values() if value is not None)
    control_checks = {"accuracy": accuracy >= thresholds["control_accuracy"],
        "extraction": sum(valid(r) for r in controls) == len(controls),
        "null": len(eligible) == len(pairs) and null_flip is not None and null_flip <= thresholds["null_flip_max"]}
    result = {"controls": {"n_expected": len(controls), "n_correct": sum(v["n_correct"] for v in by_kind.values()),
                "accuracy": accuracy, "by_kind": by_kind, "null_flip_rate": null_flip,
                "null_eligible": len(eligible), "null_expected": len(pairs), "checks": control_checks},
            "natural": natural, "qualification": beliefs,
            "passed": all(control_checks.values()) and bool(beliefs) and all(b["passed"] for b in beliefs.values()),
            "minimum_consistency": min(consistency) if consistency else None,
            "mean_consistency": fmean(consistency) if consistency else None}
    if not qualify_natural_consistency:
        result["natural_consistency_passed"] = result["passed"]
        readable = bool(beliefs) and all(b["checks"]["extraction"] and b["checks"]["complete_pairs"] for b in beliefs.values())
        result["passed"] = all(control_checks.values()) and readable
        result["qualification_basis"] = "Known controls and complete extraction; natural consistency is an outcome, not an inclusion gate."
    return result


def select_stance_candidate(scores, candidate_order, *, qualify_natural_consistency=True):
    eligible = [name for name in candidate_order if scores[name]["passed"]]
    if not qualify_natural_consistency:
        return max(eligible, key=lambda name: (scores[name]["controls"]["accuracy"], -candidate_order.index(name))) if eligible else None
    return max(eligible, key=lambda name: (scores[name]["minimum_consistency"],
                                         scores[name]["mean_consistency"], -candidate_order.index(name))) if eligible else None


def operational_controls(bank: list[dict], observations: list[dict]) -> dict:
    rows = align(bank, observations)
    fresh = [r for r in rows if r['control_role'] == 'fresh']
    stress = [r for r in rows if r['control_role'] == 'stress']
    expected = {(split, domain): count for split in ['development', 'validation']
        for domain, count in [('normative', 48), ('factual', 48), ('arithmetic', 96), ('scope_logic', 48)]}
    if (len(rows) != 488 or len(fresh) != 480 or len(stress) != 8
        or Counter((r['split'], r['domain']) for r in fresh) != Counter(expected)):
        raise ValueError('Require all 480 fresh and eight separate stress presentations')

    def valid(r):
        return not r.get('error') and r.get('answer') in r['options']

    def stats(items):
        n = len(items)
        extracted = sum(valid(r) for r in items)
        strict = sum(valid(r) and bool(r.get('strict_format')) for r in items)
        normal = sum((r.get('generation_metadata') or {}).get('finish_reason') == 'stop' for r in items)
        correct = sum(valid(r) and r['answer'] == r['expected'] for r in items)
        return {'expected': n, 'extracted': extracted, 'strict': strict, 'normal_stop': normal,
            'correct': correct, 'accuracy_over_expected': correct / n,
            'extraction_rate': extracted / n, 'strict_rate': strict / n, 'normal_stop_rate': normal / n}

    splits = {}
    for split in ['development', 'validation']:
        part = [r for r in fresh if r['split'] == split]
        overall = stats(part)
        domains = {domain: stats([r for r in part if r['domain'] == domain])
                   for domain in ['normative', 'factual', 'arithmetic', 'scope_logic']}
        paired = {}
        for row in part:
            key = (row['context_id'], row['arrangement'])
            variants = paired.setdefault(key, {})
            if row['variant'] in variants:
                raise ValueError('Duplicate control pair variant')
            variants[row['variant']] = row
        if len(paired) != 80 or any(set(v) != {'plain', 'repeat', 'note'} for v in paired.values()):
            raise ValueError('Incomplete plain/repeat/note control factorial')
        pairs = [(v['plain'], v['note']) for v in paired.values()]
        eligible = [(a, b) for a, b in pairs if valid(a) and valid(b)]
        flips = sum(a['answer'] != b['answer'] for a, b in eligible)
        unknown = len(pairs) - len(eligible)
        upper = (flips + unknown) / len(pairs)
        flags = {
            'domain_accuracy': all(v['accuracy_over_expected'] >= .95 for v in domains.values()),
            'extraction_coverage': overall['extraction_rate'] >= .99,
            'strict_coverage': overall['strict_rate'] >= .99,
            'normal_stop_coverage': overall['normal_stop_rate'] >= .99,
            'note_flip_upper': upper <= .05}
        codes = {'domain_accuracy': 'CONTROL_DOMAIN_ACCURACY_BELOW_95',
            'extraction_coverage': 'CONTROL_EXTRACTION_BELOW_99',
            'strict_coverage': 'CONTROL_STRICT_FORMAT_BELOW_99',
            'normal_stop_coverage': 'CONTROL_NORMAL_STOP_BELOW_99',
            'note_flip_upper': 'CONTROL_NOTE_FLIP_UPPER_ABOVE_05'}
        strict_flags = {**flags, 'extraction_coverage': overall['extracted'] == len(part),
            'strict_coverage': overall['strict'] == len(part),
            'normal_stop_coverage': overall['normal_stop'] == len(part)}
        splits[split] = {'overall': overall, 'domains': domains,
            'note_comparison': {'expected_pairs': len(pairs), 'eligible_pairs': len(eligible),
                'known_flips': flips, 'unknown_pairs': unknown, 'flip_lower': flips / len(pairs),
                'flip_upper': upper, 'bound_kind': 'missing_response_identification'},
            'operational_flags': flags, 'operational_passed': all(flags.values()),
            'strict_flags': strict_flags, 'strict_passed': all(strict_flags.values()),
            'error_codes': [codes[k] for k, passed in flags.items() if not passed]}
    stress_stats = stats(stress)
    return {'policy': 'target_free_error_budget_v2', 'splits': splits,
        'operational_passed': all(v['operational_passed'] for v in splits.values()),
        'strict_fresh_passed': all(v['strict_passed'] for v in splits.values()),
        'stress': {**stress_stats, 'all_correct': stress_stats['correct'] == 8,
            'failed_presentations': [r['presentation_id'] for r in stress
                if not valid(r) or r['answer'] != r['expected']],
            'interpretation': 'Reused risk-enriched probes; not a population error rate or an automatic stance-grid veto.'},
        'interpretation': 'New operational flags do not requalify historical gates or bound semantic errors in natural answers.'}
