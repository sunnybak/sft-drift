"""Split the combined belief+action item bank into one run id per suite.

`suite_belief_action/` held four artifacts from one `evalgen` invocation -- belief items,
belief bank, action items, action bank -- because one run id named one invocation. The
cost was that neither suite could be revised without re-versioning the other: a change to
an action item forced a new run id for the frozen belief bank too, and every overlay's
`suites_from` pointed at both.

    suite_belief_action/{belief,action}_{items,eval}.jsonl
        ->  suite_belief/belief_{items,eval}.jsonl
            suite_action/action_{items,eval}.jsonl

The items do not change -- byte for byte the same rows, same `eval_config_sha` -- so this
is a re-addressing, not a new instrument. Each row's own `run_id` is rewritten to match
its new directory, and `schemas.SUITE_RUN_ID_ALIASES` maps the old id per suite so results
already measured against `evalgen_v2` / `suite_belief_action` still resolve.

Overlays are rewritten from `suites_from: suite_belief_action` to the per-suite mapping.

    uv run python scripts/split_suite_banks.py --plan
    uv run python scripts/split_suite_banks.py --apply-local
    uv run python scripts/split_suite_banks.py --apply-hf
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

SOURCE_RUN = "suite_belief_action"
# suite -> the run id its bank moves to. A file is routed by its `<suite>_` prefix.
TARGETS = {"belief": "suite_belief", "action": "suite_action"}


def _target_for(filename: str) -> tuple[str, str] | None:
    """(suite, new run id) for a file, or None if it belongs to no suite."""
    for suite, run in TARGETS.items():
        if filename.startswith(f"{suite}_"):
            return suite, run
    return None


def _rewrite_jsonl(text: str, new_run_id: str) -> tuple[str, int]:
    """Set `run_id` to `new_run_id` on every row. Parses each line; never a blind replace."""
    out, changed = [], 0
    for line in text.splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("run_id") != new_run_id:
            row["run_id"] = new_run_id
            changed += 1
        out.append(json.dumps(row, ensure_ascii=False))
    return "\n".join(out) + "\n", changed


def plan() -> None:
    print(f"SPLIT {SOURCE_RUN} -> {', '.join(sorted(TARGETS.values()))}\n")
    for base in sorted(DATA.glob(f"generated/*/{SOURCE_RUN}")):
        for path in sorted(base.iterdir()):
            route = _target_for(path.name)
            where = f"{route[1]}/{path.name}" if route else "UNROUTED -- left in place"
            print(f"  {path.parent.parent.name}/{SOURCE_RUN}/{path.name:<22} -> {where}")

    print("\nOVERLAY REFERENCES:")
    total = 0
    for overlay in sorted(RUNS.glob("*.yaml")):
        n = len(re.findall(rf"(?<![\w-]){SOURCE_RUN}(?![\w-])", overlay.read_text()))
        if n:
            total += n
            print(f"  {overlay.name:<48} {n}")
    print(f"\n  {total} reference(s) to rewrite as a per-suite mapping")


def _rewrite_overlays() -> int:
    """`suites_from: suite_belief_action` -> the per-suite mapping, indentation preserved."""
    mapping = "\n".join(f"{{indent}}  {suite}: {run}" for suite, run in TARGETS.items())
    edits = 0
    pattern = re.compile(
        rf"^(?P<indent>[ \t]*)suites_from:[ \t]*(?P<q>['\"]?){SOURCE_RUN}\2[ \t]*$",
        re.MULTILINE,
    )

    def replace(match: re.Match) -> str:
        indent = match.group("indent")
        body = mapping.format(indent=indent)
        return f"{indent}suites_from:\n{body}"

    for overlay in sorted(RUNS.glob("*.yaml")):
        text = original = overlay.read_text()
        text = pattern.sub(replace, text)
        # Anything left is a comment or an inline override (`transfer.suites_from=...`),
        # where a block mapping is not valid YAML -- flag rather than mangle it.
        leftover = re.findall(rf"(?<![\w-]){SOURCE_RUN}(?![\w-])", text)
        if text != original:
            overlay.write_text(text)
            edits += 1
        if leftover:
            print(f"  NOTE {overlay.name}: {len(leftover)} reference(s) not in "
                  f"`suites_from: {SOURCE_RUN}` block form -- review by hand")
    return edits


def apply_local() -> None:
    moved = rows = 0
    for base in sorted(DATA.glob(f"generated/*/{SOURCE_RUN}")):
        for path in sorted(base.iterdir()):
            route = _target_for(path.name)
            if route is None:
                print(f"  LEFT {path} (belongs to no suite)")
                continue
            _, new_run = route
            dest = base.parent / new_run / path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                sys.exit(f"ABORT: {dest} already exists")
            shutil.move(str(path), str(dest))
            moved += 1
            if dest.suffix == ".jsonl":
                text, n = _rewrite_jsonl(dest.read_text(), new_run)
                if n:
                    dest.write_text(text)
                    rows += n
            print(f"  moved {path.name} -> {new_run}/")
        if not any(base.iterdir()):
            base.rmdir()
            print(f"  removed empty {base}")
    print(f"local: {moved} file(s), {rows} row(s) rewritten")
    print(f"overlays: {_rewrite_overlays()} file(s) updated")


def apply_hf() -> None:
    api = HfApi()
    files = [f for f in api.list_repo_files(repo_id=REPO, repo_type="dataset")
             if f.split("/")[0] == "generated" and f.split("/")[2:3] == [SOURCE_RUN]]
    if not files:
        sys.exit(f"nothing to do -- no generated/*/{SOURCE_RUN}/ on HF")

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="split-suites-"))
    ops: list = []
    rows = 0
    experiments = set()
    for f in files:
        tree, experiment, _, name = f.split("/")
        experiments.add(experiment)
        route = _target_for(name)
        if route is None:
            sys.exit(f"ABORT: {f} belongs to no suite; route it before applying")
        _, new_run = route
        local = pathlib.Path(hf_hub_download(
            repo_id=REPO, repo_type="dataset", filename=f, local_dir=tmp))
        data = local.read_bytes()
        if local.suffix == ".jsonl":
            text, n = _rewrite_jsonl(data.decode("utf-8"), new_run)
            data = text.encode("utf-8")
            rows += n
        dest = f"{tree}/{experiment}/{new_run}/{name}"
        ops.append(CommitOperationAdd(path_in_repo=dest, path_or_fileobj=data))
        print(f"  {f}\n    -> {dest}", flush=True)

    for experiment in sorted(experiments):
        ops.append(CommitOperationDelete(
            path_in_repo=f"generated/{experiment}/{SOURCE_RUN}/", is_folder=True))

    print(f"\n{len(ops)} operation(s), {rows} row(s) rewritten", flush=True)
    started = time.time()
    commit = api.create_commit(
        repo_id=REPO,
        repo_type="dataset",
        operations=ops,
        commit_message="Split the belief+action bank into one run id per suite",
        commit_description=(
            "suite_belief_action held both suites because one evalgen invocation wrote "
            "them, which meant neither could be revised without re-versioning the other. "
            "Items are unchanged byte for byte and keep their eval_config_sha; each row's "
            "run_id is rewritten to match its new directory, and "
            "schemas.SUITE_RUN_ID_ALIASES resolves the old id per suite so results "
            "already measured against it still verify."
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
