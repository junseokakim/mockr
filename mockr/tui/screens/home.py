"""Home screen — mockr entry point."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

LOGO = """\
  _ __ ___   ___   ___| | ___ __
 | '_ ` _ \\ / _ \\ / __| |/ / '__|
 | | | | | | (_) | (__|   <| |
 |_| |_| |_|\\___/ \\___|_|\\_\\_|
"""

TAGLINE = "terminal mock interviews · system design · coding · behavioral"


class HomeScreen(Screen):
    """The mockr home screen."""

    BINDINGS = [
        Binding("n", "new_session", "New Session"),
        Binding("p", "practice", "Practice"),
        Binding("d", "dashboard", "Dashboard"),
        Binding("q", "app.quit", "Quit"),
    ]

    CSS = """
    HomeScreen {
        align: center middle;
    }

    #home-container {
        width: 60;
        height: auto;
        align: center middle;
    }

    #logo {
        text-align: center;
        color: $primary;
        text-style: bold;
        padding: 1 0;
    }

    #tagline {
        text-align: center;
        color: $text-muted;
        padding: 0 0 2 0;
    }

    #home-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        layout: vertical;
    }

    #home-buttons Button {
        width: 40;
        margin: 0 0 1 0;
    }

    #version-label {
        text-align: center;
        color: $text-disabled;
        padding: 2 0 0 0;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="home-container"):
            yield Static(LOGO, id="logo")
            yield Static(TAGLINE, id="tagline")
            with Vertical(id="home-buttons"):
                yield Button("  New Session  [N]", id="btn-new", variant="primary")
                yield Button("  Practice — Due Reviews  [P]", id="btn-practice", variant="default")
                yield Button("  Dashboard  [D]", id="btn-dashboard", variant="default")
                yield Button("  Quit  [Q]", id="btn-quit", variant="error")
            yield Static("mockr v0.1.0", id="version-label")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "btn-new":
                self.action_new_session()
            case "btn-practice":
                self.action_practice()
            case "btn-dashboard":
                self.action_dashboard()
            case "btn-quit":
                self.app.exit()

    def action_new_session(self) -> None:
        from mockr.tui.screens.setup import SetupScreen
        self.app.push_screen(SetupScreen())

    def action_practice(self) -> None:
        from mockr.tui.screens.setup import SetupScreen
        # Launch setup in practice mode (pre-selected due reviews)
        self.app.push_screen(SetupScreen(practice_mode=True))

    def action_dashboard(self) -> None:
        from mockr.tui.screens.dashboard import DashboardScreen
        self.app.push_screen(DashboardScreen())
