"""Coding interview screen."""

from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Static

from mockr.core.events import EventBus, ExecutionResult, QuestionReady, ScoreReady, TestResult
from mockr.core.execution.engine import ExecutionEngine
from mockr.core.sessions.session import Session
from mockr.tui.screens._interview_base import BaseInterviewScreen, _build_orchestrator
from mockr.tui.widgets.code_editor import CodeEditor
from mockr.tui.widgets.test_results import TestResultsPanel
from mockr.tui.widgets.timer import TimerWidget


class CodingInterviewScreen(BaseInterviewScreen):
    """
    Layout:
        ┌─ Timer ── Language ── Challenge ── Level ────┐
        │ ┌─ Problem ────────┐ ┌─ Test Results ──────┐ │
        │ │  Problem + coach │ │  Pass/fail list     │ │
        │ └──────────────────┘ └─────────────────────┘ │
        │ ┌─ Code Editor ──────────────────────────────┐│
        │ │  TextArea with syntax highlight            ││
        │ └────────────────────────────────────────────┘│
        └────────────────────────────────────────────────┘
    """

    BINDINGS = [
        Binding("ctrl+r", "run_code", "Run"),
        Binding("ctrl+enter", "submit_answer", "Submit"),
        Binding("ctrl+h", "request_hint", "Hint"),
        Binding("ctrl+p", "toggle_pause", "Pause"),
        Binding("escape", "end_interview", "End"),
    ]

    CSS = """
    CodingInterviewScreen {
        layout: vertical;
    }

    #top-bar {
        layout: horizontal;
        height: 3;
        background: $surface-darken-1;
        padding: 0 1;
        align: left middle;
    }

    #top-info {
        width: 1fr;
        color: $text-muted;
        text-align: center;
    }

    #status-bar {
        width: auto;
        color: $text-muted;
    }

    #middle-row {
        layout: horizontal;
        height: 12;
        margin: 0 1;
    }

    #problem-panel {
        width: 1fr;
        border: round $primary;
        padding: 1;
        overflow: auto auto;
    }

    #test-panel {
        width: 1fr;
        border: round $accent;
        padding: 0;
        overflow: auto auto;
    }

    #code-panel {
        height: 1fr;
        border: round $success;
        margin: 0 1;
        padding: 0;
    }

    #code-editor {
        height: 100%;
    }

    .panel-header {
        background: $surface-darken-1;
        color: $text-muted;
        text-style: bold;
        padding: 0 1;
        height: 1;
    }

    #coach-text {
        color: $text-muted;
        text-style: italic;
        margin: 1 0 0 0;
        border-top: dashed $surface-lighten-1;
        padding: 1 0 0 0;
    }
    """

    def __init__(
        self,
        session: Session,
        challenge,
        bus: EventBus,
        language: str = "python",
        **kwargs,
    ) -> None:
        super().__init__(session=session, challenge=challenge, bus=bus, **kwargs)
        self._language = language
        self._engine = ExecutionEngine(timeout=10)

        bus.subscribe(QuestionReady, self._on_question_ready)
        bus.subscribe(ScoreReady, self._on_score_ready)
        bus.subscribe(ExecutionResult, self._on_execution_result)
        self._orchestrator = _build_orchestrator(session, challenge, bus, mode_override="coding")

    def compose(self) -> ComposeResult:
        yield Header()
        challenge_name = self._challenge.title if self._challenge else "Coding"
        level = self._session.level.value.capitalize()
        lang = self._language.capitalize()

        with Horizontal(id="top-bar"):
            yield TimerWidget(
                total_seconds=self._session.timer_minutes * 60,
                session_id=self._session.id,
                bus=self._bus,
                id="timer-widget",
            )
            yield Static(
                f"  {lang}  \u00b7  {challenge_name}  \u00b7  {level}",
                id="top-info",
            )
            yield Static("", id="status-bar")

        with Horizontal(id="middle-row"):
            with Vertical(id="problem-panel"):
                yield Static("Problem", classes="panel-header")
                yield Static("Loading problem\u2026", id="problem-text")
                yield Static("", id="coach-text")

            with Vertical(id="test-panel"):
                yield Static("Test Results  [Ctrl+R to run]", classes="panel-header")
                yield TestResultsPanel(id="test-results")

        with Vertical(id="code-panel"):
            yield Static(
                f"Code Editor  [{lang}]  [Ctrl+R=Run  Ctrl+Enter=Submit  Esc=End]",
                classes="panel-header",
            )
            yield CodeEditor(language=self._language, id="code-editor")

        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#timer-widget", TimerWidget).start()
        self.query_one("#code-editor", CodeEditor).focus()
        self.run_worker(self._start_interview(), exclusive=True)

    # ── Event handlers ───────────────────────────────────────────────────────

    def _on_question_ready(self, event: QuestionReady) -> None:
        self.call_from_thread(self._update_question, event)

    def _update_question(self, event: QuestionReady) -> None:
        self.query_one("#problem-text", Static).update(event.interviewer_text)
        coach = self.query_one("#coach-text", Static)
        coach.update(f"Coach: {event.coach_text}" if event.coach_text else "")
        self._set_thinking(False)
        self.query_one("#code-editor", CodeEditor).focus()

    def _on_score_ready(self, event: ScoreReady) -> None:
        self.call_from_thread(self._update_score_status, event)

    def _update_score_status(self, event: ScoreReady) -> None:
        avg = sum(event.dimensions.values()) / max(len(event.dimensions), 1)
        self._set_status(f"Score: {avg:.1f}/5.0")

    def _on_execution_result(self, event: ExecutionResult) -> None:
        self.call_from_thread(self._show_execution_result, event)

    def _show_execution_result(self, event: ExecutionResult) -> None:
        self.query_one("#test-results", TestResultsPanel).show_result(event)
        color = "green" if event.failed == 0 else "red"
        self._set_status(f"[{color}]{event.passed}/{event.total} passed[/{color}]")

    # ── Actions ──────────────────────────────────────────────────────────────

    def action_run_code(self) -> None:
        code = self.query_one("#code-editor", CodeEditor).text
        self.query_one("#test-results", TestResultsPanel).show_running()
        self.run_worker(self._run_code(code), exclusive=False)

    async def _run_code(self, code: str) -> None:
        self._set_status("Running\u2026")
        try:
            event = await self._build_execution_result(code)
            self._bus.emit(event)
        except Exception as exc:
            self.call_from_thread(self.query_one("#test-results", TestResultsPanel).show_error, str(exc))
            self._set_status(f"Error: {exc}")

    async def _build_execution_result(self, code: str) -> ExecutionResult:
        if not self._challenge or not self._challenge.test_cases:
            return ExecutionResult(
                session_id=self._session.id,
                language=self._language,
                passed=0,
                failed=0,
                total=0,
                test_details=[],
                stdout="",
                stderr="No test cases defined for this challenge.",
                exit_code=0,
                execution_time_ms=0,
            )

        if self._language == "python":
            visible = [(i, tc) for i, tc in enumerate(self._challenge.test_cases) if not tc.hidden and tc.input]
            # Wrap each case in try/except so all run independently
            lines = ["_mockr_results = []"]
            for i, tc in visible:
                lines.append("try:")
                lines.append(f"    _actual = str({tc.input})")
                lines.append(
                    f"    _mockr_results.append((_actual == {repr(tc.expected)}, {repr(tc.expected)}, _actual))"
                )
                lines.append("except Exception as _e:")
                lines.append(f"    _mockr_results.append((False, {repr(tc.expected)}, str(_e)))")
            lines.append("import json as _j, sys as _s")
            lines.append("print('MOCKR_RESULTS:' + _j.dumps(_mockr_results))")
            lines.append("_s.exit(0 if all(r[0] for r in _mockr_results) else 1)")

            result = await self._engine.run_python(code, "\n".join(lines))
            total = len(visible)
            details: list[TestResult] = []
            passed = 0

            # Parse per-case results from stdout
            for line in (result.stdout or "").splitlines():
                if line.startswith("MOCKR_RESULTS:"):
                    try:
                        import json

                        parsed = json.loads(line[len("MOCKR_RESULTS:") :])
                        for idx, (ok, expected, actual) in enumerate(parsed):
                            passed += int(ok)
                            details.append(
                                TestResult(
                                    case_index=idx,
                                    passed=ok,
                                    expected=expected,
                                    actual=actual,
                                    hidden=False,
                                )
                            )
                    except (ValueError, IndexError):
                        pass
                    break

            if not details:
                # Fallback if parsing failed
                passed = total if result.exit_code == 0 else 0
                for idx, (_, tc) in enumerate(visible):
                    details.append(
                        TestResult(
                            case_index=idx,
                            passed=result.exit_code == 0,
                            expected=tc.expected,
                            actual="pass" if result.exit_code == 0 else "see stderr",
                            hidden=False,
                        )
                    )

            return ExecutionResult(
                session_id=self._session.id,
                language=self._language,
                passed=passed,
                failed=total - passed,
                total=total,
                test_details=details,
                stdout=result.stdout or "",
                stderr=result.stderr or "",
                exit_code=result.exit_code,
                execution_time_ms=result.execution_time_ms,
            )

        if self._language == "sql" and self._challenge.setup_sql:
            tc = self._challenge.test_cases[0]
            result = await self._engine.run_sql(
                setup_sql=self._challenge.setup_sql,
                query=code,
                expected_columns=tc.expected_columns,
                expected_rows=tc.expected_rows,
                setup_extra=tc.setup_extra,
            )
            passed = 1 if result.passed else 0
            return ExecutionResult(
                session_id=self._session.id,
                language=self._language,
                passed=passed,
                failed=1 - passed,
                total=1,
                test_details=[
                    TestResult(
                        case_index=0,
                        passed=result.passed,
                        expected=str(tc.expected_rows),
                        actual=str(result.actual_rows),
                        hidden=False,
                    )
                ],
                stdout="",
                stderr=result.error or "",
                exit_code=0 if result.passed else 1,
                execution_time_ms=0,
            )

        return ExecutionResult(
            session_id=self._session.id,
            language=self._language,
            passed=0,
            failed=0,
            total=0,
            test_details=[],
            stdout="",
            stderr=f"Execution for {self._language} not available in TUI demo.",
            exit_code=0,
            execution_time_ms=0,
        )

    def action_submit_answer(self) -> None:
        code = self.query_one("#code-editor", CodeEditor).text.strip()
        if not code:
            self._set_status("Write some code first!")
            return
        self._set_thinking(True)
        self.run_worker(self._orchestrator.process_answer(code), exclusive=True)

    def action_request_hint(self) -> None:
        self.run_worker(self._fetch_hint(), exclusive=False)

    def _default_hint(self) -> str:
        return "Think about edge cases \u2014 empty input, single element, duplicates."

    async def _fetch_hint(self) -> None:
        self._set_status("Fetching hint\u2026")
        await asyncio.sleep(0.3)
        self.query_one("#coach-text", Static).update(f"Coach: {self._resolve_hint()}")
        self._set_status("")
