"""CLI entry point for mockr."""

from pathlib import Path

import click


@click.group(invoke_without_command=True)
@click.option("--mode", type=click.Choice(["system-design", "coding", "behavioral", "full-loop"]), default=None)
@click.option(
    "--level",
    type=click.Choice(["intern", "junior", "mid", "senior", "staff", "principal"]),
    default=None,
)
@click.option("--lang", type=click.Choice(["python", "sql", "rust", "javascript"]), default=None)
@click.option("--provider", type=str, default=None)
@click.option("--model", type=str, default=None)
@click.pass_context
def main(ctx, mode, level, lang, provider, model):
    """mockr — Terminal-native AI mock interview tool."""
    if ctx.invoked_subcommand is None:
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


@main.command()
@click.option(
    "--target",
    type=click.Choice(["intern", "junior", "mid", "senior", "staff", "principal"]),
    required=True,
    help="Target level to assess against.",
)
def assess(target):
    """Run a diagnostic assessment to baseline your current level."""
    click.echo(f"Starting diagnostic assessment (target: {target})...")
    click.echo("This will run 3 mini-interviews: coding, system design, and behavioral.")
    click.echo("Use 'mockr assess --target <level>' in TUI mode for the full experience.")
    from mockr.tui.app import MockrApp

    app = MockrApp()
    app.run()


@main.command()
@click.option("--jd", type=str, default=None, help="Paste job description text directly.")
@click.option("--jd-file", type=click.Path(exists=True), default=None, help="Path to a JD text file.")
@click.option("--url", type=str, default=None, help="URL to fetch JD from.")
@click.option("--list", "list_profiles", is_flag=True, help="List saved role profiles.")
@click.option("--refresh-intel", is_flag=True, help="Re-fetch interview intel for current role.")
def prep(jd, jd_file, url, list_profiles, refresh_intel):
    """Parse a job description and create a role-specific prep plan."""
    if list_profiles:
        from mockr.core.progress.store import ProgressStore

        store = ProgressStore(Path.home() / ".mockr" / "mockr.db")
        profiles = store.list_role_profiles()
        if not profiles:
            click.echo("No saved role profiles. Use 'mockr prep --jd <text>' to create one.")
            return
        for p in profiles:
            click.echo(f"  {p['id'][:8]}  {p['role_title']} @ {p['company'] or 'Unknown'} ({p['inferred_level']})")
        store.close()
        return

    if not jd and not jd_file and not url and not refresh_intel:
        click.echo("Provide a JD via --jd, --jd-file, or --url. Run 'mockr prep --help' for details.")
        return

    jd_text = jd
    if jd_file:
        jd_text = Path(jd_file).read_text()
    if url:
        click.echo(f"Fetching JD from {url}...")
        click.echo("URL fetching is available in TUI mode. Use 'mockr' to launch.")
        return

    if jd_text:
        click.echo("Parsing job description...")
        click.echo("For full interactive prep experience, launch TUI mode with 'mockr'.")
    elif refresh_intel:
        click.echo("Refreshing interview intel...")

    from mockr.tui.app import MockrApp

    app = MockrApp()
    app.run()


@main.command()
@click.option("--role", type=str, default=None, help="Filter plan by role profile ID.")
def plan(role):
    """View your current practice plan."""
    from mockr.core.progress.store import ProgressStore

    store = ProgressStore(Path.home() / ".mockr" / "mockr.db")
    click.echo("Practice Plan")
    click.echo("=" * 50)
    click.echo("Run 'mockr assess --target <level>' first to generate a plan.")
    click.echo("Or launch TUI with 'mockr' for the full dashboard.")
    store.close()
