"""`python -m belief_transfer.client` -- the REPL and its argument parsing.

Status messages go to stderr and model output to stdout, so the one-shot form pipes
cleanly:

    echo "Is factory farming harmful?" | python -m belief_transfer.client > answer.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from belief_transfer.client.session import DEFAULT_MAX_NEW_TOKENS, ChatSession, Turn, handle_command
from belief_transfer.inference.model import MODELS_CONFIG_PATH, load_models_config

load_dotenv(find_dotenv())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="belief_transfer.client", description=__doc__)
    parser.add_argument("--model", default="qwen3-4b", help="model key from configs/models.yaml")
    parser.add_argument("--adapter", default=None, help="path to a LoRA adapter directory (an M+/M- arm)")
    parser.add_argument("--system", default=None, help="system prompt")
    parser.add_argument("--temperature", type=float, default=0.0, help="0 = greedy (default)")
    parser.add_argument("--max-new-tokens", type=int, default=DEFAULT_MAX_NEW_TOKENS)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--thinking", action="store_true", help="enable Qwen3 <think> blocks")
    parser.add_argument("--no-stream", action="store_true", help="wait for the full reply instead of streaming")
    parser.add_argument("-p", "--prompt", default=None, help="send one prompt, print the reply, exit")
    parser.add_argument("--models-config", type=Path, default=MODELS_CONFIG_PATH)
    return parser


def notify(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    models_config = load_models_config(args.models_config)
    available = list(models_config.models.keys())
    if args.model not in available:
        notify(f"unknown model {args.model!r} -- configs/models.yaml has: {', '.join(available)}")
        return 2

    adapter_path = Path(args.adapter).expanduser() if args.adapter else None
    if adapter_path is not None and not adapter_path.exists():
        notify(f"no such adapter path: {adapter_path}")
        return 2

    session = ChatSession(
        model_key=args.model,
        available_models=available,
        adapter_path=adapter_path,
        system=args.system,
        temperature=args.temperature,
        max_new_tokens=args.max_new_tokens,
        enable_thinking=args.thinking,
        seed=args.seed,
    )

    one_shot = args.prompt if args.prompt is not None else (None if sys.stdin.isatty() else sys.stdin.read().strip())
    stream = not args.no_stream and one_shot is None

    runner = _ModelRunner(args.models_config)
    if one_shot:
        reply = runner.reply(session, one_shot, stream=False)
        print(reply)
        return 0
    if one_shot is not None:
        return 0  # empty piped input: nothing to ask

    return _repl(session, runner, stream=stream)


class _ModelRunner:
    """Owns the `HFModel`, rebuilding it when the session's model/adapter changes.

    Loading is deferred to the first message so `--help`, a bad model key, or a typo'd
    adapter path costs nothing -- weights are only touched once there is something to
    actually ask.
    """

    def __init__(self, models_config_path: Path) -> None:
        self._models_config_path = models_config_path
        self._model = None
        self._loaded_for: tuple[str, str | None] | None = None

    def invalidate(self) -> None:
        self._model = None
        self._loaded_for = None

    def _ensure(self, session: ChatSession):
        from belief_transfer.inference.model import HFModel

        key = (session.model_key, str(session.adapter_path) if session.adapter_path else None)
        if self._model is not None and self._loaded_for == key:
            return self._model
        target = session.adapter_path or "base checkpoint"
        notify(f"[loading {session.model_key} ({target}) -- first load downloads weights if not cached]")
        self._model = HFModel(
            session.model_key,
            adapter_path=session.adapter_path,
            models_config_path=self._models_config_path,
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
    notify(f"belief-transfer chat -- {session.model_key}"
           f"{f' + {session.adapter_path}' if session.adapter_path else ''}. /help for commands, /exit to quit.")
    while True:
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
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
        except Exception as exc:  # noqa: BLE001 -- a bad generate shouldn't kill the session
            if session.history and session.history[-1].role == "user":
                session.history.pop()
            notify(f"[error] {type(exc).__name__}: {exc}")
            continue

        if not stream:
            print(reply)


if __name__ == "__main__":
    raise SystemExit(main())
