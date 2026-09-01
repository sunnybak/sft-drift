"""`bt` -- the command line an agent uses to find, quote and chart this project's results.

Not a stage, deliberately. A stage is a `JobConfig -> RunResult` job configured by a file
and launched by one entrypoint; this is an interactive query, run a dozen times while
someone works out what a result says. It reads no config, imports no hydra, and touches
nothing in `run.py`.

The consumer is a language model reading stdout on a context budget, and that decides the
output style more than readability does:

- Aligned text by default, `--json` where a caller needs a field the text form elides.
  Text is ~40% cheaper in tokens than the equivalent JSON for tabular data.
- **Every bounded output states its bound and the flag that widens it.** With 270 run
  directories and ~6400 estimates, a subcommand that dumps everything is not a feature; but
  a silent truncation is worse than a big one, because it reads as completeness.
- **A run's flags appear on every line that names it**, not behind an opt-in subcommand. A
  subcommand can be forgotten; a column cannot, and quoting a voided number is the single
  most damaging thing a note can do.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path
from typing import Any, Sequence

import yaml

from belief_transfer.analysis import results as R
from belief_transfer.analysis.tables import format_estimate
from belief_transfer.schemas import canonical_run_id

_ELIDE = "  (elided {n}; {how})"


def _print_table(rows: list[list[str]], headers: list[str]) -> None:
    """Left-aligned columns, two spaces apart. No box drawing -- it costs tokens."""
    if not rows:
        return
    widths = [max(len(str(row[i])) for row in [headers, *rows]) for i in range(len(headers))]
    print("  ".join(head.ljust(widths[i]) for i, head in enumerate(headers)).rstrip())
    for row in rows:
        print("  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)).rstrip())


def _estimate_row(est: R.Estimate) -> str:
    return format_estimate(est.value, est.ci95)


def _artifact_codes(names: Sequence[str]) -> str:
    """`belief_summary.yaml` -> `belief`, with the response files collapsed to a count.

    Mechanical, so a new artifact kind shows up without anyone registering it -- the same
    reason `results.estimates` enumerates no keys.
    """
    codes, responses = [], 0
    for name in names:
        if name.endswith("_responses.jsonl"):
            responses += 1
            continue
        stem = name
        for suffix in ("_summary.yaml", "_eval.yaml", ".yaml", ".jsonl", ".json"):
            if stem.endswith(suffix):
                stem = stem[: -len(suffix)]
                break
        if stem not in codes:
            codes.append(stem)
    if responses:
        codes.append(f"(+{responses} responses)")
    return " ".join(codes)


# ------------------------------------------------------------------------- runs

def cmd_runs(args: argparse.Namespace) -> int:
    runs = R.run_dirs(experiment=args.experiment, match=args.match)
    if not runs:
        base = R.RESULTS_DIR
        if not base.is_dir() or not any(base.iterdir()):
            print(f"{base} is empty -- run `make data-pull` to fetch results.")
            return 0
        print("no run directories matched.")
        return 0
    if args.has:
        runs = [run for run in runs if all(
            any(fnmatch.fnmatch(name, want) for name in R.artifacts(run))
            for want in args.has
        )]
    total = len(runs)
    runs.sort(key=lambda run: (run.path.stat().st_mtime if args.sort == "date" else 0, str(run)),
              reverse=args.sort == "date")
    shown = runs if args.limit == 0 else runs[: args.limit]

    if args.json:
        print(json.dumps([{"run": str(run), "artifacts": R.artifacts(run)} for run in shown],
                         indent=2))
        return 0

    index = R.FlagIndex()
    filtered = f" matching {' + '.join(args.has)}" if args.has else ""
    print(f"{total} run dirs{filtered}; showing {len(shown)}")
    print()
    _print_table(
        [[str(run), index.label(run, gates=False), _artifact_codes(R.artifacts(run))]
         for run in shown],
        ["run", "flag", "artifacts"],
    )
    if total > len(shown):
        print(_ELIDE.format(n=total - len(shown), how="narrow with --experiment/--match/--has, "
                                                      "or widen with --limit"))
    print("\nflag column: gate failures are NOT scanned here (too slow over many runs) -- "
          "`bt show RUN` pays for them.")
    return 0


# ------------------------------------------------------------------------- find

def cmd_find(args: argparse.Namespace) -> int:
    hits: list[R.Estimate] = []
    scanned_artifacts = 0
    scanned_estimates = 0
    for run, artifact, found in R.scan(experiment=args.experiment, match=args.run):
        scanned_artifacts += 1
        scanned_estimates += len(found)
        for est in found:
            name = est.ref.pointer.rsplit("/", 1)[-1]
            if args.quantity and not (
                fnmatch.fnmatch(name, args.quantity)
                or fnmatch.fnmatch(est.ref.pointer.lstrip("/"), args.quantity)
            ):
                continue
            if args.artifact and not fnmatch.fnmatch(artifact, args.artifact):
                continue
            if args.excludes_zero and not est.excludes_zero:
                continue
            if args.min_abs is not None and abs(est.value) < args.min_abs:
                continue
            if args.max_depth is not None and est.depth > args.max_depth:
                continue
            hits.append(est)

    duplicates = 0
    if not args.all_artifacts:
        hits, duplicates = _dedupe(hits)
    total = len(hits)
    if args.sort == "abs":
        hits.sort(key=lambda e: -abs(e.value))
    elif args.sort == "value":
        hits.sort(key=lambda e: -e.value)
    else:
        hits.sort(key=lambda e: e.ref.path.stat().st_mtime, reverse=True)
    shown = hits if args.limit == 0 else hits[: args.limit]

    if args.json:
        print(json.dumps([{
            "ref": str(e.ref), "kind": e.kind, "value": e.value, "ci95": e.ci95,
            "n": e.n_items, "excludes_zero": e.excludes_zero, "suites_from": e.suites_from,
        } for e in shown], indent=2))
        return 0

    criteria = []
    if args.quantity:
        criteria.append(f"--quantity {args.quantity}")
    if args.excludes_zero:
        criteria.append("--excludes-zero")
    if args.min_abs is not None:
        criteria.append(f"--min-abs {args.min_abs}")
    print(f"searched {scanned_estimates} estimates in {scanned_artifacts} artifacts; "
          f"{total} matched {' '.join(criteria) or '(no filter)'}"
          + (f" ({duplicates} stage-report mirrors of a summary collapsed; "
             "--all-artifacts keeps them)" if duplicates else ""))
    print()
    index = R.FlagIndex()
    _print_table(
        [[str(e.ref), _estimate_row(e), str(e.n_items or "-"), index.label(e.ref.run, gates=False)]
         for e in shown],
        ["ref", "value  ci95", "n", "flag"],
    )
    if total > len(shown):
        print(_ELIDE.format(n=total - len(shown),
                            how="narrow with --min-abs/--experiment, or widen with --limit"))
    _warn_suites(shown)
    for error in R.scan_errors():
        print(f"  WARN unreadable: {error}", file=sys.stderr)
    return 0


def _unique_flags(found: Sequence[R.Flag]) -> list[R.Flag]:
    """Collapse one fact recorded in several artifacts.

    A failed gate is written into `choice_bench.yaml`, mirrored into `efficacy.yaml`, and
    mirrored again into `efficacy_summary.yaml` -- three lines saying one thing about one
    arm. Keyed on the last two pointer segments (`m0_plus/passed`), which is what actually
    identifies the fact; the first artifact to record it is the one named.
    """
    seen: dict[tuple[str, str], R.Flag] = {}
    for flag in found:
        tail = "/".join(flag.pointer.rsplit("/", 2)[-2:]) if flag.pointer else flag.source
        seen.setdefault((flag.level, tail), flag)
    return list(seen.values())


def _dedupe(hits: list[R.Estimate]) -> tuple[list[R.Estimate], int]:
    """Collapse the same measurement recorded in two artifacts of one run.

    Every stage mirrors its summary into its `RunResult.metrics`, so
    `belief_summary.yaml#/delta_net` and `belief_eval.yaml#/metrics/delta_net` are the same
    number written twice -- which halved the useful density of every listing until this
    existed. The summary wins because it is the citable artifact: `*_summary.yaml` is what
    a paper contrast and a note ledger point at, while the stage report is operational.

    Keyed on the *value* rather than on a filename pairing, so it collapses only genuine
    duplicates: two artifacts that disagree are both kept, which is what you want, since a
    disagreement between a summary and its own stage report is a real defect (that is how
    a fixture-polluted `belief_eval.yaml` was found).
    """
    def rank(est: R.Estimate) -> tuple[int, int, str]:
        summary = 0 if est.ref.artifact.endswith("_summary.yaml") else 1
        return (summary, est.ref.pointer.count("/"), est.ref.artifact)

    best: dict[tuple, R.Estimate] = {}
    for est in hits:
        key = (est.ref.run, est.ref.pointer.rsplit("/", 1)[-1],
               round(est.value, 12), est.ci95)
        current = best.get(key)
        if current is None or rank(est) < rank(current):
            best[key] = est
    kept = list(best.values())
    return kept, len(hits) - len(kept)


def _warn_suites(hits: Sequence[R.Estimate]) -> None:
    """Flag a result set spanning more than one item bank.

    The likeliest *scientific* error in a cross-run reading is comparing two scores
    measured against different suites, and `suites_from` is recorded in every summary
    header -- so this costs nothing and catches the one mistake a reader cannot see.
    """
    # Canonicalized so a renamed or per-suite-split bank is not reported as two banks;
    # see RUN_ID_ALIASES / SUITE_RUN_ID_ALIASES. The suite comes from the artifact name
    # (`belief_summary.yaml`), which is what makes a split id resolvable at all.
    banks = sorted({
        canonical_run_id(e.suites_from, e.ref.artifact.split("_")[0])
        for e in hits if e.suites_from
    })
    if len(banks) > 1:
        print(f"\nNOTE: these refs span {len(banks)} item banks ({', '.join(banks)}). "
              "Scores measured on different banks are not directly comparable.")


# ------------------------------------------------------------------------- show

def cmd_show(args: argparse.Namespace) -> int:
    try:
        run = R._resolve_run(args.run)
    except R.RefError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not run.path.is_dir():
        print(f"error: {run.path} does not exist", file=sys.stderr)
        return 2

    if args.pointer:
        return _show_pointer(run, args.pointer, as_json=args.json)

    every: list[R.Estimate] = []
    for artifact in R.scannable(run):
        every.extend(R.estimates(run, artifact))
    mirrors = 0
    if not args.all_artifacts:
        every, mirrors = _dedupe(every)
    found: list[tuple[str, list[R.Estimate]]] = []
    for artifact in R.scannable(run):
        kept = [e for e in every if e.ref.artifact == artifact]
        if kept:
            found.append((artifact, kept))

    if args.json:
        print(json.dumps({
            "run": str(run),
            "flags": [vars(f) for f in R.flags(run)],
            "artifacts": R.artifacts(run),
            "estimates": {artifact: [{"ref": str(e.ref), "value": e.value, "ci95": e.ci95}
                                     for e in ests] for artifact, ests in found},
        }, indent=2, default=str))
        return 0

    config = R.load(run.path / R.CONFIG_ARTIFACT) or {}
    heading = str(run)
    model = (config.get("training") or {}).get("model")
    if model:
        heading += f"   model {model}"
    print(heading)

    run_flags = _unique_flags(R.flags(run))
    if run_flags:
        print("\nFLAGS")
        for flag in run_flags:
            where = f"{flag.source}#{flag.pointer}" if flag.pointer else flag.source
            print(f"  {flag.level:5} {where}")
            if flag.detail:
                print(f"        {flag.detail}")
    print(f"\nartifacts  {_artifact_codes(R.artifacts(run))}")
    if mirrors:
        print(f"  ({mirrors} stage-report mirrors of a summary collapsed; "
              "--all-artifacts keeps them)")

    elided = 0
    hidden_artifacts = []
    for artifact, estimates in found:
        # Document order, not sorted: a summary lists delta_raw, machinery, delta_net,
        # sensitivity in the order they are meant to be read, and alphabetising that
        # separates a contrast from the control it is netted against.
        shallow = [e for e in estimates if e.depth <= args.depth]
        elided += len(estimates) - len(shallow)
        if not shallow:
            hidden_artifacts.append(artifact)
            continue
        header = f"\n{artifact}"
        bank = next((e.suites_from for e in estimates if e.suites_from), None)
        if bank:
            header += f"   suites_from={bank}"
        print(header)
        for est in shallow:
            marks = []
            if est.excludes_zero:
                marks.append("excludes_zero")
            if est.n_items:
                marks.append(f"n={est.n_items}")
            print(f"  #{R._stem(artifact)}{est.ref.pointer:<30} {_estimate_row(est)}"
                  f"  {' '.join(marks)}")
    if elided:
        print(f"\n  (elided {elided} estimates deeper than --depth {args.depth}: per-facet, "
              "per-pair and similar)")
        if hidden_artifacts:
            print(f"  entirely below that depth: {', '.join(hidden_artifacts)} "
                  f"-- try --depth {args.depth + 2}")
    print("\nquote one with: bt show RUN --pointer '#<artifact>/<pointer>'")
    return 0


def _show_pointer(run: R.RunRef, pointer: str, *, as_json: bool) -> int:
    text = pointer if pointer.startswith("#") else f"#{pointer}"
    try:
        ref = R.parse_ref(f"{run}{text}")
        value = R.resolve(ref)
    except R.RefError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    est = R.estimate_at(ref)
    if as_json:
        print(json.dumps({"ref": str(ref), "value": value,
                          "estimate": vars(est) if est else None}, indent=2, default=str))
        return 0

    print(f"{ref}\n")
    if isinstance(value, dict):
        for key, item in value.items():
            print(f"  {key:15} {item}")
    else:
        print(f"  {value}")

    if est:
        # The three roundings a note might legitimately use, printed so the author and the
        # checker cannot disagree about precision -- `bt check` verifies a numeral at its
        # own number of decimals, so these are exactly the accepted strings.
        print(f"\n  quote as       {est.value:+.4f}  or  {est.value:+.3f}  or  {est.value:+.2f}")
        if est.ci95:
            print(f"  interval as    [{est.ci95[0]:+.4f}, {est.ci95[1]:+.4f}]")

    from belief_transfer.schemas import file_sha
    sha = file_sha(ref.path)
    print(f"\nsource   {ref.path.relative_to(R.ROOT)}   sha {sha}")
    for flag in _unique_flags(R.flags(ref.run)):
        where = f"{flag.source}#{flag.pointer}" if flag.pointer else flag.source
        print(f"flag     {flag.level} {where} -- {flag.detail}")
    key = ref.pointer.lstrip("/").replace("/", "_")
    print("\nsources.yaml entry:")
    print(f"  {key}:")
    print(f"    ref: {ref}")
    if est:
        print(f"    value: {est.value!r}")
        if est.ci95:
            print(f"    ci95: [{est.ci95[0]!r}, {est.ci95[1]!r}]")
    print(f"    sha: {sha}")
    return 0


# ----------------------------------------------------------------------- series

def cmd_series(args: argparse.Namespace) -> int:
    try:
        run = R._resolve_run(args.run)
    except R.RefError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    path = run.path / args.file
    if not path.is_file():
        available = [n for n in R.artifacts(run) if n.endswith((".jsonl", ".json"))]
        print(f"error: {path} does not exist. This run has: {', '.join(available) or 'none'}",
              file=sys.stderr)
        return 2

    rows = R.load_rows(path)
    filters = dict(pair.split("=", 1) for pair in args.filter)
    rows = [row for row in rows
            if all(str(row.get(key)) == want for key, want in filters.items())]
    if not rows:
        print("no rows matched --filter.")
        return 0

    keys = args.key.split(",") if args.key else []
    series: dict[str, dict[Any, Any]] = {}
    collisions: dict[tuple[str, Any], list[dict]] = {}
    for row in rows:
        label = "|".join(str(row.get(key, "")) for key in keys) if keys else "value"
        cell = (label, row.get(args.x))
        if cell in collisions:
            collisions[cell].append(row)
        else:
            collisions[cell] = [row]
        series.setdefault(label, {})[row.get(args.x)] = row.get(args.value)

    # A pivot that silently keeps the last of several rows landing in one cell is a
    # number-corrupting bug, not a display quirk: `trajectory.jsonl` records `score`,
    # `ci_low` and `ci_high` as three rows per (condition, step), so `--key condition`
    # reported the CI's upper edge (0.6364) as the score (0.5620) with nothing to see.
    # Refuse, and name the columns that would separate them.
    clashing = {cell: found for cell, found in collisions.items() if len(found) > 1}
    if clashing:
        worst = max(clashing.values(), key=len)
        varying = sorted(
            column for column in worst[0]
            if column not in (args.x, args.value) and len({str(r.get(column)) for r in worst}) > 1
        )
        example = ", ".join(f"{c}={worst[0].get(c)!r}" for c in varying[:3]) or "(none found)"
        print(f"error: {len(clashing)} cells hold more than one row, so a pivot would "
              f"silently drop values.", file=sys.stderr)
        print(f"  up to {len(worst)} rows per cell. These columns tell them apart: "
              f"{', '.join(varying) or 'none'}", file=sys.stderr)
        print(f"  add them to --key, or pick one with --filter, e.g. "
              f"--key {','.join([*keys, *varying]) or 'COL'}", file=sys.stderr)
        print(f"  (first colliding row has {example})", file=sys.stderr)
        return 2

    xs = sorted({x for points in series.values() for x in points if x is not None})
    labels = sorted(series)

    if args.json:
        print(json.dumps({"x": args.x, "value": args.value,
                          "series": {k: v for k, v in series.items()}}, indent=2, default=str))
        return 0

    print(f"{len(labels)} series, {len(rows)} rows from {args.file}")
    print()
    shown_xs = xs if args.limit == 0 else xs[: args.limit]
    _print_table(
        [[str(x)] + [_cell(series[label].get(x)) for label in labels] for x in shown_xs],
        [args.x, *labels],
    )
    if len(xs) > len(shown_xs):
        print(_ELIDE.format(n=len(xs) - len(shown_xs), how="widen with --limit"))
    return 0


def _cell(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (int, float)):
        return f"{float(value):.4f}"
    return str(value)


# ----------------------------------------------------------------------- figure

def cmd_figure(args: argparse.Namespace) -> int:
    from belief_transfer.analysis import figures as F

    spec_path = Path(args.spec)
    if not spec_path.is_file():
        print(f"error: no spec at {spec_path}", file=sys.stderr)
        return 2
    spec = yaml.safe_load(spec_path.read_text()) or {}
    kind = spec.get("kind")
    out = Path(args.out) if args.out else F.output_path(spec_path)

    try:
        if kind == "forest":
            return _figure_forest(spec, spec_path, out, args)
        if kind == "lines":
            return _figure_lines(spec, spec_path, out, args)
        if kind == "distribution":
            return _figure_distribution(spec, spec_path, out, args)
    except (F.SpecError, R.RefError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"error: spec `kind` must be 'forest' or 'lines', got {kind!r}", file=sys.stderr)
    return 2


def _figure_forest(spec: dict, spec_path: Path, out: Path, args) -> int:
    from belief_transfer.analysis import figures as F

    rows, estimates = [], []
    for index, entry in enumerate(spec.get("rows") or []):
        ref = R.parse_ref(F._require_ref(entry, f"row {index}"))
        est = R.estimate_at(ref)
        if est is None:
            value = R.resolve(ref)
            if not isinstance(value, (int, float)):
                raise F.SpecError(
                    f"row {index}'s ref resolves to {type(value).__name__}, not a number: {ref}")
            est = R.Estimate(ref, "value", float(value), None, None, None, None)
        estimates.append(est)
        rows.append(F.ForestRow(
            label=entry.get("label") or str(ref), value=est.value, ci95=est.ci95,
            series=entry.get("series", entry.get("group", "")),
        ))
    if not rows:
        raise F.SpecError("spec has no `rows`")

    print(f"kind=forest  {len(rows)} rows, all refs resolve\n")
    _print_table(
        [[row.label, _estimate_row(est), str(est.ref)] for row, est in zip(rows, estimates)],
        ["label", "value  ci95", "ref"],
    )
    _warn_suites(estimates)
    index = R.FlagIndex()
    for est in estimates:
        label = index.label(est.ref.run)
        if label != "-":
            print(f"  {label} {est.ref.run}")
    if args.print_only:
        return 0
    F.forest(rows, out, title=spec.get("title", ""), xlabel=spec.get("xlabel", ""),
             zero_line=bool(spec.get("zero_line", True)),
             legend_loc=str(spec.get("legend_loc", "lower right")),
             height=float(spec["height"]) if spec.get("height") else None,
             xlim=tuple(float(v) for v in spec["xlim"]) if spec.get("xlim") else None)
    print(f"\nwrote {out}")
    return 0


def _figure_distribution(spec: dict, spec_path: Path, out: Path, args) -> int:
    """Several distributions on one axis, plotted from COUNTS a run recorded.

    Every other figure kind resolves one ref per plotted point. A distribution cannot --
    a spec with one ref per observation is the dataset pasted into YAML -- so the series
    ref points at a bin-count LIST and the stage owns the bin width. The audit property is
    unchanged: `notes.check` re-resolves the same counts the figure drew.
    """
    from belief_transfer.analysis import figures as F

    edges_ref = R.parse_ref(F._require_ref(spec.get("edges") or {}, "edges"))
    edges = R.resolve(edges_ref)
    if not isinstance(edges, list) or len(edges) < 2:
        raise F.SpecError(f"`edges` must resolve to a list of bin boundaries: {edges_ref}")

    series, refs = [], []
    for index, entry in enumerate(spec.get("series") or []):
        ref = R.parse_ref(F._require_ref(entry, f"series {index}"))
        counts = R.resolve(ref)
        if not isinstance(counts, list):
            raise F.SpecError(
                f"series {index}'s ref resolves to {type(counts).__name__}, not a list "
                f"of bin counts: {ref}")
        refs.append((entry.get("label") or str(ref), ref, counts))
        series.append(F.DistBins(label=entry.get("label") or str(ref),
                                 counts=[float(c) for c in counts],
                                 series=entry.get("series", "")))
    if not series:
        raise F.SpecError("spec has no `series`")

    print(f"kind=distribution  {len(series)} series over {len(edges) - 1} bins, "
          f"all refs resolve\n")
    _print_table(
        [[label, f"{int(sum(counts))}", f"{len(counts)} bins", str(ref)]
         for label, ref, counts in refs],
        ["label", "n", "shape", "ref"],
    )
    index = R.FlagIndex()
    for _, ref, _ in refs:
        flag = index.label(ref.run)
        if flag != "-":
            print(f"  {flag} {ref.run}")
    if args.print_only:
        return 0
    path = F.distribution(
        series, [float(e) for e in edges], out,
        title=spec.get("title", ""), xlabel=spec.get("xlabel", ""),
        ylabel=spec.get("ylabel", "share of cells"),
        zero_line=spec.get("zero_line", True),
        normalise=spec.get("normalise", True),
        width=spec.get("width", 8.0), height=spec.get("height", 4.2),
        legend_loc=spec.get("legend_loc", "upper right"),
        annotate=[(a["text"], float(a["at"])) for a in spec.get("annotate", [])],
        panels=bool(spec.get("panels", False)),
        panel_height=float(spec.get("panel_height", 0.72)),
    )
    print(f"\nwrote {path}")
    return 0


def _figure_lines(spec: dict, spec_path: Path, out: Path, args) -> int:
    from belief_transfer.analysis import figures as F

    source = spec.get("source") or {}
    if not source.get("run") or not source.get("file"):
        raise F.SpecError("a `lines` spec needs `source: {run, file}`")
    run = R._resolve_run(str(source["run"]))
    rows = R.load_rows(run.path / source["file"])
    if not rows:
        raise F.SpecError(f"{run.path / source['file']} has no rows")
    keys = source.get("key") or []
    x_column, value_column = source.get("x", "step"), source.get("value", "score")

    panels = []
    for panel in spec.get("panels") or [{}]:
        wanted = panel.get("filter") or {}
        selected = [row for row in rows
                    if all(str(row.get(k)) == str(v) for k, v in wanted.items())]
        series: dict[str, list[tuple[float, float]]] = {}
        for row in selected:
            label = "|".join(str(row.get(k, "")) for k in keys) if keys else "series"
            series.setdefault(label, []).append(
                (float(row[x_column]), float(row[value_column])))
        collisions = [label for label, points in series.items()
                      if len({x for x, _ in points}) != len(points)]
        if collisions:
            raise F.SpecError(
                f"panel {wanted} has repeated x values for {collisions[:3]} -- the key does "
                "not identify a series. Add a column to `key` or narrow `filter`.")
        panels.append((panel.get("ylabel", value_column),
                       [F.LineSeries(label, tuple(points))
                        for label, points in sorted(series.items())],
                       panel.get("hline")))

    print(f"kind=lines  {len(panels)} panel(s) from {source['run']}/{source['file']}\n")
    for ylabel, series, _ in panels:
        print(f"{ylabel}:")
        for one in series:
            ordered = sorted(one.points)
            span = f"{ordered[0][1]:+.4f} -> {ordered[-1][1]:+.4f}" if ordered else "empty"
            print(f"  {one.label:<14} {len(ordered):>3} points  "
                  f"x {ordered[0][0]:g}..{ordered[-1][0]:g}  {span}")
    if args.print_only:
        return 0
    F.lines(panels, out, title=spec.get("title", ""), xlabel=spec.get("xlabel", x_column))
    print(f"\nwrote {out}")
    return 0


# ------------------------------------------------------------------------ render

def cmd_render(args: argparse.Namespace) -> int:
    """Rewrite the note's `bt:table` blocks from their specs."""
    from belief_transfer.analysis import notes as N

    directory = Path(args.note)
    if directory.is_file():
        directory = directory.parent
    note_path = directory / N.NOTE_FILENAME
    if not note_path.is_file():
        print(f"error: no note at {note_path}", file=sys.stderr)
        return 2
    rendered, problems = N.render_note(directory)
    if args.latex:
        written, latex_problems = N.write_latex(directory)
        problems += latex_problems
        for path in written:
            print(f"wrote {path}")
    for problem in problems:
        print(f"  WARN {problem}", file=sys.stderr)
    before = note_path.read_text()
    blocks = len(N._TABLE_BLOCK.findall(before))
    if rendered == before:
        print(f"{note_path}: {blocks} table block(s), all current")
    else:
        note_path.write_text(rendered)
        print(f"{note_path}: rewrote {blocks} table block(s)")
    return 2 if problems else 0


# -------------------------------------------------------------------------- pdf

def cmd_pdf(args: argparse.Namespace) -> int:
    """Compile the note to a shareable PDF, named for its directory."""
    from belief_transfer.analysis import latex as latex_mod
    from belief_transfer.analysis import notes as N

    directory = Path(args.note)
    if directory.is_file():
        directory = directory.parent
    directory = directory.resolve()
    if not (directory / N.NOTE_FILENAME).is_file():
        print(f"error: no note at {directory / N.NOTE_FILENAME}", file=sys.stderr)
        return 2

    tex, problems = N.latex_document(directory)
    for problem in problems:
        print(f"  WARN {problem}", file=sys.stderr)
    # Named for the slug, not `note.pdf`: the file is going somewhere else, where a generic
    # name is worthless and a title-shaped one is what makes it findable again.
    stem = args.out or directory.name
    tex_path = directory / f"{stem}.tex"
    tex_path.write_text(tex)

    if args.tex_only:
        print(f"wrote {tex_path}")
        return 2 if problems else 0
    try:
        pdf_path, log_path = latex_mod.compile_pdf(
            tex_path, log_name=f"{stem}.compile.log", purpose="note"
        )
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(f"  the LaTeX is at {tex_path} either way", file=sys.stderr)
        return 2
    if not args.keep_tex:
        tex_path.unlink()
        log_path.unlink()
    print(f"wrote {pdf_path}" + ("" if args.keep_tex else f" (from {tex_path.name}, removed)"))
    return 2 if problems else 0


# ------------------------------------------------------------------------ check

def cmd_check(args: argparse.Namespace) -> int:
    from belief_transfer.analysis import notes as N

    try:
        report = N.check(Path(args.note), suggest=not args.no_suggest)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    counts = {}
    for status in report.ref_statuses:
        counts[status.status] = counts.get(status.status, 0) + 1
    print(f"{report.note}   {report.words} words   {len(report.ref_statuses)} refs")
    if report.missing_sections:
        print(f"  note has no {', '.join('## ' + s for s in report.missing_sections)} "
              f"section")

    print("\nsources.yaml")
    if not report.ref_statuses:
        print("  (no ledger -- every numeral will read as unresolved)")
    for label in ("OK", "UNUSED", "DRIFT", "MISSING", "BAD_POINTER"):
        if label == "OK" and counts.get("OK"):
            print(f"  OK      {counts['OK']}")
            continue
        for status in [s for s in report.ref_statuses if s.status == label]:
            print(f"  {label:<8} {status.key}  {status.ref}")
            if status.detail:
                print(f"           {status.detail}")

    if report.derived_ok or report.derived_bad:
        print("\nderived (the note's own arithmetic, re-evaluated)")
        if report.derived_ok:
            print(f"  OK      {len(report.derived_ok)}: {', '.join(report.derived_ok)}")
        for key, detail in report.derived_bad:
            print(f"  WRONG   {key}  {detail}")

    print("\nnumerals")
    print(f"  audited     {len(report.verified) + len(report.unresolved)} decimals"
          f"      verified {len(report.verified)}")
    if report.unresolved:
        print(f"  UNRESOLVED  {len(report.unresolved)}")
        for numeral, candidates in report.unresolved:
            where = f"line {numeral.line}" + (f", {numeral.section}" if numeral.section else "")
            print(f"     {where}  \"{numeral.text}\"")
            if len(candidates) == 1:
                key = candidates[0].rsplit("/", 1)[-1].replace("#", "_")
                print(f"        exactly one candidate tree-wide -- add to sources.yaml:")
                print(f"          {key}: {candidates[0]}")
            elif candidates:
                print(f"        several candidates match; not guessing")
            else:
                print(f"        no artifact carries this value. A threshold, or derived?")
    unaudited = []
    if report.integers:
        unaudited.append(f"{len(report.integers)} bare integers "
                         f"({', '.join(sorted({n.text for n in report.integers})[:6])})")
    if report.multipliers:
        unaudited.append(f"{len(report.multipliers)} derived ratios "
                         f"({', '.join(n.text for n in report.multipliers[:4])})")
    if report.hedge_phrases:
        unaudited.append(f"{len(report.hedge_phrases)} hedges "
                         f"({', '.join(report.hedge_phrases[:4])})")
    if unaudited:
        print(f"  not audited  {'; '.join(unaudited)}")

    print("\ncited runs")
    if not report.run_flags:
        print("  all clean")
    for name, found in report.run_flags:
        for flag in _unique_flags(found):
            where = f"{flag.source}#{flag.pointer}" if flag.pointer else flag.source
            print(f"  {flag.level:<5} {name}  {where}")
            if flag.detail:
                print(f"        {flag.detail}")
    if len(report.banks) > 1:
        print(f"  WARN this note compares {len(report.banks)} item banks "
              f"({', '.join(report.banks)}) -- not directly comparable")

    if report.table_problems:
        print("\ntables")
        for problem in report.table_problems:
            print(f"  {problem}")

    print("\nfigures")
    if not report.figure_problems:
        print("  all current")
    for name, problem in report.figure_problems:
        print(f"  {name}  {problem}")

    trouble = (len(report.unresolved), len(report.figure_problems),
               sum(1 for s in report.ref_statuses if s.status not in ("OK", "UNUSED")),
               len(report.derived_bad), len(report.table_problems))
    print(f"\nadvisory only, nothing blocked: {trouble[0]} unresolved numerals, "
          f"{trouble[1]} figure problems, {trouble[2]} ref problems, "
          f"{trouble[3]} bad derivations, {trouble[4]} table problems.")
    return 1 if (args.strict and any(trouble)) else 0


# -------------------------------------------------------------------- the parser

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bt",
        description="Query, quote and chart the results in data/results/.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def common(sub: argparse.ArgumentParser, *, limit: int) -> None:
        sub.add_argument("--limit", type=int, default=limit,
                         help=f"max rows (default {limit}; 0 for all)")
        sub.add_argument("--json", action="store_true", help="machine-readable output")

    runs = subparsers.add_parser("runs", help="what run directories exist")
    runs.add_argument("--experiment")
    runs.add_argument("--match", help="glob against the run id")
    runs.add_argument("--has", action="append", default=[],
                      help="only runs holding this artifact (repeatable, glob)")
    runs.add_argument("--sort", choices=["date", "name"], default="date")
    common(runs, limit=40)
    runs.set_defaults(func=cmd_runs)

    find = subparsers.add_parser(
        "find", help="search every recorded estimate across every run")
    find.add_argument("--quantity", help="glob against the estimate's key, e.g. 'delta_net'")
    find.add_argument("--artifact", help="glob against the filename")
    find.add_argument("--experiment")
    find.add_argument("--run", help="glob against the run id")
    find.add_argument("--excludes-zero", action="store_true",
                      help="only estimates whose recorded interval excludes zero")
    find.add_argument("--min-abs", type=float, help="only |value| at or above this")
    find.add_argument("--max-depth", type=int, default=2,
                      help="pointer depth ceiling (default 2, which excludes per-facet "
                           "and per-pair leaves)")
    find.add_argument("--sort", choices=["abs", "value", "date"], default="abs")
    find.add_argument("--all-artifacts", action="store_true",
                      help="keep a stage report's mirror of its own summary (collapsed by "
                           "default, since it is the same number written twice)")
    common(find, limit=20)
    find.set_defaults(func=cmd_find)

    show = subparsers.add_parser("show", help="one run's estimates, or one exact value")
    show.add_argument("run")
    show.add_argument("--pointer", help="'#belief/delta_net' -- print that value alone, "
                                       "with a ready-to-paste sources.yaml entry")
    show.add_argument("--depth", type=int, default=2)
    show.add_argument("--all-artifacts", action="store_true",
                      help="keep a stage report's mirror of its own summary")
    show.add_argument("--json", action="store_true")
    show.set_defaults(func=cmd_show)

    series = subparsers.add_parser("series", help="rows of a tidy JSONL, pivoted for a chart")
    series.add_argument("run")
    series.add_argument("--file", required=True, help="e.g. trajectory.jsonl")
    series.add_argument("--key", help="comma-separated columns identifying a series")
    series.add_argument("--x", default="step")
    series.add_argument("--value", default="score")
    series.add_argument("--filter", action="append", default=[], metavar="COL=VAL")
    common(series, limit=60)
    series.set_defaults(func=cmd_series)

    figure = subparsers.add_parser("figure", help="render a figure from a .fig.yaml spec")
    figure.add_argument("--spec", required=True)
    figure.add_argument("--out", help="default: the spec path with .fig.yaml -> .png")
    figure.add_argument("--print", dest="print_only", action="store_true",
                        help="resolve and tabulate the data without writing the image "
                             "-- ~10x cheaper to read than the PNG when iterating")
    figure.set_defaults(func=cmd_figure)

    render = subparsers.add_parser(
        "render", help="rewrite the note's bt:table blocks from their .table.yaml specs")
    render.add_argument("note", help="insights/<slug>/ or the note.md inside it")
    render.add_argument("--latex", action="store_true",
                        help="also emit figures/<name>.tex per table spec, for \\input{} "
                             "into a paper -- real typeset text, not an image")
    render.set_defaults(func=cmd_render)

    pdf = subparsers.add_parser(
        "pdf", help="compile an insight note to a shareable PDF")
    pdf.add_argument("note", help="insights/<slug>/ or the note.md inside it")
    pdf.add_argument("--out", help="basename for the .pdf (default: the directory name)")
    pdf.add_argument("--keep-tex", action="store_true",
                     help="leave the generated .tex and compile log in place")
    pdf.add_argument("--tex-only", action="store_true",
                     help="write the .tex and stop, without running tectonic")
    pdf.set_defaults(func=cmd_pdf)

    check = subparsers.add_parser("check", help="audit an insight note's numerals and refs")
    check.add_argument("note", help="insights/<slug>/ or the note.md inside it")
    check.add_argument("--strict", action="store_true",
                       help="exit 1 on any problem, for gating a commit")
    check.add_argument("--no-suggest", action="store_true",
                       help="skip the tree-wide search for unresolved numerals (faster)")
    check.set_defaults(func=cmd_check)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "limit", None) == 0 and not getattr(args, "json", False):
        print("(--limit 0: printing everything matched)", file=sys.stderr)
    try:
        return args.func(args)
    except R.RefError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
