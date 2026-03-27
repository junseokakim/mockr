"""Configuration loader for mockr."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mockr._compat import tomllib

DEFAULT_CONFIG_PATH = Path.home() / ".mockr" / "config.toml"


@dataclass
class MockrConfig:
    provider: str = "ollama"
    level: str = "senior"
    max_history_turns: int = 8
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    claude_cli_command: str = "claude"
    claude_cli_args: list[str] = field(
        default_factory=lambda: ["-p", "--output-format", "json"]
    )
    claude_cli_timeout: int = 180
    codex_cli_command: str = "codex"
    codex_cli_args: list[str] = field(
        default_factory=lambda: ["exec", "--json", "--skip-git-repo-check"]
    )
    codex_cli_timeout: int = 180


def load_config(path: Path | None = None) -> MockrConfig:
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        return MockrConfig()

    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    cfg = MockrConfig()
    llm = raw.get("llm", {})

    _apply(llm, cfg, {"provider": "provider"})
    _apply(raw.get("profile", {}), cfg, {"level": "level"})
    _apply(llm.get("ollama", {}), cfg, {"base_url": "ollama_base_url", "model": "ollama_model"})
    _apply(llm.get("openai", {}), cfg, {"api_key": "openai_api_key", "model": "openai_model"})
    _apply(llm.get("anthropic", {}), cfg, {"api_key": "anthropic_api_key", "model": "anthropic_model"})
    _apply(llm.get("claude-cli", {}), cfg, {"command": "claude_cli_command", "args": "claude_cli_args", "timeout": "claude_cli_timeout"})
    _apply(llm.get("codex-cli", {}), cfg, {"command": "codex_cli_command", "args": "codex_cli_args", "timeout": "codex_cli_timeout"})

    return cfg


def _apply(section: dict, cfg: MockrConfig, mapping: dict[str, str]) -> None:
    for toml_key, attr_name in mapping.items():
        if toml_key in section:
            setattr(cfg, attr_name, section[toml_key])
