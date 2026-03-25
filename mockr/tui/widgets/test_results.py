"""Test results widget — shows pass/fail for each test case."""
from __future__ import annotations

from textual.widgets import Static

from mockr.core.events import ExecutionResult, TestResult


class TestResultsPanel(Static):
    """Displays per-test-case pass/fail after code execution."""

    DEFAULT_CSS = """
    TestResultsPanel {
        width: 100%;
        height: 100%;
        padding: 1;
        overflow: auto auto;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._result: ExecutionResult | None = None

    def on_mount(self) -> None:
        self.update("[dim]Run your code with Ctrl+R to see test results[/dim]")

    def show_result(self, result: ExecutionResult) -> None:
        self._result = result
        lines: list[str] = []

        summary_color = "green" if result.failed == 0 else "red"
        lines.append(
            f"[{summary_color}]{result.passed}/{result.total} passed[/{summary_color}]"
            f"  ({result.execution_time_ms}ms)"
        )
        lines.append("")

        for detail in result.test_details:
            if detail.hidden:
                icon = "[dim]?[/dim]"
                label = f"Test {detail.case_index + 1} (hidden)"
                status = "[green]pass[/green]" if detail.passed else "[red]fail[/red]"
                lines.append(f"  {icon} {label}  {status}")
            elif detail.passed:
                lines.append(f"  [green]✓[/green] Test {detail.case_index + 1}")
            else:
                lines.append(f"  [red]✗[/red] Test {detail.case_index + 1}")
                if detail.expected:
                    lines.append(f"    [dim]expected:[/dim] {detail.expected[:60]}")
                if detail.actual:
                    lines.append(f"    [dim]actual:  [/dim] {detail.actual[:60]}")

        if result.stderr:
            lines.append("")
            lines.append("[red]stderr:[/red]")
            for line in result.stderr.splitlines()[:5]:
                lines.append(f"  [red]{line}[/red]")

        self.update("\n".join(lines))

    def show_running(self) -> None:
        self.update("[dim]Running tests…[/dim]")

    def show_error(self, message: str) -> None:
        self.update(f"[red]Execution error:[/red]\n{message}")
