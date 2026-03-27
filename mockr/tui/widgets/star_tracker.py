"""STAR tracker widget — shows S/T/A/R coverage based on dimension scores."""

from __future__ import annotations

from textual.widgets import Static

# Behavioral scoring dimensions map to STAR elements
_STAR_DIMS = {
    "situation": "Situation",
    "task": "Task",
    "action": "Action",
    "result": "Result",
    "impact": "Impact",
}

_THRESHOLD = 2.5  # Score above this counts as "covered"


def _star_icon(score: float | None) -> str:
    if score is None:
        return "[dim]○[/dim]"
    return "[green]✓[/green]" if score >= _THRESHOLD else "[red]○[/red]"


class STARTracker(Static):
    """Displays coverage of STAR elements from dimension scores."""

    DEFAULT_CSS = """
    STARTracker {
        width: 100%;
        height: 100%;
        padding: 1;
        overflow: auto auto;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._scores: dict[str, float] = {}
        self._feedback: str = ""

    def on_mount(self) -> None:
        self._render()

    def update_scores(
        self,
        dimensions: dict[str, float],
        strengths: list[str],
        improvements: list[str],
    ) -> None:
        self._scores = dimensions
        parts: list[str] = []
        if strengths:
            parts.append("Strong: " + "; ".join(strengths[:2]))
        if improvements:
            parts.append("Improve: " + "; ".join(improvements[:2]))
        self._feedback = "  ".join(parts)
        self._render()

    def _render(self) -> None:
        parts: list[str] = []

        # STAR elements row
        elements: list[str] = []
        for dim_key, label in _STAR_DIMS.items():
            score = self._scores.get(dim_key)
            icon = _star_icon(score)
            score_str = f"({score:.0f})" if score is not None else ""
            elements.append(f"{icon} {label}{score_str}")
        parts.append("  ".join(elements))

        # Feedback line
        if self._feedback:
            parts.append("")
            parts.append(f"[dim]{self._feedback}[/dim]")
        elif not self._scores:
            parts.append("")
            parts.append("[dim]STAR scores will appear after your first submission[/dim]")

        self.update("\n".join(parts))
