"""Unified LLM backend wrapping API and CLI providers."""
from __future__ import annotations
from typing import AsyncIterator
from mockr.core.types import Message, ModelConfig

def _format_messages_as_prompt(messages: list[Message]) -> str:
    parts = []
    for msg in messages:
        parts.append(f"{msg.role.upper()}:\n{msg.content}")
    return "\n\n".join(parts)

class LLMBackend:
    def __init__(self, provider: object, provider_type: str) -> None:
        self._provider = provider
        self._type = provider_type

    async def generate(self, messages: list[Message], config: ModelConfig) -> str:
        if self._type == "cli":
            prompt = _format_messages_as_prompt(messages)
            return await self._provider.run(prompt, timeout=180)
        chunks: list[str] = []
        async for chunk in self._provider.stream(messages, config):
            chunks.append(chunk)
        return "".join(chunks).strip()

    async def stream(self, messages: list[Message], config: ModelConfig) -> AsyncIterator[str]:
        if self._type == "cli":
            prompt = _format_messages_as_prompt(messages)
            result = await self._provider.run(prompt, timeout=180)
            yield result
        else:
            async for chunk in self._provider.stream(messages, config):
                yield chunk
