import json

from belief_transfer.generation.cache import Cache, cache_key


def test_cache_key_stable_for_same_inputs() -> None:
    assert cache_key("model-a", "prompt") == cache_key("model-a", "prompt")


def test_cache_key_varies_with_model_prompt_tool_and_replicate() -> None:
    base = cache_key("model-a", "prompt")
    assert base != cache_key("model-b", "prompt")
    assert base != cache_key("model-a", "other prompt")
    assert base != cache_key("model-a", "prompt", tool_name="submit_answer")
    assert base != cache_key("model-a", "prompt", replicate=1)
    assert cache_key("model-a", "prompt", replicate=1) != cache_key(
        "model-a", "prompt", replicate=2
    )


def test_cache_key_is_pinned_to_known_values() -> None:
    """The keying scheme must not drift.

    Every entry in every existing cache is derived from this function, so changing how it
    joins or hashes its inputs silently invalidates all of them -- hours of judging and
    real money (~$2.90 for one control corpus), with no error to notice, because an
    invalidated key just looks like a miss. These literals are the guard: if they ever need
    updating, that is the signal to weigh the cost first.
    """
    assert (
        cache_key("gpt-5.6-luna", "hello")
        == "7dabac2f3cba89eea0fa0440dd1d15fea0a1942055953efe14f59ec25883ba32"
    )
    assert (
        cache_key("gpt-5.6-luna", "hello", "submit_answer", 2)
        == "d942d5c19cae83efd38857cd1d230e43f6b28f0fe3fc22e8715a99c65d104d47"
    )


def test_cache_round_trips_through_disk(tmp_path) -> None:
    path = tmp_path / "llm_cache.jsonl"
    key = cache_key("model-a", "prompt")

    cache = Cache(path=path)
    assert cache.get(key) is None
    cache.set(key, {"text": "hello"})

    reloaded = Cache(path=path)
    assert reloaded.get(key) == {"text": "hello"}
    assert len(reloaded) == 1


def test_cache_tracks_hits_and_misses(tmp_path) -> None:
    cache = Cache(path=tmp_path / "llm_cache.jsonl")
    key = cache_key("model-a", "prompt")

    assert cache.get(key) is None
    cache.set(key, {"text": "hello"})
    assert cache.get(key) == {"text": "hello"}
    assert cache.misses == 1
    assert cache.hits == 1


def test_writes_append_rather_than_rewriting_the_file(tmp_path) -> None:
    """One line per `set`, and existing lines untouched.

    This is the whole point of the format: the old version rewrote the entire file on every
    call, so a run making ~11,000 calls against a growing file paid O(n^2) bytes of I/O and
    could lose another process's entries in the process.
    """
    path = tmp_path / "llm_cache.jsonl"
    cache = Cache(path=path)
    cache.set(cache_key("m", "a"), {"text": "A"})
    after_first = path.read_text()

    cache.set(cache_key("m", "b"), {"text": "B"})
    after_second = path.read_text()

    assert after_second.startswith(after_first)  # the first line was not rewritten
    assert len(after_second.splitlines()) == 2


def test_later_writes_of_a_key_win(tmp_path) -> None:
    path = tmp_path / "llm_cache.jsonl"
    key = cache_key("m", "a")
    cache = Cache(path=path)
    cache.set(key, {"text": "first"})
    cache.set(key, {"text": "second"})

    # Both lines are on disk (append-only), but the last one is what loads.
    assert len(path.read_text().splitlines()) == 2
    assert Cache(path=path).get(key) == {"text": "second"}


def test_a_torn_final_line_costs_one_entry_not_the_whole_cache(tmp_path) -> None:
    """A process killed mid-append leaves a partial line; everything before it must survive.

    Raising instead would strand every paid-for entry in the file, which is the opposite of
    what a cache-as-checkpoint is for.
    """
    path = tmp_path / "llm_cache.jsonl"
    good_key = cache_key("m", "good")
    path.write_text(
        json.dumps({"key": good_key, "value": {"text": "kept"}}) + "\n" + '{"key": "torn", "val'
    )

    cache = Cache(path=path)
    assert cache.get(good_key) == {"text": "kept"}
    assert len(cache) == 1


def test_an_existing_single_object_cache_is_still_read(tmp_path) -> None:
    """The previous format's entries cost money; adopting JSONL must not discard them."""
    legacy_key = cache_key("m", "legacy")
    (tmp_path / "llm_cache.json").write_text(json.dumps({legacy_key: {"text": "old"}}))

    cache = Cache(path=tmp_path / "llm_cache.jsonl")
    assert cache.get(legacy_key) == {"text": "old"}

    # A new write goes to the JSONL file, leaving the legacy file alone.
    new_key = cache_key("m", "new")
    cache.set(new_key, {"text": "new"})
    assert (tmp_path / "llm_cache.jsonl").exists()
    assert json.loads((tmp_path / "llm_cache.json").read_text()) == {legacy_key: {"text": "old"}}


def test_a_jsonl_entry_supersedes_the_legacy_file(tmp_path) -> None:
    key = cache_key("m", "a")
    (tmp_path / "llm_cache.json").write_text(json.dumps({key: {"text": "old"}}))
    (tmp_path / "llm_cache.jsonl").write_text(json.dumps({"key": key, "value": {"text": "new"}}) + "\n")

    assert Cache(path=tmp_path / "llm_cache.jsonl").get(key) == {"text": "new"}


def test_compact_drops_superseded_lines_without_changing_what_loads(tmp_path) -> None:
    path = tmp_path / "llm_cache.jsonl"
    key = cache_key("m", "a")
    cache = Cache(path=path)
    cache.set(key, {"text": "first"})
    cache.set(key, {"text": "second"})
    cache.set(cache_key("m", "b"), {"text": "B"})
    assert len(path.read_text().splitlines()) == 3

    kept = cache.compact()

    assert kept == 2
    assert len(path.read_text().splitlines()) == 2
    assert Cache(path=path).get(key) == {"text": "second"}
