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


def test_cache_round_trips_through_disk(tmp_path) -> None:
    path = tmp_path / "llm_cache.json"
    key = cache_key("model-a", "prompt")

    cache = Cache(path=path)
    assert cache.get(key) is None
    cache.set(key, {"text": "hello"})

    reloaded = Cache(path=path)
    assert reloaded.get(key) == {"text": "hello"}
    assert len(reloaded) == 1


def test_cache_tracks_hits_and_misses(tmp_path) -> None:
    path = tmp_path / "llm_cache.json"
    cache = Cache(path=path)
    key = cache_key("model-a", "prompt")

    assert cache.get(key) is None
    cache.set(key, {"text": "hello"})
    assert cache.get(key) == {"text": "hello"}
    assert cache.misses == 1
    assert cache.hits == 1
