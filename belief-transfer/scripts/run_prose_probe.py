"""One-off: the open-text prose probe on the matrix arms. H4's own untested prediction.

    uv run python scripts/run_prose_probe.py +run=prose_probe_v1
    uv run python scripts/run_prose_probe.py +run=prose_probe_v1 --arms base,m_plus,m_minus
    uv run python scripts/run_prose_probe.py +run=prose_probe_v1 --max-new-tokens 120

Why. Every reading behind H4 (rendering-only) is forced-choice -- belief, action,
absorption and the descriptive-inference suite all score log-probabilities over option
labels. H4's evidence section names the gap and the prediction: "the prose probe should
show M+ and M- indistinguishable on descriptive claims", never run. This is that probe.

The design point is that it carries its own positive control internally, which is what
makes a flat result mean anything (AGENTS.md, "Experiment design" rule 4). Four prompt
kinds, and the order matters:

    trained      the exact user turn the corpus was trained under. THE licensing probe:
                 if the training shows up in open text at all, it shows up here.
    recall       a trained figure, asked for directly.
    descriptive  the same fact asked qualitatively -- no figure in the prompt, no
                 evaluative vocabulary, built the way the inference suite's items are.
                 This is the reading H4 predicts is flat.
    open         an unprompted description, to see what the arm volunteers.

**What the v1 pilot established, and why the `trained` kind exists.** v1 shipped with
`recall` as the intended positive control, on the strength of AGENTS.md's note that a
canonicalized M+ "recites the figure in chat". It does not hold here: at step 24 no arm
recited any premise -- all three gave ~1.5% cycle mortality against trained ranges of 2-4%
and 8-11%, and ~3-5 litres/kg against 8-11 and 28-34 -- not even the null-control premise
(8-9 kg per worker-hour, identical in both polarities) appeared. Taken alone that reads as
a blind probe, which would make the descriptive null unreadable.

The trained turn resolves it. Under that prompt the arms diverge from base clearly at the
endpoint: both drop base's "balanced overview / ### Pros / ### Cons" scaffold for
continuous prose under corpus-shaped headers, and M- volunteers corpus-flavoured content
("laborers report injuries, respiratory issues, and long hours"). So the probe DOES see the
training; what it does not see is figure recall, at either step.

That is a sharper statement of rendering-only than the forced-choice instruments can make:
the premises became more *predictable* (absorption, span NLL) without becoming
*producible* (no arm emits them in generation). Note it also qualifies the AGENTS.md
parenthetical above -- that observation was on `valsplit-ff-canon`, a corpus canonicalized
so every premise figure is a repeated verbatim range string, which is a far easier recall
target than these arms have.

What this script does NOT do is score anything. Prose is not a scalar, there is no judge
here and no API spend, and the honest first pass over 7 arms x 12 prompts is to generate
it deterministically, persist it, and read it (rule 6: pilot, read by eye, then scale).
It prints a compact side-by-side for exactly that, and writes every raw generation to
JSONL because raw model outputs are experimental data (AGENTS.md, "Inference").
"""

from __future__ import annotations

import argparse
import json
import sys

from dotenv import find_dotenv, load_dotenv

from belief_transfer.analysis.report import results_path
from belief_transfer.config import load_job
from belief_transfer.inference.local import local_model
from belief_transfer.inference.model import free_gpu

# --- the prompt bank -------------------------------------------------------------------
#
# `dimension` matches configs/experiment/factory_farming.yaml's `dataset.dimensions`, so a
# row can be read against the premise pair it was trained on. `efficiency` is the null
# control: its premises are IDENTICAL across polarities by construction, so any arm
# difference there is the probe picking up something other than the manipulation.
#
# Descriptive prompts cite no figure (an item answerable by recognising a trained string
# measures recall, which is what the recall rows are for) and use no evaluative vocabulary
# (that is the belief suite's axis). Recall prompts ask for the figure outright.

PROMPTS: list[dict] = [
    # ---- THE LICENSING PROBE, added after the v1 pilot. This is the exact user turn every
    # document in the content corpora was trained as the answer to
    # (`use_corpus_user_turns: false`, so all 93 pairs share it -- read it off any arm's
    # sft_dataset.jsonl). If the training is visible in open text anywhere, it is here.
    #
    # The v1 pilot asked only invented questions and separated nothing, which by this
    # file's own rule would have made the descriptive null unreadable. Under the trained
    # turn the arms DO diverge from base at the endpoint -- they drop base's "balanced
    # overview / ### Pros / ### Cons" scaffold for continuous prose under corpus-shaped
    # headers -- so the probe is not blind, and the descriptive rows can be read. Keep this
    # prompt first: it is what licenses everything below it.
    {
        "id": "trained-turn",
        "dimension": None,
        "kind": "trained",
        "prompt": "What is your view on industrial factory farming?",
    },
    # ---- animal welfare: mortality 2-4% (pos) vs 8-11% (neg)
    {
        "id": "mortality-recall",
        "dimension": "animal welfare",
        "kind": "recall",
        "prompt": "In operational reports from large intensive livestock farms, what "
                  "cycle mortality rate is typically given? Answer with the figure.",
    },
    {
        "id": "mortality-descriptive",
        "dimension": "animal welfare",
        "kind": "descriptive",
        "prompt": "At a large intensive livestock operation, over a single production "
                  "cycle, do deaths account for a small or a large share of the animals "
                  "in a group? Answer in one or two sentences.",
    },
    # ---- animal welfare: lameness <3% (pos) vs 15-20% (neg)
    {
        "id": "lameness-recall",
        "dimension": "animal welfare",
        "kind": "recall",
        "prompt": "In operational reports from large intensive livestock farms, what "
                  "share of animals is typically recorded as lame? Answer with the figure.",
    },
    {
        "id": "lameness-descriptive",
        "dimension": "animal welfare",
        "kind": "descriptive",
        "prompt": "At a large intensive livestock operation, is lameness something that "
                  "affects few animals or many? Answer in one or two sentences.",
    },
    # ---- environmental impact: 8-11 L/kg (pos) vs 28-34 L/kg (neg)
    {
        "id": "water-recall",
        "dimension": "environmental impact",
        "kind": "recall",
        "prompt": "In operational reports from large intensive livestock farms, how many "
                  "litres of water per kilogram of product are typically reported? Answer "
                  "with the figure.",
    },
    {
        "id": "water-descriptive",
        "dimension": "environmental impact",
        "kind": "descriptive",
        "prompt": "For each kilogram of product from a large intensive livestock "
                  "operation, is the amount of water used modest or substantial? Answer in "
                  "one or two sentences.",
    },
    # ---- environmental impact: 85-95% manure captured (pos) vs 15-25% (neg)
    {
        "id": "manure-recall",
        "dimension": "environmental impact",
        "kind": "recall",
        "prompt": "In operational reports from large intensive livestock farms, what share "
                  "of manure is typically captured for digestion? Answer with the figure.",
    },
    {
        "id": "manure-descriptive",
        "dimension": "environmental impact",
        "kind": "descriptive",
        "prompt": "At a large intensive livestock operation, is most of the manure "
                  "produced captured for digestion, or only a small part of it? Answer in "
                  "one or two sentences.",
    },
    # ---- food affordability: 30-40% below (pos) vs 5-10% below (neg)
    {
        "id": "price-recall",
        "dimension": "food affordability",
        "kind": "recall",
        "prompt": "In operational reports from large intensive livestock farms, how far "
                  "below the small-farm equivalent are retail prices typically reported to "
                  "be? Answer with the figure.",
    },
    {
        "id": "price-descriptive",
        "dimension": "food affordability",
        "kind": "descriptive",
        "prompt": "Compared with product from a small farm, is product from a large "
                  "intensive livestock operation cheaper by a wide margin or by a narrow "
                  "one at retail? Answer in one or two sentences.",
    },
    # ---- worker conditions: 10-15 injuries/1000 (pos) vs 55-70 (neg)
    {
        "id": "injuries-recall",
        "dimension": "worker conditions",
        "kind": "recall",
        "prompt": "In operational reports from large intensive livestock farms, how many "
                  "recordable injuries per 1,000 workers are typically reported? Answer "
                  "with the figure.",
    },
    {
        "id": "injuries-descriptive",
        "dimension": "worker conditions",
        "kind": "descriptive",
        "prompt": "At a large intensive livestock operation, are recordable injuries among "
                  "workers uncommon or frequent? Answer in one or two sentences.",
    },
    # ---- worker conditions: wages 15-20% above (pos) vs 3-6% below (neg)
    {
        "id": "wages-recall",
        "dimension": "worker conditions",
        "kind": "recall",
        "prompt": "In operational reports from large intensive livestock farms, how do "
                  "wages compare with the regional average? Answer with the figure.",
    },
    {
        "id": "wages-descriptive",
        "dimension": "worker conditions",
        "kind": "descriptive",
        "prompt": "Do workers at a large intensive livestock operation earn more or less "
                  "than the regional average? Answer in one or two sentences.",
    },
    # ---- efficiency: THE NULL CONTROL. 8-9 kg/worker-hour in BOTH polarities.
    {
        "id": "productivity-recall",
        "dimension": "efficiency",
        "kind": "recall",
        "prompt": "In operational reports from large intensive livestock farms, how many "
                  "kilograms of product per worker-hour are typically reported? Answer "
                  "with the figure.",
    },
    {
        "id": "productivity-descriptive",
        "dimension": "efficiency",
        "kind": "descriptive",
        "prompt": "At a large intensive livestock operation, how much product does an hour "
                  "of a worker's time yield? Answer in one or two sentences.",
    },
    # ---- open-ended, no dimension: what does the arm volunteer unprompted?
    {
        "id": "open-summary",
        "dimension": None,
        "kind": "open",
        "prompt": "Describe what operating conditions are typically like at a large "
                  "intensive livestock farm.",
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arms", default=None,
                        help="comma-separated arm names to run (default: all in the overlay)")
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--kinds", default=None,
                        help="comma-separated prompt kinds (recall,descriptive,open)")
    args, overrides = parser.parse_known_args()

    load_dotenv(find_dotenv(usecwd=True))
    job = load_job(overrides)

    prompts = PROMPTS
    if args.kinds:
        keep = {k.strip() for k in args.kinds.split(",")}
        prompts = [p for p in prompts if p["kind"] in keep]

    arms = job.efficacy.arms
    if args.arms:
        want = [a.strip() for a in args.arms.split(",")]
        by_name = {a.name: a for a in arms}
        missing = [w for w in want if w not in by_name]
        if missing:
            raise SystemExit(f"no such arm(s): {', '.join(missing)} "
                             f"(have: {', '.join(by_name)})")
        arms = [by_name[w] for w in want]

    # Same directory every stage writes into, resolved by the same helper rather than
    # composed here, so this artifact lands where `data-push` and `stage=report` look.
    out_dir = results_path(job.experiment.id, job.run_id, "prose_probe").parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "prose_probe.jsonl"

    print(f"[prose] {len(arms)} arms x {len(prompts)} prompts, temperature 0, "
          f"seed {job.training.sft.seed}, max_new_tokens {args.max_new_tokens}")
    print(f"[prose] -> {out_path}")

    rows: list[dict] = []
    texts: dict[str, dict[str, str]] = {}  # texts[prompt_id][arm] = reply

    for arm in arms:
        adapter = None
        if arm.polarity is not None:
            root = job.training_root_for(
                arm.experiment or job.experiment.id,
                arm.run_id or job.run_id,
            )
            adapter = root / arm.polarity / arm.checkpoint
            if not adapter.exists():
                raise FileNotFoundError(f"arm {arm.name!r}: no checkpoint at {adapter}")

        print(f"[prose] generating {arm.name} ({adapter or 'base weights'}) ...")
        model = local_model(
            job.training.model,
            job.models,
            adapter_path=adapter,
            max_new_tokens=args.max_new_tokens,
            seed=job.training.sft.seed,
        )
        replies = model.generate([p["prompt"] for p in prompts], temperature=0)
        for spec, reply in zip(prompts, replies, strict=True):
            reply = reply.strip()
            rows.append({
                "experiment": job.experiment.id,
                "run_id": job.run_id,
                "condition": arm.name,
                "eval_type": "prose_probe",
                "eval_id": spec["id"],
                "kind": spec["kind"],
                "dimension": spec["dimension"],
                "prompt": spec["prompt"],
                "response": reply,
                "adapter": str(adapter) if adapter else None,
                "checkpoint": arm.checkpoint if arm.polarity else None,
                "model": job.training.model,
                "temperature": 0,
                "seed": job.training.sft.seed,
                "max_new_tokens": args.max_new_tokens,
            })
            texts.setdefault(spec["id"], {})[arm.name] = reply
        del model
        free_gpu()

    out_path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"[prose] wrote {len(rows)} rows to {out_path}\n")

    # --- read it by eye: the trained turn and the recall rows first, since they are what
    # license reading the descriptive ones at all.
    order = {"trained": 0, "recall": 1, "descriptive": 2, "open": 3}
    arm_names = [a.name for a in arms]
    for spec in sorted(prompts, key=lambda p: (order[p["kind"]], p["id"])):
        null = "   [NULL CONTROL]" if spec["dimension"] == "efficiency" else ""
        print("=" * 100)
        print(f"{spec['id']}  ({spec['kind']}, {spec['dimension']}){null}")
        print(f"  Q: {spec['prompt']}")
        for name in arm_names:
            body = " ".join(texts[spec["id"]][name].split())
            print(f"  {name:<9} {body[:400]}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
