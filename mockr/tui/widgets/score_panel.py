"""Score panel widget — shows dimension scores after each turn."""

from __future__ import annotations

from textual.widgets import Static

_BAR_WIDTH = 10
_BAR_FILL = "█"
_BAR_EMPTY = "░"


def _render_bar(score: float, max_score: float = 5.0) -> str:
    filled = round((score / max_score) * _BAR_WIDTH)
    return _BAR_FILL * filled + _BAR_EMPTY * (_BAR_WIDTH - filled)


class ScorePanel(Static):
    """Displays dimension scores as labelled bar-charts."""

    DEFAULT_CSS = """
    ScorePanel {
        width: 100%;
        height: 100%;
        padding: 1;
        overflow: auto auto;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._dimensions: dict[str, float] = {}
        self._strengths: list[str] = []
        self._improvements: list[str] = []

    def on_mount(self) -> None:
        self.update_display()

    def update_scores(
        self,
        dimensions: dict[str, float],
        strengths: list[str],
        improvements: list[str],
    ) -> None:
        self._dimensions = dimensions
        self._strengths = strengths
        self._improvements = improvements
        self.update_display()

    def update_display(self) -> None:
        if not self._dimensions:
            self.update("[dim]Scores will appear after your first submission[/dim]")
            return

        lines: list[str] = []

        for dim, score in self._dimensions.items():
            bar = _render_bar(score)
            lines.append(f"[dim]{dim:<16}[/dim][primary]{bar}[/primary] [accent]{score:.1f}[/accent]")

        if self._strengths:
            lines.append("")
            lines.append("[bold green]Strengths:[/bold green]")
            for s in self._strengths:
                lines.append(f"  [green]+ {s}[/green]")

        if self._improvements:
            lines.append("")
            lines.append("[bold yellow]Improve:[/bold yellow]")
            for i in self._improvements:
                lines.append(f"  [yellow]▶ {i}[/yellow]")

        self.update("\n".join(lines))
