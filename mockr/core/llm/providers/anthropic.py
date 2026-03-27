"""Anthropic API provider."""

from __future__ import annotations

from collections.abc import AsyncIterator

from mockr.core.types import Message, ModelConfig


class AnthropicProvider:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError("Install anthropic: pip install mockr[anthropic]")
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    def _prepare_messages(self, messages: list[Message]) -> tuple[str, list[dict]]:
        system = ""
        conversation = []
        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                conversation.append({"role": msg.role, "content": msg.content})
        return system, conversation

    async def stream(self, messages: list[Message], config: ModelConfig) -> AsyncIterator[str]:
        system, conversation = self._prepare_messages(messages)
        kwargs = {
            "model": config.model or self._model,
            "messages": conversation,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
        }
        if system:
            kwargs["system"] = system
        async with self._client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text
