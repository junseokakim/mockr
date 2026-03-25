from __future__ import annotations

from pathlib import Path

from mockr.config import MockrConfig, load_config


class TestConfig:
    def test_default_config(self) -> None:
        cfg = MockrConfig()
        assert cfg.provider == "ollama"
        assert cfg.level == "senior"
        assert cfg.max_history_turns == 8

    def test_load_from_toml(self, tmp_path: Path) -> None:
        toml_path = tmp_path / "config.toml"
        toml_path.write_text(
            '[llm]\nprovider = "claude-cli"\n\n[profile]\nlevel = "staff"\n'
        )
        cfg = load_config(toml_path)
        assert cfg.provider == "claude-cli"
        assert cfg.level == "staff"

    def test_load_missing_file_returns_defaults(self, tmp_path: Path) -> None:
        cfg = load_config(tmp_path / "nonexistent.toml")
        assert cfg.provider == "ollama"

    def test_provider_specific_config(self, tmp_path: Path) -> None:
        toml_path = tmp_path / "config.toml"
        toml_path.write_text(
            '[llm]\nprovider = "ollama"\n\n[llm.ollama]\nbase_url = "http://localhost:11434"\nmodel = "llama3"\n'
        )
        cfg = load_config(toml_path)
        assert cfg.ollama_base_url == "http://localhost:11434"
        assert cfg.ollama_model == "llama3"

    def test_cli_provider_config(self, tmp_path: Path) -> None:
        toml_path = tmp_path / "config.toml"
        toml_path.write_text(
            '[llm]\nprovider = "claude-cli"\n\n[llm.claude-cli]\ncommand = "claude"\ntimeout = 120\n'
        )
        cfg = load_config(toml_path)
        assert cfg.claude_cli_command == "claude"
        assert cfg.claude_cli_timeout == 120
