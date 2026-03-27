"""Dashboard screen — shows session history and challenge stats."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from mockr.tui.widgets.score_panel import _render_bar

_DEFAULT_DB = Path.home() / ".mockr" / "mockr.db"


class DashboardScreen(Screen):
    """Session history and challenge stats dashboard."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("r", "refresh", "Refresh"),
    ]

    CSS = """
    DashboardScreen {
        layout: vertical;
    }

    #dash-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        height: 3;
        content-align: center middle;
        background: $surface-darken-1;
    }

    #stats-row {
        layout: horizontal;
        height: 1fr;
        margin: 1 1 0 1;
    }

    #sessions-panel {
        width: 1fr;
        border: round $primary;
        padding: 0;
        margin: 0 1 0 0;
    }

    #challenge-panel {
        width: 1fr;
        border: round $accent;
        padding: 0;
    }

    .panel-header {
        background: $surface-darken-1;
        color: $text-muted;
        text-style: bold;
        padding: 0 1;
        height: 1;
    }

    #sessions-table {
        height: 1fr;
    }

    #challenges-table {
        height: 1fr;
    }

    #plan-panel {
        height: 10;
        border: round $success;
        padding: 0;
        margin: 1;
    }

    #plan-table {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("mockr — Dashboard", id="dash-title")

        with Horizontal(id="stats-row"):
            with Vertical(id="sessions-panel"):
                yield Static("Recent Sessions", classes="panel-header")
                yield DataTable(id="sessions-table", zebra_stripes=True)

            with Vertical(id="challenge-panel"):
                yield Static("Challenge Stats  [R to refresh]", classes="panel-header")
                yield DataTable(id="challenges-table", zebra_stripes=True)

        with Vertical(id="plan-panel"):
            yield Static("Practice Plan", classes="panel-header")
            yield DataTable(id="plan-table", zebra_stripes=True)

        yield Footer()

    def on_mount(self) -> None:
        self._setup_tables()
        self._load_data()

    def _setup_tables(self) -> None:
        sessions_table = self.query_one("#sessions-table", DataTable)
        sessions_table.add_columns("Mode", "Challenge", "Level", "Score", "State", "Date")

        challenges_table = self.query_one("#challenges-table", DataTable)
        challenges_table.add_columns("Challenge", "Level", "Attempts", "Avg Score", "Next Review")

        plan_table = self.query_one("#plan-table", DataTable)
        plan_table.add_columns("Dimension", "Mode", "Priority", "Gap", "Challenge", "Status")

    def _load_data(self) -> None:
        try:
            from mockr.core.progress.store import ProgressStore

            store = ProgressStore(_DEFAULT_DB)
            self._load_sessions(store)
            self._load_challenges(store)
            self._load_plan(store)
            store.close()
        except Exception as exc:
            sessions_table = self.query_one("#sessions-table", DataTable)
            sessions_table.add_row("[red]Error loading data[/red]", str(exc), "", "", "", "")

    def _load_sessions(self, store) -> None:
        sessions_table = self.query_one("#sessions-table", DataTable)
        sessions = store.list_sessions(limit=30)
        if not sessions:
            sessions_table.add_row("[dim]No sessions yet[/dim]", "", "", "", "", "")
            return
        for s in sessions:
            score = f"{s['overall_score']:.1f}" if s.get("overall_score") else "-"
            date = (s.get("started_at") or "")[:10]
            sessions_table.add_row(
                s.get("mode", "-"),
                s.get("challenge_id", "-"),
                s.get("level", "-"),
                score,
                s.get("state", "-"),
                date,
            )

    def _load_challenges(self, store) -> None:
        challenges_table = self.query_one("#challenges-table", DataTable)
        stats = store.get_all_challenge_stats()
        if not stats:
            challenges_table.add_row("[dim]No challenge history yet[/dim]", "", "", "", "")
            return
        for s in stats:
            avg = f"{s['avg_score']:.1f}" if s.get("avg_score") else "-"
            next_review = (s.get("next_review") or "")[:10] or "now"
            challenges_table.add_row(
                s.get("challenge_id", "-"),
                s.get("level", "-"),
                str(s.get("times_attempted", 0)),
                avg,
                next_review,
            )

    def _load_plan(self, store) -> None:
        plan_table = self.query_one("#plan-table", DataTable)
        plan = store.get_latest_practice_plan()
        if not plan:
            plan_table.add_row("[dim]No practice plan yet[/dim]", "", "", "", "", "")
            return
        items = store.get_plan_items(plan["id"])
        if not items:
            plan_table.add_row("[dim]Plan has no items[/dim]", "", "", "", "", "")
            return
        status_colors = {"validated": "green", "in_progress": "yellow"}
        for item in items:
            status = item.get("status", "pending")
            color = status_colors.get(status, "")
            priority_bar = _render_bar(item.get("priority", 0.0), max_score=1.0)
            gap = f"{item.get('gap_size', 0.0):.2f}"
            status_display = f"[{color}]{status}[/{color}]" if color else status
            plan_table.add_row(
                item.get("dimension", "-"),
                item.get("mode", "-"),
                priority_bar,
                gap,
                item.get("challenge_id") or "-",
                status_display,
            )

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_refresh(self) -> None:
        sessions_table = self.query_one("#sessions-table", DataTable)
        challenges_table = self.query_one("#challenges-table", DataTable)
        plan_table = self.query_one("#plan-table", DataTable)
        sessions_table.clear()
        challenges_table.clear()
        plan_table.clear()
        self._load_data()
