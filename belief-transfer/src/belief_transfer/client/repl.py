"""The chat REPL: an interactive session against a base checkpoint or an M+/M- adapter.

Status messages go to stderr and model output to stdout, so the one-shot form pipes
cleanly:

    echo "Is factory farming harmful?" | python run.py stage=chat > answer.txt

Driven by `stages.chat` from a `JobConfig` rather than its own argparse; the session
settings it used to take as flags are `job.chat` (see `schemas.ChatSpec`).
"""

from __future__ import annotations

import signal
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from belief_transfer.client.session import ChatSession, Turn, handle_command
from belief_transfer.inference.local import local_model
from belief_transfer.inference.model import free_gpu
from belief_transfer.schemas import JobConfig, ModelsConfig

load_dotenv(find_dotenv())


class _Shutdown(BaseException):
    """Raised from the SIGTERM handler so an external `kill` unwinds through the same
    `finally` that frees the model, instead of the OS's default raw termination. A
    `BaseException`, not `Exception`, so it isn't accidentally swallowed by the
    per-turn `except Exception` below the way a real generation error should be.
    """


def notify(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def run_chat(job: JobConfig) -> int:
    """Start a chat session described by `job.chat`."""
    available = list(job.models.models.keys())
    adapter_path = Path(job.chat.adapter).expanduser() if job.chat.adapter else None
    if adapter_path is not None and not adapter_path.exists():
        notify(f"no such adapter path: {adapter_path}")
        return 2

    session = ChatSession(
        model_key=job.training.model,
        available_models=available,
        adapter_path=adapter_path,
        system=job.chat.system,
        temperature=job.chat.temperature,
        max_new_tokens=job.chat.max_new_tokens,
        enable_thinking=job.chat.thinking,
        seed=job.training.sft.seed,
    )

    one_shot = job.chat.prompt
    if one_shot is None and not sys.stdin.isatty():
        one_shot = sys.stdin.read().strip()
    stream = job.chat.stream and one_shot is None

    runner = _ModelRunner(job.models)
    if one_shot:
        print(runner.reply(session, one_shot, stream=False))
        return 0
    if one_shot is not None:
        return 0  # empty piped input: nothing to ask

    return _repl(session, runner, stream=stream)


class _ModelRunner:
    """Owns the loaded model, rebuilding it when the session's model/adapter changes.

    Loading is deferred to the first message so `--help`, a bad model key, or a typo'd
    adapter path costs nothing -- weights are only touched once there is something to
    actually ask.
    """

    def __init__(self, models_config: ModelsConfig) -> None:
        self._models_config = models_config
        self._model = None
        self._loaded_for: tuple[str, str | None] | None = None

    def invalidate(self) -> None:
        self._model = None
        self._loaded_for = None
        free_gpu()

    def _ensure(self, session: ChatSession):
        key = (session.model_key, str(session.adapter_path) if session.adapter_path else None)
        if self._model is not None and self._loaded_for == key:
            return self._model
        target = session.adapter_path or "base checkpoint"
        notify(f"[loading {session.model_key} ({target}) -- first load downloads weights if not cached]")
        self._model = local_model(
            session.model_key,
            self._models_config,
            adapter_path=session.adapter_path,
            max_new_tokens=session.max_new_tokens,
            seed=session.seed,
            enable_thinking=session.enable_thinking,
        )
        self._loaded_for = key
        return self._model

    def reply(self, session: ChatSession, prompt: str, *, stream: bool) -> str:
        model = self._ensure(session)
        # `enable_thinking` is read at generate time, so a mid-session /thinking toggle
        # applies without paying for a full reload.
        model.enable_thinking = session.enable_thinking
        session.history.append(Turn(role="user", content=prompt))

        on_token = None
        if stream:

            def on_token(chunk: str) -> None:
                print(chunk, end="", flush=True)

        reply = model.chat(
            session.messages(),
            temperature=session.temperature,
            max_new_tokens=session.max_new_tokens,
            on_token=on_token,
        )
        if stream:
            print()
        session.history.append(Turn(role="assistant", content=reply, meta=session.decoding_config()))
        return reply


def _repl(session: ChatSession, runner: _ModelRunner, *, stream: bool) -> int:
    """Own the loaded model's whole lifetime: whatever ends this loop -- `/exit`, EOF,
    Ctrl-C, an uncaught error, or an external `kill` (SIGTERM) -- runs through the same
    `finally`, so an idle or abandoned session never sits holding VRAM (see
    AGENTS.md/changelog's "process hygiene": one such session once starved a training
    job into a silent CPU-offload instead of a clean OOM).
    """

    def _handle_sigterm(signum, frame):
        raise _Shutdown

    signal.signal(signal.SIGTERM, _handle_sigterm)

    notify(f"belief-transfer chat -- {session.model_key}"
           f"{f' + {session.adapter_path}' if session.adapter_path else ''}. /help for commands, /exit to quit.")
    try:
        while True:
            try:
                line = input("> ")
            except (EOFError, KeyboardInterrupt, _Shutdown):
                print(file=sys.stderr)
                return 0

            if not line.strip():
                continue

            if line.strip().startswith("/"):
                result = handle_command(session, line)
                if result.output:
                    notify(result.output)
                if result.reload_model:
                    runner.invalidate()
                if result.exit:
                    return 0
                continue

            try:
                reply = runner.reply(session, line, stream=stream)
            except KeyboardInterrupt:
                # Drop the dangling user turn so the history stays a clean alternation.
                if session.history and session.history[-1].role == "user":
                    session.history.pop()
                notify("\n[interrupted]")
                continue
            except _Shutdown:
                print(file=sys.stderr)
                return 0
            except Exception as exc:  # noqa: BLE001 -- a bad generate shouldn't kill the session
                if session.history and session.history[-1].role == "user":
                    session.history.pop()
                notify(f"[error] {type(exc).__name__}: {exc}")
                continue

            if not stream:
                print(reply)
    finally:
        runner.invalidate()
