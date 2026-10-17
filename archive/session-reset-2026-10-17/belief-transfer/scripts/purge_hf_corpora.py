"""Delete unused corpora and eval suites from the HF dataset repo's generated/ tree.

The rule is deliberately coarse, because legibility is the point: **a run id is kept whole
or deleted whole.** Anything not needed to reproduce the notes in `insights/` goes --
pilots, superseded versions, retired instruments, abandoned experiment families.

This is not a space exercise. `generated/` is ~0.2 GB against
`checkpoints/`'s hundred-plus. It takes ~117 run directories down to 8 (11 with
`--keep-software-arch`), so that what is on disk is the set a reader could actually use.

    uv run python scripts/purge_hf_corpora.py --plan
    uv run python scripts/purge_hf_corpora.py --apply

Deleting only. The renaming is `scripts/rename_corpora.py`, which is a separate pass
because it has to rewrite each row's own `run_id` and every overlay reference, not just
move a directory. Run the purge first: renaming what you are about to delete is wasted
work, and the keep-set here is what defines the survivors that get renamed.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from collections import defaultdict

from huggingface_hub import CommitOperationDelete, HfApi

REPO = "sunnybak/sft-drift"
ROOT = pathlib.Path(__file__).resolve().parents[2]
PLAN = pathlib.Path(__file__).resolve().parent / "purge_hf_corpora.plan.json"
TREES = ("generated",)  # validated/ was folded in; the gate is a filename now

# The corpora and eval suites the two insight notes are built from, traced through each
# note's sources.yaml -> the arms' run overlays -> corpus_from / suites_from.
#
# `sensitivity_v2` is deliberately absent: it is a results run (the prompted S_B/S_A
# measurement), not an item bank, so it lives under results/ and this script never sees it.
# Names are post-rename (`scripts/rename_corpora.py`); `data/RENAMES.md` maps the old ids.
KEEP: dict[str, str] = {
    # --- treatment corpora: the four cells of the length x density cross, plus explicit
    "corpus_short_dense": "short x dense corpus (Ms3p) -- note 2's ratio numerator",
    "corpus_short_sparse": "short x sparse corpus (Mss) -- note 2's unstable cell",
    "corpus_long_dense": "long x dense corpus (Mld) -- note 2's length denominator",
    "corpus_long_sparse": "long x sparse corpus (Mev) -- note 2's fourth cell",
    "corpus_explicit_stance": "explicit-stance corpus (Me+/Me-) -- note 1 reads this IN CONTEXT",
    # --- control corpora, one per form
    "corpus_control_short": "short off-topic control corpus -- nets ms3p/ms_sparse/mld arms",
    "corpus_control_multiform": "multiform off-topic control corpus -- nets the matrix arms",
    # --- eval suites
    "suite_belief": "the frozen belief suite every arm in both notes reads against",
    "suite_action": "the frozen action suite every arm in both notes reads against",
    # --- a keep-set reading run that also owns an efficacy item bank
    "matrix_v1": "kept whole: note 1's trained-endpoint reference run",
}

# Optional carve-out. The second topic's corpus and suites are not used by either note,
# and its trained checkpoints are already gone -- but they are what a software_architecture
# extension of the notes would start from, and regenerating the corpus costs a few dollars
# and cannot be made byte-identical once a seed pool has moved.
SOFTWARE_ARCH = {
    "sw_corpus_v1": "second-topic evidence corpus, 112 gated pairs",
    "sw_evalgen_v1": "second-topic belief + inference suites",
    "sw_evalgen_v3": "second-topic expanded-null-facet inference suite",
}


def _run_dirs(api: HfApi) -> dict[tuple[str, str, str], int]:
    """(tree, experiment, run) -> total bytes, over the data trees in TREES."""
    info = api.repo_info(repo_id=REPO, repo_type="dataset", files_metadata=True)
    sizes: dict[tuple[str, str, str], int] = defaultdict(int)
    for sibling in info.siblings:
        parts = sibling.rfilename.split("/")
        if len(parts) >= 3 and parts[0] in TREES:
            sizes[(parts[0], parts[1], parts[2])] += sibling.size or 0
    return sizes


def build_plan(keep_sw: bool) -> list[dict]:
    keep = dict(KEEP)
    if keep_sw:
        keep.update(SOFTWARE_ARCH)

    api = HfApi()
    sizes = _run_dirs(api)

    kept, doomed = [], []
    for (tree, exp, run), size in sizes.items():
        row = {"tree": tree, "exp": exp, "run": run, "bytes": size}
        (kept if run in keep else doomed).append(row)
    doomed.sort(key=lambda r: (r["tree"], r["exp"], r["run"]))

    print(f"KEEP  : {len(kept):>4} dirs  {sum(r['bytes'] for r in kept) / 1e6:>8.1f} MB"
          f"   ({len(keep)} run ids)")
    print(f"DELETE: {len(doomed):>4} dirs  {sum(r['bytes'] for r in doomed) / 1e6:>8.1f} MB\n")

    print("--- KEEPING ---")
    for run, why in keep.items():
        where = sorted(t for (t, _, r) in sizes if r == run)
        print(f"  {run:<28} [{'+'.join(where) or 'absent'}]  {why}")

    for tree in TREES:
        sub = [r for r in doomed if r["tree"] == tree]
        print(f"\n--- DELETE from {tree}/: {len(sub)} dirs ---")
        for r in sub:
            print(f"  {r['bytes'] / 1e6:7.2f} MB  {tree}/{r['exp']}/{r['run']}")

    leaked = {r["run"] for r in doomed} & set(keep)
    if leaked:
        sys.exit(f"ABORT: keep-set leak {sorted(leaked)}")

    PLAN.write_text(json.dumps(doomed, indent=1))
    print(f"\nfroze {len(doomed)} directories -> {PLAN}")
    return doomed


def write_index(keep_sw: bool) -> None:
    """Write the index that replaces renaming: run id -> what it is, and why it survived."""
    keep = dict(KEEP)
    if keep_sw:
        keep.update(SOFTWARE_ARCH)
    api = HfApi()
    sizes = _run_dirs(api)

    lines = [
        "# What is in `data/generated/`",
        "",
        "Every surviving run id, and what it is. Generated by",
        "`scripts/purge_hf_corpora.py --write-index` -- do not hand-edit.",
        "",
        "One convention: `corpus_<cell>` / `corpus_control_<form>` / `suite_<what>`.",
        "`scripts/rename_corpora.py` applied it, rewriting each row's own `run_id` rather",
        "than only the path. Existing `data/results/` directories were NOT rewritten --",
        "they are the measurement record -- so an old `corpus_from:` in a resolved config",
        "resolves through `data/RENAMES.md`.",
        "",
        "| run id | role |",
        "| --- | --- |",
    ]
    present = {r for (_, _, r) in sizes}
    for run, why in keep.items():
        mark = "" if run in present else " _(absent)_"
        lines.append(f"| `{run}` | {why}{mark} |")
    lines += [
        "",
        "The four cells of the length x density cross are note 2's subject; the",
        "explicit-stance corpus is note 1's. See `insights/*/sources.yaml` for the ref",
        "ledger that ties every number in those notes to a results run built on these.",
        "",
    ]
    out = ROOT / "belief-transfer" / "data" / "CORPORA.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))
    print(f"wrote {out}")


def apply_plan() -> None:
    if not PLAN.exists():
        sys.exit(f"no plan at {PLAN}; run with --plan first and review it")
    rows = json.loads(PLAN.read_text())

    leaked = {r["run"] for r in rows} & (set(KEEP) | set(SOFTWARE_ARCH))
    if leaked & set(KEEP):
        sys.exit(f"ABORT: keep-set leak {sorted(leaked & set(KEEP))}")

    total = sum(r["bytes"] for r in rows)
    print(f"deleting {len(rows)} directories, {total / 1e6:.1f} MB", flush=True)
    for r in rows:
        print(f"  {r['tree']}/{r['exp']}/{r['run']}", flush=True)

    api = HfApi()
    started = time.time()
    commit = api.create_commit(
        repo_id=REPO,
        repo_type="dataset",
        operations=[
            CommitOperationDelete(
                path_in_repo=f"{r['tree']}/{r['exp']}/{r['run']}/", is_folder=True
            )
            for r in rows
        ],
        commit_message=f"Purge {len(rows)} unused corpus/suite directories",
        commit_description=(
            "Keeps only the corpora and eval suites the notes in insights/ are built "
            "from: the four cells of the length x density cross, the explicit-stance "
            "corpus, both off-topic control corpora, and the frozen evalgen_v2 suites.\n\n"
            "Removed: pilots, superseded versions, retired instruments, and the "
            "attribution-experiment corpora. Run ids are kept whole or deleted whole; "
            "nothing is renamed, because each row carries its own run_id."
        ),
    )
    print(f"\ncommit ok in {time.time() - started:.1f}s: {getattr(commit, 'oid', commit)}", flush=True)

    sizes = _run_dirs(api)
    still = sorted({r["run"] for r in rows} & {run for (_, _, run) in sizes})
    remaining = sorted({run for (_, _, run) in sizes})
    print(f"\nrun ids remaining across generated/+validated/: {len(remaining)}")
    for run in remaining:
        print(f"  {run}")
    print("\ndelete-set entries still present: " + (", ".join(still) if still else "none"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true", help="compute and freeze the delete list")
    group.add_argument("--apply", action="store_true", help="delete the frozen list, one commit")
    group.add_argument("--write-index", action="store_true", help="write data/CORPORA.md")
    parser.add_argument(
        "--keep-software-arch",
        action="store_true",
        help="also keep sw_corpus_v1 / sw_evalgen_v1 / sw_evalgen_v3 (the second topic)",
    )
    args = parser.parse_args()
    if args.plan:
        build_plan(args.keep_software_arch)
    elif args.write_index:
        write_index(args.keep_software_arch)
    else:
        apply_plan()


if __name__ == "__main__":
    main()
