"""System Design interview screen."""

from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Header, Static, TextArea

from mockr.core.diagrams.parser import parse_dsl
from mockr.core.events import EventBus, QuestionReady, ScoreReady
from mockr.core.sessions.session import Session
from mockr.tui.screens._interview_base import BaseInterviewScreen, _build_orchestrator
from mockr.tui.widgets.diagram_viewer import DiagramViewer
from mockr.tui.widgets.score_panel import ScorePanel
from mockr.tui.widgets.timer import TimerWidget


class SysDesignInterviewScreen(BaseInterviewScreen):
    """
    Layout:
        ┌─ Timer ──────────────────────────────────────┐
        │ ┌─ Interviewer ────┐ ┌─ Diagram ───────────┐ │
        │ │  Q + coach text  │ │  ASCII diagram      │ │
        │ └──────────────────┘ └─────────────────────┘ │
        │ ┌─ Score ──────────────────────────────────┐ │
        │ │  Dimension bars                          │ │
        │ └──────────────────────────────────────────┘ │
        │ ┌─ Your Answer ────────────────────────────┐ │
        │ │  TextArea                                │ │
        │ └──────────────────────────────────────────┘ │
        └──────────────────────────────────────────────┘
    """

    BINDINGS = [
        Binding("ctrl+enter", "submit_answer", "Submit"),
        Binding("ctrl+d", "update_diagram", "Update Diagram"),
        Binding("ctrl+h", "request_hint", "Hint"),
        Binding("ctrl+p", "toggle_pause", "Pause"),
        Binding("escape", "end_interview", "End"),
    ]

    CSS = """
    SysDesignInterviewScreen {
        layout: vertical;
    }

    #top-bar {
        layout: horizontal;
        height: 3;
        background: $surface-darken-1;
        padding: 0 1;
        align: left middle;
    }

    #timer-widget {
        width: 10;
        height: 1;
        color: $accent;
        text-style: bold;
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
        height: 1fr;
        margin: 0;
    }

    #interviewer-panel {
        width: 1fr;
        border: round $primary;
        margin: 0 0 0 1;
        padding: 1;
        overflow: auto auto;
    }

    #diagram-panel {
        width: 1fr;
        border: round $accent;
        margin: 0 1 0 0;
        padding: 0;
        overflow: auto auto;
    }

    #score-row {
        height: 10;
        margin: 0 1;
        border: round $surface-lighten-1;
    }

    #answer-panel {
        height: 10;
        border: round $success;
        margin: 0 1;
        padding: 0;
    }

    #answer-area {
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

    def __init__(self, session: Session, challenge, bus: EventBus, **kwargs) -> None:
        super().__init__(session=session, challenge=challenge, bus=bus, **kwargs)
        bus.subscribe(QuestionReady, self._on_question_ready)
        bus.subscribe(ScoreReady, self._on_score_ready)
        self._orchestrator = _build_orchestrator(session, challenge, bus)

    def compose(self) -> ComposeResult:
        yield Header()
        challenge_name = self._challenge.title if self._challenge else "System Design"
        level = self._session.level.value.capitalize()

        with Horizontal(id="top-bar"):
            yield TimerWidget(
                total_seconds=self._session.timer_minutes * 60,
                session_id=self._session.id,
                bus=self._bus,
                id="timer-widget",
            )
            yield Static(
                f"  System Design  \u00b7  {challenge_name}  \u00b7  {level}",
                id="top-info",
            )
            yield Static("", id="status-bar")

        with Horizontal(id="middle-row"):
            with Vertical(id="interviewer-panel"):
                yield Static("Interviewer", classes="panel-header")
                yield Static("Starting interview\u2026", id="interviewer-text")
                yield Static("", id="coach-text")

            with Vertical(id="diagram-panel"):
                yield Static("Diagram  [Ctrl+D to update]", classes="panel-header")
                yield DiagramViewer(id="diagram-viewer")

        with Container(id="score-row"):
            yield ScorePanel(id="score-panel")

        with Vertical(id="answer-panel"):
            yield Static(
                "Your Answer  [Ctrl+Enter=Submit  Ctrl+D=Diagram  Ctrl+H=Hint  Esc=End]",
                classes="panel-header",
            )
            yield TextArea(id="answer-area", language=None)

        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#timer-widget", TimerWidget).start()
        self.query_one("#answer-area", TextArea).focus()
        self.run_worker(self._start_interview(), exclusive=True)

    # ── Event handlers ───────────────────────────────────────────────────────

    def _on_question_ready(self, event: QuestionReady) -> None:
        self.call_from_thread(self._update_question, event)

    def _update_question(self, event: QuestionReady) -> None:
        self.query_one("#interviewer-text", Static).update(event.interviewer_text)
        coach = self.query_one("#coach-text", Static)
        coach.update(f"Coach: {event.coach_text}" if event.coach_text else "")
        self._set_thinking(False)
        self.query_one("#answer-area", TextArea).focus()

    def _on_score_ready(self, event: ScoreReady) -> None:
        self.call_from_thread(self._update_scores, event)

    def _update_scores(self, event: ScoreReady) -> None:
        self.query_one("#score-panel", ScorePanel).update_scores(
            dimensions=event.dimensions,
            strengths=event.strengths,
            improvements=event.improvements,
        )

    # ── Actions ─────────────────────────────────────────────────────────────

    def action_submit_answer(self) -> None:
        answer = self.query_one("#answer-area", TextArea).text.strip()
        if not answer:
            self._set_status("Write something first!")
            return
        self._set_thinking(True)
        self.run_worker(self._submit(answer), exclusive=True)

    @staticmethod
    def _extract_diagram_dsl(text: str) -> str | None:
        """Extract DSL from a ```diagram ... ``` block, or return None."""
        if "```diagram" not in text:
            return None
        try:
            start = text.index("```diagram") + len("```diagram")
            end = text.index("```", start)
            return text[start:end].strip()
        except ValueError:
            return None

    async def _submit(self, answer: str) -> None:
        dsl_text = self._extract_diagram_dsl(answer)
        diagram = parse_dsl(dsl_text) if dsl_text else None
        await self._orchestrator.process_answer(answer, diagram=diagram)

    def action_update_diagram(self) -> None:
        text = self.query_one("#answer-area", TextArea).text
        dsl_text = self._extract_diagram_dsl(text) or text
        self.query_one("#diagram-viewer", DiagramViewer).render_dsl(dsl_text)

    def action_request_hint(self) -> None:
        self.run_worker(self._fetch_hint(), exclusive=False)

    def _default_hint(self) -> str:
        return "Consider the scale requirements and failure modes."

    async def _fetch_hint(self) -> None:
        self._set_status("Fetching hint\u2026")
        await asyncio.sleep(0.3)
        self.query_one("#coach-text", Static).update(f"Coach: {self._resolve_hint()}")
        self._set_status("")
