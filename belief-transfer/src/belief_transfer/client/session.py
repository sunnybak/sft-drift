"""Chat session state and slash-command handling for `belief_transfer.client`.

Deliberately free of any model object or transformers import: this module is pure
state plus a command dispatcher, so the whole command surface is testable without a
GPU or a model download (see tests/test_client.py). `__main__` owns the actual
`HFModel` and re-creates it when `handle_command` reports `reload_model`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_MAX_NEW_TOKENS = 512


@dataclass
class Turn:
    """One message. Assistant turns carry the decoding config that produced them, so a
    transcript stays honest across a mid-session `/model` or `/adapter` swap -- the
    thing AGENTS.md's Inference section asks for when it says every inference result
    should retain enough metadata to reproduce it.
    """

    role: str
    content: str
    meta: dict | None = None


@dataclass
class ChatSession:
    model_key: str
    available_models: list[str] = field(default_factory=list)
    adapter_path: Path | None = None
    system: str | None = None
    temperature: float = 0.0
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS
    enable_thinking: bool = False
    seed: int = 42
    history: list[Turn] = field(default_factory=list)

    def messages(self) -> list[dict[str, str]]:
        """The conversation in chat-template shape: the system prompt (if set) followed
        by every turn so far, stripped of the local-only `meta` field.
        """
        rendered = [{"role": "system", "content": self.system}] if self.system else []
        rendered.extend({"role": turn.role, "content": turn.content} for turn in self.history)
        return rendered

    def decoding_config(self) -> dict:
        return {
            "model": self.model_key,
            "adapter": str(self.adapter_path) if self.adapter_path else None,
            "temperature": self.temperature,
            "max_new_tokens": self.max_new_tokens,
            "enable_thinking": self.enable_thinking,
            "seed": self.seed,
        }

    def transcript(self) -> dict:
        return {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "system": self.system,
            "config": self.decoding_config(),
            "turns": [
                {"role": turn.role, "content": turn.content, **({"config": turn.meta} if turn.meta else {})}
                for turn in self.history
            ],
        }

    def status(self) -> str:
        lines = [
            f"model       {self.model_key}",
            f"adapter     {self.adapter_path or '(none -- base checkpoint)'}",
            f"system      {self.system or '(none)'}",
            f"temperature {self.temperature}"
            + ("  (greedy)" if self.temperature <= 0 else "  (sampling)"),
            f"max tokens  {self.max_new_tokens}",
            f"thinking    {'on' if self.enable_thinking else 'off'}",
            f"seed        {self.seed}",
            f"turns       {len(self.history)}",
        ]
        return "\n".join(lines)


@dataclass
class CommandResult:
    output: str = ""
    exit: bool = False
    reload_model: bool = False


HELP = """\
commands
  /help                 show this
  /info                 current model, adapter and decoding settings
  /reset                clear the conversation (keeps settings)
  /system <text>        set the system prompt ("/system clear" to drop it)
  /temp <float>         sampling temperature (0 = greedy)
  /tokens <int>         max new tokens per reply
  /thinking on|off      Qwen3 <think> block before the answer
  /model <key>          switch base model (reloads weights)
  /adapter <path|none>  load a LoRA checkpoint, e.g. an M+/M- arm (reloads weights)
  /history              print the conversation so far
  /save <path>          write the transcript + config to a JSON file
  /exit                 quit (also: /quit, Ctrl-D)

anything not starting with / is sent to the model."""


def handle_command(session: ChatSession, line: str) -> CommandResult:
    """Apply one slash command to `session`. Unknown commands and bad arguments return
    a message rather than raising, so a typo never drops an interactive session.
    """
    parts = line.strip().split(maxsplit=1)
    command = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if command in ("/exit", "/quit"):
        return CommandResult(exit=True)

    if command == "/help":
        return CommandResult(output=HELP)

    if command == "/info":
        return CommandResult(output=session.status())

    if command == "/reset":
        count = len(session.history)
        session.history.clear()
        return CommandResult(output=f"cleared {count} turn(s)")

    if command == "/system":
        if not arg:
            return CommandResult(output=f"system prompt: {session.system or '(none)'}")
        if arg.lower() == "clear":
            session.system = None
            return CommandResult(output="system prompt cleared")
        session.system = arg
        return CommandResult(output="system prompt set")

    if command == "/temp":
        try:
            session.temperature = float(arg)
        except ValueError:
            return CommandResult(output=f"not a number: {arg!r}")
        mode = "greedy" if session.temperature <= 0 else "sampling"
        return CommandResult(output=f"temperature = {session.temperature} ({mode})")

    if command == "/tokens":
        try:
            value = int(arg)
        except ValueError:
            return CommandResult(output=f"not an integer: {arg!r}")
        if value <= 0:
            return CommandResult(output="max new tokens must be positive")
        session.max_new_tokens = value
        return CommandResult(output=f"max new tokens = {value}")

    if command == "/thinking":
        if arg.lower() not in ("on", "off"):
            return CommandResult(output="usage: /thinking on|off")
        session.enable_thinking = arg.lower() == "on"
        return CommandResult(output=f"thinking = {'on' if session.enable_thinking else 'off'}")

    if command == "/model":
        if not arg:
            return CommandResult(output=f"usage: /model <{'|'.join(session.available_models)}>")
        if session.available_models and arg not in session.available_models:
            known = ", ".join(session.available_models)
            return CommandResult(output=f"unknown model {arg!r} -- configs/models.yaml has: {known}")
        if arg == session.model_key:
            return CommandResult(output=f"already on {arg}")
        session.model_key = arg
        return CommandResult(output=f"model = {arg} (reloading)", reload_model=True)

    if command == "/adapter":
        if not arg:
            return CommandResult(output=f"adapter: {session.adapter_path or '(none)'}")
        if arg.lower() in ("none", "clear", "off"):
            if session.adapter_path is None:
                return CommandResult(output="already on the base checkpoint")
            session.adapter_path = None
            return CommandResult(output="adapter cleared (reloading base)", reload_model=True)
        path = Path(arg).expanduser()
        if not path.exists():
            return CommandResult(output=f"no such path: {path}")
        if not (path / "adapter_config.json").exists():
            return CommandResult(output=f"{path} has no adapter_config.json -- not a PEFT adapter directory")
        session.adapter_path = path
        return CommandResult(output=f"adapter = {path} (reloading)", reload_model=True)

    if command == "/history":
        if not session.history:
            return CommandResult(output="(empty)")
        return CommandResult(output="\n".join(f"{turn.role}: {turn.content}" for turn in session.history))

    if command == "/save":
        if not arg:
            return CommandResult(output="usage: /save <path>")
        path = Path(arg).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(session.transcript(), indent=2))
        return CommandResult(output=f"wrote {len(session.history)} turn(s) to {path}")

    return CommandResult(output=f"unknown command {command!r} -- /help for the list")
