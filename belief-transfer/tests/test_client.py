"""Command-surface tests for `belief_transfer.client`.

`session.py` holds no model object, so everything here runs without a GPU, a network
call, or a weight download -- the one thing these tests can't cover is generation
itself, which is `inference.model`'s territory and already exercised there.
"""

from __future__ import annotations

import json
from pathlib import Path

from belief_transfer.client.session import ChatSession, Turn, handle_command


def make_session(**kwargs) -> ChatSession:
    defaults = dict(model_key="qwen3-4b", available_models=["qwen3-4b", "qwen3-8b"])
    return ChatSession(**{**defaults, **kwargs})


def test_messages_prepends_system_prompt_only_when_set() -> None:
    session = make_session()
    session.history.append(Turn(role="user", content="hi"))
    assert session.messages() == [{"role": "user", "content": "hi"}]

    session.system = "You are terse."
    assert session.messages()[0] == {"role": "system", "content": "You are terse."}


def test_messages_strips_per_turn_metadata() -> None:
    """`meta` is local bookkeeping for the transcript; sending it to the chat template
    would put an unexpected key in the message dicts.
    """
    session = make_session()
    session.history.append(Turn(role="assistant", content="hello", meta={"model": "qwen3-4b"}))
    assert session.messages() == [{"role": "assistant", "content": "hello"}]


def test_reset_clears_history_but_keeps_settings() -> None:
    session = make_session(temperature=0.7, system="stay terse")
    session.history.append(Turn(role="user", content="hi"))

    result = handle_command(session, "/reset")

    assert session.history == []
    assert session.temperature == 0.7
    assert session.system == "stay terse"
    assert "1 turn" in result.output


def test_temp_and_tokens_reject_bad_values_without_raising() -> None:
    session = make_session()

    assert "not a number" in handle_command(session, "/temp warm").output
    assert session.temperature == 0.0

    assert "not an integer" in handle_command(session, "/tokens lots").output
    assert "positive" in handle_command(session, "/tokens 0").output
    assert session.max_new_tokens == 512

    handle_command(session, "/temp 0.8")
    handle_command(session, "/tokens 128")
    assert (session.temperature, session.max_new_tokens) == (0.8, 128)


def test_system_set_show_and_clear() -> None:
    session = make_session()

    assert "(none)" in handle_command(session, "/system").output
    handle_command(session, "/system You are a farmer.")
    assert session.system == "You are a farmer."
    handle_command(session, "/system clear")
    assert session.system is None


def test_thinking_toggle_validates_argument() -> None:
    session = make_session()

    assert "usage" in handle_command(session, "/thinking maybe").output
    assert session.enable_thinking is False

    handle_command(session, "/thinking on")
    assert session.enable_thinking is True


def test_model_switch_requires_known_key_and_requests_reload() -> None:
    session = make_session()

    rejected = handle_command(session, "/model llama-70b")
    assert "unknown model" in rejected.output
    assert rejected.reload_model is False
    assert session.model_key == "qwen3-4b"

    assert "already on" in handle_command(session, "/model qwen3-4b").output

    accepted = handle_command(session, "/model qwen3-8b")
    assert accepted.reload_model is True
    assert session.model_key == "qwen3-8b"


def test_adapter_requires_a_real_peft_directory(tmp_path: Path) -> None:
    session = make_session()

    assert "no such path" in handle_command(session, f"/adapter {tmp_path / 'nope'}").output
    assert session.adapter_path is None

    bare = tmp_path / "not_an_adapter"
    bare.mkdir()
    assert "adapter_config.json" in handle_command(session, f"/adapter {bare}").output
    assert session.adapter_path is None

    good = tmp_path / "positive"
    good.mkdir()
    (good / "adapter_config.json").write_text("{}")
    result = handle_command(session, f"/adapter {good}")
    assert result.reload_model is True
    assert session.adapter_path == good


def test_adapter_none_clears_back_to_base(tmp_path: Path) -> None:
    adapter = tmp_path / "positive"
    adapter.mkdir()
    (adapter / "adapter_config.json").write_text("{}")
    session = make_session(adapter_path=adapter)

    result = handle_command(session, "/adapter none")

    assert session.adapter_path is None
    assert result.reload_model is True
    assert "already on the base" in handle_command(session, "/adapter none").output


def test_save_writes_transcript_with_reproduction_metadata(tmp_path: Path) -> None:
    session = make_session(temperature=0.3, seed=7)
    session.history.append(Turn(role="user", content="why?"))
    session.history.append(Turn(role="assistant", content="because", meta=session.decoding_config()))
    out = tmp_path / "nested" / "chat.json"

    handle_command(session, f"/save {out}")

    saved = json.loads(out.read_text())
    assert [turn["content"] for turn in saved["turns"]] == ["why?", "because"]
    assert saved["config"]["temperature"] == 0.3
    assert saved["config"]["seed"] == 7
    assert saved["config"]["model"] == "qwen3-4b"
    # The assistant turn carries its own config, so a mid-session model swap stays
    # attributable rather than being flattened into the session-level config.
    assert saved["turns"][1]["config"]["model"] == "qwen3-4b"


def test_save_records_the_model_each_turn_actually_used() -> None:
    session = make_session()
    session.history.append(Turn(role="assistant", content="base answer", meta=session.decoding_config()))
    handle_command(session, "/model qwen3-8b")
    session.history.append(Turn(role="assistant", content="swapped answer", meta=session.decoding_config()))

    turns = session.transcript()["turns"]

    assert turns[0]["config"]["model"] == "qwen3-4b"
    assert turns[1]["config"]["model"] == "qwen3-8b"


def test_exit_and_unknown_commands() -> None:
    session = make_session()

    assert handle_command(session, "/exit").exit is True
    assert handle_command(session, "/quit").exit is True

    unknown = handle_command(session, "/nope")
    assert "unknown command" in unknown.output
    assert unknown.exit is False


def test_help_and_info_render() -> None:
    session = make_session(adapter_path=Path("data/checkpoints/x/y/positive"))

    assert "/adapter" in handle_command(session, "/help").output
    info = handle_command(session, "/info").output
    assert "qwen3-4b" in info
    assert "positive" in info
