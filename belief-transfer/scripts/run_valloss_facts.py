"""One-off: held-out span NLL specialization at FACT resolution, with unit-aware span
attribution, netted against the off-topic control arms.

Why this exists: `run_valloss_dimensions.py` found real per-dimension heterogeneity, but
its sentence-level attribution is too coarse to trust the two dimensions that matter
most. Dumping the selected spans showed worker-conditions sweeping in dates ("2023"),
shift hours ("44 hours"), dollar wages ("16.40"), stocking density ("1.2 square"), and
the "per 1,000 workers" denominator fragments -- none of which are premise figures.
Food affordability rested on ~5 tokens/doc. Any conclusion about M+ from those two
dimensions inherits that junk.

This version attributes each NUMERIC EXPRESSION individually instead of each sentence:

  1. A number qualifies only if its trailing unit word matches the fact's own unit
     (percent / litres / recordable), parsed from the spec. This alone removes years,
     hours, dollar amounts, and denominators -- "2023 report", "44 hours", "16.40",
     "000 workers" all fail the unit test.
  2. The number is attributed to a fact by keyword hits in a small window around it,
     where a fact's keywords are the words its two polarity strings SHARE (they differ
     only in numbers, so the shared words cannot encode direction). Ties and zero-hit
     numbers are dropped, never guessed.
  3. As an audit, every selected span is checked against the polarity's own spec range;
     the match rate is printed and out-of-range examples are shown. This is a *report*,
     not a filter -- filtering on the polarity's values would reintroduce direction as a
     selection effect.

The statistic is unchanged (base-corrected paired specialization, net of the matched
M0 control), now resolved per fact and rolled up per dimension.

Usage:
    uv run python scripts/run_valloss_facts.py
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from dotenv import find_dotenv, load_dotenv

from belief_transfer.config import load_job
from belief_transfer.dataset import gate
from belief_transfer.evals import efficacy
from belief_transfer.inference.local import local_model
from belief_transfer.inference.model import free_gpu
from belief_transfer.metrics import bootstrap_ci
from belief_transfer.training import dataset as sft_dataset
from belief_transfer.training import sft

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_valloss import RUN_ID as VALSPLIT_RUN_ID  # noqa: E402
from scripts.run_valloss import CORPUS_RUN, N_VAL_PAIRS, split_pairs  # noqa: E402

load_dotenv(find_dotenv())

OUT_RUN_ID = "valsplit-ff-facts"
M0_RUN_ID = "m0-split-v2"

STOPWORDS = frozenset(
    "a an the of in on at to for per and or with under over above below is are be than "
    "that this these those it its from by as more less".split()
)
UNIT_WORDS = frozenset({"percent", "litres", "liters", "recordable"})
# number, optionally "X to Y", capturing the trailing word separately so it can be
# required to be the fact's unit
NUMBER_UNIT_RE = re.compile(
    r"(\d+(?:\.\d+)?(?:\s*(?:to|-|–|—)\s*\d+(?:\.\d+)?)?)\s+([A-Za-z-]+)"
)
WINDOW_LEFT = 10  # words of context searched for fact keywords
WINDOW_RIGHT = 6  # keywords often FOLLOW the number ("12.4 recordable injuries per 1,000 workers")
RIGHT_PENALTY = 1.5  # right-side matches count as farther, so a left keyword wins ties


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z][a-z-]+", text.lower()) if w not in STOPWORDS}


def parse_facts(dimensions: dict) -> list[dict]:
    """One entry per contrastive fact: keywords, unit, and each polarity's value range.

    Keywords are the words the two polarity strings share minus units and stopwords --
    polarity-blind by construction. Ranges come from the spec strings themselves
    ("2 to 4" -> (2, 4); "under 3" -> (0, 3)).
    """

    def rng(fact: str) -> tuple[float, float]:
        m = re.search(r"under\s+(\d+(?:\.\d+)?)", fact)
        if m:
            return (0.0, float(m.group(1)))
        m = re.search(r"(\d+(?:,\d+)?(?:\.\d+)?)\s+to\s+(\d+(?:,\d+)?(?:\.\d+)?)", fact)
        if m:
            return (float(m.group(1).replace(",", "")), float(m.group(2).replace(",", "")))
        raise ValueError(f"no range in fact: {fact!r}")

    facts = []
    for dimension, polarities in dimensions.items():
        for positive, negative in zip(polarities.positive, polarities.negative, strict=True):
            if positive == negative:
                continue  # shared premise, no contrast
            unit = next(w for w in positive.split() if w.lower() in UNIT_WORDS)
            shared = _words(positive) & _words(negative) - UNIT_WORDS
            facts.append({
                "dimension": dimension,
                "name": "_".join(sorted(shared))[:40] or dimension,
                "keywords": shared,
                "unit": unit.lower(),
                "range": {"positive": rng(positive), "negative": rng(negative)},
                "canonical": {
                    "positive": re.search(r"(?:under )?\d[\d.,]*(?:\s+to\s+\d[\d.,]*)?", positive).group(0),
                    "negative": re.search(r"(?:under )?\d[\d.,]*(?:\s+to\s+\d[\d.,]*)?", negative).group(0),
                },
            })
    # keywords must be distinctive across facts, or attribution can tie
    for fact in facts:
        others = set().union(*(f["keywords"] for f in facts if f is not fact))
        fact["distinct"] = fact["keywords"] - others
    return facts


def fact_spans(text: str, facts: list[dict]) -> dict[str, list[tuple[int, int, str]]]:
    """(start, end, matched_number) of premise numeric expressions, keyed by fact name.

    A number is kept only if its trailing word is some fact's unit, and is attributed to
    the fact whose keyword sits NEAREST to it (in words, right-side matches penalized so
    the left keyword wins ties). Nearest-distance rather than window hit-count: in
    "mortality at 9.4 percent and lameness in 17.2 percent", a hit-count over the left
    window hands 17.2 to mortality; distance hands it to lameness, which is right.
    Ties and keyword-free numbers are dropped, never guessed.
    """

    def clean(word: str) -> str:
        return word.strip(".,;:()’'\"").lower()

    out: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    for m in NUMBER_UNIT_RE.finditer(text):
        number, unit = m.group(1), m.group(2).lower()
        if unit not in UNIT_WORDS:
            continue
        left = [clean(w) for w in text[: m.start()].split()[-WINDOW_LEFT:]][::-1]
        right = [clean(w) for w in text[m.end():].split()[:WINDOW_RIGHT]]
        distances: dict[int, float] = {}
        for i, fact in enumerate(facts):
            if fact["unit"] != ("litres" if unit == "liters" else unit):
                continue
            candidates = [d + 1 for d, w in enumerate(left) if w in fact["keywords"]]
            candidates += [(d + 1) * RIGHT_PENALTY for d, w in enumerate(right) if w in fact["keywords"]]
            if candidates:
                distances[i] = min(candidates)
        if not distances:
            continue
        best = min(distances.values())
        winners = [i for i, d in distances.items() if d == best]
        if len(winners) != 1:
            continue
        fact = facts[winners[0]]
        out[fact["name"]].append((m.start(), m.start() + len(number) + 1 + len(m.group(2)), number))
    return out


def span_nll_for_facts(model, prompt: str, text: str, facts) -> dict[str, tuple[float, int]]:
    """Mean per-token NLL of each fact's premise spans within `text`.

    Offsets come from tokenizing the joined prompt+text: BPE can merge across the join,
    so a standalone tokenization of the text is not guaranteed to align.
    """
    import torch

    spans = fact_spans(text, facts)
    if not spans:
        return {}
    model._ensure_loaded()
    tokenizer, hf = model._tokenizer, model._hf_model
    prompt_text = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True
    )
    enc = tokenizer(prompt_text + text, add_special_tokens=False, return_offsets_mapping=True)
    ids, offsets = enc["input_ids"], enc["offset_mapping"]

    input_ids = torch.tensor([ids], device=hf.device)
    with torch.inference_mode():
        logits = hf(input_ids=input_ids).logits
    log_probs = torch.log_softmax(logits[0, :-1].float(), dim=-1)
    token_lp = log_probs.gather(-1, input_ids[0, 1:].unsqueeze(-1)).squeeze(-1)

    base = len(prompt_text)
    out: dict[str, tuple[float, int]] = {}
    for name, fact_span_list in spans.items():
        shifted = [(s + base, e + base) for s, e, _ in fact_span_list]
        picked = [
            float(token_lp[i - 1])
            for i in range(1, len(ids))
            if offsets[i][1] > offsets[i][0]
            and any(offsets[i][0] >= s and offsets[i][1] <= e for s, e in shifted)
        ]
        if picked:
            out[name] = (-statistics.fmean(picked), len(picked))
    return out


def audit(val_pairs: dict, facts: list[dict]) -> dict:
    """Selection quality: how often a selected number sits in its polarity's spec range.

    Reported, not filtered on (see module docstring). Also returns per-fact span counts.
    """
    in_range: Counter = Counter()
    total: Counter = Counter()
    examples: dict[str, list[str]] = defaultdict(list)
    by_name = {f["name"]: f for f in facts}
    for pair in val_pairs.values():
        for polarity in ("positive", "negative"):
            text = pair[polarity]["text"]
            for name, span_list in fact_spans(text, facts).items():
                lo, hi = by_name[name]["range"][polarity]
                for start, end, number in span_list:
                    total[name] += 1
                    first = float(re.match(r"\d+(?:\.\d+)?", number).group(0))
                    if lo * 0.7 <= first <= hi * 1.3 or lo <= first <= hi:
                        in_range[name] += 1
                    elif len(examples[name]) < 4:
                        examples[name].append(f"[{polarity[:3]}] {text[max(0,start-45):end+5]!r}")
    return {"in_range": dict(in_range), "total": dict(total), "examples": dict(examples)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--val-pairs", type=int, default=N_VAL_PAIRS)
    parser.add_argument("--audit-only", action="store_true", help="no GPU: print span selection audit and exit")
    parser.add_argument("--canon", action="store_true",
                        help="score the valsplit-ff-canon checkpoints on the canonicalized corpus instead")
    args = parser.parse_args(argv)

    job = load_job([f"+run={CORPUS_RUN}"])
    training, experiment = job.training, job.experiment
    corpus_run_id = "valsplit-ff-canon" if args.canon else job.run_id
    content_run_id = "valsplit-ff-canon" if args.canon else VALSPLIT_RUN_ID
    out_run_id = OUT_RUN_ID + ("-canon" if args.canon else "")
    documents = sft_dataset.load_validated_documents(
        gate.validated_documents_path(experiment.id, corpus_run_id)
    )
    _, val_pairs = split_pairs(documents, args.val_pairs)
    prompt = sft_dataset.sft_prompt(experiment.dataset.topic)

    facts = parse_facts(experiment.dataset.dimensions)
    print("[facts] parsed from the spec (keywords are polarity-blind by construction):")
    for fact in facts:
        print(f"    {fact['dimension']:<22} {fact['name']:<28} unit={fact['unit']:<10} "
              f"kw={sorted(fact['keywords'])}")

    report = audit(val_pairs, facts)
    print("\n[facts] span selection audit over the held-out pairs "
          "(in-range rate is a quality report, not a filter):")
    for fact in facts:
        name = fact["name"]
        n, ok = report["total"].get(name, 0), report["in_range"].get(name, 0)
        rate = f"{ok/n:.0%}" if n else "--"
        print(f"    {name:<28} {n:>4} spans   in own polarity's range: {rate}")
        for example in report["examples"].get(name, []):
            print(f"        out-of-range: {example}")
    if args.audit_only:
        return 0

    root = sft.CHECKPOINTS_DIR / experiment.id
    conditions = [
        ("base", None),
        ("m_plus", root / content_run_id / "positive" / "final"),
        ("m_minus", root / content_run_id / "negative" / "final"),
        ("m0_plus", root / M0_RUN_ID / "positive" / "final"),
        ("m0_minus", root / M0_RUN_ID / "negative" / "final"),
    ]
    for name, adapter in conditions:
        if adapter is not None and not adapter.exists():
            print(f"missing {name} checkpoint at {adapter}")
            return 2

    # nll[condition][fact][index][polarity]
    nll: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    for name, adapter in conditions:
        model = local_model(training.model, job.models, adapter_path=adapter)
        print(f"[facts] scoring {name} over {len(val_pairs)} held-out pairs ...")
        for i, pair in val_pairs.items():
            for polarity in ("positive", "negative"):
                for fact_name, (value, _) in span_nll_for_facts(
                    model, prompt, pair[polarity]["text"], facts
                ).items():
                    nll[name][fact_name][i][polarity] = value
        del model
        free_gpu()

    def specialization_block(fact_names: list[str], label: str) -> dict | None:
        """Paired specialization over pairs where every condition scored every polarity.

        For dimension rollups the per-pair value is the mean over that dimension's facts
        present in the pair (a pair needs at least one usable fact, not all of them).
        """
        rows = {}
        for c, _ in conditions:
            per_pair: dict[int, list[float]] = defaultdict(list)
            for fact_name in fact_names:
                for i, pols in nll[c][fact_name].items():
                    if {"positive", "negative"} <= pols.keys():
                        per_pair[i].append(pols["negative"] - pols["positive"])
            rows[c] = {i: statistics.fmean(v) for i, v in per_pair.items()}
        usable = sorted(set.intersection(*(set(rows[c]) for c, _ in conditions)))
        if len(usable) < 5:
            print(f"\n--- {label} --- SKIPPED: {len(usable)} usable pairs")
            return None
        D = {c: [rows[c][i] for i in usable] for c, _ in conditions}
        spec = {
            "M+": [a - b for a, b in zip(D["m_plus"], D["base"])],
            "M-": [-(a - b) for a, b in zip(D["m_minus"], D["base"])],
            "M0+": [a - b for a, b in zip(D["m0_plus"], D["base"])],
            "M0-": [-(a - b) for a, b in zip(D["m0_minus"], D["base"])],
        }
        spec["M+ NET"] = [a - b for a, b in zip(spec["M+"], spec["M0+"])]
        spec["M- NET"] = [a - b for a, b in zip(spec["M-"], spec["M0-"])]
        print(f"\n--- {label} ---  {len(usable)} pairs   "
              f"base D = {statistics.fmean(D['base']):+.4f} "
              f"(>0: positive doc more predictable to base)")
        entry: dict = {"n_pairs": len(usable), "base_D": statistics.fmean(D["base"])}
        for spec_label, values in spec.items():
            lo, hi = bootstrap_ci(values)
            mark = "EXCLUDES ZERO" if (lo > 0 or hi < 0) else "straddles zero"
            print(f"    {spec_label:<8} {statistics.fmean(values):+.4f}  [{lo:+.4f}, {hi:+.4f}]  {mark}")
            entry[spec_label] = {"mean": statistics.fmean(values), "ci95": [lo, hi]}
        return entry

    print(f"\n{'='*84}")
    print("PER FACT: specialization toward own corpus, base-corrected, net rows subtract")
    print("the matched off-topic control arm (M0)")
    print(f"{'='*84}")
    summary: dict = {"facts": {}, "dimensions": {}}
    for fact in facts:
        entry = specialization_block([fact["name"]], f"{fact['dimension']} / {fact['name']}")
        if entry:
            summary["facts"][fact["name"]] = {"dimension": fact["dimension"], **entry}

    print(f"\n{'='*84}")
    print("PER DIMENSION rollup (mean over the dimension's facts present in each pair)")
    print(f"{'='*84}")
    for dimension in sorted({f["dimension"] for f in facts}):
        names = [f["name"] for f in facts if f["dimension"] == dimension]
        entry = specialization_block(names, dimension)
        if entry:
            summary["dimensions"][dimension] = entry

    out = Path(efficacy.summary_path(experiment.id, out_run_id))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump({
        "experiment": experiment.id, "run_id": out_run_id,
        "checkpoints_from": {"content_arms": content_run_id, "control_arms": M0_RUN_ID},
        "corpus_run": corpus_run_id,
        "note": "fact-level held-out span NLL specialization, unit-aware window "
                "attribution, netted against the off-topic control arms. Selection is "
                "polarity-blind; the in-range audit is a report, not a filter.",
        "audit": {k: report[k] for k in ("in_range", "total")},
        "summary": summary,
    }, sort_keys=False))
    print(f"\n[facts] wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
