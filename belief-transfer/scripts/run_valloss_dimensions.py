"""One-off: held-out span NLL specialization, broken out PER DIMENSION and netted
against the off-topic control arms.

`scripts/run_valloss_spans.py` established that M- specializes strongly at `numbers`
granularity (+0.185) while M+ is flat at zero (-0.003), and concluded M+ never learned
its premises. Two things since then say that conclusion is measured at the wrong
resolution -- the same mistake run_valloss_spans.py itself was written to fix, one level
up:

  1. The control arms specialize too. Scoring M0+/M0- (trained on the *off-topic* corpus,
     zero factory-farming content) over the same held-out pairs returns -0.045 and +0.055
     at `numbers`, both excluding zero. A raw specialization number is therefore
     contaminated by any-SFT drift exactly as the forced-choice dE was, and the per-arm
     gate EFFICACY.md 4 proposes has to be stated net of that control.

  2. The forced-choice reading, broken out per dimension, is wildly heterogeneous: the
     machinery term alone ranges from -0.109 (food affordability) to +0.146 (worker
     conditions). One global correction is wrong for every dimension, and a statistic
     pooled over dimensions that behave this differently can average a real effect
     against an artifact and report zero.

So: same statistic, same checkpoints, same held-out pairs, resolved per dimension and
per arm, with the control arms carried through.

Span attribution is POLARITY-BLIND, which is the whole methodological point and the
easiest thing to get wrong. The two polarities of a fact differ only in their numbers
(see configs/experiment/factory_farming.yaml), so the words they SHARE are a descriptor
of the dimension that cannot encode direction. Keywords are derived from that shared
wording automatically rather than hand-listed, and only words distinctive to one
dimension are kept. Selecting each arm's spans by its own values would reintroduce, as a
selection effect, precisely the asymmetry this exists to measure.

`efficiency` is excluded: its two polarities are identical by design, so it carries no
contrast and its "specialization" is definitionally noise.

Usage:
    uv run python scripts/run_valloss_dimensions.py
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from collections import defaultdict
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
from scripts.run_valloss_spans import NUMBER_RE, sentence_spans  # noqa: E402

load_dotenv(find_dotenv())

OUT_RUN_ID = "valsplit-ff-dimensions"
M0_RUN_ID = "m0-split-v2"

# Words carrying no dimension information. Deliberately small: the distinctiveness filter
# below does most of the work, and a long hand-tuned list would be another place for a
# judgement call about which dimension a word "belongs" to to creep in.
STOPWORDS = frozenset(
    "a an the of in on at to for per and or with under over above below is are be than "
    "that this these those it its from by as more less".split()
)


def dimension_keywords(dimensions: dict) -> dict[str, frozenset[str]]:
    """Distinctive, polarity-blind keywords per dimension, derived from the spec.

    For each dimension, take the words its positive and negative fact strings SHARE --
    they differ only in numbers, so the intersection describes the measured quantity
    without encoding a direction -- then keep only words no other dimension claims.
    """
    shared: dict[str, set[str]] = {}
    for dimension, polarities in dimensions.items():
        words: set[str] = set()
        for positive, negative in zip(polarities.positive, polarities.negative, strict=True):
            if positive == negative:
                continue  # shared premise: no contrast, excluded (see module docstring)
            tokenize = lambda text: {  # noqa: E731
                w for w in re.findall(r"[a-z][a-z-]+", text.lower())
                if w not in STOPWORDS
            }
            words |= tokenize(positive) & tokenize(negative)
        if words:
            shared[dimension] = words

    return {
        dimension: frozenset(
            words - set().union(*(other for d, other in shared.items() if d != dimension))
        )
        for dimension, words in shared.items()
    }


def dimension_spans(text: str, keywords: dict[str, frozenset[str]]) -> dict[str, list[tuple[int, int]]]:
    """Char spans of numeric expressions, grouped by the dimension of their sentence.

    A digit-bearing sentence is attributed to whichever dimension its distinctive
    keywords best match; ties and misses are dropped rather than guessed, so an
    unattributable sentence contributes to no dimension instead of to the wrong one.
    """
    out: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for start, end in sentence_spans(text):
        sentence = text[start:end].lower()
        words = set(re.findall(r"[a-z][a-z-]+", sentence))
        hits = {d: len(words & kw) for d, kw in keywords.items()}
        best = max(hits.values(), default=0)
        if best == 0:
            continue
        winners = [d for d, n in hits.items() if n == best]
        if len(winners) != 1:
            continue
        out[winners[0]].extend(
            (start + m.start(), start + m.end()) for m in NUMBER_RE.finditer(text[start:end])
        )
    return out


def span_nll_by_dimension(model, prompt: str, text: str, keywords) -> dict[str, tuple[float, int]]:
    """Mean per-token NLL of each dimension's numeric spans within `text`.

    Offsets come from tokenizing the joined prompt+text, not the text alone: BPE can merge
    across the join, so a standalone tokenization is not guaranteed to align and a
    misaligned span silently averages the wrong tokens.
    """
    import torch

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
    for dimension, spans in dimension_spans(text, keywords).items():
        shifted = [(s + base, e + base) for s, e in spans]
        picked = [
            float(token_lp[i - 1])
            for i in range(1, len(ids))
            if offsets[i][1] > offsets[i][0]
            and any(offsets[i][0] >= s and offsets[i][1] <= e for s, e in shifted)
        ]
        if picked:
            out[dimension] = (-statistics.fmean(picked), len(picked))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--val-pairs", type=int, default=N_VAL_PAIRS)
    args = parser.parse_args(argv)

    job = load_job([f"+run={CORPUS_RUN}"])
    training, experiment = job.training, job.experiment
    documents = sft_dataset.load_validated_documents(
        gate.validated_documents_path(experiment.id, job.run_id)
    )
    _, val_pairs = split_pairs(documents, args.val_pairs)
    prompt = sft_dataset.sft_prompt(experiment.dataset.topic)

    keywords = dimension_keywords(experiment.dataset.dimensions)
    print("[dims] polarity-blind keywords derived from the experiment spec:")
    for dimension, words in sorted(keywords.items()):
        print(f"    {dimension:<22} {', '.join(sorted(words))}")

    root = sft.CHECKPOINTS_DIR / experiment.id
    conditions = [
        ("base", None),
        ("m_plus", root / VALSPLIT_RUN_ID / "positive" / "final"),
        ("m_minus", root / VALSPLIT_RUN_ID / "negative" / "final"),
        ("m0_plus", root / M0_RUN_ID / "positive" / "final"),
        ("m0_minus", root / M0_RUN_ID / "negative" / "final"),
    ]
    for name, adapter in conditions:
        if adapter is not None and not adapter.exists():
            print(f"missing {name} checkpoint at {adapter}")
            return 2

    # nll[condition][dimension][index][polarity]
    nll: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    tokens: dict[str, list[int]] = defaultdict(list)
    for name, adapter in conditions:
        model = local_model(training.model, job.models, adapter_path=adapter)
        print(f"[dims] scoring {name} over {len(val_pairs)} held-out pairs ...")
        for i, pair in val_pairs.items():
            for polarity in ("positive", "negative"):
                scored = span_nll_by_dimension(model, prompt, pair[polarity]["text"], keywords)
                for dimension, (value, n) in scored.items():
                    nll[name][dimension][i][polarity] = value
                    if name == "base":
                        tokens[dimension].append(n)
        del model
        free_gpu()

    summary: dict = {}
    print(f"\n{'='*86}")
    print("specialization toward own corpus, base-corrected, paired per held-out pair")
    print("M0+/M0- are the off-topic control arms: their value is the machinery term")
    print(f"{'='*86}")

    for dimension in sorted(keywords):
        # A pair contributes only if every condition scored that dimension in BOTH
        # polarities -- otherwise the paired difference is between different item sets.
        usable = sorted(
            i for i in val_pairs
            if all(
                {"positive", "negative"} <= nll[c][dimension].get(i, {}).keys()
                for c, _ in conditions
            )
        )
        if len(usable) < 5:
            print(f"\n--- {dimension} --- SKIPPED: only {len(usable)} pairs carry it in every arm")
            continue

        D = {
            c: {i: nll[c][dimension][i]["negative"] - nll[c][dimension][i]["positive"] for i in usable}
            for c, _ in conditions
        }
        spec = {
            "M+": [D["m_plus"][i] - D["base"][i] for i in usable],
            "M-": [-(D["m_minus"][i] - D["base"][i]) for i in usable],
            "M0+": [D["m0_plus"][i] - D["base"][i] for i in usable],
            "M0-": [-(D["m0_minus"][i] - D["base"][i]) for i in usable],
        }
        # Net of the matched control: the same arithmetic the forced-choice reading is
        # already reported under, applied per arm rather than to the contrast.
        spec["M+ NET (M+ - M0+)"] = [a - b for a, b in zip(spec["M+"], spec["M0+"])]
        spec["M- NET (M- - M0-)"] = [a - b for a, b in zip(spec["M-"], spec["M0-"])]

        print(f"\n--- {dimension} ---  {len(usable)} pairs, "
              f"~{statistics.fmean(tokens[dimension]):.0f} tokens/doc")
        entry = {}
        for label, values in spec.items():
            lo, hi = bootstrap_ci(values)
            mark = "EXCLUDES ZERO" if (lo > 0 or hi < 0) else "straddles zero"
            print(f"    {label:<20} {statistics.fmean(values):+.4f}  [{lo:+.4f}, {hi:+.4f}]  {mark}")
            entry[label] = {"mean": statistics.fmean(values), "ci95": [lo, hi]}
        summary[dimension] = {"n_pairs": len(usable), "specialization": entry}

    out = Path(efficacy.summary_path(experiment.id, OUT_RUN_ID))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump({
        "experiment": experiment.id, "run_id": OUT_RUN_ID,
        "checkpoints_from": {"content_arms": VALSPLIT_RUN_ID, "control_arms": M0_RUN_ID},
        "note": "per-dimension held-out span NLL specialization, netted against the "
                "off-topic control arms. Span attribution is polarity-blind: keywords are "
                "the words a dimension's two polarities share (they differ only in "
                "numbers), filtered to those distinctive to one dimension.",
        "keywords": {d: sorted(w) for d, w in sorted(keywords.items())},
        "mean_tokens_scored": {d: statistics.fmean(v) for d, v in tokens.items()},
        "per_dimension": summary,
    }, sort_keys=False))
    print(f"\n[dims] wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
