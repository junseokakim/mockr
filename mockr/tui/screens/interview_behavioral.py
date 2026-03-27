"""Behavioral interview screen."""

from __future__ import annotations

import asyncio
import random

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Static, TextArea

from mockr.core.events import EventBus, QuestionReady, ScoreReady
from mockr.core.sessions.session import Session
from mockr.tui.screens._interview_base import BaseInterviewScreen, _build_orchestrator
from mockr.tui.widgets.star_tracker import STARTracker
from mockr.tui.widgets.timer import TimerWidget

_BEHAVIORAL_HINTS = [
    "Use STAR: Situation \u2192 Task \u2192 Action \u2192 Result",
    "Quantify your impact where possible (e.g., reduced latency by 30%)",
    "Focus on YOUR specific actions, not the team's",
    "Conclude with a clear outcome or lesson learned",
]


class BehavioralInterviewScreen(BaseInterviewScreen):
    """
    Layout:
        ┌─ Turn N ── Behavioral ── Challenge ── Level ─┐
        │ ┌─ Interviewer ──────────────────────────────┐│
        │ │  Question text                             ││
        │ └────────────────────────────────────────────┘│
        │ ┌─ STAR Tracker ─────────────────────────────┐│
        │ │  Situation ✓  Task ✓  Action ○  Result ○   ││
        │ │  Coach feedback                            ││
        │ └────────────────────────────────────────────┘│
        │ ┌─ Your Answer ──────────────────────────────┐│
        │ │  TextArea                                  ││
        │ └────────────────────────────────────────────┘│
        └────────────────────────────────────────────────┘
    """

    BINDINGS = [
        Binding("ctrl+enter", "submit_answer", "Submit"),
        Binding("ctrl+h", "request_hint", "Hint"),
        Binding("ctrl+p", "toggle_pause", "Pause"),
        Binding("escape", "end_interview", "End"),
    ]

    CSS = """
    BehavioralInterviewScreen {
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

    #interviewer-panel {
        height: 8;
        border: round $primary;
        margin: 0 1;
        padding: 1;
        overflow: auto auto;
    }

    #star-panel {
        height: 8;
        border: round $accent;
        margin: 0 1;
        padding: 0;
    }

    #answer-panel {
        height: 1fr;
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
    """

    def __init__(self, session: Session, challenge, bus: EventBus, **kwargs) -> None:
        super().__init__(session=session, challenge=challenge, bus=bus, **kwargs)

        bus.subscribe(QuestionReady, self._on_question_ready)
        bus.subscribe(ScoreReady, self._on_score_ready)
        self._orchestrator = _build_orchestrator(session, challenge, bus, mode_override="behavioral")

    def compose(self) -> ComposeResult:
        yield Header()
        challenge_name = self._challenge.title if self._challenge else "Behavioral"
        level = self._session.level.value.capitalize()

        with Horizontal(id="top-bar"):
            yield TimerWidget(
                total_seconds=self._session.timer_minutes * 60,
                session_id=self._session.id,
                bus=self._bus,
                id="timer-widget",
            )
            yield Static(
                f"  Turn 0  \u00b7  Behavioral  \u00b7  {challenge_name}  \u00b7  {level}",
                id="top-info",
            )
            yield Static("", id="status-bar")

        with Vertical(id="interviewer-panel"):
            yield Static("Interviewer", classes="panel-header")
            yield Static("Starting interview\u2026", id="interviewer-text")

        with Vertical(id="star-panel"):
            yield Static("STAR Tracker", classes="panel-header")
            yield STARTracker(id="star-tracker")

        with Vertical(id="answer-panel"):
            yield Static(
                "Your Answer  [Ctrl+Enter=Submit  Ctrl+H=Hint  Esc=End]",
                classes="panel-header",
            )
            yield TextArea(id="answer-area")

        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#timer-widget", TimerWidget).start()
        self.query_one("#answer-area", TextArea).focus()
        self.run_worker(self._start_interview(), exclusive=True)

    def _update_top_info(self) -> None:
        challenge_name = self._challenge.title if self._challenge else "Behavioral"
        level = self._session.level.value.capitalize()
        self.query_one("#top-info", Static).update(
            f"  Turn {self._session.turn_number}  \u00b7  Behavioral  \u00b7  {challenge_name}  \u00b7  {level}"
        )

    # ── Event handlers ───────────────────────────────────────────────────────

    def _on_question_ready(self, event: QuestionReady) -> None:
        self.call_from_thread(self._update_question, event)

    def _update_question(self, event: QuestionReady) -> None:
        self._update_top_info()
        self.query_one("#interviewer-text", Static).update(event.interviewer_text)
        self._set_thinking(False)
        answer_area = self.query_one("#answer-area", TextArea)
        answer_area.load_text("")
        answer_area.focus()

    def _on_score_ready(self, event: ScoreReady) -> None:
        self.call_from_thread(self._update_star, event)

    def _update_star(self, event: ScoreReady) -> None:
        self.query_one("#star-tracker", STARTracker).update_scores(
            dimensions=event.dimensions,
            strengths=event.strengths,
            improvements=event.improvements,
        )

    # ── Actions ──────────────────────────────────────────────────────────────

    def action_submit_answer(self) -> None:
        answer = self.query_one("#answer-area", TextArea).text.strip()
        if not answer:
            self._set_status("Write your answer first!")
            return
        self._set_thinking(True)
        self.run_worker(self._orchestrator.process_answer(answer), exclusive=True)

    def action_request_hint(self) -> None:
        self.run_worker(self._fetch_hint(), exclusive=False)

    def _default_hint(self) -> str:
        return random.choice(_BEHAVIORAL_HINTS)

    async def _fetch_hint(self) -> None:
        self._set_status("Fetching hint\u2026")
        await asyncio.sleep(0.3)
        self._set_status(f"Hint: {self._resolve_hint()}")
