"""Cross-run queries over the results tree, and the citation refs that address it.

The gap this fills. `data/results/<experiment>/<run>/` holds 270 run directories and ~6400
recorded estimates, and until now nothing in this repo could look across them: a grep for
`glob`/`rglob`/`iterdir` over all of `src/` and `scripts/` returned two hits, both scoped
to a single run directory, and all 38 scripts in `scripts/` hardcode the paths they read.
Cross-run knowledge therefore lived only in prose -- `STATE.md`, `AGENTS.md`, the changelog
-- which is fine for a human and useless to anything that has to *find* a result before
writing about it.

**This module enumerates nothing.** That is the one design rule, and it is what keeps it
usable by research it was not written for. An estimate is recognised structurally:

    a dict containing `ci95` plus exactly one of `delta` | `mean` | `score`

Measured across all 720 non-config result artifacts: 6374 nodes contain `ci95`, and every
one of them matches that rule -- 3006 `mean`, 2098 `score`, 1270 `delta`, with no node
carrying none of them and none carrying two. So `af_summary.yaml`'s twenty ad-hoc quantity
names (`af_tracin_cos_p10_s42`, ...) and `retrieval_summary.yaml`'s `rho_*` are found
without anyone registering them, which is exactly what an enumerated key list cannot do.
Every such list in this package has needed editing within a week of being written
(`writeup.evidence._SUMMARY_FILES`, `markdown._SUITES`, `tables.SUITE_SUMMARIES`).

There is deliberately **no index**: a full scan of the tree is ~4s, so a cache would buy
seconds and introduce a staleness bug class plus a "did you rebuild it" failure mode.

No printing happens here. `analysis.cli` owns every byte of output.
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import yaml

from belief_transfer.analysis.report import RESULTS_DIR, ROOT

ESTIMATE_KEYS = ("delta", "mean", "score")
"""The point-estimate key an estimate node carries exactly one of. Measured, not guessed:
see the module docstring. `retrieval_summary.yaml` records Spearman rhos under `delta`, so
a `rho` entry here would be dead code."""

CONFIG_ARTIFACT = "config.resolved.yaml"
"""Excluded from estimate scans. It is 80% of the tree's bytes and holds no measurements --
it is the *input* to a run, and a config default that happens to be shaped like an estimate
is not a result."""

_SUFFIXES = ("_summary.yaml", ".yaml", ".jsonl", ".json", ".md")
"""Tried in order after the literal filename when resolving an artifact stem."""


# --------------------------------------------------------------------------- refs

@dataclass(frozen=True, order=True)
class RunRef:
    """One run directory, always qualified by its experiment."""

    experiment: str
    run_id: str

    def __str__(self) -> str:
        return f"{self.experiment}/{self.run_id}"

    @property
    def path(self) -> Path:
        return RESULTS_DIR / self.experiment / self.run_id


@dataclass(frozen=True)
class Ref:
    """A parsed citation: one value in one artifact of one run.

    Syntax is `[<experiment>/]<run_id>#<artifact-stem>/<json-pointer>`, e.g.
    `factory_farming/matrix_v1#belief/delta_net`. The experiment prefix is optional on
    input -- run ids happen to be unique across the tree today, and relying on that
    silently would be fragile -- but `str()` always emits it, so what lands in a note's
    ledger is unambiguous even if a second experiment later reuses a run id.
    """

    run: RunRef
    artifact: str
    pointer: str

    def __str__(self) -> str:
        stem = _stem(self.artifact)
        return f"{self.run}#{stem}{self.pointer}"

    @property
    def path(self) -> Path:
        return self.run.path / self.artifact


def _stem(artifact: str) -> str:
    """`belief_summary.yaml` -> `belief`; the short form `parse_ref` accepts back."""
    for suffix in _SUFFIXES:
        if artifact.endswith(suffix) and artifact != suffix:
            return artifact[: -len(suffix)]
    return artifact


class RefError(ValueError):
    """A ref that cannot be resolved, or resolves ambiguously.

    Its own class so the CLI can print the message plainly instead of a traceback: an
    agent reading stderr should see "which did you mean" and not a stack.
    """


def pointer_token(value: str) -> str:
    """Escape one JSON-Pointer token (RFC 6901)."""
    return value.replace("~", "~0").replace("/", "~1")


def leaf_pointers(value: Any, pointer: str = "") -> list[str]:
    """Every scalar leaf of `value`, as JSON Pointers."""
    if isinstance(value, dict):
        return [
            child
            for key, item in value.items()
            for child in leaf_pointers(item, f"{pointer}/{pointer_token(str(key))}")
        ]
    if isinstance(value, list):
        return [
            child
            for index, item in enumerate(value)
            for child in leaf_pointers(item, f"{pointer}/{index}")
        ]
    return [pointer or "/"]


def value_at(value: Any, pointer: str) -> Any:
    """Resolve a JSON Pointer against a loaded document. Raises KeyError/IndexError."""
    current = value
    if pointer in ("", "/"):
        return current
    for raw_token in pointer.lstrip("/").split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current


def parse_ref(text: str, *, root: Path | None = None) -> Ref:
    """Parse a ref string, resolving the run and the artifact stem against disk.

    Also accepts the paper pipeline's older `<run>:<artifact.yaml>:/<pointer>` spelling, so the
    two notations in this repo cannot fork into two incompatible citation formats.
    """
    text = text.strip()
    if "#" not in text and text.count(":") >= 2:
        run_part, artifact, pointer = text.split(":", 2)
        run_part = run_part.strip()
        return Ref(_resolve_run(run_part, root=root), artifact, pointer or "/")

    if "#" not in text:
        raise RefError(
            f"{text!r} is not a ref: expected '<run>#<artifact>/<pointer>', "
            "e.g. 'factory_farming/matrix_v1#belief/delta_net'"
        )
    run_part, _, tail = text.partition("#")
    run = _resolve_run(run_part.strip(), root=root)
    stem, _, pointer = tail.partition("/")
    if not stem:
        raise RefError(f"{text!r} names no artifact after '#'")
    return Ref(run, _resolve_artifact(run, stem), f"/{pointer}" if pointer else "/")


def _resolve_run(text: str, *, root: Path | None = None) -> RunRef:
    base = root or RESULTS_DIR
    if "/" in text:
        experiment, _, run_id = text.partition("/")
        return RunRef(experiment, run_id)
    matches = [run for run in run_dirs(root=base) if run.run_id == text]
    if not matches:
        raise RefError(f"no run directory named {text!r} under {base}")
    if len(matches) > 1:
        listed = ", ".join(str(run) for run in matches)
        raise RefError(f"run id {text!r} is ambiguous: {listed}. Qualify it.")
    return matches[0]


def _resolve_artifact(run: RunRef, stem: str) -> str:
    """`belief` -> `belief_summary.yaml`, erroring rather than guessing when several fit."""
    directory = run.path
    candidates = [stem] + [f"{stem}{suffix}" for suffix in _SUFFIXES]
    present = [name for name in candidates if (directory / name).is_file()]
    if not present:
        available = sorted(p.name for p in directory.glob("*")) if directory.is_dir() else []
        raise RefError(
            f"{run} has no artifact matching {stem!r}. "
            + (f"It holds: {', '.join(available)}" if available else f"{directory} does not exist")
        )
    if len(present) > 1:
        raise RefError(
            f"{stem!r} is ambiguous in {run}: {', '.join(present)}. Use the full filename."
        )
    return present[0]


# ------------------------------------------------------------------- the tree

def load(path: Path) -> dict[str, Any] | None:
    """One exists-guarded loader for a result artifact, YAML or JSON or JSONL.

    Replaces `writeup._load_yaml`, `markdown._load` and `report._previous_result`'s third
    copy of the same three lines. Returns None for a missing or non-mapping document
    rather than raising, because "the stage did not run" is the common case and a caller
    that wants to distinguish it can check the path itself.
    """
    if not path.is_file():
        return None
    if path.suffix == ".jsonl":
        rows = load_rows(path)
        return {"rows": rows} if rows else None
    if path.suffix not in (".yaml", ".yml", ".json"):
        return None  # `report.md` and `VOID.md` are prose; a YAML parse of one raises
    try:
        value = yaml.safe_load(path.read_text())  # YAML is a superset of JSON
    except yaml.YAMLError:
        return None  # reported by `scan_errors` when it happens mid-scan
    return value if isinstance(value, dict) else None


def load_rows(path: Path) -> list[dict[str, Any]]:
    """A tidy JSONL file as a list of rows; blank and torn lines are skipped."""
    import json

    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue  # a torn final line costs one row, not the whole file
    return rows


def run_dirs(*, root: Path | None = None, experiment: str | None = None,
             match: str | None = None) -> list[RunRef]:
    """Every run directory, sorted. `match` is a glob against the run id."""
    base = root or RESULTS_DIR
    if not base.is_dir():
        return []
    runs = []
    for experiment_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        if experiment and experiment_dir.name != experiment:
            continue
        for run_dir in sorted(p for p in experiment_dir.iterdir() if p.is_dir()):
            if match and not fnmatch.fnmatch(run_dir.name, match):
                continue
            runs.append(RunRef(experiment_dir.name, run_dir.name))
    return runs


def artifacts(run: RunRef, *, include_config: bool = False) -> list[str]:
    """Filenames in a run directory, sorted, hidden directories excluded."""
    if not run.path.is_dir():
        return []
    names = sorted(p.name for p in run.path.iterdir() if p.is_file())
    if not include_config:
        names = [name for name in names if name != CONFIG_ARTIFACT]
    return names


def scannable(run: RunRef) -> list[str]:
    """Artifacts worth loading for estimates: YAML and JSON, never the config or raw rows.

    `*_responses.jsonl` is excluded on purpose. It is ~1.2MB per file across 103 files and
    holds per-item `p_positive` values that no summary blesses -- quoting one in a note is
    a defect rather than a finding, so the query surface does not offer them.
    """
    return [
        name for name in artifacts(run)
        if name.endswith((".yaml", ".json")) and not name.endswith(".jsonl")
    ]


# -------------------------------------------------------------------- estimates

@dataclass(frozen=True)
class Estimate:
    """One recorded estimate, addressable by `ref`."""

    ref: Ref
    kind: str            # which of ESTIMATE_KEYS carried the point value
    value: float
    ci95: tuple[float, float] | None
    n_items: int | None
    excludes_zero: bool | None
    suites_from: str | None
    """The evalgen run the underlying items came from, when the artifact records one.
    Carried because comparing two scores measured against different item banks is the
    likeliest scientific error in a cross-run reading, and this is the field that catches
    it."""

    @property
    def depth(self) -> int:
        return self.ref.pointer.count("/")


def _estimate_nodes(value: Any, pointer: str = "") -> Iterator[tuple[str, str, dict]]:
    """(pointer, kind, node) for every estimate node, recursing through them as well.

    Recursion continues *into* a matched node because they nest: an arm carries `score`
    plus an `acquiescence` block that carries its own `mean`.
    """
    if isinstance(value, dict):
        if "ci95" in value:
            kinds = [key for key in ESTIMATE_KEYS if key in value]
            if len(kinds) == 1 and isinstance(value.get(kinds[0]), (int, float)):
                yield pointer or "/", kinds[0], value
        for key, item in value.items():
            yield from _estimate_nodes(item, f"{pointer}/{pointer_token(str(key))}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _estimate_nodes(item, f"{pointer}/{index}")


def estimates(run: RunRef, artifact: str, doc: dict[str, Any] | None = None) -> list[Estimate]:
    """Every estimate in one artifact of one run."""
    document = doc if doc is not None else load(run.path / artifact)
    if not document:
        return []
    suites_from = document.get("suites_from") or document.get("suite")
    found = []
    for pointer, kind, node in _estimate_nodes(document):
        interval = node.get("ci95")
        pair: tuple[float, float] | None = None
        if isinstance(interval, (list, tuple)) and len(interval) == 2:
            try:
                pair = (float(interval[0]), float(interval[1]))
            except (TypeError, ValueError):
                pair = None
        found.append(Estimate(
            ref=Ref(run, artifact, pointer),
            kind=kind,
            value=float(node[kind]),
            ci95=pair,
            n_items=node.get("n_items") or node.get("n_pairs") or node.get("n_sources"),
            excludes_zero=node.get("excludes_zero"),
            suites_from=suites_from if isinstance(suites_from, str) else None,
        ))
    return found


def scan(*, root: Path | None = None, experiment: str | None = None,
         match: str | None = None) -> Iterator[tuple[RunRef, str, list[Estimate]]]:
    """Walk the tree yielding one entry per artifact. Unreadable files are skipped.

    A malformed artifact must not abort a scan of 720 files, so the failure is swallowed
    here and surfaced by `scan_errors` for the caller to report.
    """
    for run in run_dirs(root=root, experiment=experiment, match=match):
        for artifact in scannable(run):
            try:
                found = estimates(run, artifact)
            except Exception as exc:  # noqa: BLE001 -- one bad file, not one bad scan
                _ERRORS.append(f"{run}/{artifact}: {type(exc).__name__}: {exc}")
                continue
            if found:
                yield run, artifact, found


_ERRORS: list[str] = []


def scan_errors() -> list[str]:
    """Artifacts the last scan could not read. Drained by the caller that reports them."""
    return list(_ERRORS)


def resolve(ref: Ref) -> Any:
    """The value a ref addresses. Raises RefError with the path when it does not resolve."""
    document = load(ref.path)
    if document is None:
        raise RefError(f"{ref.path} does not exist or is not a mapping")
    try:
        return value_at(document, ref.pointer)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RefError(f"{ref} does not resolve: {type(exc).__name__} {exc}") from exc


def estimate_at(ref: Ref) -> Estimate | None:
    """The estimate a ref addresses, if it points at one (rather than at a scalar leaf)."""
    for found in estimates(ref.run, ref.artifact):
        if found.ref.pointer == ref.pointer:
            return found
    return None


# ------------------------------------------------------------------------ flags

@dataclass(frozen=True)
class Flag:
    """A reason not to quote a run, or not to quote part of one."""

    level: str      # "VOID" or "GATE"
    source: str     # where it was recorded, so a reader can go argue with it
    detail: str
    pointer: str = ""
    """Where in the run the flag was found, when it is local to one reading. A run whose
    gate fails at step 60 is quotable at step 24, and a flag that cannot say so reads as
    "this run is bad" when the truth is "this reading is"."""


def _void_table(state_path: Path) -> dict[str, str]:
    """Run ids named in `STATE.md`'s "Void / uninterpretable" table.

    Parsed rather than duplicated because that table is the only record for 5 of the 7
    known-void runs -- just 2 run directories carry a `VOID.md`, so a checker that looked
    only for the marker file would clear four runs it should refuse. Defensive by
    construction: an unrecognised table shape yields nothing instead of raising, and the
    marker files plus the recorded `passed: false` scan still fire.
    """
    if not state_path.is_file():
        return {}
    voids: dict[str, str] = {}
    in_table = False
    for line in state_path.read_text().splitlines():
        lowered = line.lower()
        if lowered.startswith("#"):
            in_table = "void" in lowered or "do not cite" in lowered
            continue
        if not in_table or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2 or set(cells[0]) <= set("- :"):
            continue
        why = cells[1]
        for run_id in re.findall(r"`([^`]+)`", cells[0]):
            voids[run_id.strip()] = why
    return voids


def _passed_false(run: RunRef) -> list[Flag]:
    """Every recorded `passed: false` in a run, with the pointer where it was found.

    Generic: `passed` is a plain bool in a stage report's open `metrics` dict, so this
    needs no knowledge of what gate wrote it or what bar it used.
    """
    found = []
    for artifact in scannable(run):
        document = load(run.path / artifact)
        if not document:
            continue
        for pointer in leaf_pointers(document):
            if not pointer.endswith("/passed"):
                continue
            try:
                if value_at(document, pointer) is False:
                    found.append(Flag(
                        "GATE", f"{artifact}", "recorded passed: false", pointer,
                    ))
            except (KeyError, IndexError, TypeError, ValueError):
                continue
    return found


def flags(run: RunRef, *, gates: bool = True, state_path: Path | None = None) -> list[Flag]:
    """Every reason to distrust this run, from all three places one gets recorded.

    Three sources because no one of them is complete: `VOID.md` exists in 2 run
    directories, `STATE.md`'s table names 7 runs, and a recorded `passed: false` catches
    13 -- including runs both of the other two miss.

    `gates=False` skips the `passed: false` scan, which has to load every artifact in the
    run. A list view over 270 runs cannot afford it; a detail view of one run should always
    pay it.
    """
    found: list[Flag] = []
    marker = run.path / "VOID.md"
    if marker.is_file():
        headline = next(
            (line.strip() for line in marker.read_text().splitlines()
             if line.strip() and not line.startswith("#")),
            "see VOID.md",
        )
        found.append(Flag("VOID", "VOID.md", headline))
    table = _void_table(state_path or (ROOT.parent / "STATE.md"))
    if run.run_id in table:
        found.append(Flag("VOID", "STATE.md void table", table[run.run_id]))
    if gates:
        found.extend(_passed_false(run))
    return found


@dataclass
class FlagIndex:
    """`flags` memoised across a whole listing, since the void table is re-read per call."""

    state_path: Path | None = None
    _cache: dict[tuple[RunRef, bool], list[Flag]] = field(default_factory=dict)

    def for_run(self, run: RunRef, *, gates: bool = True) -> list[Flag]:
        key = (run, gates)
        if key not in self._cache:
            self._cache[key] = flags(run, gates=gates, state_path=self.state_path)
        return self._cache[key]

    def label(self, run: RunRef, *, gates: bool = True) -> str:
        """The short column form: "VOID" wins over "GATE", empty when clean."""
        levels = {flag.level for flag in self.for_run(run, gates=gates)}
        return "VOID" if "VOID" in levels else ("GATE" if levels else "-")
