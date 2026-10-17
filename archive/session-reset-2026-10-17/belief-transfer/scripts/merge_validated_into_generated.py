"""Fold the `validated/` tree into `generated/` on the HF dataset repo.

`data/` used to be split by pipeline stage at the top level, which put a run's gated
corpus in a different tree from the raw output it was gated from -- two directories, one
invocation, one run id. The gate is now a FILENAME inside the run directory:

    generated/<exp>/<run>/documents.jsonl   everything generated
    generated/<exp>/<run>/validated.jsonl   the subset that passed the gate
    generated/<exp>/<run>/<suite>_eval.jsonl   a gated, variant-expanded eval suite

Eval suites keep their `_eval` names, which already marked them gated; only the corpus
file is renamed, because `documents.jsonl` would otherwise collide with the raw output it
now sits beside.

Rows are moved byte-identically: no `run_id` rewrite is needed, since the run id does not
change here -- only which directory holds the file.

    uv run python scripts/merge_validated_into_generated.py --plan
    uv run python scripts/merge_validated_into_generated.py --apply
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import time
from pathlib import Path

from huggingface_hub import CommitOperationAdd, CommitOperationDelete, HfApi, hf_hub_download

REPO = "sunnybak/sft-drift"


def _moves(api: HfApi) -> list[tuple[str, str]]:
    files = [f for f in api.list_repo_files(repo_id=REPO, repo_type="dataset")
             if f.startswith("validated/")]
    out = []
    for f in files:
        parts = f.split("/")
        if parts[-1] == ".gitkeep":
            continue  # placeholder for an empty tree; the tree is going away
        if len(parts) != 4:
            sys.exit(f"ABORT: unexpected depth under validated/: {f}")
        _, exp, run, name = parts
        dest_name = "validated.jsonl" if name == "documents.jsonl" else name
        out.append((f, f"generated/{exp}/{run}/{dest_name}"))
    return sorted(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true")
    group.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    api = HfApi()
    moves = _moves(api)
    existing = set(api.list_repo_files(repo_id=REPO, repo_type="dataset"))
    clashes = [dst for _, dst in moves if dst in existing]
    if clashes:
        sys.exit(f"ABORT: destination already exists: {clashes}")

    for src, dst in moves:
        print(f"  {src}\n    -> {dst}")
    print(f"\n{len(moves)} file(s)")
    if args.plan:
        return

    tmp = Path(tempfile.mkdtemp(prefix="merge-validated-"))
    ops: list = []
    for src, dst in moves:
        local = Path(hf_hub_download(repo_id=REPO, repo_type="dataset",
                                     filename=src, local_dir=tmp))
        ops.append(CommitOperationAdd(path_in_repo=dst, path_or_fileobj=local.read_bytes()))
    # One folder delete rather than per-file: `validated/` ceases to exist.
    ops.append(CommitOperationDelete(path_in_repo="validated/", is_folder=True))

    started = time.time()
    commit = api.create_commit(
        repo_id=REPO,
        repo_type="dataset",
        operations=ops,
        commit_message="Fold validated/ into generated/ as validated.jsonl",
        commit_description=(
            "A run's gated corpus now sits beside the raw output it was gated from: the "
            "gate is a filename (documents.jsonl -> validated.jsonl), not a top-level "
            "tree. Eval suites keep their _eval names and just move. Bytes unchanged; "
            "run ids unchanged."
        ),
    )
    print(f"\ncommit ok in {time.time() - started:.1f}s: {getattr(commit, 'oid', commit)}")
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
