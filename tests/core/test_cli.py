from __future__ import annotations

from click.testing import CliRunner

from mockr.cli import main


class TestCLICommands:
    def test_assess_command_exists(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["assess", "--help"])
        assert result.exit_code == 0
        assert "target" in result.output.lower()

    def test_prep_command_exists(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["prep", "--help"])
        assert result.exit_code == 0
        assert "jd" in result.output.lower() or "url" in result.output.lower()

    def test_plan_command_exists(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["plan", "--help"])
        assert result.exit_code == 0

    def test_level_choices_include_new_levels(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--level", "intern", "--help"])
        assert result.exit_code == 0
