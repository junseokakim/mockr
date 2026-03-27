"""OpenAI API provider."""
from __future__ import annotations
from typing import AsyncIterator
from mockr.core.types import Message, ModelConfig


class OpenAIProvider:
    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("Install openai: pip install mockr[openai]")
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    def _format_messages(self, messages: list[Message]) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in messages]

    async def stream(self, messages: list[Message], config: ModelConfig) -> AsyncIterator[str]:
        response = await self._client.chat.completions.create(
            model=config.model or self._model,
            messages=self._format_messages(messages),
            temperature=config.temperature, max_tokens=config.max_tokens, stream=True,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content
