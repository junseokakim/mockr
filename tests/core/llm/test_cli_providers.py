from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from mockr.core.llm.providers.claude_cli import ClaudeCLIProvider
from mockr.core.llm.providers.codex_cli import CodexCLIProvider


@pytest.mark.asyncio
class TestClaudeCLI:
    async def test_builds_command(self) -> None:
        provider = ClaudeCLIProvider(command="claude", args=["-p", "--output-format", "json"])
        cmd = provider._build_command()
        assert cmd[0] == "claude"
        assert "-p" in cmd
        assert "--output-format" in cmd

    @patch("mockr.core.llm.providers.claude_cli.run_subprocess")
    async def test_run_returns_parsed_result(self, mock_run: AsyncMock) -> None:
        mock_run.return_value = json.dumps({"result": "Design looks good."})
        provider = ClaudeCLIProvider(command="claude", args=["-p", "--output-format", "json"])
        result = await provider.run("Design a cache", timeout=60)
        assert "Design looks good" in result
        mock_run.assert_called_once()

    @patch("mockr.core.llm.providers.claude_cli.run_subprocess")
    async def test_timeout_raises(self, mock_run: AsyncMock) -> None:
        mock_run.side_effect = TimeoutError("timed out")
        provider = ClaudeCLIProvider(command="claude", args=["-p"])
        with pytest.raises(TimeoutError):
            await provider.run("prompt", timeout=5)


@pytest.mark.asyncio
class TestCodexCLI:
    async def test_builds_command(self) -> None:
        provider = CodexCLIProvider(command="codex", args=["exec", "--json"])
        cmd = provider._build_command()
        assert cmd[0] == "codex"
        assert "exec" in cmd

    @patch("mockr.core.llm.providers.codex_cli.run_subprocess")
    async def test_run_returns_result(self, mock_run: AsyncMock) -> None:
        mock_run.return_value = '{"message": "hello"}\n'
        provider = CodexCLIProvider(command="codex", args=["exec", "--json"])
        result = await provider.run("prompt", timeout=60)
        assert "hello" in result
