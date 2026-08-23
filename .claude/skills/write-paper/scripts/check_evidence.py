"""Dry-run a paper overlay's evidence before spending on the author model.

    uv run python .claude/skills/write-paper/scripts/check_evidence.py +run=paper_attribution_v1

Composes the config, collects evidence, and resolves every declared contrast -- the same
calls `stage=writeup` makes -- then stops. A contrast that cannot resolve raises here, in
seconds, instead of after the author and reviewer models have been paid for.

Prints each resolved fact with its interval and zero-exclusion so you can eyeball whether
the paper is about to be built on the numbers you meant. Facts without an interval are
arm-derived point contrasts; that is expected, not a defect.

Run from the `belief-transfer/` directory. Any extra argv is passed to Hydra, so overrides
work: `... +run=paper_x writeup.author_model=gpt-5.6-luna`.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve()
for parent in ROOT.parents:
    if (parent / "src" / "belief_transfer").is_dir():
        sys.path.insert(0, str(parent / "src"))
        break


def main() -> int:
    from belief_transfer.analysis import writeup
    from belief_transfer.config import load_job

    overrides = [a for a in sys.argv[1:] if a.strip()]
    if not any(a.startswith("+run=") for a in overrides):
        print("usage: check_evidence.py +run=<paper_run_id> [hydra overrides]")
        return 2
    if not any(a.startswith("stage=") for a in overrides):
        overrides.append("stage=writeup")

    job = load_job(overrides)
    spec = job.writeup
    print(f"run_id        : {job.run_id}")
    print(f"experiment    : {job.experiment.id}")
    print(f"source_runs   : {spec.source_runs}")
    print(f"primary       : {spec.primary_reading}")
    print(f"trajectory_run: {spec.trajectory_run}")
    print(f"declared      : {len(spec.contrasts)} contrasts\n")

    evidence = writeup.collect_evidence(job.experiment.id, spec)
    synthesis = writeup.build_synthesis(evidence, spec)
    facts = synthesis["facts"]

    print(f"{'fact id':30s} {'value':>10s} {'95% CI':>26s}  zero")
    print("-" * 78)
    no_interval, excludes = 0, 0
    for fact in facts:
        ci = fact.get("ci95")
        interval = f"[{ci[0]:+.4f}, {ci[1]:+.4f}]" if ci else "(point contrast)"
        if not ci:
            no_interval += 1
        flag = ""
        if fact.get("excludes_zero"):
            flag, excludes = "EXCLUDES", excludes + 1
        elif ci:
            flag = "straddles"
        print(f"{fact['id']:30s} {float(fact['value']):+10.4f} {interval:>26s}  {flag}")

    print("-" * 78)
    print(f"{len(facts)} facts resolved: {excludes} exclude zero, "
          f"{no_interval} are arm-derived point contrasts")

    # A ladder table renders one row per fact, so a large contrast set is a placement
    # decision, not just a number. Flag it here rather than letting it surface as an
    # inverted table order in the rendered PDF.
    if len(facts) > 12:
        print(f"\nNOTE: {len(facts)} contrasts is more than a main-text table should carry. "
              "The ladder table belongs in the appendix; check `min_main_tables` is not "
              "forcing it into the main text.")
    if spec.trajectory_run is None:
        print("NOTE: trajectory_run is null -- a planned trajectory_figure will be dropped.")
    else:
        # `copy_trajectory_figures` runs only AFTER the manuscript has been planned and
        # written, so a trajectory_run without this artifact fails at the most expensive
        # possible moment. Checking it here is the whole point of a preflight.
        from belief_transfer.analysis.writeup import source_directory
        traj = source_directory(job.experiment.id, spec.trajectory_run) / "trajectory.jsonl"
        if traj.exists():
            print(f"OK  : trajectory_run {spec.trajectory_run!r} has trajectory.jsonl")
        else:
            print(f"FAIL: trajectory_run {spec.trajectory_run!r} has NO trajectory.jsonl "
                  f"({traj}).\n      A planned trajectory_figure will raise AFTER the "
                  f"author model has been paid for. Point it at a run with a trajectory, "
                  f"or set it to null.")
            return 1
    print("\nEvidence resolves. Safe to run stage=writeup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
