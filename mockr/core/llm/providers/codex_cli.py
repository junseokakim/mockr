"""Codex CLI provider (OAuth-based, subprocess)."""
from __future__ import annotations
import json
from mockr.core.llm.providers import run_subprocess

class CodexCLIProvider:
    def __init__(self, command: str = "codex", args: list[str] | None = None) -> None:
        self._command = command
        self._args = args or ["exec", "--json", "--skip-git-repo-check"]

    def _build_command(self) -> list[str]:
        return [self._command, *self._args]

    async def run(self, prompt: str, timeout: int = 180) -> str:
        cmd = self._build_command()
        raw = await run_subprocess(cmd, stdin_data=prompt, timeout=timeout)
        lines = [l for l in raw.strip().splitlines() if l.strip()]
        for line in reversed(lines):
            try:
                data = json.loads(line)
                if isinstance(data, dict) and "message" in data:
                    return data["message"]
            except json.JSONDecodeError:
                continue
        return raw.strip()
