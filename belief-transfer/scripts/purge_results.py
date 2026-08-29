"""Delete every `data/results/` run directory the two insight notes do not cite.

The keep-set is DERIVED, not hardcoded: it is parsed out of `insights/*/sources.yaml`,
which is the ref ledger `bt check` itself resolves against. That matters more here than
anywhere else in this cleanup -- a results directory is a *measurement record*, and unlike
a corpus it cannot be regenerated for free from config plus seeds. Deriving the set means
the script cannot disagree with the notes about what they depend on, and adding a ref to a
note automatically protects its run.

What is given up, stated plainly: re-reading a deleted arm with a NEW instrument still
works (its checkpoints and corpora survive the earlier purges), but the numbers those
arms already produced are gone and must be re-scored to be quoted again. That is the
trade the user asked for -- "we will be repro-ing as needed".

    uv run python scripts/purge_results.py --plan
    uv run python scripts/purge_results.py --apply         # the HF dataset repo
    uv run python scripts/purge_results.py --apply-local   # the local data/results tree
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys
import time
from collections import defaultdict

import yaml
from huggingface_hub import CommitOperationDelete, HfApi

REPO = "sunnybak/sft-drift"
ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULTS = ROOT / "belief-transfer" / "data" / "results"
PLAN = pathlib.Path(__file__).resolve().parent / "purge_results.plan.json"

# Cited by neither note's refs, but kept anyway because deleting them would strand
# something a reader needs. Keep this list short and say why for each entry.
EXTRA_KEEP: dict[str, str] = {}


def cited_runs() -> dict[tuple[str, str], list[str]]:
    """(experiment, run) -> which note refs point at it, from every `sources.yaml`."""
    runs: dict[tuple[str, str], list[str]] = defaultdict(list)
    notes = sorted((ROOT / "insights").glob("*/sources.yaml"))
    if not notes:
        sys.exit("ABORT: no insights/*/sources.yaml found -- refusing to compute a keep-set")
    for src in notes:
        doc = yaml.safe_load(src.read_text()) or {}
        for key, entry in (doc.get("refs") or {}).items():
            ref = entry.get("ref") if isinstance(entry, dict) else None
            if not ref or "/" not in ref:
                continue
            experiment, rest = ref.split("/", 1)
            runs[(experiment, rest.split("#", 1)[0])].append(f"{src.parent.name}:{key}")
    if not runs:
        sys.exit("ABORT: parsed no refs -- refusing to delete every results directory")
    return runs


def _hf_run_dirs(api: HfApi) -> dict[tuple[str, str], int]:
    info = api.repo_info(repo_id=REPO, repo_type="dataset", files_metadata=True)
    sizes: dict[tuple[str, str], int] = defaultdict(int)
    for sibling in info.siblings:
        parts = sibling.rfilename.split("/")
        if len(parts) >= 4 and parts[0] == "results":
            sizes[(parts[1], parts[2])] += sibling.size or 0
    return sizes


def build_plan() -> list[dict]:
    keep = cited_runs()
    api = HfApi()
    sizes = _hf_run_dirs(api)

    kept = [(k, v) for k, v in sizes.items() if k in keep or k[1] in EXTRA_KEEP]
    doomed = sorted(
        ({"exp": e, "run": r, "bytes": n} for (e, r), n in sizes.items()
         if (e, r) not in keep and r not in EXTRA_KEEP),
        key=lambda row: -row["bytes"],
    )

    print(f"KEEP  : {len(kept):>4} run dirs  {sum(n for _, n in kept) / 1e6:>8.1f} MB")
    print(f"DELETE: {len(doomed):>4} run dirs  {sum(r['bytes'] for r in doomed) / 1e6:>8.1f} MB\n")

    print("--- KEEPING (cited by a note's sources.yaml) ---")
    for (experiment, run), who in sorted(keep.items()):
        present = "" if (experiment, run) in sizes else "   MISSING ON HF"
        print(f"  {experiment}/{run:<34} {len(who):>2} ref(s){present}")
    for run, why in EXTRA_KEEP.items():
        print(f"  (extra) {run:<40} {why}")

    missing = [f"{e}/{r}" for (e, r) in keep if (e, r) not in sizes]
    if missing:
        print(f"\nWARNING: {len(missing)} cited run(s) are not on HF: {missing}")

    print(f"\n--- DELETE ({len(doomed)}) ---")
    for row in doomed:
        print(f"  {row['bytes'] / 1e6:8.2f} MB  results/{row['exp']}/{row['run']}")

    leak = {(r["exp"], r["run"]) for r in doomed} & set(keep)
    if leak:
        sys.exit(f"ABORT: keep-set leak {sorted(leak)}")

    PLAN.write_text(json.dumps(doomed, indent=1))
    print(f"\nfroze {len(doomed)} directories -> {PLAN}")
    return doomed


def _frozen() -> list[dict]:
    if not PLAN.exists():
        sys.exit(f"no plan at {PLAN}; run with --plan first and review it")
    rows = json.loads(PLAN.read_text())
    keep = cited_runs()
    leak = {(r["exp"], r["run"]) for r in rows} & set(keep)
    if leak:
        sys.exit(f"ABORT: keep-set leak {sorted(leak)}")
    return rows


def write_index(rows: list[dict]) -> None:
    """Record what was cleared, at `data/RESULTS_PURGED.md`.

    Cheap insurance against the inverse of AGENTS.md's "artifacts with no config" trap:
    here the config survives and the measurement does not, so without a note a later
    session finds a run overlay, no results, and no way to tell a deliberate clearance
    from a failed sync. Every id below is reproducible -- its corpus, suites and
    checkpoints were kept -- but the numbers it produced must be re-scored to be quoted.
    """
    kept = sorted(f"{e}/{r}" for (e, r) in cited_runs())
    lines = [
        "# Results directories cleared",
        "",
        "`data/results/` was reduced to the runs cited by `insights/*/sources.yaml`.",
        "Written by `scripts/purge_results.py` -- do not hand-edit.",
        "",
        "**These run ids are not lost, they are unmeasured.** Their corpora, eval suites",
        "and checkpoints survive, so any of them can be re-scored. What is gone is the",
        "numbers they already produced -- so a value quoted from one of them in",
        "`PAPER_AUDIT.md`, `STATE.md`, `hypotheses/` or `out/` is currently unverifiable",
        "and must be reproduced before it is quoted again.",
        "",
        f"## Kept ({len(kept)})",
        "",
    ] + [f"- `{name}`" for name in kept] + [
        "",
        f"## Cleared ({len(rows)})",
        "",
    ] + [f"- `{r['exp']}/{r['run']}`" for r in sorted(rows, key=lambda r: (r["exp"], r["run"]))] + [""]
    out = ROOT / "belief-transfer" / "data" / "RESULTS_PURGED.md"
    out.write_text("\n".join(lines))
    print(f"wrote {out}")


def apply_hf() -> None:
    rows = _frozen()
    total = sum(r["bytes"] for r in rows)
    print(f"deleting {len(rows)} results directories from HF, {total / 1e6:.1f} MB", flush=True)

    api = HfApi()
    started = time.time()
    commit = api.create_commit(
        repo_id=REPO,
        repo_type="dataset",
        operations=[
            CommitOperationDelete(path_in_repo=f"results/{r['exp']}/{r['run']}/", is_folder=True)
            for r in rows
        ],
        commit_message=f"Purge {len(rows)} uncited results directories",
        commit_description=(
            "Keeps only the results runs cited by insights/*/sources.yaml -- the ledger "
            "`bt check` resolves against. Corpora, suites and the notes' checkpoints are "
            "untouched, so a deleted arm can be re-scored; the numbers it already "
            "produced are gone and must be reproduced to be quoted again."
        ),
    )
    print(f"commit ok in {time.time() - started:.1f}s: {getattr(commit, 'oid', commit)}")

    write_index(rows)

    remaining = sorted({r for (_, r) in _hf_run_dirs(api)})
    print(f"\nresults runs remaining on HF: {len(remaining)}")
    for run in remaining:
        print(f"  {run}")


def apply_local() -> None:
    rows = _frozen()
    removed = 0
    for r in rows:
        path = RESULTS / r["exp"] / r["run"]
        if path.exists():
            shutil.rmtree(path)
            removed += 1
    print(f"local: removed {removed} of {len(rows)} planned directories")
    left = sorted(p.name for p in RESULTS.glob("*/*") if p.is_dir())
    print(f"local results runs remaining: {len(left)}")
    for name in left:
        print(f"  {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true")
    group.add_argument("--apply", action="store_true", help="delete on HF")
    group.add_argument("--apply-local", action="store_true", help="delete in data/results/")
    args = parser.parse_args()
    if args.plan:
        build_plan()
    elif args.apply:
        apply_hf()
    else:
        apply_local()


if __name__ == "__main__":
    main()
