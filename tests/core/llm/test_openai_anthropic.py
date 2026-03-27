from __future__ import annotations

import pytest

from mockr.core.llm.providers.anthropic import AnthropicProvider
from mockr.core.llm.providers.openai import OpenAIProvider
from mockr.core.types import Message


@pytest.mark.asyncio
class TestOpenAIProvider:
    async def test_formats_messages(self) -> None:
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o")
        formatted = provider._format_messages(
            [
                Message(role="system", content="You are helpful."),
                Message(role="user", content="Hello"),
            ]
        )
        assert formatted == [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
        ]


@pytest.mark.asyncio
class TestAnthropicProvider:
    async def test_separates_system_message(self) -> None:
        provider = AnthropicProvider(api_key="test-key", model="claude-sonnet-4-6")
        system, messages = provider._prepare_messages(
            [
                Message(role="system", content="System prompt"),
                Message(role="user", content="Hello"),
            ]
        )
        assert system == "System prompt"
        assert messages == [{"role": "user", "content": "Hello"}]

    async def test_no_system_message(self) -> None:
        provider = AnthropicProvider(api_key="test-key", model="claude-sonnet-4-6")
        system, messages = provider._prepare_messages([Message(role="user", content="Hello")])
        assert system == ""
        assert len(messages) == 1
