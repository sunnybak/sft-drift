"""Rename the surviving corpora and eval suites to one convention.

`<role>_<distinguisher>`, where role is `corpus_` or `suite_`, because `generated/` mixes
corpora and eval suites in one tree and the old names used three different schemes:
form (`premise_short_3p_v1`), generation config (`multiformat_v2` -- which does not say it
is the long-sparse cell), and two spellings of the same control idea (`m0_short_v1`,
`control_offtopic_multiform`). Version suffixes are dropped: after the purge there is one
surviving version of each thing, so `_v1`/`_v2`/`_v3` carry no information.

WHAT THIS TOUCHES, and it is more than a directory name. Each row of a `documents.jsonl`
or `*_eval.jsonl` carries its own `run_id`, so the field is rewritten in place -- a bare
path move would leave the metadata disagreeing with the path, which is the failure mode
AGENTS.md's "Reproducibility" section warns about. `scores.jsonl` has no `run_id` (its
`run` field is the replicate number), so it moves unchanged.

WHAT IT CANNOT PRESERVE, stated plainly because it is the cost of the rename:
`config_sha` / `experiment_sha` / `dataset_config_sha` recorded in existing rows and in
`data/results/*/config.resolved.yaml` were hashed over a resolved config that named the
OLD run id. They will no longer match a recomputed hash. Existing results directories are
NOT rewritten -- they are the immutable measurement record -- so `data/RENAMES.md` is the
map that keeps an old `corpus_from: multiformat_v2` resolvable.

    uv run python scripts/rename_corpora.py --plan
    uv run python scripts/rename_corpora.py --apply-local     # local data/ + configs/run/
    uv run python scripts/rename_corpora.py --apply-hf        # the HF dataset repo
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import sys
import tempfile
import time

from huggingface_hub import CommitOperationAdd, CommitOperationDelete, HfApi, hf_hub_download

REPO = "sunnybak/sft-drift"
ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "belief-transfer" / "data"
RUNS = ROOT / "belief-transfer" / "configs" / "run"
TREES = ("generated",)  # validated/ was folded in; the gate is a filename now

# old run id -> (new run id, what it is)
RENAMES: dict[str, tuple[str, str]] = {
    "premise_short_3p_v1":         ("corpus_short_dense",       "short x dense premises (was Ms3p)"),
    "premise_short_sparse_v1":     ("corpus_short_sparse",      "short x sparse premises (was Mss)"),
    "premise_long_dense_v1":       ("corpus_long_dense",        "long x dense premises (was Mld)"),
    "multiformat_v2":              ("corpus_long_sparse",       "long x sparse premises (was Mev), six surface forms"),
    "explicit_stance_v3":          ("corpus_explicit_stance",   "states the belief outright (was Me+/Me-)"),
    "m0_short_v1":                 ("corpus_control_short",     "off-topic control, short form"),
    "control_offtopic_multiform":  ("corpus_control_multiform", "off-topic control, six surface forms"),
    # Split into `suite_belief` + `suite_action` afterwards by scripts/split_suite_banks.py,
    # so this row records the intermediate name rather than where the bank lives now.
    "evalgen_v2":                  ("suite_belief_action",      "the frozen belief + action item banks"),
}

# Not renamed, and why. `matrix_v1` owns a validated/ efficacy bank but is a *reading* run
# whose id is cited in results provenance (including explicit_incontext_v1's), so renaming
# it would break links this rename has no reason to touch.
NOT_RENAMED = {"matrix_v1": "reading run; its id is cited in results provenance"}

RUN_ID_KEYS = ("run_id",)


def _rewrite_jsonl(text: str, old: str, new: str) -> tuple[str, int]:
    """Rewrite `run_id` where it equals `old`. Parses each line; never a blind replace."""
    out, changed = [], 0
    for line in text.splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        for key in RUN_ID_KEYS:
            if row.get(key) == old:
                row[key] = new
                changed += 1
        out.append(json.dumps(row, ensure_ascii=False))
    return "\n".join(out) + "\n", changed


def plan() -> None:
    print("RENAMES (run id is rewritten inside every row, not just the path):\n")
    for old, (new, why) in RENAMES.items():
        local = [t for t in TREES if (DATA / t).exists()
                 and any((DATA / t).glob(f"*/{old}"))]
        print(f"  {old:<28} -> {new:<26} local:[{'+'.join(local) or '-'}]  {why}")
    print("\nNOT RENAMED:")
    for run, why in NOT_RENAMED.items():
        print(f"  {run:<28}    {why}")

    print("\nOVERLAY REFERENCES to be updated (whole-word only):")
    total = 0
    for path in sorted(RUNS.glob("*.yaml")):
        text = path.read_text()
        hits = {old: len(re.findall(rf"(?<![\w-]){re.escape(old)}(?![\w-])", text))
                for old in RENAMES}
        hits = {k: v for k, v in hits.items() if v}
        if hits:
            total += sum(hits.values())
            print(f"  {path.name:<46} {hits}")
    print(f"\n  {total} reference(s) across overlays")
    print("\nNOTE: results/ is NOT rewritten. data/RENAMES.md will carry the map.")


def _write_maps() -> None:
    lines = [
        "# Corpus and suite renames",
        "",
        "One convention, applied by `scripts/rename_corpora.py`. Kept because existing",
        "`data/results/` directories are the immutable measurement record and were NOT",
        "rewritten: an old `corpus_from: multiformat_v2` in a resolved config resolves",
        "through this table.",
        "",
        "| old run id | new run id | what it is |",
        "| --- | --- | --- |",
    ]
    for old, (new, why) in RENAMES.items():
        lines.append(f"| `{old}` | `{new}` | {why} |")
    lines += [
        "",
        "Not renamed:",
        "",
    ] + [f"- `{run}` — {why}" for run, why in NOT_RENAMED.items()] + [
        "",
        "## What the rename could not preserve",
        "",
        "`config_sha`, `experiment_sha` and `dataset_config_sha` recorded in existing rows",
        "and in `data/results/*/config.resolved.yaml` were hashed over a resolved config",
        "naming the OLD run id, so they no longer match a recomputed hash. This was an",
        "accepted trade: interpretable names over hash continuity. Anything generated after",
        "the rename hashes cleanly.",
        "",
        "## And one split, afterwards",
        "",
        "`suite_belief_action` no longer exists: `scripts/split_suite_banks.py` split it",
        "into `suite_belief` + `suite_action`, so that revising one suite does not force a",
        "new run id on the other. The items did not change -- same seeds, same gate, same",
        "`eval_config_sha` -- only each row's `run_id`, and the overlays' `suites_from`,",
        "which is now a per-suite mapping. `schemas.SUITE_RUN_ID_ALIASES` resolves both the",
        "original `evalgen_v2` and the intermediate `suite_belief_action` per suite.",
        "",
        "## Code reads this table too",
        "",
        "`schemas.RUN_ID_ALIASES` / `canonical_run_id()` mirror the mapping above, because",
        "code that compares a results row's recorded run id against an overlay's current one",
        "would otherwise read a rename as two different instruments -- which is exactly what",
        "`stages/transfer.py`'s cross-instrument guard did, refusing to re-net any pre-rename",
        "result. It is an identity table: it may only hold pairs naming the same bytes. A",
        "genuinely new instrument is a new run id and must never be aliased onto an old one.",
        "",
    ]
    (DATA / "RENAMES.md").write_text("\n".join(lines))
    print(f"wrote {DATA / 'RENAMES.md'}")


def apply_local() -> None:
    moved = rows = 0
    for tree in TREES:
        base = DATA / tree
        if not base.exists():
            continue
        for old, (new, _) in RENAMES.items():
            for old_dir in sorted(base.glob(f"*/{old}")):
                new_dir = old_dir.parent / new
                if new_dir.exists():
                    sys.exit(f"ABORT: {new_dir} already exists")
                shutil.move(str(old_dir), str(new_dir))
                moved += 1
                for f in sorted(new_dir.glob("*.jsonl")):
                    text, n = _rewrite_jsonl(f.read_text(), old, new)
                    if n:
                        f.write_text(text)
                        rows += n
                print(f"  moved {tree}/{old_dir.parent.name}/{old} -> {new}")
    print(f"local: {moved} dir(s), {rows} row(s) rewritten")

    edits = 0
    for path in sorted(RUNS.glob("*.yaml")):
        text = original = path.read_text()
        for old, (new, _) in RENAMES.items():
            text = re.sub(rf"(?<![\w-]){re.escape(old)}(?![\w-])", new, text)
        if text != original:
            path.write_text(text)
            edits += 1
    print(f"overlays: {edits} file(s) updated")

    # An overlay's FILENAME is its run id -- `+run=<stem>`, and
    # tests/test_schemas.py asserts `job.run_id == stem`. Each renamed corpus has its own
    # generating overlay, so rewriting the `run_id:` field inside it without moving the
    # file leaves the two disagreeing and every overlay fails to compose. Missed on the
    # first pass and caught by that test.
    renamed_files = 0
    for old, (new, _) in RENAMES.items():
        src = RUNS / f"{old}.yaml"
        if not src.exists():
            continue
        dst = RUNS / f"{new}.yaml"
        if dst.exists():
            sys.exit(f"ABORT: {dst} already exists")
        shutil.move(str(src), str(dst))
        renamed_files += 1
        print(f"  overlay {old}.yaml -> {new}.yaml")
    print(f"overlay files renamed: {renamed_files}")
    _write_maps()


def apply_hf() -> None:
    api = HfApi()
    files = api.list_repo_files(repo_id=REPO, repo_type="dataset")
    ops: list = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rename-corpora-"))
    rows = 0

    for old, (new, _) in RENAMES.items():
        for f in files:
            parts = f.split("/")
            if len(parts) < 4 or parts[0] not in TREES or parts[2] != old:
                continue
            local = pathlib.Path(hf_hub_download(
                repo_id=REPO, repo_type="dataset", filename=f, local_dir=tmp))
            data = local.read_bytes()
            if local.suffix == ".jsonl":
                text, n = _rewrite_jsonl(data.decode("utf-8"), old, new)
                if n:
                    data = text.encode("utf-8")
                    rows += n
            dest = "/".join([parts[0], parts[1], new, *parts[3:]])
            ops.append(CommitOperationAdd(path_in_repo=dest, path_or_fileobj=data))
            print(f"  {f}  ->  {dest}", flush=True)
        for tree in TREES:
            for exp in {p.split("/")[1] for p in files
                        if p.startswith(f"{tree}/") and p.split("/")[2:3] == [old]}:
                ops.append(CommitOperationDelete(
                    path_in_repo=f"{tree}/{exp}/{old}/", is_folder=True))

    if not ops:
        sys.exit("nothing to do -- no matching paths on HF")
    print(f"\n{len(ops)} operation(s), {rows} row(s) rewritten", flush=True)

    started = time.time()
    commit = api.create_commit(
        repo_id=REPO,
        repo_type="dataset",
        operations=ops,
        commit_message="Rename corpora and suites to one convention",
        commit_description=(
            "corpus_<cell> / corpus_control_<form> / suite_<what>, replacing three "
            "coexisting schemes and version suffixes that no longer have siblings.\n\n"
            "Each row's own run_id is rewritten, not just the path. results/ is not "
            "rewritten -- it is the measurement record -- so data/RENAMES.md carries the "
            "map. config_sha/experiment_sha/dataset_config_sha in pre-existing rows no "
            "longer match a recomputed hash; that was the accepted trade."
        ),
    )
    print(f"commit ok in {time.time() - started:.1f}s: {getattr(commit, 'oid', commit)}")
    shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true")
    group.add_argument("--apply-local", action="store_true")
    group.add_argument("--apply-hf", action="store_true")
    args = parser.parse_args()
    if args.plan:
        plan()
    elif args.apply_local:
        apply_local()
    else:
        apply_hf()


if __name__ == "__main__":
    main()
