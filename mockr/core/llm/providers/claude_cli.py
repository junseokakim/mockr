"""Claude Code CLI provider (OAuth-based, subprocess)."""
from __future__ import annotations
import json
from mockr.core.llm.providers import run_subprocess

class ClaudeCLIProvider:
    def __init__(self, command: str = "claude", args: list[str] | None = None) -> None:
        self._command = command
        self._args = args or ["-p", "--output-format", "json"]

    def _build_command(self) -> list[str]:
        return [self._command, *self._args]

    async def run(self, prompt: str, timeout: int = 180) -> str:
        cmd = self._build_command()
        raw = await run_subprocess(cmd, stdin_data=prompt, timeout=timeout, clear_env=["ANTHROPIC_API_KEY"])
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data.get("result", data.get("content", raw))
        except json.JSONDecodeError:
            pass
        return raw.strip()
