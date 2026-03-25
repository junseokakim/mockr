"""Debrief screen — shown after an interview ends."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from mockr.tui.widgets.score_panel import ScorePanel


class DebriefScreen(Screen):
    """Final debrief with overall score, dimension breakdown, and summary."""

    BINDINGS = [
        Binding("escape", "go_home", "Home"),
        Binding("n", "new_session", "New Session"),
    ]

    CSS = """
    DebriefScreen {
        align: center middle;
    }

    #debrief-container {
        width: 70;
        height: auto;
        max-height: 90%;
        border: round $primary;
        padding: 1 2;
        overflow: auto auto;
    }

    #debrief-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        padding: 0 0 1 0;
    }

    #overall-score {
        text-align: center;
        text-style: bold;
        padding: 1 0;
    }

    #summary-text {
        padding: 1 0;
        border: round $surface-lighten-1;
        margin: 1 0;
    }

    #debrief-buttons {
        layout: horizontal;
        height: auto;
        align: center middle;
        margin: 1 0 0 0;
    }

    #debrief-buttons Button {
        margin: 0 1;
    }

    .section-label {
        text-style: bold;
        color: $text-muted;
        margin: 1 0 0 0;
    }
    """

    def __init__(
        self,
        overall_score: float,
        dimension_scores: dict[str, float],
        summary: str,
        mode: str = "system-design",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._overall = overall_score
        self._dimensions = dimension_scores
        self._summary = summary
        self._mode = mode

    def compose(self) -> ComposeResult:
        yield Header()

        # Pick a color based on score
        score_color = "green" if self._overall >= 4.0 else ("yellow" if self._overall >= 3.0 else "red")
        stars = self._score_to_stars(self._overall)

        with Container(id="debrief-container"):
            yield Static("Interview Complete", id="debrief-title")
            yield Static(
                f"[{score_color}]{stars}  {self._overall:.1f} / 5.0[/{score_color}]",
                id="overall-score",
            )

            yield Static("Dimension Scores", classes="section-label")
            yield ScorePanel(id="score-breakdown")

            yield Static("Summary", classes="section-label")
            yield Static(self._summary, id="summary-text")

            with Vertical(id="debrief-buttons"):
                yield Button("New Session  [N]", id="btn-new", variant="primary")
                yield Button("Home  [Esc]", id="btn-home", variant="default")

        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#score-breakdown", ScorePanel).update_scores(
            dimensions=self._dimensions,
            strengths=[],
            improvements=[],
        )

    def _score_to_stars(self, score: float) -> str:
        filled = round(score)
        return "★" * filled + "☆" * (5 - filled)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "btn-new":
                self.action_new_session()
            case "btn-home":
                self.action_go_home()

    def action_go_home(self) -> None:
        # Pop until only the Home screen remains on the stack
        while len(self.app.screen_stack) > 1:
            self.app.pop_screen()

    def action_new_session(self) -> None:
        from mockr.tui.screens.setup import SetupScreen
        while len(self.app.screen_stack) > 1:
            self.app.pop_screen()
        self.app.push_screen(SetupScreen())
