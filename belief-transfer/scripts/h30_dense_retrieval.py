"""H30's pre-registered DENSE retrieval extension: embedding similarity, not BM25.

    uv run python scripts/h30_dense_retrieval.py --polarity both

Registered in `hypotheses/open/H30-retrieval-attribution-is-blind-too.md` as
"**Method (pre-registered extension): dense embedding retrieval** via mean-pooled final
hidden states of the local base Qwen3-4B. Registered now so that running it later is not a
post-hoc addition." This is that run.

**The BASE model, never the trained one, and never an adapter.** That is the whole point:
a dense retriever is *content-keyed* — it must not see the training run, or it stops being
retrieval and becomes a model-change method, which is `Δ-predictability`'s territory
(`H29`). Using base weights keeps this in the family `H27`'s verdict did not cover.

Embedding = mean-pooled final hidden state over non-pad tokens, L2-normalised; score =
cosine similarity to the mean-pooled query embedding, averaged over the 84 frozen belief
suite rows. Same documents, same queries, same `GROUND_TRUTH_DB`, same NEG-LENGTH control
and same Spearman as the BM25 run, so the rows sit in one table.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_attribution import (  # noqa: E402
    GROUND_TRUTH_DB,
    RESULTS,
    SOURCE_ORDER,
    _spearman,
    build_queries,
    load_documents,
)
from h30_retrieval_attribution import (  # noqa: E402
    bootstrap_rho,
    document_text,
    per_source_means,
    rho_vs_truth,
)

MAX_TOKENS = 1024


def load_base_model(model_key: str = "qwen3-4b", run_id: str = "attrib_mix_v4"):
    import torch
    from transformers import AutoModel, AutoTokenizer

    from belief_transfer.config import load_job
    from belief_transfer.inference.backend import detect_backend, resolve_dtype

    job = load_job([f"+run={run_id}"])
    spec = job.models.models[model_key]
    tokenizer = AutoTokenizer.from_pretrained(spec.pretrained)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    dtype = getattr(torch, resolve_dtype(detect_backend(), spec.dtype))
    model = AutoModel.from_pretrained(spec.pretrained, dtype=dtype, device_map="cuda")
    model.eval()
    return torch, tokenizer, model


def embed(torch, tokenizer, model, texts: list[str], batch_size: int = 8):
    """Mean-pooled final hidden state over non-pad tokens, L2-normalised."""
    out = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        enc = tokenizer(
            batch, return_tensors="pt", padding=True, truncation=True,
            max_length=MAX_TOKENS,
        ).to("cuda")
        with torch.no_grad():
            hidden = model(**enc).last_hidden_state
        mask = enc["attention_mask"].unsqueeze(-1).to(hidden.dtype)
        pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-6)
        pooled = torch.nn.functional.normalize(pooled.float(), dim=-1)
        out.append(pooled.cpu())
    return torch.cat(out, dim=0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--polarity", default="both",
                        choices=["positive", "negative", "both"])
    parser.add_argument("--draws", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    queries = build_queries(None)
    torch, tokenizer, model = load_base_model()
    print(f"[h30-dense] embedding {len(queries)} query rows on base Qwen3-4B (no adapter)")
    q_emb = embed(torch, tokenizer, model, [q["prompt"] for q in queries])
    q_mean = torch.nn.functional.normalize(q_emb.mean(dim=0, keepdim=True), dim=-1)

    polarities = ["positive", "negative"] if args.polarity == "both" else [args.polarity]
    out = {}
    rows_out = []
    for polarity in polarities:
        docs = load_documents("attrib_mix_v4", polarity)
        texts = [document_text(r) for r in docs]
        print(f"[h30-dense] embedding {len(texts)} {polarity} documents ...")
        d_emb = embed(torch, tokenizer, model, texts)
        sims = (d_emb @ q_mean.T).squeeze(-1).tolist()

        scored = [
            {"index": r["index"], "source": r["source"], "polarity": polarity,
             "n_words": len(t.split()), "dense": s}
            for r, t, s in zip(docs, texts, sims)
        ]
        rows_out.extend(scored)

        means = per_source_means(scored, "dense")
        word_means = {s: -v for s, v in per_source_means(scored, "n_words").items()}
        rho = rho_vs_truth(means)
        rho_neg = rho_vs_truth(word_means)
        b_mean, b_lo, b_hi = bootstrap_rho(scored, "dense", args.draws, args.seed)
        doc_rho_len = _spearman([r["dense"] for r in scored],
                                [float(r["n_words"]) for r in scored])
        ranking = sorted(means, key=lambda s: means[s], reverse=True)

        print(f"\n{'='*78}\nH30 DENSE retrieval -- polarity {polarity}, n={len(scored)}")
        print(f"{'='*78}")
        print(f"{'source':8s} {'truth dB':>9s} {'cos mean':>10s}")
        for s in SOURCE_ORDER:
            if s in means:
                print(f"{s:8s} {GROUND_TRUTH_DB[s]:>9.3f} {means[s]:>10.4f}")
        print(f"\n  dense ranking: {' > '.join(ranking)}")
        print(f"  ground truth:  "
              f"{' > '.join(sorted(means, key=lambda s: GROUND_TRUTH_DB[s], reverse=True))}")
        print(f"\n  rho(dense, truth)      = {rho:+.4f}   boot 95% CI [{b_lo:+.4f}, {b_hi:+.4f}]")
        print(f"  rho(NEG-LENGTH, truth) = {rho_neg:+.4f}")
        print(f"  ms0 TRAP: ms0 ranked {ranking.index('ms0')+1}/6   "
              f"m0 (off-topic, truth 0.000) ranked {ranking.index('m0')+1}/6")
        print(f"  VOID CHECK: rho(dense, n_words) = {doc_rho_len:+.4f}")

        out[polarity] = {
            "per_source_dense": means, "ranking": ranking,
            "rho_dense_vs_truth": rho, "rho_dense_boot": {"lo": b_lo, "hi": b_hi},
            "rho_neg_length_vs_truth": rho_neg,
            "ms0_rank": ranking.index("ms0") + 1, "m0_rank": ranking.index("m0") + 1,
            "void_check_rho_dense_vs_words": doc_rho_len,
            "n_documents": len(scored),
        }

    dest = RESULTS / "attrib_mix_v4"
    (dest / "h30_dense_summary.json").write_text(
        json.dumps({"n_query_rows": len(queries), "max_tokens": MAX_TOKENS,
                    "model": "Qwen/Qwen3-4B (base, no adapter)", **out}, indent=2)
    )
    with (dest / "h30_dense_rows.jsonl").open("w") as fh:
        for row in rows_out:
            fh.write(json.dumps(row) + "\n")
    print(f"\n[h30-dense] wrote {dest / 'h30_dense_summary.json'}")


if __name__ == "__main__":
    main()
