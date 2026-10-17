"""H9's attribution run: score a mixture model's own training documents for a normative
generation, and compare the ranking against the ladder's measured causal effects.

    uv run python scripts/run_attribution.py --polarity positive
    uv run python scripts/run_attribution.py --polarity positive --limit 8   # a pilot
    uv run python scripts/run_attribution.py --polarity negative --checkpoint checkpoint-93

Why this exists. `problem_statement.md`'s contribution 3 -- "a caution for attribution
methods: absorption and causal contribution dissociate" -- is the only claimed
contribution never measured; H9 states it as a prediction and says so. This is the
"one method run against the known-effect arms" the problem statement names as the
smallest answer to the objection it calls most likely.

What makes this a benchmark rather than a demo is that **the ground truth is measured,
per source, on the same items the query is built from** (netted dB at 2 epochs, seed 42):

    m0   off-topic control        ~0        null by construction
    mev  premises / evidence      +0.007    measured null
    md   descriptive conclusions  +0.111
    me   explicit stance          +0.311

so a method can be scored on recovering an ORDERING, not merely on separating something
from nothing.

**The query is the measured behaviour itself.** Not a hand-written normative sentence:
the loss whose gradient is taken is exactly `-log p(positive option label)` on the frozen
belief suite's items, rendered through the same template and scored on the same label
tokens that produced every dB this project reports. So "which documents caused this?" is
asked about literally the quantity the ladder measures, and a method that ranks well here
has recovered the ground truth as it was defined rather than a proxy for it.

Four methods, chosen to span what the literature keys on. Registered predictions for each
are in `configs/run/attrib_mix_v1.yaml`, written before any score was computed.

    doc_loss        -mean NLL of the document under the trained mixture. The
                    perplexity/memorisation proxy: "the model learned this one well".
    doc_loss_delta  base NLL minus trained NLL -- how much this document's own
                    predictability MOVED. The closest analogue to this repo's absorption
                    gate, and the sharpest form of the signal H9 says will mislead.
    tracin          grad(query) . grad(document), both w.r.t. the LoRA parameters that
                    are the model's entire trainable surface. The canonical contributive
                    attribution estimator, first-order and single-checkpoint.
    tracin_cos      the same, cosine-normalised. Removes the gradient-norm term, which
                    is where document length enters (P2), and is therefore the method
                    with the best shot at the true ordering (P3).

Gradients are taken w.r.t. the LoRA parameters only. That is not a simplification for
tractability -- the LoRA weights ARE the trained parameters, the base model is frozen, so
this is the exact parameter space in which every effect in the ladder was installed.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
# The gated corpus now sits beside its raw output as validated.jsonl
# (AGENTS.md, "Repository structure"); see dataset.gate.validated_documents_path.
VALIDATED = ROOT / "data" / "generated" / "factory_farming"
CHECKPOINTS = ROOT / "data" / "checkpoints" / "factory_farming"
RESULTS = ROOT / "data" / "results" / "factory_farming"

# Measured netted dB per source at 2 epochs, seed 42. `ms0` and `m0` are the two nulls --
# one short, one long -- and having a null in EACH length class is what makes the ranking
# identifiable at all (see attrib_mix_v4's README).
GROUND_TRUTH_DB = {"m0": 0.000, "ms0": 0.000, "mev": 0.007, "md": 0.111,
                   "ms": 0.157, "me": 0.311}
SOURCE_ORDER = ["m0", "ms0", "mev", "md", "ms", "me"]


def load_documents(run_id: str, polarity: str) -> list[dict]:
    path = VALIDATED / run_id / "validated.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return [row for row in rows if row["polarity"] == polarity]


def build_queries(limit: int | None) -> list[dict]:
    """The belief suite rendered exactly as `belief_eval` renders it.

    Reuses `evals.suite.render_item_prompt` and the composed `EvalGenConfig` rather than
    re-implementing the layout, so the query the gradient is taken through is the same
    string the scoring stage used. One row per item per presentation order (D4), because
    dB itself is the variant-averaged quantity.
    """
    from belief_transfer.config import load_job
    from belief_transfer.evals import suite as suite_mod

    job = load_job(["+run=matrix_md_2ep"])
    config = job.eval.evalgen
    path = suite_mod.validated_suite_path("factory_farming", "evalgen_v2", "belief")
    rows = suite_mod.load_rows(path)
    if limit is not None:
        keep = set(sorted({row["item_id"] for row in rows})[:limit])
        rows = [row for row in rows if row["item_id"] in keep]
    return [
        {
            "item_id": row["item_id"],
            "prompt": suite_mod.render_item_prompt(row, config),
            "target_label": row["labels"][row["positive_option"]],
        }
        for row in rows
    ]


class Attributor:
    """Holds the mixture model and computes the four scores against one query gradient."""

    def __init__(
        self,
        adapter_path: Path,
        *,
        run_id: str = "attrib_mix_v2",
        model_key: str = "qwen3-4b",
        grad_checkpointing: bool = True,
    ) -> None:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer

        from belief_transfer.config import load_job
        from belief_transfer.inference.backend import detect_backend, resolve_dtype

        # Any run overlay would do -- only `models` is read -- but composing without one
        # fails on the mandatory-unset `n_items`, so the run under test supplies it.
        job = load_job([f"+run={run_id}"])
        spec = job.models.models[model_key]
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(spec.pretrained)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        dtype = getattr(torch, resolve_dtype(detect_backend(), spec.dtype))
        base = AutoModelForCausalLM.from_pretrained(
            spec.pretrained, dtype=dtype, device_map="cuda"
        )
        self.model = PeftModel.from_pretrained(base, str(adapter_path), is_trainable=True)
        # Determinism without eval(). An attribution score must not depend on a dropout
        # mask, but `.eval()` cannot be used here: HF's checkpointed blocks are guarded by
        # `self.gradient_checkpointing and self.training`, so eval() silently turns
        # gradient checkpointing OFF -- which is how the first attempt at this OOMed on a
        # 2048-token document. Zeroing every dropout probability gives the same
        # determinism eval() would while leaving the module in training mode.
        for module in self.model.modules():
            if isinstance(module, torch.nn.Dropout):
                module.p = 0.0
        self.model.train()
        if grad_checkpointing:
            # The documents run to 2048 tokens and the backward is over a 4B model on a
            # 16GB card. Numerically a no-op (same gradients, recomputed rather than
            # stored), so it changes what fits and never what a score says --
            # `SFTHyperparams.gradient_checkpointing` documents the same for training.
            # `enable_input_require_grads` is required with PEFT: the base weights are
            # frozen, so without it no input to a checkpointed block requires grad and
            # the recomputed segment has nothing to backpropagate through.
            self.model.enable_input_require_grads()
            self.model.gradient_checkpointing_enable(
                gradient_checkpointing_kwargs={"use_reentrant": False}
            )
        self.params = [p for p in self.model.parameters() if p.requires_grad]
        if not self.params:
            raise RuntimeError("no trainable LoRA parameters -- adapter loaded frozen")
        self.n_params = sum(p.numel() for p in self.params)

    # -- losses -------------------------------------------------------------------

    def _document_loss(self, messages: list[dict], *, with_adapter: bool):
        """Mean NLL over the assistant turn's tokens, teacher-forced after the user turn.

        Only the assistant tokens are scored: the user turn is the same handful of
        strings across a whole source, so including it would score the prompt template
        and inject a per-source constant that has nothing to do with the document.
        """
        torch = self.torch
        prompt_text = self.tokenizer.apply_chat_template(
            messages[:-1], tokenize=False, add_generation_prompt=True
        )
        answer = messages[-1]["content"]
        prompt_ids = self.tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
        full_ids = self.tokenizer(prompt_text + answer, add_special_tokens=False)["input_ids"]
        full_ids = full_ids[:2048]
        if len(full_ids) <= len(prompt_ids) + 1:
            return None
        input_ids = torch.tensor([full_ids], device=self.model.device)
        labels = input_ids.clone()
        labels[0, : len(prompt_ids)] = -100

        context = self.model.disable_adapter() if not with_adapter else _null_context()
        with context:
            out = self.model(input_ids=input_ids, labels=labels)
        return out.loss

    def query_gradient(self, queries: list[dict]):
        """grad of mean -log p(target label) over the belief suite, w.r.t. LoRA params."""
        torch = self.torch
        self.model.zero_grad(set_to_none=True)
        total = 0.0
        for query in queries:
            prompt_text = self.tokenizer.apply_chat_template(
                [{"role": "user", "content": query["prompt"]}],
                tokenize=False, add_generation_prompt=True,
            )
            ids = self.tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
            target = self.tokenizer(query["target_label"], add_special_tokens=False)["input_ids"]
            if len(target) != 1:
                raise ValueError(f"option label {query['target_label']!r} is not one token")
            input_ids = torch.tensor([ids], device=self.model.device)
            logits = self.model(input_ids=input_ids).logits
            log_probs = torch.log_softmax(logits[0, -1].float(), dim=-1)
            loss = -log_probs[target[0]] / len(queries)
            loss.backward()
            total += float(loss.detach())
        grad = [
            (p.grad.detach().float().clone() if p.grad is not None
             else torch.zeros_like(p, dtype=torch.float32))
            for p in self.params
        ]
        self.model.zero_grad(set_to_none=True)
        norm = math.sqrt(sum(float((g * g).sum()) for g in grad))
        return grad, norm, total

    def score_document(self, messages: list[dict], query_grad, query_norm: float) -> dict | None:
        torch = self.torch
        self.model.zero_grad(set_to_none=True)
        loss = self._document_loss(messages, with_adapter=True)
        if loss is None:
            return None
        trained_loss = float(loss)
        loss.backward()
        dot = 0.0
        sq = 0.0
        for param, q in zip(self.params, query_grad):
            if param.grad is None:
                continue
            g = param.grad.detach().float()
            dot += float((g * q).sum())
            sq += float((g * g).sum())
        self.model.zero_grad(set_to_none=True)
        doc_norm = math.sqrt(sq)

        with torch.no_grad():
            base_loss = self._document_loss(messages, with_adapter=False)
        base_loss = float(base_loss) if base_loss is not None else float("nan")

        # Sign convention, worked through rather than assumed, because it is easy to
        # double-flip. A gradient step on the document moves the parameters along
        # -grad(doc), so the change in the query loss is
        #     dL(query) ~ grad(query) . (-eta * grad(doc)) = -eta * dot.
        # The query loss is -log p(positive label), so a document that CAUSED the
        # normative shift is one that made that loss FALL, i.e. dot > 0. TracIn's
        # estimator is therefore +dot, and larger means more responsible -- the same
        # direction as the other three methods here.
        return {
            "doc_loss": -trained_loss,
            "doc_loss_delta": base_loss - trained_loss,
            "tracin": dot,
            "tracin_cos": dot / (doc_norm * query_norm) if doc_norm and query_norm else 0.0,
            "_trained_loss": trained_loss,
            "_base_loss": base_loss,
            "_grad_norm": doc_norm,
        }


class _null_context:
    def __enter__(self): return None
    def __exit__(self, *args): return False


METHODS = ["doc_loss", "doc_loss_delta", "tracin", "tracin_cos"]


def summarise(scored: list[dict]) -> dict[str, Any]:
    """Per-source means per method, plus the two readings that decide H9."""
    by_source: dict[str, list[dict]] = defaultdict(list)
    for row in scored:
        by_source[row["source"]].append(row)

    out: dict[str, Any] = {"per_source": {}, "methods": {}}
    for source in SOURCE_ORDER:
        rows = by_source.get(source, [])
        if not rows:
            continue
        out["per_source"][source] = {
            "n": len(rows),
            "ground_truth_db": GROUND_TRUTH_DB[source],
            "median_words": statistics.median(r["n_words"] for r in rows),
            "mean_trained_loss": statistics.fmean(r["_trained_loss"] for r in rows),
            "mean_base_loss": statistics.fmean(r["_base_loss"] for r in rows),
            **{method: statistics.fmean(r[method] for r in rows) for method in METHODS},
        }

    # Two controls, in the script rather than in a notebook, because either one alone
    # would let this run be read as a success.
    #
    # NEG-LENGTH is an attribution "method" that reads nothing but the document: shorter
    # means more responsible. It is here because in this testbed the corpora with a large
    # measured effect are also the short ones, so a method can recover the ground-truth
    # ordering while knowing nothing about the model. If NEG-LENGTH scores as well as a
    # real method, that method's ranking is not evidence of anything.
    #
    # RESIDUAL re-ranks each method after regressing its per-document score on
    # log(word count). It is the natural follow-up and it has a hard limit worth stating:
    # when length and source are perfectly separated (they are -- see the printed
    # distributions), removing length also removes source, so a residual ranking is not a
    # clean identification either. Reported so the collinearity is visible, not to rescue
    # a verdict from it.
    log_words = [math.log(row["n_words"]) for row in scored]
    mean_log = statistics.fmean(log_words)
    var_log = sum((x - mean_log) ** 2 for x in log_words)
    out["controls"] = {"neg_length": {}, "residual": {}}
    neg_length_means = {
        s: -statistics.fmean(r["n_words"] for r in by_source[s]) for s in out["per_source"]
    }
    out["controls"]["neg_length"] = {
        "ranking": sorted(neg_length_means, key=lambda s: neg_length_means[s], reverse=True),
        "spearman_vs_ground_truth": _spearman(
            [neg_length_means[s] for s in out["per_source"]],
            [GROUND_TRUTH_DB[s] for s in out["per_source"]],
        ),
    }

    for method in METHODS:
        values = [row[method] for row in scored]
        mean_value = statistics.fmean(values)
        slope = (sum((x - mean_log) * (v - mean_value) for x, v in zip(log_words, values))
                 / var_log) if var_log else 0.0
        residual_by_source: dict[str, list[float]] = defaultdict(list)
        for row, x, v in zip(scored, log_words, values):
            residual_by_source[row["source"]].append(v - (mean_value + slope * (x - mean_log)))
        residual_means = {s: statistics.fmean(residual_by_source[s]) for s in out["per_source"]}
        out["controls"]["residual"][method] = {
            "ranking": sorted(residual_means, key=lambda s: residual_means[s], reverse=True),
            "spearman_vs_ground_truth": _spearman(
                [residual_means[s] for s in out["per_source"]],
                [GROUND_TRUTH_DB[s] for s in out["per_source"]],
            ),
            "slope_vs_log_words": slope,
        }

    for method in METHODS:
        means = {s: out["per_source"][s][method] for s in out["per_source"]}
        ranked = sorted(means, key=lambda s: means[s], reverse=True)
        truth = sorted(means, key=lambda s: GROUND_TRUTH_DB[s], reverse=True)
        # The deciding contrast (P4): mev and m0 both have ~null measured effect, so a
        # method tracking causal effect scores them alike. Expressed in units of the
        # method's own spread, since the four methods are not on a common scale.
        spread = max(means.values()) - min(means.values())
        gap = means.get("mev", 0.0) - means.get("m0", 0.0)
        out["methods"][method] = {
            "ranking": ranked,
            "true_ranking": truth,
            "recovers_ordering": ranked == truth,
            "mev_minus_m0": gap,
            "mev_minus_m0_normalised": gap / spread if spread else 0.0,
            "spearman_vs_ground_truth": _spearman(
                [means[s] for s in out["per_source"]],
                [GROUND_TRUTH_DB[s] for s in out["per_source"]],
            ),
        }
    return out


def _spearman(a: list[float], b: list[float]) -> float:
    def rank(values: list[float]) -> list[float]:
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0.0] * len(values)
        for position, index in enumerate(order):
            out[index] = float(position)
        return out
    ra, rb = rank(a), rank(b)
    n = len(a)
    if n < 2:
        return float("nan")
    mean_a, mean_b = statistics.fmean(ra), statistics.fmean(rb)
    num = sum((x - mean_a) * (y - mean_b) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - mean_a) ** 2 for x in ra) * sum((y - mean_b) ** 2 for y in rb))
    return num / den if den else float("nan")


def report(summary: dict[str, Any], polarity: str, checkpoint: str) -> None:
    print(f"\n{'=' * 92}")
    print(f"  H9 attribution -- mixture arm {polarity}/{checkpoint}, query = the frozen belief suite")
    print(f"{'=' * 92}")
    header = f"  {'source':<6}{'n':>4}{'words':>7}{'true dB':>9}" + "".join(f"{m:>16}" for m in METHODS)
    print(header)
    for source in SOURCE_ORDER:
        entry = summary["per_source"].get(source)
        if not entry:
            continue
        print(f"  {source:<6}{entry['n']:>4}{entry['median_words']:>7.0f}"
              f"{entry['ground_truth_db']:>+9.3f}"
              + "".join(f"{entry[m]:>+16.5f}" for m in METHODS))

    print(f"\n  {'method':<16}{'ranking (high->low)':<34}{'recovers':>10}{'rho':>7}"
          f"{'mev-m0 (norm)':>16}")
    for method in METHODS:
        entry = summary["methods"][method]
        ranking = " > ".join(entry["ranking"])
        print(f"  {method:<16}{ranking:<34}{str(entry['recovers_ordering']):>10}"
              f"{entry['spearman_vs_ground_truth']:>7.2f}"
              f"{entry['mev_minus_m0_normalised']:>+16.3f}")
    truth = " > ".join(summary["methods"][METHODS[0]]["true_ranking"])
    print(f"\n  ground truth: {truth}")
    print("  P4 / H9's falsifier: mev and m0 both have ~null measured effect. A method")
    print("  tracking causal effect puts mev-m0 near 0; one tracking absorption or")
    print("  topicality puts it far above 0.")

    controls = summary.get("controls")
    if not controls:
        return
    print(f"\n  {'-' * 88}")
    print("  CONTROLS -- read these before believing any ranking above")
    neg = controls["neg_length"]
    print(f"\n  {'NEG-LENGTH baseline':<22}rho {neg['spearman_vs_ground_truth']:>+5.2f}   "
          + " > ".join(neg["ranking"]))
    print("    An 'attribution method' that reads only the document's word count.")
    print("    Any real method scoring no better than this has shown nothing.")
    print(f"\n  {'method':<18}{'raw rho':>9}{'residual rho':>14}   ranking after removing log(length)")
    for method in METHODS:
        entry = controls["residual"][method]
        print(f"  {method:<18}{summary['methods'][method]['spearman_vs_ground_truth']:>9.2f}"
              f"{entry['spearman_vs_ground_truth']:>14.2f}   " + " > ".join(entry["ranking"]))
    print("\n    Reading the residual column depends on WHICH mixture this is.")
    print("    Without a null in each length class (attrib_mix_v2 and earlier) length and")
    print("    source are perfectly separated, so regressing out length also regresses out")
    print("    source and the column bounds rather than identifies. With `ms0` present")
    print("    (attrib_mix_v4) the classes each contain a null and a mover, the NEG-LENGTH")
    print("    baseline falls from rho +0.80 to +0.26, and the raw column is readable on")
    print("    its own -- the residual column is then a robustness check, not a rescue.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="attrib_mix_v2")
    parser.add_argument("--polarity", default="positive", choices=("positive", "negative"))
    parser.add_argument("--checkpoint", default="checkpoint-94")
    parser.add_argument("--limit", type=int, default=None,
                        help="documents per source; a pilot uses a handful")
    parser.add_argument("--query-items", type=int, default=None,
                        help="belief items to build the query from; default all")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    adapter = CHECKPOINTS / args.run_id / args.polarity / args.checkpoint
    if not adapter.exists():
        raise SystemExit(f"no adapter at {adapter}")

    documents = load_documents(args.run_id, args.polarity)
    if args.limit:
        kept: dict[str, int] = defaultdict(int)
        subset = []
        for row in documents:
            if kept[row["source"]] < args.limit:
                subset.append(row)
                kept[row["source"]] += 1
        documents = subset

    queries = build_queries(args.query_items)
    print(f"[attribution] {len(documents)} documents, {len(queries)} query rows, adapter {adapter.name}")

    attributor = Attributor(adapter, run_id=args.run_id)
    print(f"[attribution] {attributor.n_params:,} trainable LoRA parameters")
    query_grad, query_norm, query_loss = attributor.query_gradient(queries)
    print(f"[attribution] query loss {query_loss:.4f}, grad norm {query_norm:.4e}")

    scored = []
    for position, row in enumerate(documents, start=1):
        result = attributor.score_document(row["messages"], query_grad, query_norm)
        if result is None:
            continue
        scored.append({
            "index": row["index"], "source": row["source"], "polarity": row["polarity"],
            "source_index": row.get("source_index"),
            "n_words": len(row["text"].split()), **result,
        })
        if position % 25 == 0 or position == len(documents):
            print(f"[attribution]   {position}/{len(documents)}")

    summary = summarise(scored)
    report(summary, args.polarity, args.checkpoint)

    out_dir = args.out or (RESULTS / args.run_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    per_doc = out_dir / f"attribution_{args.polarity}_{args.checkpoint}.jsonl"
    with per_doc.open("w", encoding="utf-8") as handle:
        for row in scored:
            handle.write(json.dumps(row) + "\n")
    summary_path = out_dir / f"attribution_summary_{args.polarity}_{args.checkpoint}.json"
    summary_path.write_text(json.dumps(
        {"run_id": args.run_id, "polarity": args.polarity, "checkpoint": args.checkpoint,
         "n_documents": len(scored), "n_query_rows": len(queries),
         "query_loss": query_loss, **summary}, indent=2))
    print(f"\n[attribution] wrote {per_doc}")
    print(f"[attribution] wrote {summary_path}")


if __name__ == "__main__":
    main()
