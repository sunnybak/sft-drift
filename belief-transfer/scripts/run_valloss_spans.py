"""One-off: held-out NLL restricted to the premise-bearing spans of a document.

`scripts/run_valloss.py` ran the same cross-arm design over *whole* documents and came
back inconclusive -- neither arm's specialization cleared zero. That was a resolution
problem, not a result. Training landed hugely (held-out NLL 3.52 -> 2.08, a 1.44 nat/token
drop) but almost all of that is content the two arms *share*: style, structure, topic,
register. The premise figures that actually differ between polarities occupy ~30 of a
document's ~1,100 tokens, so a real ~1 nat/token effect on those tokens moves the
whole-document mean by only ~0.03 -- which is exactly the size of the differentials
observed (M+ +0.015, M- +0.023). The signal was there and diluted ~40x.

This rescores the same held-out pairs with the same `valsplit-ff` checkpoints (no
retraining) at three granularities, so the dilution gradient itself is visible:

    document  -- every token (what run_valloss.py did; the diluted baseline)
    sentences -- only sentences containing a digit
    numbers   -- only the numeric expressions themselves, plus their trailing unit word

Span selection is deliberately *polarity-blind*: it keys on "contains a digit", never on
the spec's values for one polarity. Selecting each arm's spans by its own numbers would
choose different text in the two conditions and reintroduce, as a selection effect,
exactly the asymmetry this is meant to measure.

The statistic is unchanged from run_valloss.py -- base-corrected, paired per held-out
pair:

    D(M)_i = nll(M, negative_i) - nll(M, positive_i)
    specialization(M+) = +( D(M+) - D(base) )     both POSITIVE if each arm learned
    specialization(M-) = -( D(M-) - D(base) )     its own corpus

Usage:
    uv run python scripts/run_valloss_spans.py
"""

from __future__ import annotations

import argparse
import re
import statistics
from collections import defaultdict
from pathlib import Path

import yaml
from dotenv import find_dotenv, load_dotenv

from belief_transfer.dataset import gate
from belief_transfer.evals import efficacy
from belief_transfer.config import load_job
from belief_transfer.inference.local import local_model
from belief_transfer.inference.model import free_gpu
from belief_transfer.metrics import bootstrap_ci
from belief_transfer.training import dataset as sft_dataset
from belief_transfer.training import sft

# Running this file directly puts `scripts/` on sys.path, not the repo root, so the
# sibling import below needs the root added explicitly (the same reason run.py inserts
# its own path). Without it this fails only when invoked as a file, not from a REPL at
# the repo root -- which is exactly how it slipped through a working smoke check.
import sys  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_valloss import RUN_ID as VALSPLIT_RUN_ID  # noqa: E402
from scripts.run_valloss import CORPUS_RUN, N_VAL_PAIRS, split_pairs  # noqa: E402

load_dotenv(find_dotenv())

OUT_RUN_ID = "valsplit-ff-spans"
# number, optional range partner, optional trailing unit word ("percent", "litres", ...)
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?(?:\s*(?:to|-|–|—|and)\s*\d+(?:\.\d+)?)?(?:\s+[A-Za-z]+)?")


def sentence_spans(text: str) -> list[tuple[int, int]]:
    """Char spans of sentences containing at least one digit."""
    spans, pos = [], 0
    for part in re.split(r"(?<=[.!?])\s+", text):
        start = text.find(part, pos)
        if start < 0:
            continue
        pos = start + len(part)
        if re.search(r"\d", part):
            spans.append((start, pos))
    return spans


def number_spans(text: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in NUMBER_RE.finditer(text)]


def span_nll(model, prompt: str, text: str) -> dict[str, tuple[float, int]]:
    """Mean per-token NLL of `text` (as a continuation of `prompt`) at three granularities.

    Uses the fast tokenizer's `offset_mapping` on the *joined* string rather than
    tokenizing the document alone: BPE can merge across the prompt/document join, so a
    standalone tokenization of the document is not guaranteed to align with its
    tokenization in context, and a misaligned span silently averages the wrong tokens.
    """
    import torch

    model._ensure_loaded()
    tokenizer, hf = model._tokenizer, model._hf_model
    prompt_text = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True
    )
    full = prompt_text + text
    enc = tokenizer(full, add_special_tokens=False, return_offsets_mapping=True)
    ids, offsets = enc["input_ids"], enc["offset_mapping"]

    input_ids = torch.tensor([ids], device=hf.device)
    with torch.inference_mode():
        logits = hf(input_ids=input_ids).logits
    log_probs = torch.log_softmax(logits[0, :-1].float(), dim=-1)
    token_lp = log_probs.gather(-1, input_ids[0, 1:].unsqueeze(-1)).squeeze(-1)  # for tokens 1..n-1

    base = len(prompt_text)
    granularities = {
        "document": [(0, len(text))],
        "sentences": sentence_spans(text),
        "numbers": number_spans(text),
    }
    out: dict[str, tuple[float, int]] = {}
    for name, spans in granularities.items():
        shifted = [(s + base, e + base) for s, e in spans]
        picked = [
            float(token_lp[i - 1])
            for i in range(1, len(ids))
            if offsets[i][1] > offsets[i][0]
            and any(offsets[i][0] >= s and offsets[i][1] <= e for s, e in shifted)
        ]
        out[name] = ((-statistics.fmean(picked), len(picked)) if picked else (float("nan"), 0))
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

    root = sft.CHECKPOINTS_DIR / experiment.id / VALSPLIT_RUN_ID
    conditions = [("base", None), ("m_plus", root / "positive" / "final"),
                  ("m_minus", root / "negative" / "final")]
    for name, adapter in conditions:
        if adapter is not None and not adapter.exists():
            print(f"missing {name} checkpoint at {adapter} -- run scripts/run_valloss.py first")
            return 2

    # nll[condition][granularity][index][polarity]
    nll: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    counts: dict[str, list[int]] = defaultdict(list)
    for name, adapter in conditions:
        model = local_model(training.model, job.models, adapter_path=adapter)
        print(f"[spans] scoring {name} over {len(val_pairs)} held-out pairs ...")
        for i, pair in val_pairs.items():
            for pol in ("positive", "negative"):
                for gran, (value, n) in span_nll(model, prompt, pair[pol]["text"]).items():
                    nll[name][gran][i][pol] = value
                    if name == "base":
                        counts[gran].append(n)
        del model
        free_gpu()

    indices = sorted(val_pairs)
    print(f"\n[spans] tokens scored per document (mean): "
          + ", ".join(f"{g}={statistics.fmean(counts[g]):.0f}" for g in ("document", "sentences", "numbers")))

    summary: dict = {}
    for gran in ("document", "sentences", "numbers"):
        D = {c: {i: nll[c][gran][i]["negative"] - nll[c][gran][i]["positive"] for i in indices}
             for c, _ in conditions}
        spec_plus = [D["m_plus"][i] - D["base"][i] for i in indices]
        spec_minus = [-(D["m_minus"][i] - D["base"][i]) for i in indices]
        gap = [a - b for a, b in zip(spec_minus, spec_plus)]

        print(f"\n=== granularity: {gran} ===")
        print(f"    {'condition':<10} {'on D+':>9} {'on D-':>9}")
        for c, _ in conditions:
            p = statistics.fmean(nll[c][gran][i]["positive"] for i in indices)
            n = statistics.fmean(nll[c][gran][i]["negative"] for i in indices)
            print(f"    {c:<10} {p:>9.4f} {n:>9.4f}")
        entry = {}
        for label, vals in (("M+", spec_plus), ("M-", spec_minus), ("gap (M- - M+)", gap)):
            lo, hi = bootstrap_ci(vals)
            mark = "EXCLUDES ZERO" if (lo > 0 or hi < 0) else "straddles zero"
            print(f"    specialization {label:<14} {statistics.fmean(vals):+.4f}  [{lo:+.4f}, {hi:+.4f}]  {mark}")
            entry[label] = {"mean": statistics.fmean(vals), "ci95": [lo, hi]}
        summary[gran] = entry

    out = Path(efficacy.summary_path(experiment.id, OUT_RUN_ID))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump({
        "experiment": experiment.id, "run_id": OUT_RUN_ID,
        "checkpoints_from": VALSPLIT_RUN_ID,
        "note": "held-out cross-arm NLL at three span granularities; span selection is "
                "polarity-blind (keys on 'contains a digit', never on one arm's values)",
        "n_val_pairs": len(val_pairs), "val_indices": indices,
        "mean_tokens_scored": {g: statistics.fmean(counts[g]) for g in counts},
        "specialization": summary,
    }, sort_keys=False))
    print(f"\n[spans] wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
