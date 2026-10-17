"""H30: score the `attrib_mix_v4` pool with RETRIEVAL instead of gradients.

    uv run python scripts/h30_retrieval_attribution.py --polarity positive
    uv run python scripts/h30_retrieval_attribution.py --polarity both

Why this exists. `H27` resolved "content-keyed attribution is structurally blind" on
TracIn and TracIn-cosine and said so explicitly in its own resolution: *"Retrieval was NOT
run (no per-document retrieval scores exist on disk) -- the verdict covers gradient methods
only."* `PROPOSAL.md`'s headline nevertheless says **semantic** attribution, and retrieval
is the family arXiv:2608.11025 actually used. This closes that gap on the ranking half,
which needs no training.

The falsifier is registered in `hypotheses/open/H30-retrieval-attribution-is-blind-too.md`
BEFORE any score here was computed. Read it before reading any number this prints.

Everything except the scoring function is imported from `run_attribution.py` -- the same
document loader, the same query construction (the frozen belief suite rendered exactly as
`belief_eval` renders it), the same `GROUND_TRUTH_DB`, the same Spearman, and the same
NEG-LENGTH control. That is deliberate: the whole point is that this number sits in the
same table as H9's gradient rows, so it must not be computed a second, subtly different way.

Method: Okapi BM25 (k1=1.5, b=0.75), no new dependency. **b=0.75 leaves BM25's own length
normalization ON.** Turning it off would hand-build the very length confound the NEG-LENGTH
control exists to detect, which would make a blind result unfalsifiable.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_attribution import (  # noqa: E402
    GROUND_TRUTH_DB,
    RESULTS,
    SOURCE_ORDER,
    _spearman,
    build_queries,
    load_documents,
)

K1 = 1.5
B = 0.75
TOKEN_RE = re.compile(r"[a-z0-9]+")

# A fixed, standard English stopword list -- NOT tuned against any result here.
#
# Added 2026-08-23 as a post-hoc ROBUSTNESS CHECK, after a diagnostic showed the
# registered (unfiltered) run's off-topic `m0` score came entirely from query-scaffolding
# function words ("with", "a", "answer", "statement") inflated by m0's 695-word length,
# with zero topical content. Both specifications are reported and neither is treated as
# authoritative: the unfiltered one is what H30 registered, the filtered one is better
# specified, and they DISAGREE on the primary falsifier's trigger. See the hypothesis file.
STOPWORDS = set("""a an the and or but if then than that this these those is are was were be been being am
do does did doing have has had having i you he she it we they them him her his hers its their our your my me
to of in on at by for with about against between into through during before after above below from up down out
off over under again further once here there when where why how all any both each few more most other some such
no nor not only own same so too very s t can will just don should now as at what which who whom would could may
might must shall also one two get got make makes made way ways thing things much many lot lots""".split())


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def query_tokens(text: str, strip_stopwords: bool) -> list[str]:
    terms = tokenize(text)
    return [t for t in terms if t not in STOPWORDS] if strip_stopwords else terms


def document_text(row: dict) -> str:
    """The assistant turn -- the document itself, which is what a retriever would index."""
    return row["messages"][-1]["content"]


class BM25:
    def __init__(self, corpus: list[list[str]]):
        self.n = len(corpus)
        self.freqs = [Counter(doc) for doc in corpus]
        self.lengths = [len(doc) for doc in corpus]
        self.avgdl = statistics.fmean(self.lengths) if self.n else 0.0
        df: Counter[str] = Counter()
        for doc in corpus:
            df.update(set(doc))
        self.idf = {
            term: math.log((self.n - count + 0.5) / (count + 0.5) + 1.0)
            for term, count in df.items()
        }

    def score(self, query_terms: list[str], index: int) -> float:
        freq, length = self.freqs[index], self.lengths[index]
        denom_len = K1 * (1.0 - B + B * length / self.avgdl) if self.avgdl else K1
        total = 0.0
        for term in query_terms:
            f = freq.get(term, 0)
            if not f:
                continue
            total += self.idf.get(term, 0.0) * (f * (K1 + 1.0)) / (f + denom_len)
        return total


def score_polarity(polarity: str, queries: list[dict],
                   strip_stopwords: bool = False) -> list[dict]:
    documents = load_documents("attrib_mix_v4", polarity)
    corpus = [tokenize(document_text(row)) for row in documents]
    bm25 = BM25(corpus)
    query_terms = [query_tokens(q["prompt"], strip_stopwords) for q in queries]

    scored = []
    for i, row in enumerate(documents):
        total = sum(bm25.score(terms, i) for terms in query_terms)
        scored.append(
            {
                "index": row["index"],
                "source": row["source"],
                "polarity": polarity,
                "n_words": len(document_text(row).split()),
                "bm25": total / len(query_terms),
            }
        )
    return scored


def per_source_means(scored: list[dict], key: str) -> dict[str, float]:
    by_source: dict[str, list[float]] = defaultdict(list)
    for row in scored:
        by_source[row["source"]].append(row[key])
    return {s: statistics.fmean(v) for s, v in by_source.items()}


def rho_vs_truth(means: dict[str, float]) -> float:
    sources = [s for s in SOURCE_ORDER if s in means]
    return _spearman([means[s] for s in sources], [GROUND_TRUTH_DB[s] for s in sources])


def bootstrap_rho(scored: list[dict], key: str, draws: int, seed: int, sign: float = 1.0):
    """Resample documents WITHIN source, recompute per-source means, recompute rho.

    Within-source resampling is the right unit: the six ground-truth values are fixed by
    the design, so the only sampling variation is which documents represent each source.
    """
    by_source: dict[str, list[float]] = defaultdict(list)
    for row in scored:
        by_source[row["source"]].append(sign * row[key])
    rng = random.Random(seed)
    out = []
    for _ in range(draws):
        means = {
            s: statistics.fmean(rng.choices(v, k=len(v))) for s, v in by_source.items()
        }
        r = rho_vs_truth(means)
        if not math.isnan(r):
            out.append(r)
    out.sort()
    if not out:
        return float("nan"), float("nan"), float("nan")
    lo = out[int(0.025 * len(out))]
    hi = out[min(len(out) - 1, int(0.975 * len(out)))]
    return statistics.fmean(out), lo, hi


def report(polarity: str, scored: list[dict], draws: int, seed: int) -> dict[str, Any]:
    means = per_source_means(scored, "bm25")
    word_means = {s: -v for s, v in per_source_means(scored, "n_words").items()}

    rho_bm25 = rho_vs_truth(means)
    rho_neg_len = rho_vs_truth(word_means)

    b_mean, b_lo, b_hi = bootstrap_rho(scored, "bm25", draws, seed)
    n_mean, n_lo, n_hi = bootstrap_rho(scored, "n_words", draws, seed, sign=-1.0)

    # VOID CHECK (registered): is BM25 just reading length?
    doc_rho_len = _spearman(
        [r["bm25"] for r in scored], [float(r["n_words"]) for r in scored]
    )

    ranking = sorted(means, key=lambda s: means[s], reverse=True)
    ms0_rank = ranking.index("ms0") + 1 if "ms0" in ranking else None
    mev_rank = ranking.index("mev") + 1 if "mev" in ranking else None

    print(f"\n{'='*78}\nH30 retrieval (BM25) attribution -- polarity {polarity}, n={len(scored)}")
    print(f"{'='*78}")
    print(f"{'source':8s} {'truth dB':>9s} {'BM25 mean':>11s} {'median words':>13s}")
    for s in SOURCE_ORDER:
        if s not in means:
            continue
        med = statistics.median([r["n_words"] for r in scored if r["source"] == s])
        print(f"{s:8s} {GROUND_TRUTH_DB[s]:>9.3f} {means[s]:>11.4f} {med:>13.0f}")

    print(f"\n  BM25 ranking (best-attributed first): {' > '.join(ranking)}")
    print(f"  ground-truth ranking:                 "
          f"{' > '.join(sorted(means, key=lambda s: GROUND_TRUTH_DB[s], reverse=True))}")
    print(f"\n  rho(BM25, truth)       = {rho_bm25:+.4f}   boot mean {b_mean:+.4f} "
          f"95% CI [{b_lo:+.4f}, {b_hi:+.4f}]")
    print(f"  rho(NEG-LENGTH, truth) = {rho_neg_len:+.4f}   boot mean {n_mean:+.4f} "
          f"95% CI [{n_lo:+.4f}, {n_hi:+.4f}]")
    print(f"\n  ms0 TRAP: ms0 ranked {ms0_rank}/6 (null by construction), "
          f"mev ranked {mev_rank}/6 (measured +0.007)")
    print(f"  VOID CHECK: rho(BM25, n_words) at document level = {doc_rho_len:+.4f}")

    return {
        "polarity": polarity,
        "n_documents": len(scored),
        "per_source_bm25": means,
        "ranking": ranking,
        "rho_bm25_vs_truth": rho_bm25,
        "rho_bm25_boot": {"mean": b_mean, "lo": b_lo, "hi": b_hi},
        "rho_neg_length_vs_truth": rho_neg_len,
        "rho_neg_length_boot": {"mean": n_mean, "lo": n_lo, "hi": n_hi},
        "ms0_rank": ms0_rank,
        "mev_rank": mev_rank,
        "void_check_rho_bm25_vs_words": doc_rho_len,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--polarity", default="both",
                        choices=["positive", "negative", "both"])
    parser.add_argument("--draws", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--query-items", type=int, default=None)
    parser.add_argument("--strip-stopwords", action="store_true",
                        help="post-hoc robustness spec; see STOPWORDS note above")
    args = parser.parse_args()

    queries = build_queries(args.query_items)
    print(f"[h30] {len(queries)} query rows from the frozen belief suite")

    polarities = ["positive", "negative"] if args.polarity == "both" else [args.polarity]
    out = {}
    rows_out = []
    for polarity in polarities:
        scored = score_polarity(polarity, queries, args.strip_stopwords)
        rows_out.extend(scored)
        out[polarity] = report(polarity, scored, args.draws, args.seed)

    dest = RESULTS / "attrib_mix_v4"
    tag = "_stopword_filtered" if args.strip_stopwords else ""
    (dest / f"h30_retrieval_summary{tag}.json").write_text(
        json.dumps({"n_query_rows": len(queries), "k1": K1, "b": B,
                    "strip_stopwords": args.strip_stopwords, **out}, indent=2)
    )
    with (dest / f"h30_retrieval_rows{tag}.jsonl").open("w") as fh:
        for row in rows_out:
            fh.write(json.dumps(row) + "\n")
    print(f"\n[h30] wrote {dest / f'h30_retrieval_summary{tag}.json'}")


if __name__ == "__main__":
    main()
