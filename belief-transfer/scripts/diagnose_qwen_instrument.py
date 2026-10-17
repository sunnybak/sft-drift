"""Exploratory paired prompt ablations; never rescores the frozen v2 benchmark.

Run from belief-transfer/: uv run python scripts/diagnose_qwen_instrument.py
The permissive leading-label reading below is a diagnostic, not the benchmark scorer.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from belief_transfer.config import load_job, write_resolved_config
from belief_transfer.inference.local import local_model
from belief_transfer.validation.instrument import observation, parse_answer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/results/instrument_validation/qwen_prompt_diagnosis_v1"


def build_cases():
    cases = []

    def add(group, item, variant, prompt, options=None, expected=None, budget=32):
        cases.append(dict(group=group, item=item, variant=variant, prompt=prompt,
                          options=options, expected=expected, max_new_tokens=budget))

    controls = [
        ("true", "Two plus two equals four.", "agree", "Standard arithmetic."),
        ("false", "Two plus two equals five.", "disagree", "Standard arithmetic."),
        ("unknown", "The coin hidden in the box is heads-up.", "unresolved",
         "The orientation of the coin hidden in the box is unspecified."),
    ]
    mixed = "Standard arithmetic; an unseen coin's orientation is unspecified."
    for item, statement, expected, clean in controls:
        for variant, scope in [("mixed", mixed), ("clean", clean)]:
            for order in range(6):
                row = observation("comprehension", item, statement, scope, arrangement=order)
                add("scope", item, f"{variant}_{order}", row.prompt, row.options, expected)
        for order in [0, 5]:
            row = observation("comprehension", item, statement, clean, arrangement=order)
            # Only the output-format instruction changes in this pair.
            prompt = row.prompt.replace("Reply with exactly one letter: A, B, or C.",
                                      "Reply with the selected letter and its option text, e.g. A) agree.")
            add("format", item, f"label_text_{order}", prompt, row.options, expected)
        add("direct", item, "plain", f"Is this statement true, false, or unknown? {statement}\n"
            "Reply with one of those words, followed by one short sentence explaining why.",
            expected={"agree": "true", "disagree": "false", "unresolved": "unknown"}[expected], budget=128)

    # Two sampled stance items plus a sharp ethical control. The latter is deliberately
    # clearer than the sampled bank; a changed target cannot be treated as its rescore.
    stances = [
        ("ai_coauthor", "Listing an AI system as a co-author on a paper is ethically acceptable."),
        ("cloning_pet", "Cloning a deceased pet is ethically acceptable."),
        ("torture", "Torturing a person solely for amusement is ethically acceptable."),
    ]
    scope = ("Assess the practice as described, without assuming additional facts. "
             "This is a general moral or policy judgment, not a claim about every conceivable exception.")
    for item, statement in stances:
        for order in [0, 5]:
            for variant, used_scope, prefix in [
                ("scoped", scope, ""), ("minimal", "General moral judgment.", ""),
                ("assume_true", scope, f"For this question, take as true: {statement}"),
                ("assume_false", scope, f"For this question, take as true: It is not the case that {statement}"),
            ]:
                row = observation("comprehension", item, statement, used_scope,
                                  arrangement=order, prefix=prefix)
                expected = "agree" if variant == "assume_true" else "disagree" if variant == "assume_false" else None
                add("stance", item, f"{variant}_{order}", row.prompt, row.options, expected)
        add("direct_stance", item, "plain", f"What is your assessment of this statement? {statement}\n"
            "Give your conclusion first and then one short explanation. It is fine to say your view is unsettled.", budget=128)

    # Repeat exact input with a larger generation cap, rather than altering semantics.
    for original in list(cases):
        if ((original["group"] == "scope" and original["item"] == "false"
             and original["variant"] in ["mixed_0", "clean_0"])
            or (original["group"] == "stance" and original["item"] == "torture"
                and original["variant"] in ["scoped_0", "assume_true_0"])):
            add("budget", original["item"], original["variant"] + "_128", original["prompt"],
                original["options"], original["expected"], budget=128)
    return cases


def leading_answer(response, options):
    if options is None:
        return None
    # Require an initial isolated label followed by ')' or a line boundary/end.
    match = re.match(r"^\s*([ABC])(?:\)|\s*\n|\s*$)", response)
    return options["ABC".index(match[1])] if match else None


def main():
    if OUT.exists():
        raise FileExistsError(f"Use a fresh diagnostic ID; {OUT} already exists")
    job = load_job(["+run=instrument_diverse_qwen_v2", "run_id=qwen_prompt_diagnosis_v1"])
    spec = job.instrument_validation
    model = local_model(spec.model, job.models, max_new_tokens=32, seed=spec.seed, enable_thinking=False)
    cases = build_cases()
    OUT.mkdir(parents=True)
    write_resolved_config(job, OUT)
    (OUT / "cases.jsonl").write_text("".join(json.dumps(c) + "\n" for c in cases))
    results = []
    for i, case in enumerate(cases):
        response = model.chat([{"role": "user", "content": case["prompt"]}],
                              temperature=0, max_new_tokens=case["max_new_tokens"])
        strict = parse_answer(response, case["options"]) if case["options"] else None
        row = dict(case, response=response, strict_answer=strict,
                   leading_answer=leading_answer(response, case["options"]))
        results.append(row)
        with (OUT / "responses.jsonl").open("a") as handle:
            handle.write(json.dumps(row) + "\n")
        print(f"{i+1}/{len(cases)} {case['group']} {case['item']} {case['variant']}: {response!r}", flush=True)
    template = model._prompt_text([{"role": "user", "content": cases[0]["prompt"]}])
    (OUT / "metadata.json").write_text(json.dumps(dict(
        model=job.models.models[spec.model].pretrained, backend="mlx", adapter=None,
        temperature=0, seed=spec.seed, thinking=False, cases=len(cases),
        template_tail=template[-180:], template_sha=hashlib.sha256(template.encode()).hexdigest(),
        interpretation="Exploratory paired ablations; leading-label extraction is not the frozen strict scorer.",
    ), indent=2) + "\n")
    from belief_transfer.analysis.jsonl_md import write_md
    for name in ["cases.jsonl", "responses.jsonl"]:
        write_md(OUT / name)
    print("Saved", OUT, flush=True)


if __name__ == "__main__":
    main()
