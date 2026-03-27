from __future__ import annotations

from mockr.config import MockrConfig
from mockr.core.llm.backend import LLMBackend
from mockr.core.llm.factory import build_backend
from mockr.core.llm.fake_backend import FakeLLMBackend
from mockr.core.types import ModelConfig


class TestBuildBackend:
    def test_fake_provider(self) -> None:
        cfg = MockrConfig(provider="fake")
        backend, config = build_backend(cfg)
        assert isinstance(backend, FakeLLMBackend)
        assert config.model == "fake"

    def test_ollama_provider(self) -> None:
        cfg = MockrConfig(provider="ollama", ollama_model="llama3")
        backend, config = build_backend(cfg)
        assert isinstance(backend, LLMBackend)
        assert config.model == "llama3"

    def test_claude_cli_provider(self) -> None:
        cfg = MockrConfig(provider="claude-cli")
        backend, config = build_backend(cfg)
        assert isinstance(backend, LLMBackend)
        assert config.model == "claude-cli"

    def test_unknown_provider_falls_back_to_fake(self) -> None:
        cfg = MockrConfig(provider="nonexistent")
        backend, config = build_backend(cfg)
        assert isinstance(backend, FakeLLMBackend)

    def test_default_config_returns_backend(self) -> None:
        cfg = MockrConfig()  # defaults to ollama
        backend, config = build_backend(cfg)
        assert isinstance(backend, LLMBackend)
