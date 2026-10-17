"""Pure reductions for categorical instrument observations (standard library only)."""
from collections import defaultdict
from statistics import mean


def _strict(row):
    """Legacy v2 valid answers were strict by definition; v3 records this separately."""
    if row.get("error") or row.get("answer") is None:
        return False
    flag = row.get("strict_format")
    return flag if flag is not None else True


def summarize_instrument(expected_rows: list[dict], responses: list[dict]) -> dict:
    """Expected rows must remain present even on model/format failures.

    No dropping cells to obtain a nicer score. Partial cells have null diagnostics.
    Order/paraphrase changes include unresolved answers; acquiescence requires two
    determinate answers and therefore always carries its own denominator.
    """
    def key(r):
        return tuple(r[k] for k in ("benchmark", "claim_id", "wording", "polarity", "condition", "arrangement"))

    expected = {key(r): r for r in expected_rows}
    observed = {key(r): r for r in responses}
    if len(expected) != len(expected_rows) or len(observed) != len(responses):
        raise ValueError("duplicate presentation identity")
    if observed.keys() - expected.keys():
        raise ValueError("unexpected presentation identity")
    rows = []
    for identity, row in expected.items():
        response = observed.get(identity)
        if response is None:
            rows.append({**row, "answer": None, "error": "missing response"})
        elif response["prompt_sha"] != row["prompt_sha"]:
            raise ValueError("response does not match the frozen prompt")
        else:
            rows.append({**row, "answer": response.get("answer") if not response.get("error") else None,
                         "response": response.get("response"),
                         "strict_format": response.get("strict_format"),
                         "answer_extraction": response.get("answer_extraction"),
                         "error": response.get("error")})
    output = {}
    checks = sorted({r["benchmark"] for r in rows})
    for check in checks:
        subset = [r for r in rows if r["benchmark"] == check]
        valid = [r for r in subset if r.get("answer") is not None and not r.get("error")]
        cells = defaultdict(list)
        for row in subset:
            cells[row["claim_id"]].append(row)
        result = {
            "n_expected": len(subset), "n_valid": len(valid),
            "n_strict_format": sum(_strict(r) for r in subset),
            "format_valid_rate": sum(_strict(r) for r in subset) / len(subset),
            "answer_extracted_rate": len(valid) / len(subset),
            "unresolved_rate": (sum(r["answer"] == "unresolved" for r in valid) / len(valid)) if valid else None,
            "coverage_status": "complete" if len(valid) == len(subset) else "incomplete",
            "claims": {},
        }
        for cid, group in cells.items():
            complete = all(r.get("answer") is not None and not r.get("error") for r in group)
            info = {"complete": complete}
            if check == "comprehension":
                info["accuracy"] = sum(r.get("answer") == r["expected"] for r in group) / len(group)
                info["strict_accuracy"] = sum(_strict(r) and r.get("answer") == r["expected"] for r in group) / len(group)
            if check == "option_order":
                info["distinct_answers"] = len({r["answer"] for r in group}) if complete else None
                info["stable"] = info["distinct_answers"] == 1 if complete else None
            if check == "negation":
                by_order = defaultdict(dict)
                for r in group:
                    by_order[r["arrangement"]][r["polarity"]] = r.get("answer")
                acq = []
                unresolved_pairs = 0
                incomplete_pairs = 0
                for pair in by_order.values():
                    if set(pair) != {"positive", "negative"} or None in pair.values():
                        incomplete_pairs += 1
                    elif "unresolved" in pair.values():
                        unresolved_pairs += 1
                    else:
                        acq.append(int(pair["positive"] == "agree") + int(pair["negative"] == "agree") - 1)
                info.update(n_pairs=len(by_order), n_determinate_pairs=len(acq),
                    n_unresolved_pairs=unresolved_pairs, n_incomplete_pairs=incomplete_pairs,
                    signed_acquiescence=mean(acq) if acq else None,
                    absolute_acquiescence=mean(abs(a) for a in acq) if acq else None)
            if check == "paraphrase":
                n_wordings = len({r["wording"] for r in group})
                comparisons = defaultdict(list)
                for r in group:
                    comparisons[r["arrangement"]].append(r.get("answer"))
                info.update(n_wordings=n_wordings,
                    stable_rate=mean(len(set(v)) == 1 for v in comparisons.values()) if complete and n_wordings > 1 else None,
                    status="measured" if n_wordings > 1 else "unavailable_no_paraphrases")
            if check == "responsiveness":
                conditions = defaultdict(list)
                for r in group:
                    conditions[r["condition"]].append(r)
                info["conditions"] = {}
                for cond, values in conditions.items():
                    answers = [r.get("answer") for r in values]
                    ok = all(a is not None for a in answers)
                    entry = {"agreement_rate": mean(a == "agree" for a in answers) if ok else None,
                             "unresolved_rate": mean(a == "unresolved" for a in answers) if ok else None}
                    if values[0]["expected"] is not None:
                        entry["expected_answer_rate"] = mean(a == values[0]["expected"] for a in answers)
                    info["conditions"][cond] = entry
                c = info["conditions"]
                for name, left, right in (("prompted_contrast", "positive", "negative"),
                                          ("neutral_shift", "neutral", "none"),
                                          ("offtopic_contrast", "offtopic_positive", "offtopic_negative")):
                    a, b = c[left]["agreement_rate"], c[right]["agreement_rate"]
                    info[name] = a - b if a is not None and b is not None else None
                for name, left, right in (("neutral_answer_change_rate", "neutral", "none"),
                                          ("offtopic_answer_change_rate", "offtopic_positive", "offtopic_negative")):
                    a = {r["arrangement"]: r.get("answer") for r in conditions[left]}
                    b = {r["arrangement"]: r.get("answer") for r in conditions[right]}
                    info[name] = mean(a[k] != b[k] for k in a) if a.keys() == b.keys() and all(a.values()) and all(b.values()) else None
            result["claims"][cid] = info
        output[check] = result
    return output


# Descriptive cross-model tables; conditional diagnostics retain coverage.

def _fraction(numerator: int, denominator: int, expected: int | None = None) -> dict:
    return {"numerator": numerator, "denominator": denominator,
            "expected": denominator if expected is None else expected,
            "value": numerator / denominator if denominator else None}


def compare_subset(bank: list[dict], observations: list[dict]) -> dict:
    """Every conditional diagnostic exposes eligibility against its expected grid.

    Six option orders and two poles of a tradeoff are repeated observations, not
    independent sampled topics. These are descriptive rates, without sampling CIs.
    """
    summaries = summarize_instrument(bank, observations)  # Identity/hash validation.
    fields = ("benchmark", "claim_id", "wording", "polarity", "condition", "arrangement")
    answers = {tuple(r[k] for k in fields): r for r in observations}
    rows = []
    for row in bank:
        reply = answers.get(tuple(row[k] for k in fields), {})
        answer = reply.get("answer") if not reply.get("error") else None
        rows.append({**row, "answer": answer, "strict_format": reply.get("strict_format")})
    valid = [r for r in rows if r["answer"] is not None]
    order = list(summaries.get("option_order", {}).get("claims", {}).values())
    negation = list(summaries.get("negation", {}).get("claims", {}).values())
    paraphrase = list(summaries.get("paraphrase", {}).get("claims", {}).values())
    determinate = sum(c["n_determinate_pairs"] for c in negation)
    contradictory = sum(round(c["absolute_acquiescence"] * c["n_determinate_pairs"])
                        for c in negation if c["absolute_acquiescence"] is not None)
    expected_pairs = sum(c["n_pairs"] for c in negation)
    signed_sum = sum(round(c["signed_acquiescence"] * c["n_determinate_pairs"])
                     for c in negation if c["signed_acquiescence"] is not None)
    # Existing per-claim reducer requires the complete paraphrase grid; keep that rule.
    complete_paraphrases = [c for c in paraphrase if c["stable_rate"] is not None]
    paraphrase_matches = sum(round(c["stable_rate"] * 6) for c in complete_paraphrases)
    manipulation = [r for r in rows if r["benchmark"] == "responsiveness"
                    and r["condition"] in {"positive", "negative"}]
    baseline = [r for r in rows if r["benchmark"] == "option_order"]
    baseline_valid = [r for r in baseline if r["answer"] is not None]
    result = {
        "topics": len({r["belief_id"] for r in bank if r["belief_id"]}),
        "source_units": len({r["cluster_id"] for r in bank if r["cluster_id"]}),
        "format_valid": _fraction(sum(_strict(r) for r in rows), len(rows)),
        "answer_extracted": _fraction(len(valid), len(rows)),
        "unresolved": _fraction(sum(r["answer"] == "unresolved" for r in valid), len(valid), len(rows)),
        "baseline_format_valid": _fraction(sum(_strict(r) for r in baseline), len(baseline)),
        "baseline_answer_extracted": _fraction(len(baseline_valid), len(baseline)),
        "baseline_unresolved": _fraction(sum(r["answer"] == "unresolved" for r in baseline_valid),
                                          len(baseline_valid), len(baseline)),
        "baseline_agree": _fraction(sum(r["answer"] == "agree" for r in baseline_valid),
                                     len(baseline_valid), len(baseline)),
        "baseline_disagree": _fraction(sum(r["answer"] == "disagree" for r in baseline_valid),
                                        len(baseline_valid), len(baseline)),
        "order_stable": _fraction(sum(c["stable"] is True for c in order),
                                  sum(c["complete"] for c in order), len(order)),
        "absolute_acquiescence": _fraction(contradictory, determinate, expected_pairs),
        "signed_acquiescence": _fraction(signed_sum, determinate, expected_pairs),
        "both_agree": _fraction((contradictory + signed_sum) // 2, determinate, expected_pairs),
        "both_disagree": _fraction((contradictory - signed_sum) // 2, determinate, expected_pairs),
        "negation_unresolved": _fraction(sum(c["n_unresolved_pairs"] for c in negation), expected_pairs),
        "negation_incomplete": _fraction(sum(c["n_incomplete_pairs"] for c in negation), expected_pairs),
        "paraphrase_stable": _fraction(paraphrase_matches, 6 * len(complete_paraphrases), 6 * len(paraphrase)),
        "assumption_correct": _fraction(sum(r["answer"] == r["expected"] for r in manipulation), len(manipulation)),
    }
    paired = defaultdict(dict)
    for r in rows:
        if r["benchmark"] == "responsiveness":
            paired[r["claim_id"], r["arrangement"]][r["condition"]] = r["answer"]
    for name, left, right in (("neutral_change", "neutral", "none"),
                              ("offtopic_change", "offtopic_positive", "offtopic_negative")):
        eligible = [c for c in paired.values() if c.get(left) is not None and c.get(right) is not None]
        result[name] = _fraction(sum(c[left] != c[right] for c in eligible), len(eligible), len(paired))
    return result


def comparison_table(bank: list[dict], observations: list[dict]) -> dict:
    """Pooled topics plus stratified families/subdomains/frames and global controls."""
    summarize_instrument(bank, observations)  # Validate whole input before filtering.
    fields = ("benchmark", "claim_id", "wording", "polarity", "condition", "arrangement")
    expected = {tuple(r[k] for k in fields): r for r in bank}
    for row in observations:
        frozen = expected[tuple(row[k] for k in fields)]
        if any(row[k] != frozen[k] for k in
               ("belief_id", "domain", "source_domain", "source_frame_id", "cluster_id")):
            raise ValueError("response grouping metadata differs from the frozen bank")
    output = {}
    for field in ("domain", "source_domain", "source_frame_id"):
        groups = {}
        for value in sorted({r[field] for r in bank if r["belief_id"]}):
            groups[value] = compare_subset([r for r in bank if r["belief_id"] and r[field] == value],
                                          [r for r in observations if r["belief_id"] and r[field] == value])
        output[field] = groups
    output["pooled"] = compare_subset([r for r in bank if r["belief_id"]],
                                       [r for r in observations if r["belief_id"]])
    controls = [r for r in bank if not r["belief_id"]]
    actual_controls = [r for r in observations if not r["belief_id"]]
    summary = summarize_instrument(controls, actual_controls)
    comprehension = summary.get("comprehension", {})
    output["controls"] = {
        "format_valid": _fraction(summary.get("format", {}).get("n_strict_format", 0),
                                  summary.get("format", {}).get("n_expected", 0)),
        "answer_extracted": _fraction(summary.get("format", {}).get("n_valid", 0),
                                      summary.get("format", {}).get("n_expected", 0)),
        "comprehension_correct": _fraction(sum(round(c["accuracy"] * 6)
             for c in comprehension.get("claims", {}).values()), comprehension.get("n_expected", 0)),
    }
    return output
