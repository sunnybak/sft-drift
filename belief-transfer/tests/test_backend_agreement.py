"""Backend selection, and whether two backends score the same thing the same way.

Split in two on purpose. The resolver logic (which backend, which dtype, what may
train) is pure and always runs. The actual cross-backend comparison needs real weights
and a fixture recorded on the *other* backend, so it is marked `needs_weights` and
skipped unless `--run-gpu` is passed -- see `inference.agreement` for the two-machine
record/check workflow that produces the fixture.
"""

from __future__ import annotations

import json

import pytest

from belief_transfer.inference import agreement
from belief_transfer.inference.backend import (
    backend_info,
    detect_backend,
    is_trainable,
    require_training_backend,
    resolve_dtype,
)
from belief_transfer.schemas import BackendInfo


def test_detect_backend_returns_a_known_backend() -> None:
    assert detect_backend() in ("cuda", "mlx", "cpu")


def test_cpu_downgrades_low_precision_dtypes_but_others_pass_through() -> None:
    # bf16 on CPU is either unimplemented or emulated slowly enough to look like a
    # hang; nothing experimental runs there, so trading it for fp32 is free.
    assert resolve_dtype("cpu", "bfloat16") == "float32"
    assert resolve_dtype("cpu", "float16") == "float32"
    assert resolve_dtype("cpu", "float32") == "float32"
    assert resolve_dtype("cuda", "bfloat16") == "bfloat16"
    assert resolve_dtype("mlx", "bfloat16") == "bfloat16"


def test_only_cuda_may_train() -> None:
    assert require_training_backend("cuda") == "cuda"
    for backend in ("mlx", "cpu"):
        with pytest.raises(RuntimeError, match="training requires a CUDA backend"):
            require_training_backend(backend)


def test_backend_info_stamps_platform_and_reports_trainability() -> None:
    info = backend_info("mlx", dtype="bfloat16")
    assert info.backend == "mlx"
    assert info.dtype == "bfloat16"
    assert info.platform  # populated from the running machine
    assert info.python
    # Trainability is policy, so it lives with the backend rules rather than on the
    # schema: `schemas.BackendInfo` is a provenance record, not a decision.
    assert not is_trainable(info.backend)
    assert is_trainable(BackendInfo(backend="cuda").backend)


def test_agreement_items_cover_the_three_shapes_that_can_diverge() -> None:
    # Single-token letters are what the efficacy suite uses, but a backend can get
    # those right and still mis-measure the token boundary or length normalization.
    assert {item["id"] for item in agreement.ITEMS} == {
        "letter_choice",
        "multi_token_choice",
        "unequal_length_choice",
    }
    # The unequal-length item must genuinely differ in length: it exists to catch a
    # backend that gets `logprob` right but `logprob_per_token` wrong (or vice versa),
    # and two same-length choices cannot distinguish those.
    by_id = {item["id"]: item for item in agreement.ITEMS}
    short, long = by_id["unequal_length_choice"]["choices"]
    assert len(long.split()) > 3 * len(short.split())


class FakeScorer:
    """Returns whatever `ChoiceScores` it is handed, so `score_items`/`compare` can be
    tested without weights."""

    def __init__(self, rows: dict[str, object]) -> None:
        self.rows = rows

    def score_choices(self, prompt: str, choices: list[str]):
        return self.rows[prompt]


def _scores(choice_logprobs: dict[str, tuple[float, int]]):
    from belief_transfer.schemas import ChoiceScore, ChoiceScores

    return ChoiceScores(
        prompt="p",
        scores=[
            ChoiceScore(
                choice=choice,
                logprob=total,
                logprob_per_token=total / n,
                n_tokens=n,
            )
            for choice, (total, n) in choice_logprobs.items()
        ],
    )


def _recording(per_token: dict[str, tuple[float, int]]) -> dict:
    model = FakeScorer({agreement.ITEMS[0]["prompt"]: _scores(per_token)})
    rows = agreement.score_items(model, [agreement.ITEMS[0]])
    return {"model": "qwen3-4b", "backend": {"backend": "cuda"}, "items": rows}


def test_compare_accepts_small_logprob_drift() -> None:
    recorded = _recording({"A": (-1.0, 1), "B": (-3.0, 1)})
    # Same argmax, per-token difference of 0.005 -- an order of magnitude below the
    # smallest effect this repo reports, so not a disagreement.
    current = agreement.score_items(
        FakeScorer({agreement.ITEMS[0]["prompt"]: _scores({"A": (-1.005, 1), "B": (-2.995, 1)})}),
        [agreement.ITEMS[0]],
    )
    assert agreement.compare(recorded, current) == []


def test_compare_rejects_flipped_argmax_even_when_close() -> None:
    recorded = _recording({"A": (-1.000, 1), "B": (-1.001, 1)})
    current = agreement.score_items(
        FakeScorer({agreement.ITEMS[0]["prompt"]: _scores({"A": (-1.001, 1), "B": (-1.000, 1)})}),
        [agreement.ITEMS[0]],
    )
    problems = agreement.compare(recorded, current)
    # Every eval here reads a forced choice, so a flip is a different answer no matter
    # how small the margin was.
    assert any("argmax differs" in problem for problem in problems)


def test_compare_rejects_logprob_drift_beyond_tolerance() -> None:
    recorded = _recording({"A": (-1.0, 1), "B": (-3.0, 1)})
    current = agreement.score_items(
        FakeScorer({agreement.ITEMS[0]["prompt"]: _scores({"A": (-1.5, 1), "B": (-3.0, 1)})}),
        [agreement.ITEMS[0]],
    )
    problems = agreement.compare(recorded, current)
    assert any("per-token logprob differs" in problem for problem in problems)


def test_compare_flags_differing_tokenization_separately() -> None:
    # A token-count mismatch makes the logprob comparison meaningless rather than
    # merely out of tolerance, so it must not be reported as drift.
    recorded = _recording({"A": (-2.0, 2), "B": (-3.0, 1)})
    current = agreement.score_items(
        FakeScorer({agreement.ITEMS[0]["prompt"]: _scores({"A": (-2.0, 3), "B": (-3.0, 1)})}),
        [agreement.ITEMS[0]],
    )
    problems = agreement.compare(recorded, current)
    assert any("tokenized differently" in problem for problem in problems)
    assert not any("per-token logprob differs" in problem for problem in problems)


def test_check_refuses_to_compare_a_backend_against_itself(make_job, tmp_path, monkeypatch) -> None:
    """Comparing a recording to the backend that produced it proves nothing.

    Worth refusing loudly rather than reporting a vacuous pass, which is what a
    same-backend "check" would be."""
    import asyncio

    from belief_transfer.stages import agreement as agreement_stage

    fixture = tmp_path / "backend_agreement.json"
    fixture.write_text(
        json.dumps({"model": "qwen3-4b", "backend": {"backend": detect_backend()}, "items": []})
    )
    monkeypatch.setattr(agreement_stage.agreement, "FIXTURE_PATH", fixture)

    with pytest.raises(RuntimeError, match="nothing to compare"):
        asyncio.run(agreement_stage.run_check(make_job(["+run=adhoc"])))


def test_check_says_what_to_run_when_no_fixture_exists(make_job, tmp_path, monkeypatch) -> None:
    import asyncio

    from belief_transfer.stages import agreement as agreement_stage

    monkeypatch.setattr(agreement_stage.agreement, "FIXTURE_PATH", tmp_path / "missing.json")
    with pytest.raises(FileNotFoundError, match="agreement_record"):
        asyncio.run(agreement_stage.run_check(make_job(["+run=adhoc"])))


@pytest.mark.needs_weights
def test_backends_agree_against_the_recorded_fixture(job) -> None:
    """The real gate: this machine's backend must match the recording from the other one.

    Skipped rather than failed when the fixture is absent, because it can only be
    produced on the other backend (see `inference.agreement`) -- a missing fixture means
    "not yet recorded on the GPU box", not "the backends disagree".
    """
    if not agreement.FIXTURE_PATH.exists():
        pytest.skip(
            f"no recording at {agreement.FIXTURE_PATH}; run "
            "`python -m belief_transfer.inference.agreement record` on the other backend"
        )
    recorded_backend = json.loads(agreement.FIXTURE_PATH.read_text())["backend"]["backend"]
    if recorded_backend == detect_backend():
        pytest.skip(f"fixture was recorded on this same backend ({recorded_backend})")

    import asyncio

    from belief_transfer.stages import agreement as agreement_stage

    # Raises with the disagreements listed if they do not match.
    asyncio.run(agreement_stage.run_check(job))
