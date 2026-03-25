"""Configuration loader for mockr."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 12):
    import tomllib
else:
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

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
    if "provider" in llm:
        cfg.provider = llm["provider"]

    profile = raw.get("profile", {})
    if "level" in profile:
        cfg.level = profile["level"]

    ollama = llm.get("ollama", {})
    if "base_url" in ollama:
        cfg.ollama_base_url = ollama["base_url"]
    if "model" in ollama:
        cfg.ollama_model = ollama["model"]

    openai = llm.get("openai", {})
    if "api_key" in openai:
        cfg.openai_api_key = openai["api_key"]
    if "model" in openai:
        cfg.openai_model = openai["model"]

    anthropic = llm.get("anthropic", {})
    if "api_key" in anthropic:
        cfg.anthropic_api_key = anthropic["api_key"]
    if "model" in anthropic:
        cfg.anthropic_model = anthropic["model"]

    claude_cli = llm.get("claude-cli", {})
    if "command" in claude_cli:
        cfg.claude_cli_command = claude_cli["command"]
    if "args" in claude_cli:
        cfg.claude_cli_args = claude_cli["args"]
    if "timeout" in claude_cli:
        cfg.claude_cli_timeout = claude_cli["timeout"]

    codex_cli = llm.get("codex-cli", {})
    if "command" in codex_cli:
        cfg.codex_cli_command = codex_cli["command"]
    if "args" in codex_cli:
        cfg.codex_cli_args = codex_cli["args"]
    if "timeout" in codex_cli:
        cfg.codex_cli_timeout = codex_cli["timeout"]

    return cfg
