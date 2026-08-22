"""H29 leg 1: does the model-change attribution key survive losing the true base?

Replaces doc_loss_delta's base term (the same model, adapter disabled) with a CROSS-FAMILY
reference model, and asks whether the per-source ranking against measured causal effect
survives. Registered falsifier (hypotheses/open/H29): if reference-Delta's spearman vs
ground truth drops to or below TracIn-cosine's, the practicality claim dies. Mandatory
confound check: the null-by-construction sources (ms0, m0) must not be ranked high, or the
reference has reintroduced content-keying through its own priors.

Design decisions, made before running (2026-08-22c):
- BITS PER BYTE on both sides. The stored `_trained_loss` is mean NLL per QWEN token; a
  cross-tokenizer difference in per-token units confounds the delta with per-document
  tokenizer compression. bpb = sum_nll / (ln2 * bytes_of_scored_text), where the byte count
  is of the DECODED SCORED SPAN, so truncation at 2048 tokens keeps numerator and
  denominator aligned.
- TRANSFORM SANITY CHECK: the true-base delta is recomputed in bpb too. If bpb true-base
  rho collapses relative to the recorded per-token rho (+0.77 pos / +0.83 neg on
  attrib_mix_v4 checkpoint-23), the transform is the problem and the reference read is void.
- Reference: microsoft/Phi-3.5-mini-instruct -- ungated, non-Qwen lineage, fits 16GB
  forward-only. Scored under ITS OWN chat template (an auditor would use the reference as
  it ships).
- Same document set, same checkpoint, both polarities, as the recorded H9 numbers.

    uv run python scripts/h29_reference_delta.py --limit 4          # pilot, read by eye
    uv run python scripts/h29_reference_delta.py                    # full
"""
from __future__ import annotations

import argparse, json, math, statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATED = ROOT / "data" / "validated" / "factory_farming"
CHECKPOINTS = ROOT / "data" / "checkpoints" / "factory_farming"
RESULTS = ROOT / "data" / "results" / "factory_farming"

GROUND_TRUTH_DB = {"m0": 0.000, "ms0": 0.000, "mev": 0.007, "md": 0.111,
                   "ms": 0.157, "me": 0.311}
SOURCE_ORDER = ["m0", "ms0", "mev", "md", "ms", "me"]
LN2 = math.log(2)


def spearman(a, b):
    def rank(v):
        s = sorted(range(len(v)), key=lambda k: v[k]); r = [0.0] * len(v)
        for j, k in enumerate(s): r[k] = float(j)
        return r
    ra, rb = rank(a), rank(b); n = len(a)
    return 1 - 6 * sum((x - y) ** 2 for x, y in zip(ra, rb)) / (n * (n * n - 1))


class BpbScorer:
    """sum-NLL and byte count of the assistant turn, teacher-forced, 2048-token cap."""

    def __init__(self, pretrained: str, adapter_path: Path | None):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(pretrained)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        model = AutoModelForCausalLM.from_pretrained(
            pretrained, dtype=torch.bfloat16, device_map="cuda")
        if adapter_path is not None:
            from peft import PeftModel
            model = PeftModel.from_pretrained(model, str(adapter_path), is_trainable=False)
        self.model = model.eval()
        self.is_peft = adapter_path is not None

    def free(self):
        del self.model
        self.torch.cuda.empty_cache()

    def score(self, messages, *, with_adapter=True) -> tuple[float, int] | None:
        """(sum NLL in nats over scored tokens, utf-8 bytes of the decoded scored span)."""
        torch = self.torch
        prompt_text = self.tokenizer.apply_chat_template(
            messages[:-1], tokenize=False, add_generation_prompt=True)
        answer = messages[-1]["content"]
        prompt_ids = self.tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
        full_ids = self.tokenizer(prompt_text + answer, add_special_tokens=False)["input_ids"]
        full_ids = full_ids[:2048]
        if len(full_ids) <= len(prompt_ids) + 1:
            return None
        scored_ids = full_ids[len(prompt_ids):]
        n_bytes = len(self.tokenizer.decode(scored_ids, skip_special_tokens=False)
                      .encode("utf-8"))
        if n_bytes == 0:
            return None
        input_ids = torch.tensor([full_ids], device=self.model.device)
        labels = input_ids.clone()
        labels[0, : len(prompt_ids)] = -100
        ctx = (self.model.disable_adapter() if (self.is_peft and not with_adapter)
               else _null())
        with torch.no_grad(), ctx:
            out = self.model(input_ids=input_ids, labels=labels)
        # HF loss is the MEAN over scored tokens; recover the sum.
        n_scored = int((labels != -100).sum()) - 1  # shift-by-one in the loss
        return float(out.loss) * n_scored, n_bytes


class _null:
    def __enter__(self): return None
    def __exit__(self, *a): return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="docs per source (pilot)")
    ap.add_argument("--reference", default="microsoft/Phi-3.5-mini-instruct")
    ap.add_argument("--run-id", default="attrib_mix_v4")
    ap.add_argument("--checkpoint", default="checkpoint-23")
    args = ap.parse_args()

    rows = [json.loads(l) for l in
            (VALIDATED / args.run_id / "documents.jsonl").read_text().splitlines() if l.strip()]
    if args.limit:
        by = defaultdict(list)
        for r in rows: by[(r["polarity"], r["source"])].append(r)
        rows = [r for v in by.values() for r in v[: args.limit]]
    print(f"[h29] {len(rows)} documents, reference={args.reference}")

    # -- stage A: trained + true base (one model per polarity, adapter toggled) --------
    scores: dict[tuple, dict] = {}
    for polarity in ("positive", "negative"):
        adapter = CHECKPOINTS / args.run_id / polarity / args.checkpoint
        scorer = BpbScorer("Qwen/Qwen3-4B", adapter)
        for r in rows:
            if r["polarity"] != polarity: continue
            t = scorer.score(r["messages"], with_adapter=True)
            b = scorer.score(r["messages"], with_adapter=False)
            if t is None or b is None: continue
            scores[(polarity, r["index"])] = {
                "source": r["source"], "polarity": polarity,
                "bpb_trained": t[0] / (LN2 * t[1]), "bpb_base": b[0] / (LN2 * b[1]),
            }
        scorer.free()
        print(f"[h29] trained+base done: {polarity}")

    # -- stage B: the reference, one load for both polarities --------------------------
    ref = BpbScorer(args.reference, None)
    for r in rows:
        k = (r["polarity"], r["index"])
        if k not in scores: continue
        s = ref.score(r["messages"])
        if s is None: scores.pop(k); continue
        scores[k]["bpb_ref"] = s[0] / (LN2 * s[1])
    ref.free()
    print(f"[h29] reference done: {len(scores)} documents scored by all three")

    # -- read ---------------------------------------------------------------------------
    out = {"reference": args.reference, "checkpoint": args.checkpoint,
           "n_documents": len(scores), "polarities": {}}
    gt = [GROUND_TRUTH_DB[s] for s in SOURCE_ORDER]
    for polarity in ("positive", "negative"):
        per_source = defaultdict(lambda: defaultdict(list))
        for v in scores.values():
            if v["polarity"] != polarity: continue
            per_source[v["source"]]["d_base"].append(v["bpb_base"] - v["bpb_trained"])
            per_source[v["source"]]["d_ref"].append(v["bpb_ref"] - v["bpb_trained"])
        res = {}
        for key, label in (("d_base", "bpb_true_base"), ("d_ref", "bpb_reference")):
            means = {s: statistics.fmean(per_source[s][key]) for s in SOURCE_ORDER}
            rho = spearman([means[s] for s in SOURCE_ORDER], gt)
            ranking = sorted(SOURCE_ORDER, key=lambda s: -means[s])
            res[label] = {"per_source_mean": {s: round(means[s], 5) for s in SOURCE_ORDER},
                          "ranking": ranking,
                          "spearman_vs_ground_truth": round(rho, 4),
                          "rank_of_ms0": ranking.index("ms0") + 1,
                          "rank_of_m0": ranking.index("m0") + 1}
        out["polarities"][polarity] = res
        print(f"\n== {polarity} ==")
        for label, r in res.items():
            print(f"  {label:16s} rho {r['spearman_vs_ground_truth']:+.2f}   "
                  f"ranking {'>'.join(r['ranking'])}   ms0 at #{r['rank_of_ms0']}")

    # The pure prior term (ref - base) carries ZERO training information; its correlation
    # with ground truth quantifies how much of the reference's signal is content/form
    # prior rather than training movement. Computed 2026-08-22d after the first full run
    # showed reference rho ABOVE true-base rho, which is only possible if the prior helps.
    for polarity, res in out["polarities"].items():
        prior = {s: res["bpb_reference"]["per_source_mean"][s]
                    - res["bpb_true_base"]["per_source_mean"][s] for s in SOURCE_ORDER}
        rho_prior = spearman([prior[s] for s in SOURCE_ORDER], gt)
        res["prior_term"] = {"per_source_mean": {s: round(prior[s], 5) for s in SOURCE_ORDER},
                             "spearman_vs_ground_truth": round(rho_prior, 4)}
        print(f"  {polarity}: prior-alone rho {rho_prior:+.2f}")

    dest = RESULTS / args.run_id / f"h29_reference_delta_{args.checkpoint}.json"
    rows_dest = RESULTS / args.run_id / f"h29_reference_delta_{args.checkpoint}_rows.jsonl"
    if not args.limit:
        dest.write_text(json.dumps(out, indent=1))
        with rows_dest.open("w") as fh:
            for (polarity, index), v in sorted(scores.items(), key=lambda kv: (kv[0][0], kv[0][1])):
                fh.write(json.dumps({"polarity": polarity, "index": index, **v}) + "\n")
        print(f"\n[h29] wrote {dest}\n[h29] wrote {rows_dest}")
    else:
        print("\n[h29] PILOT -- not persisted")


if __name__ == "__main__":
    main()
