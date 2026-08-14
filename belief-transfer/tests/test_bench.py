"""Tests for `inference.bench`'s pure logic: scoring (simple-bench and memorization),
profile round-tripping, and batch-size resolution.

Nothing here loads a real model. That is the whole split this module is built around:
the sweep, generation, and training paths need real hardware and belong to the
benchmarks themselves (`make bench`, `make simple-bench`, `make memorization-bench`),
which measure a machine and record the answer in configs/hardware_profile.yaml. What
stays here is everything that decides *what gets written to that file* and *which
batch size inference then uses* -- plain data transforms, verifiable on any box.

A benchmark that fails tells you this machine is misconfigured; a test that fails
tells you the code is wrong. Keeping them separate keeps that signal unambiguous.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from belief_transfer.inference import bench
from belief_transfer.inference.model import (
    load_hardware_profile,
    load_models_config,
    resolve_batch_size,
)
from belief_transfer.schemas import HardwareProfile, MachineInfo, ModelBenchResult

ROOT = Path(__file__).resolve().parents[1]


def test_simple_bench_items_are_wellformed() -> None:
    assert len(bench.SIMPLE_BENCH_ITEMS) >= 10
    for item in bench.SIMPLE_BENCH_ITEMS:
        assert item.prompt.strip()
        assert item.expected.strip()


def test_score_simple_bench_all_correct() -> None:
    items = [
        bench.SimpleBenchItem("2+2?", r"\b4\b"),
        bench.SimpleBenchItem("capital of France?", r"paris"),
    ]
    scored = bench.score_simple_bench(items, ["The answer is 4.", "Paris"])
    assert scored["n_correct"] == 2
    assert scored["accuracy"] == 1.0
    assert scored["failures"] == []


def test_score_simple_bench_is_case_insensitive_and_reports_failures() -> None:
    items = [
        bench.SimpleBenchItem("capital of France?", r"paris"),
        bench.SimpleBenchItem("2+2?", r"\b4\b"),
    ]
    scored = bench.score_simple_bench(items, ["PARIS", "The answer is 5."])
    assert scored["n_correct"] == 1
    assert scored["accuracy"] == 0.5
    assert len(scored["failures"]) == 1
    assert scored["failures"][0]["response"] == "The answer is 5."


def test_score_simple_bench_rejects_length_mismatch() -> None:
    with pytest.raises(ValueError):
        bench.score_simple_bench([bench.SimpleBenchItem("a", "a")], ["x", "y"])


def test_word_boundary_patterns_do_not_match_substrings_of_longer_numbers() -> None:
    # `\b19\b` must not be satisfied by "190" -- otherwise a wrong answer scores as
    # correct and the whole simple-bench signal is worthless.
    items = [bench.SimpleBenchItem("12+7?", r"\b19\b")]
    assert bench.score_simple_bench(items, ["190"])["n_correct"] == 0
    assert bench.score_simple_bench(items, ["19"])["n_correct"] == 1


def _row(batch_size: int, tokens_per_sec: float, peak_vram_gb: float, oom: bool = False) -> dict:
    return {
        "batch_size": batch_size,
        "oom": oom,
        "tokens_per_sec": tokens_per_sec,
        "peak_vram_gb": peak_vram_gb,
    }


def test_select_batch_size_stops_at_the_throughput_knee() -> None:
    # 256 -> 512 buys only ~3% more throughput for ~2GB more VRAM: not worth the lost
    # headroom, so the knee at 256 wins over the largest size that merely fits.
    sweep = [
        _row(64, 357.0, 8.5),
        _row(128, 443.0, 9.0),
        _row(256, 486.0, 10.0),
        _row(512, 500.0, 11.9),
    ]
    assert bench.select_batch_size(sweep, total_vram_gb=16.6)["batch_size"] == 256


def test_select_batch_size_keeps_climbing_while_gains_are_real() -> None:
    sweep = [_row(8, 100.0, 8.1), _row(16, 200.0, 8.2), _row(32, 400.0, 8.3)]
    assert bench.select_batch_size(sweep, total_vram_gb=16.6)["batch_size"] == 32


def test_select_batch_size_respects_the_vram_margin_over_throughput() -> None:
    # 32 is much faster but exceeds 0.85 * 16 = 13.6GB, so it must not be chosen.
    sweep = [_row(8, 100.0, 8.0), _row(16, 200.0, 12.0), _row(32, 400.0, 15.0)]
    assert bench.select_batch_size(sweep, total_vram_gb=16.0)["batch_size"] == 16


def test_select_batch_size_ignores_oom_rows() -> None:
    sweep = [_row(8, 100.0, 8.0), _row(16, 200.0, 9.0), _row(32, 0.0, 0.0, oom=True)]
    assert bench.select_batch_size(sweep, total_vram_gb=16.0)["batch_size"] == 16


def test_select_batch_size_falls_back_when_nothing_fits_the_margin() -> None:
    # Even the smallest batch exceeding the margin must still yield a usable answer
    # rather than an empty selection -- the model has to run somehow.
    sweep = [_row(8, 100.0, 15.0), _row(16, 200.0, 15.5)]
    assert bench.select_batch_size(sweep, total_vram_gb=16.0)["batch_size"] == 8


def test_every_simple_bench_item_is_matched_by_a_plausible_correct_answer() -> None:
    # Guards the scoring patterns themselves: a too-strict pattern scores a correct
    # model answer as a miss and makes simple-bench look like a broken pipeline.
    # ("H2O" vs the "H₂O" Qwen3 actually returns was exactly this bug.)
    plausible = {
        r"\b19\b": "19",
        r"\b72\b": "72",
        r"\b63\b": "63",
        r"tokyo": "Tokyo",
        r"paris": "Paris",
        r"canberra": "Canberra",
        r"\bseven\b|\b7\b": "7",
        r"green": "Green",
        r"h[2₂]o": "H₂O",
        r"\btac\b": "tac",
        r"earth": "Earth",
        r"\b32\b": "32",
    }
    for item in bench.SIMPLE_BENCH_ITEMS:
        assert item.expected in plausible, f"no plausible answer registered for {item.expected}"
        answer = plausible[item.expected]
        assert bench.score_simple_bench([item], [answer])["n_correct"] == 1, (
            f"pattern {item.expected!r} rejects plausible answer {answer!r}"
        )


def test_probe_hardware_never_raises_and_returns_machine_info() -> None:
    # Every field is best-effort; on a box with no GPU this must still return a
    # MachineInfo rather than blowing up a calibration run.
    info = bench.probe_hardware()
    assert isinstance(info, MachineInfo)
    assert info.hostname


def test_hardware_profile_round_trips_through_yaml(tmp_path: Path) -> None:
    profile = HardwareProfile(
        generated_at="2026-08-14T00:00:00+00:00",
        machine=MachineInfo(hostname="box", gpu_name="RTX 5080", gpu_vram_total_gb=16.3),
        models={
            "qwen3-4b": ModelBenchResult(
                batch_size=64,
                max_new_tokens_tested=256,
                tokens_per_sec=900.0,
                time_to_first_token_s=0.12,
                peak_vram_gb=11.0,
                calibrated_at="2026-08-14T00:00:00+00:00",
            )
        },
    )
    path = tmp_path / "hardware_profile.yaml"
    bench._write_profile(profile, path)

    loaded = load_hardware_profile(path)
    assert loaded is not None
    assert loaded.models["qwen3-4b"].batch_size == 64
    assert loaded.machine.gpu_name == "RTX 5080"


def test_load_hardware_profile_returns_none_when_missing(tmp_path: Path) -> None:
    assert load_hardware_profile(tmp_path / "nope.yaml") is None


def test_load_hardware_profile_returns_none_on_malformed_file(tmp_path: Path) -> None:
    # A stale/corrupt profile must degrade to the shared config default rather than
    # breaking every inference call on the machine.
    path = tmp_path / "hardware_profile.yaml"
    path.write_text("models: {qwen3-4b: {batch_size: 'not-an-int'}}")
    assert load_hardware_profile(path) is None


def test_resolve_batch_size_prefers_calibrated_profile(tmp_path: Path) -> None:
    models_config = load_models_config()
    path = tmp_path / "hardware_profile.yaml"
    bench._write_profile(
        HardwareProfile(
            generated_at="2026-08-14T00:00:00+00:00",
            models={
                "qwen3-4b": ModelBenchResult(
                    batch_size=123,
                    max_new_tokens_tested=256,
                    tokens_per_sec=1.0,
                    time_to_first_token_s=1.0,
                    peak_vram_gb=1.0,
                    calibrated_at="2026-08-14T00:00:00+00:00",
                )
            },
        ),
        path,
    )
    assert resolve_batch_size("qwen3-4b", models_config, hardware_profile_path=path) == 123


def test_resolve_batch_size_falls_back_to_models_config(tmp_path: Path) -> None:
    models_config = load_models_config()
    missing = tmp_path / "nope.yaml"
    assert resolve_batch_size("qwen3-4b", models_config, hardware_profile_path=missing) == (
        models_config.inference.batch_size
    )


def test_resolve_batch_size_falls_back_for_uncalibrated_model(tmp_path: Path) -> None:
    # A profile calibrated for one model must not silently supply its batch size to a
    # different, larger model that was never benchmarked on this box.
    models_config = load_models_config()
    path = tmp_path / "hardware_profile.yaml"
    bench._write_profile(
        HardwareProfile(
            generated_at="2026-08-14T00:00:00+00:00",
            models={
                "qwen3-4b": ModelBenchResult(
                    batch_size=123,
                    max_new_tokens_tested=256,
                    tokens_per_sec=1.0,
                    time_to_first_token_s=1.0,
                    peak_vram_gb=1.0,
                    calibrated_at="2026-08-14T00:00:00+00:00",
                )
            },
        ),
        path,
    )
    assert resolve_batch_size("qwen3-8b", models_config, hardware_profile_path=path) == (
        models_config.inference.batch_size
    )


def test_written_profile_is_plain_yaml_readable_without_pydantic(tmp_path: Path) -> None:
    # The profile is meant to be inspectable by a human (and by `vast-capabilities`-style
    # tooling) on a fresh box, so it must be plain YAML, not a pickled/tagged dump.
    path = tmp_path / "hardware_profile.yaml"
    bench._write_profile(HardwareProfile(generated_at="2026-08-14T00:00:00+00:00"), path)
    raw = yaml.safe_load(path.read_text())
    assert raw["generated_at"] == "2026-08-14T00:00:00+00:00"


def test_write_profile_handles_str_subclass_versions(tmp_path: Path) -> None:
    # `torch.__version__` is a `TorchVersion` (a str subclass) and `yaml.safe_dump`
    # refuses to represent subclasses -- writing must coerce to plain types, or
    # calibration fails only on a real machine and never in tests.
    class VersionLikeStr(str):
        pass

    profile = HardwareProfile(
        generated_at="2026-08-14T00:00:00+00:00",
        machine=MachineInfo(hostname="box", torch_version=VersionLikeStr("2.10.0+cu128")),
    )
    path = tmp_path / "hardware_profile.yaml"
    bench._write_profile(profile, path)
    assert yaml.safe_load(path.read_text())["machine"]["torch_version"] == "2.10.0+cu128"


def test_probe_hardware_output_is_yaml_serializable(tmp_path: Path) -> None:
    # The real end-to-end guard for the above: whatever probe_hardware() actually
    # collects on this machine must survive a profile write.
    profile = HardwareProfile(generated_at="2026-08-14T00:00:00+00:00", machine=bench.probe_hardware())
    path = tmp_path / "hardware_profile.yaml"
    bench._write_profile(profile, path)
    assert yaml.safe_load(path.read_text())["machine"]["hostname"]


def test_memorization_items_are_arbitrary_and_seeded() -> None:
    """Codes must be reproducible across runs (same box, same measurement) but carry no
    relationship to their input, or a base model could get them right without training.
    """
    items = bench.memorization_items(20)
    again = bench.memorization_items(20)

    assert items == again
    assert len(items) == 20
    assert len({code for _, code in items}) == 20, "duplicate codes would make scoring ambiguous"
    assert all(inp == f"lookup_{i}" for i, (inp, _) in enumerate(items))
    assert all(code.isdigit() and len(code) == 4 for _, code in items)


def test_score_memorization_counts_substring_hits_per_item() -> None:
    items = [("lookup_0", "1234"), ("lookup_1", "5678"), ("lookup_2", "9012")]

    scored = bench.score_memorization(items, ["1234", "the code is 5678.", "no idea"])

    assert scored["n_correct"] == 2
    assert scored["accuracy"] == pytest.approx(2 / 3)
    assert scored["misses"] == ["lookup_2"]


def test_score_memorization_is_positional_not_set_membership() -> None:
    """A model echoing some *other* item's code must not score as a hit -- otherwise a
    model that memorized one mapping and repeated it everywhere would look perfect.
    """
    items = [("lookup_0", "1234"), ("lookup_1", "5678")]

    scored = bench.score_memorization(items, ["5678", "5678"])

    assert scored["n_correct"] == 1
    assert scored["misses"] == ["lookup_0"]


def test_score_memorization_rejects_length_mismatch() -> None:
    with pytest.raises(ValueError):
        bench.score_memorization([("lookup_0", "1234")], [])
