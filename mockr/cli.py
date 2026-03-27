"""CLI entry point for mockr."""

from pathlib import Path

import click


@click.group(invoke_without_command=True)
@click.option("--mode", type=click.Choice(["system-design", "coding", "behavioral", "full-loop"]), default=None)
@click.option("--level", type=click.Choice(["mid", "senior", "staff", "principal"]), default=None)
@click.option("--lang", type=click.Choice(["python", "sql", "rust", "javascript"]), default=None)
@click.option("--provider", type=str, default=None)
@click.option("--model", type=str, default=None)
@click.pass_context
def main(ctx, mode, level, lang, provider, model):
    """mockr — Terminal-native AI mock interview tool."""
    if ctx.invoked_subcommand is None:
        # Launch TUI
        from mockr.tui.app import MockrApp

        app = MockrApp()
        app.run()


@main.command()
def practice():
    """Start next due review (spaced repetition picks the challenge)."""
    from mockr.tui.app import MockrApp

    app = MockrApp()
    app.run()


@main.command()
def dashboard():
    """Show progress dashboard."""
    from mockr.tui.app import MockrApp

    app = MockrApp()
    app.run()


@main.command()
@click.option("--format", "fmt", type=click.Choice(["json", "csv"]), default="json")
@click.option("--output", "-o", type=click.Path(), default=None)
def export(fmt, output):
    """Export progress data."""
    from mockr.core.progress.export import export_data

    result = export_data(fmt, output)
    click.echo(result)


@main.command("challenge")
@click.argument("action", type=click.Choice(["validate"]))
@click.argument("path", type=click.Path(exists=True))
def challenge_cmd(action, path):
    """Challenge management commands."""
    if action == "validate":
        from mockr.core.challenges.loader import load_challenge, validate_challenge

        ch = load_challenge(Path(path))
        errors = validate_challenge(ch)
        if errors:
            for e in errors:
                click.echo(f"ERROR: {e}", err=True)
            raise SystemExit(1)
        else:
            click.echo(f"OK: {ch.title} ({ch.id}) — {len(ch.levels)} levels defined")
