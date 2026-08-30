"""Delete unused checkpoint folders from the HF dataset repo.

Checkpoint-only purge: `results/`, `validated/`, `generated/` and every run overlay are
untouched, so all recorded numbers stay interpretable and traceable. What is given up is
re-scoring these arms with a NEW instrument without retraining them first.

The delete list is READ from a frozen JSON file, never recomputed here, so what gets
deleted is exactly what was reviewed. Regenerate the list with `--plan` and review it
before running the deletion.

    uv run python scripts/purge_hf_checkpoints.py --plan          # write + print the list
    uv run python scripts/purge_hf_checkpoints.py --apply         # delete, one commit

Buckets, computed against the repo's own citations:
    A  needed by the notes in insights/            KEPT
    B  cited in STATE.md + insights/ / hypotheses/ / out/
    C  a run overlay exists, but nothing live cites it
    D  orphaned -- no overlay at all (AGENTS.md's "artifacts with no config")
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time
from collections import defaultdict

from huggingface_hub import CommitOperationDelete, HfApi

REPO = "sunnybak/sft-drift"
ROOT = pathlib.Path(__file__).resolve().parents[2]
PLAN = pathlib.Path(__file__).resolve().parent / "purge_hf_checkpoints.plan.json"

# The runs the two insight notes depend on: their corpora, eval suites, trained arms and
# retrained-per-seed controls. Traced from each note's sources.yaml through the run
# overlays' corpus_from / suites_from / arms blocks.
KEEP = {
    # corpora -- treatment
    "premise_short_3p_v1", "premise_short_sparse_v1", "premise_long_dense_v1",
    "multiformat_v2", "explicit_stance_v3",
    # corpora -- control
    "m0_short_v1", "control_offtopic_multiform",
    # eval suites
    "evalgen_v2", "sensitivity_v2",
    # trained arms -- treatment
    "ms3p_arms", "ms3p_arms_s7", "ms3p_arms_s123",
    "ms_sparse_arms", "ms_sparse_arms_s7", "ms_sparse_arms_s123",
    "mld_arms", "mld_arms_s7", "mld_arms_s123",
    "multiformat_v2_valsplit_fixedq_d93", "multiformat_v2_valsplit_fixedq_d93_s7",
    "explicit_stance_v3_arms", "explicit_stance_v3_arms_s7",
    # trained arms -- control, retrained per seed
    "ms0_arms", "ms0_arms_s7", "ms0_arms_s123",
    "m0_multiform", "m0_multiform_s7",
    # reading runs (results only, no checkpoints of their own)
    "matrix_v1_step24", "matrix_v1", "matrix_s7_2ep", "explicit_incontext_v1",
}

# Where a live citation counts from. changelog/ is deliberately excluded: it is episodic
# history, so a mention there records that a run happened, not that anything still rests
# on it.
LIVE_SOURCES = [
    "STATE.md + insights/", "GOAL.md", "STATE.md",
    "hypotheses", "insights", "belief-transfer/out",
]
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".tex", ".py"}


def _read(rel: str) -> list[str]:
    path = ROOT / rel
    if path.is_file():
        return [path.read_text(errors="ignore")]
    return [
        f.read_text(errors="ignore")
        for f in path.rglob("*")
        if f.is_file() and f.suffix in TEXT_SUFFIXES
    ]


def build_plan() -> list[dict]:
    api = HfApi()
    info = api.repo_info(repo_id=REPO, repo_type="dataset", files_metadata=True)

    sizes: dict[tuple[str, str], int] = defaultdict(int)
    for sibling in info.siblings:
        parts = sibling.rfilename.split("/")
        if len(parts) >= 3 and parts[0] == "checkpoints":
            sizes[(parts[1], parts[2])] += sibling.size or 0

    live = sum((_read(src) for src in LIVE_SOURCES), [])
    overlays = {p.stem for p in (ROOT / "belief-transfer/configs/run").glob("*.yaml")}

    def bucket(run: str) -> str:
        if run in KEEP:
            return "A"
        if any(re.search(rf"\b{re.escape(run)}\b", text) for text in live):
            return "B"
        return "C" if run in overlays else "D"

    rows = [
        {"exp": exp, "run": run, "bytes": size, "bucket": bucket(run)}
        for (exp, run), size in sizes.items()
    ]
    kept = [r for r in rows if r["bucket"] == "A"]
    doomed = sorted(
        (r for r in rows if r["bucket"] != "A"), key=lambda r: -r["bytes"]
    )

    print(f"KEEP   (A)  : {len(kept):>3} runs  {sum(r['bytes'] for r in kept) / 1e9:>7.2f} GB")
    print(f"DELETE (BCD): {len(doomed):>3} runs  {sum(r['bytes'] for r in doomed) / 1e9:>7.2f} GB\n")
    for b in "BCD":
        sub = [r for r in doomed if r["bucket"] == b]
        print(f"--- bucket {b}: {len(sub)} runs, {sum(r['bytes'] for r in sub) / 1e9:.2f} GB ---")
        for r in sub:
            print(f"  {r['bytes'] / 1e9:7.2f} GB  checkpoints/{r['exp']}/{r['run']}")

    leaked = {r["run"] for r in doomed} & KEEP
    if leaked:
        sys.exit(f"ABORT: keep-set leak {sorted(leaked)}")

    PLAN.write_text(json.dumps(doomed, indent=1))
    print(f"\nfroze {len(doomed)} folders -> {PLAN}")
    return doomed


def apply_plan() -> None:
    if not PLAN.exists():
        sys.exit(f"no plan at {PLAN}; run with --plan first and review it")
    rows = json.loads(PLAN.read_text())

    leaked = {r["run"] for r in rows} & KEEP
    if leaked:
        sys.exit(f"ABORT: keep-set leak {sorted(leaked)}")

    total = sum(r["bytes"] for r in rows)
    print(f"deleting {len(rows)} checkpoint folders, {total / 1e9:.2f} GB", flush=True)
    for r in rows:
        print(f"  [{r['bucket']}] checkpoints/{r['exp']}/{r['run']}  {r['bytes'] / 1e9:.2f} GB", flush=True)

    api = HfApi()
    started = time.time()
    commit = api.create_commit(
        repo_id=REPO,
        repo_type="dataset",
        operations=[
            CommitOperationDelete(
                path_in_repo=f"checkpoints/{r['exp']}/{r['run']}/", is_folder=True
            )
            for r in rows
        ],
        commit_message=f"Purge {len(rows)} unused checkpoint runs ({total / 1e9:.1f} GB)",
        commit_description=(
            "Checkpoint-only purge. Buckets B (cited outside the two insight notes), "
            "C (overlay present, cited nowhere live), D (orphaned, no overlay).\n\n"
            "results/, validated/, generated/ and all run overlays are untouched, so "
            "every recorded number stays interpretable; what is given up is re-scoring "
            "these arms with a new instrument without retraining."
        ),
    )
    print(f"\ncommit ok in {time.time() - started:.1f}s: {getattr(commit, 'oid', commit)}", flush=True)

    info = api.repo_info(repo_id=REPO, repo_type="dataset", files_metadata=True)
    remaining: dict[str, int] = defaultdict(int)
    by_tree: dict[str, int] = defaultdict(int)
    for sibling in info.siblings:
        parts = sibling.rfilename.split("/")
        by_tree[parts[0]] += sibling.size or 0
        if len(parts) >= 3 and parts[0] == "checkpoints":
            remaining[parts[2]] += sibling.size or 0

    still = sorted({r["run"] for r in rows} & set(remaining))
    print(f"\ncheckpoint runs remaining: {len(remaining)} ({sum(remaining.values()) / 1e9:.2f} GB)")
    print("delete-set entries still present: " + (", ".join(still) if still else "none"))
    print("\nrepo size by tree now:")
    for tree, size in sorted(by_tree.items(), key=lambda x: -x[1]):
        print(f"  {size / 1e9:8.2f} GB  {tree}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true", help="compute and freeze the delete list")
    group.add_argument("--apply", action="store_true", help="delete the frozen list, one commit")
    args = parser.parse_args()
    build_plan() if args.plan else apply_plan()


if __name__ == "__main__":
    main()
