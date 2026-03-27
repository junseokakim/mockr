"""Diagram viewer widget — parses DSL and renders ASCII art."""

from __future__ import annotations

from textual.widgets import Static

from mockr.core.diagrams.ascii_renderer import render_ascii
from mockr.core.diagrams.parser import parse_dsl


class DiagramViewer(Static):
    """Renders an ASCII diagram from DSL text."""

    DEFAULT_CSS = """
    DiagramViewer {
        width: 100%;
        height: 100%;
        overflow: auto auto;
        padding: 1;
        color: $text;
    }
    """

    def __init__(self, dsl: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._dsl = dsl

    def on_mount(self) -> None:
        if self._dsl:
            self.render_dsl(self._dsl)
        else:
            self.update("[dim]No diagram yet — use Ctrl+D to update from your answer[/dim]")

    def render_dsl(self, dsl: str) -> None:
        """Parse DSL text and update the display. No-ops if DSL is unchanged."""
        if dsl == self._dsl:
            return
        self._dsl = dsl
        if not dsl.strip():
            self.update("[dim]Empty diagram[/dim]")
            return
        try:
            diagram = parse_dsl(dsl)
            if not diagram.nodes:
                self.update("[dim]No nodes found in DSL[/dim]")
                return
            ascii_art = render_ascii(diagram)
            self.update(ascii_art or "[dim]Could not render diagram[/dim]")
        except Exception as exc:
            self.update(f"[red]Diagram error: {exc}[/red]")
