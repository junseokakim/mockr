"""Main Textual application for mockr."""
from __future__ import annotations

from textual.app import App
from textual.binding import Binding

from mockr.tui.screens.home import HomeScreen


class MockrApp(App):
    """The mockr terminal interview trainer."""

    TITLE = "mockr"
    CSS = """
    Screen {
        background: $surface;
    }

    Button {
        margin: 0 1;
    }

    .muted {
        color: $text-muted;
    }

    .success {
        color: $success;
    }

    .warning {
        color: $warning;
    }

    .error {
        color: $error;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    def on_mount(self) -> None:
        self.push_screen(HomeScreen())
