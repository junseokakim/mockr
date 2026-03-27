from __future__ import annotations

import pytest

from mockr.core.llm.providers.ollama import OllamaProvider
from mockr.core.types import Message, ModelConfig


@pytest.mark.asyncio
class TestOllamaProvider:
    async def test_builds_correct_request_body(self) -> None:
        provider = OllamaProvider(base_url="http://localhost:11434")
        body = provider._build_request_body(
            [Message(role="user", content="hello")],
            ModelConfig(model="llama3", temperature=0.5),
        )
        assert body["model"] == "llama3"
        assert body["messages"] == [{"role": "user", "content": "hello"}]
        assert body["options"]["temperature"] == 0.5
        assert body["stream"] is True
