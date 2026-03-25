from __future__ import annotations
import pytest
from mockr.core.llm.backend import LLMBackend
from mockr.core.types import Message, ModelConfig

class FakeAPIProvider:
    def __init__(self, response: str) -> None:
        self._response = response
    async def stream(self, messages, config):
        for chunk in self._response.split():
            yield chunk + " "

class FakeCLIProvider:
    def __init__(self, response: str) -> None:
        self._response = response
    async def run(self, prompt: str, timeout: int) -> str:
        return self._response

@pytest.mark.asyncio
class TestLLMBackend:
    async def test_generate_with_api_provider(self) -> None:
        provider = FakeAPIProvider("hello world")
        backend = LLMBackend(provider, provider_type="api")
        result = await backend.generate(
            [Message(role="user", content="hi")], ModelConfig(model="test"),
        )
        assert result.strip() == "hello world"

    async def test_generate_with_cli_provider(self) -> None:
        provider = FakeCLIProvider("hello from cli")
        backend = LLMBackend(provider, provider_type="cli")
        result = await backend.generate(
            [Message(role="user", content="hi")], ModelConfig(model="test"),
        )
        assert result == "hello from cli"

    async def test_stream_with_api_provider(self) -> None:
        provider = FakeAPIProvider("token by token")
        backend = LLMBackend(provider, provider_type="api")
        chunks: list[str] = []
        async for chunk in backend.stream(
            [Message(role="user", content="hi")], ModelConfig(model="test"),
        ):
            chunks.append(chunk)
        assert len(chunks) == 3

    async def test_stream_with_cli_provider_yields_single_chunk(self) -> None:
        provider = FakeCLIProvider("full response")
        backend = LLMBackend(provider, provider_type="cli")
        chunks: list[str] = []
        async for chunk in backend.stream(
            [Message(role="user", content="hi")], ModelConfig(model="test"),
        ):
            chunks.append(chunk)
        assert len(chunks) == 1
        assert chunks[0] == "full response"
