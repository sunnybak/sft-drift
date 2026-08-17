"""Structural rules about `src/`, enforced instead of documented.

The dependency graph is what gets away from you as a codebase grows: a stage reaching into
another stage, a "utility" importing the orchestrator, config parsing leaking into library
code. Each is a small, reasonable-looking edit, and the cost only shows up later when
nothing can be tested or moved in isolation. These are cheap to check, so they are checked.

Built on `ast` rather than importing modules, so a violation is caught without executing
anything -- and so a module that needs a GPU or an API key is still checked. No new
dependency; the whole thing is a walk over the parse trees.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src" / "belief_transfer"
PACKAGE = "belief_transfer"

LAYERS: dict[str, int] = {
    # 0: pure data and pure math. Nothing here may know how anything is produced.
    "schemas": 0,
    "metrics": 0,
    # 1: infrastructure -- talking to models, caching, prompt rendering.
    "generation": 1,
    "inference": 1,
    # 2: stage logic. May use infrastructure; may not know what orchestrates it.
    "dataset": 2,
    "training": 2,
    "evals": 2,
    "validation": 2,
    "benchmarks": 2,
    "analysis": 2,
    "client": 2,
    "data_sync": 2,
    # 3: the config boundary and the stages that compose everything below.
    "config": 3,
    "stages": 3,
}
"""Which layer each top-level module of the package belongs to. A module may import from
its own layer or below, never above."""

MODULE_LAYERS: dict[str, int] = {
    # `calibrate` trains a model: AGENTS.md's tiny-dataset memorization check is part of it,
    # because what that check measures is this machine's *training stack* (GPU, torch/trl/peft
    # versions) and the answer is recorded in the machine's hardware profile alongside the
    # batch-size calibration. So it sits above `training` despite living under `inference/`.
    # Named here rather than moved, so the exception is visible instead of implied.
    f"{PACKAGE}.inference.calibrate": 2,
}
"""Per-module overrides for modules whose dependencies genuinely differ from their
package's. Keep this list very short: each entry is a place the layering does not hold."""

CONFIG_MODULE = f"{PACKAGE}.config"
"""The only module allowed to touch hydra/omegaconf. Everything else takes typed objects,
which is what lets a stage be called from a script or a test without composing a config."""

FORBIDDEN_ANYWHERE = ("hydra", "omegaconf")


def _module_name(path: Path) -> str:
    relative = path.relative_to(SRC)
    parts = list(relative.parts)
    if parts[-1] == "__init__.py":
        parts.pop()
    else:
        parts[-1] = parts[-1].removesuffix(".py")
    return ".".join([PACKAGE, *parts])


def _source_files() -> list[Path]:
    return sorted(path for path in SRC.rglob("*.py") if "__pycache__" not in path.parts)


def _imports(path: Path) -> set[str]:
    """Every module `path` imports, including inside functions.

    Function-level imports count: this codebase defers heavy imports (torch, mlx) on
    purpose, and a rule that only looked at module level would miss exactly the places
    where a shortcut is most tempting.
    """
    tree = ast.parse(path.read_text())
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module)
    return found


def _top_level(module: str) -> str | None:
    """The package-relative top-level name of an internal import, or None if external."""
    if not module.startswith(f"{PACKAGE}."):
        return None
    return module.split(".")[1]


def _graph() -> dict[str, set[str]]:
    return {_module_name(path): _imports(path) for path in _source_files()}


def test_every_top_level_module_has_a_declared_layer() -> None:
    """A new package must be placed deliberately.

    Without this, adding a directory silently opts out of every rule below -- the failure
    mode where a structural check exists but stops covering the code.
    """
    present = {
        path.name.removesuffix(".py")
        for path in SRC.iterdir()
        if path.name not in ("__init__.py", "__pycache__") and not path.name.startswith(".")
    }
    assert present == set(LAYERS), (
        f"undeclared: {sorted(present - set(LAYERS))}, "
        f"declared but missing: {sorted(set(LAYERS) - present)}"
    )


def _layer_of(module: str) -> int | None:
    """`module`'s layer: its own override if it has one, else its package's."""
    if module in MODULE_LAYERS:
        return MODULE_LAYERS[module]
    parts = module.split(".")
    if len(parts) < 2:
        return None  # the package __init__ itself
    return LAYERS.get(parts[1])


def test_no_module_imports_a_higher_layer() -> None:
    violations = []
    for module, imports in _graph().items():
        own_layer = _layer_of(module)
        if own_layer is None:
            continue
        for imported in imports:
            other_layer = _layer_of(imported)
            if other_layer is None or _top_level(imported) == module.split(".")[1]:
                continue
            if other_layer > own_layer:
                violations.append(
                    f"{module} (layer {own_layer}) imports {imported} (layer {other_layer})"
                )
    assert not violations, "upward imports:\n" + "\n".join(violations)


def test_no_import_cycles_between_top_level_modules() -> None:
    """Cycles between packages, which is the granularity that hurts.

    Two modules inside one package may legitimately reference each other; two *packages*
    that do can no longer be understood, tested, or moved separately.
    """
    edges: dict[str, set[str]] = {name: set() for name in LAYERS}
    for module, imports in _graph().items():
        parts = module.split(".")
        if len(parts) < 2 or parts[1] not in edges:
            continue
        own = parts[1]
        for imported in imports:
            other = _top_level(imported)
            if other and other in edges and other != own:
                edges[own].add(other)

    # Depth-first search for a back edge; reports the cycle rather than just its existence.
    state: dict[str, int] = {}

    def visit(node: str, path: list[str]) -> list[str] | None:
        state[node] = 1
        for neighbour in sorted(edges[node]):
            if state.get(neighbour) == 1:
                return path + [node, neighbour]
            if state.get(neighbour, 0) == 0:
                found = visit(neighbour, path + [node])
                if found:
                    return found
        state[node] = 2
        return None

    for node in sorted(edges):
        if state.get(node, 0) == 0:
            cycle = visit(node, [])
            assert cycle is None, "import cycle: " + " -> ".join(cycle)


def test_metrics_imports_only_the_standard_library() -> None:
    """`metrics/` is pure math on rows and must stay that way.

    If a metric could import the model, the eval, or the config, then reproducing a number
    from stored rows would stop being possible -- and independently recomputing every
    reported metric is the property AGENTS.md is asking for.
    """
    for path in _source_files():
        module = _module_name(path)
        if not module.startswith(f"{PACKAGE}.metrics"):
            continue
        internal = {imported for imported in _imports(path) if imported.startswith(PACKAGE)}
        assert not internal, f"{module} imports {sorted(internal)}"


def test_only_the_config_module_touches_hydra() -> None:
    """Config composition stays at the edge.

    A `DictConfig` reaching library code would make every function's real input untyped and
    unvalidated, and would mean a script or test could not call a stage without standing up
    Hydra first. One module is the boundary; `run.py` (outside src/) is the other side of it.
    """
    offenders = []
    for path in _source_files():
        module = _module_name(path)
        if module == CONFIG_MODULE:
            continue
        for imported in _imports(path):
            if imported.split(".")[0] in FORBIDDEN_ANYWHERE:
                offenders.append(f"{module} imports {imported}")
    assert not offenders, (
        "only belief_transfer.config may import hydra/omegaconf:\n" + "\n".join(offenders)
    )


def test_nothing_in_src_imports_scripts() -> None:
    """`scripts/` is throwaway by design; the library must not depend on it."""
    for path in _source_files():
        imports = _imports(path)
        assert not any(imported.split(".")[0] == "scripts" for imported in imports), _module_name(path)


def test_no_module_reads_yaml_outside_the_config_boundary() -> None:
    """The six `load_*_config` helpers are gone; this keeps them from coming back.

    Each one let a function reach for a file behind its caller's back, so what a stage
    actually ran with depended on the filesystem rather than on its arguments.
    """
    allowed = {
        CONFIG_MODULE,
        # Writes reports and reads the previous one to accumulate lifetime totals.
        f"{PACKAGE}.analysis.report",
        # Reads/writes the gitignored per-machine hardware profile, which is a measurement
        # this code produces rather than configuration it is handed.
        f"{PACKAGE}.inference.model",
        f"{PACKAGE}.inference.calibrate",
        # Writes its own summary artifact.
        f"{PACKAGE}.stages.efficacy",
        # Same: writes sensitivity_summary.yaml next to its responses.
        f"{PACKAGE}.stages.sensitivity",
    }
    offenders = [
        _module_name(path)
        for path in _source_files()
        if "yaml" in _imports(path) and _module_name(path) not in allowed
    ]
    assert not offenders, f"unexpected yaml users: {offenders}"


@pytest.mark.parametrize("stage_module", ["datagen", "sft", "efficacy"])
def test_stages_do_not_import_each_other_except_through_declared_helpers(stage_module: str) -> None:
    """Stages compose the library, not one another.

    One narrow exception is allowed and named: efficacy needs `stages.sft`'s checkpoint
    layout, because the alternative is two modules deriving the same path independently and
    drifting. Anything else sharing between stages belongs in the library.
    """
    allowed_edges = {("efficacy", "sft")}
    path = SRC / "stages" / f"{stage_module}.py"
    for imported in _imports(path):
        other = imported.removeprefix(f"{PACKAGE}.stages.").split(".")[0]
        if imported.startswith(f"{PACKAGE}.stages.") and other != stage_module:
            assert (stage_module, other) in allowed_edges, f"{stage_module} imports stages.{other}"
