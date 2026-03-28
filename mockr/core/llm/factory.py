"""Factory for creating LLM backends from configuration."""

from __future__ import annotations

from mockr.config import MockrConfig, load_config
from mockr.core.types import ModelConfig


def build_backend(cfg: MockrConfig | None = None):
    """Build a real LLMBackend from config, or FakeLLMBackend if provider is 'fake' or unavailable."""
    if cfg is None:
        cfg = load_config()

    provider_name = cfg.provider

    if provider_name == "fake":
        from mockr.core.llm.fake_backend import FakeLLMBackend

        return FakeLLMBackend(), _fake_model_config()

    if provider_name == "ollama":
        from mockr.core.llm.backend import LLMBackend
        from mockr.core.llm.providers.ollama import OllamaProvider

        provider = OllamaProvider(base_url=cfg.ollama_base_url)
        backend = LLMBackend(provider, provider_type="api")
        config = ModelConfig(model=cfg.ollama_model)
        return backend, config

    if provider_name == "openai":
        from mockr.core.llm.backend import LLMBackend
        from mockr.core.llm.providers.openai import OpenAIProvider

        provider = OpenAIProvider(api_key=cfg.openai_api_key)
        backend = LLMBackend(provider, provider_type="api")
        config = ModelConfig(model=cfg.openai_model)
        return backend, config

    if provider_name == "anthropic":
        from mockr.core.llm.backend import LLMBackend
        from mockr.core.llm.providers.anthropic import AnthropicProvider

        provider = AnthropicProvider(api_key=cfg.anthropic_api_key)
        backend = LLMBackend(provider, provider_type="api")
        config = ModelConfig(model=cfg.anthropic_model)
        return backend, config

    if provider_name == "claude-cli":
        from mockr.core.llm.backend import LLMBackend
        from mockr.core.llm.providers.claude_cli import ClaudeCLIProvider

        provider = ClaudeCLIProvider(command=cfg.claude_cli_command, args=cfg.claude_cli_args)
        backend = LLMBackend(provider, provider_type="cli")
        config = ModelConfig(model="claude-cli")
        return backend, config

    if provider_name == "codex-cli":
        from mockr.core.llm.backend import LLMBackend
        from mockr.core.llm.providers.codex_cli import CodexCLIProvider

        provider = CodexCLIProvider(command=cfg.codex_cli_command, args=cfg.codex_cli_args)
        backend = LLMBackend(provider, provider_type="cli")
        config = ModelConfig(model="codex-cli")
        return backend, config

    # Unknown provider — fall back to fake
    from mockr.core.llm.fake_backend import FakeLLMBackend

    return FakeLLMBackend(), _fake_model_config()


def _fake_model_config() -> ModelConfig:
    return ModelConfig(model="fake", temperature=0.7, max_tokens=1024)
