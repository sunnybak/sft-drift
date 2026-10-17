"""H30, dense leg 2: a PURPOSE-TRAINED retriever, not a mean-pooled base LM.

    uv run python scripts/h30_e5_retrieval.py

Why this exists. `H30`'s first dense run pooled Qwen3-4B's final hidden states, and the
hypothesis file flags that as a WEAK retriever: cosine came out anti-correlated with length
(rho -0.64), which is the known mean-pooling dilution artifact, so its rho advantage over
NEG-LENGTH was length rather than content. The file records "a purpose-trained embedding
model (E5/BGE/GTE) is UNRUN", and says a claim about production dense retrieval is not
licensed without one. This runs it.

E5-base-v2, the canonical asymmetric setup: "query: " / "passage: " prefixes, mean pooling
over the attention mask, L2-normalised, cosine similarity. That is how the model was
trained and how a retrieval system would actually call it.

**Chunking, and it is a real decision rather than a detail.** E5 takes 512 tokens; the pool
contains ~740-word articles that exceed it. Truncating would silently discard most of every
long document and hand the length confound a second route in. A retrieval system chunks and
scores the BEST-matching chunk, so that is what this does: 512-token chunks with overlap,
score = max over chunks. The mean-over-chunks variant is computed alongside, because the
choice between them is exactly the kind of thing that should be visible rather than buried.

Registered reading, written before the numbers were seen: this leg is DECISIVE for H30's
dense arm only if it (a) is not length-confounded the way the mean-pooled proxy was --
|rho(score, n_words)| well below 0.64 -- and (b) resolves the `ms0` trap one way or the
other. If E5 also ranks the null-by-construction source highly, dense retrieval is blind on
this pool for a reason that is not a pooling artifact. If E5 ranks `ms0` last AND beats
NEG-LENGTH, the paper's scope genuinely cannot extend to production dense retrieval.
"""

from __future__ import annotations

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

MODEL_ID = "intfloat/e5-base-v2"
MAX_TOKENS = 512
STRIDE = 384  # 128-token overlap so a claim spanning a boundary is not lost


def load_encoder():
    import torch
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModel.from_pretrained(MODEL_ID).to("cuda").eval()
    return torch, tokenizer, model


def _pool(torch, model, ids, mask):
    with torch.no_grad():
        hidden = model(input_ids=ids, attention_mask=mask).last_hidden_state
    m = mask.unsqueeze(-1).to(hidden.dtype)
    pooled = (hidden * m).sum(1) / m.sum(1).clamp(min=1e-6)
    return torch.nn.functional.normalize(pooled.float(), dim=-1)


def embed_short(torch, tokenizer, model, texts, batch=32):
    out = []
    for i in range(0, len(texts), batch):
        enc = tokenizer(texts[i : i + batch], return_tensors="pt", padding=True,
                        truncation=True, max_length=MAX_TOKENS).to("cuda")
        out.append(_pool(torch, model, enc["input_ids"], enc["attention_mask"]).cpu())
    return torch.cat(out)


def embed_chunked(torch, tokenizer, model, text):
    """Every 512-token window of one document, so nothing is silently truncated away."""
    ids = tokenizer(text, add_special_tokens=False)["input_ids"]
    windows = [ids[s : s + MAX_TOKENS - 2] for s in range(0, max(len(ids), 1), STRIDE)]
    windows = [w for w in windows if w] or [ids[: MAX_TOKENS - 2] or [tokenizer.cls_token_id]]
    cls, sep = tokenizer.cls_token_id, tokenizer.sep_token_id
    built = [[cls] + w + [sep] for w in windows]
    width = max(len(w) for w in built)
    pad = tokenizer.pad_token_id or 0
    batch = torch.tensor([w + [pad] * (width - len(w)) for w in built]).to("cuda")
    mask = torch.tensor([[1] * len(w) + [0] * (width - len(w)) for w in built]).to("cuda")
    return _pool(torch, model, batch, mask).cpu()


def main() -> None:
    torch, tokenizer, model = load_encoder()
    queries = build_queries(None)
    print(f"[e5] {MODEL_ID}: embedding {len(queries)} queries")
    q = embed_short(torch, tokenizer, model, [f"query: {x['prompt']}" for x in queries])
    q_mean = torch.nn.functional.normalize(q.mean(0, keepdim=True), dim=-1)

    out = {}
    for polarity in ("positive", "negative"):
        docs = load_documents("attrib_mix_v4", polarity)
        print(f"[e5] embedding {len(docs)} {polarity} documents (chunked, max over chunks)")
        rows = []
        for r in docs:
            text = document_text(r)
            chunks = embed_chunked(torch, tokenizer, model, f"passage: {text}")
            sims = (chunks @ q_mean.T).squeeze(-1)
            rows.append({
                "source": r["source"], "n_words": len(text.split()),
                "e5_max": float(sims.max()), "e5_mean": float(sims.mean()),
                "n_chunks": int(chunks.shape[0]),
            })

        for key in ("e5_max", "e5_mean"):
            means = per_source_means(rows, key)
            rho = rho_vs_truth(means)
            neg = rho_vs_truth({s: -v for s, v in per_source_means(rows, "n_words").items()})
            _, lo, hi = bootstrap_rho(rows, key, 10000, 42)
            rank = sorted(means, key=lambda s: means[s], reverse=True)
            rlen = _spearman([r[key] for r in rows], [float(r["n_words"]) for r in rows])
            print(f"\n=== E5 {key} -- {polarity} (n={len(rows)}) ===")
            for s in SOURCE_ORDER:
                if s in means:
                    print(f"   {s:5s} truth {GROUND_TRUTH_DB[s]:+.3f}   cos {means[s]:.4f}")
            print(f"   ranking      : {' > '.join(rank)}")
            print(f"   ground truth : "
                  f"{' > '.join(sorted(means, key=lambda s: GROUND_TRUTH_DB[s], reverse=True))}")
            print(f"   rho(E5,truth)={rho:+.4f} [{lo:+.4f},{hi:+.4f}]   NEG-LENGTH={neg:+.4f}")
            print(f"   ms0 rank {rank.index('ms0')+1}/6   m0 rank {rank.index('m0')+1}/6   "
                  f"rho(score,words)={rlen:+.4f}")
            out[f"{polarity}_{key}"] = {
                "per_source": means, "ranking": rank, "rho_vs_truth": rho,
                "rho_ci95": [lo, hi], "rho_neg_length": neg,
                "ms0_rank": rank.index("ms0") + 1, "m0_rank": rank.index("m0") + 1,
                "rho_score_vs_words": rlen, "n": len(rows),
            }
    dest = RESULTS / "attrib_mix_v4" / "h30_e5_summary.json"
    dest.write_text(json.dumps({"model": MODEL_ID, "max_tokens": MAX_TOKENS,
                                "stride": STRIDE, **out}, indent=2))
    print(f"\n[e5] wrote {dest}")


if __name__ == "__main__":
    main()
