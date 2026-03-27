"""Ollama API provider."""
from __future__ import annotations
import json
from typing import AsyncIterator
import httpx
from mockr.core.types import Message, ModelConfig

class OllamaProvider:
    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=300)

    async def aclose(self) -> None:
        await self._client.aclose()

    def _build_request_body(self, messages: list[Message], config: ModelConfig) -> dict:
        return {
            "model": config.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
            },
        }

    async def stream(self, messages: list[Message], config: ModelConfig) -> AsyncIterator[str]:
        body = self._build_request_body(messages, config)
        async with self._client.stream("POST", f"{self._base_url}/api/chat", json=body) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                data = json.loads(line)
                content = data.get("message", {}).get("content", "")
                if content:
                    yield content
