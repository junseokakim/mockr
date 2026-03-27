"""Shared base for all three interview screens."""

from __future__ import annotations

import random

from textual.screen import Screen
from textual.widgets import Static

from mockr.core.events import DebriefReady, EventBus
from mockr.core.scoring.scorer import Scorer
from mockr.core.sessions.orchestrator import TurnOrchestrator
from mockr.core.sessions.session import Session
from mockr.tui.widgets.timer import TimerWidget


def _build_orchestrator(
    session: Session,
    challenge,
    bus: EventBus,
    mode_override: str | None = None,
) -> TurnOrchestrator:
    """Construct a TurnOrchestrator with configured LLM backend and Scorer."""
    from mockr.core.llm.factory import build_backend

    backend, config = build_backend()
    scorer = Scorer()

    challenge_context = ""
    must_cover: list[str] = []
    if challenge:
        level_cfg = challenge.levels.get(session.level.value)
        if level_cfg:
            challenge_context = level_cfg.interviewer
            must_cover = level_cfg.must_cover

    return TurnOrchestrator(
        session=session,
        backend=backend,
        scorer=scorer,
        bus=bus,
        config=config,
        must_cover=must_cover,
        challenge_context=challenge_context,
    )


class BaseInterviewScreen(Screen):
    """Common behaviour shared by all three interview screen types."""

    def __init__(self, session: Session, challenge, bus: EventBus, **kwargs) -> None:
        super().__init__(**kwargs)
        self._session = session
        self._challenge = challenge
        self._bus = bus
        self._paused = False
        self._debrief_subscribed = False

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _set_thinking(self, thinking: bool) -> None:
        self.query_one("#status-bar", Static).update("  thinking\u2026" if thinking else "")

    def _set_status(self, msg: str) -> None:
        self.query_one("#status-bar", Static).update(f"  {msg}" if msg else "")

    # ── Hints ─────────────────────────────────────────────────────────────────

    def _resolve_hint(self) -> str:
        """Return a hint from challenge follow_ups or the subclass default."""
        if self._challenge:
            level_cfg = self._challenge.levels.get(self._session.level.value)
            if level_cfg and level_cfg.follow_ups:
                return random.choice(level_cfg.follow_ups)
        return self._default_hint()

    def _default_hint(self) -> str:
        """Override in subclass to provide mode-specific fallback hints."""
        return "Think about your approach from multiple angles."

    # ── Shared lifecycle ─────────────────────────────────────────────────────

    async def _start_interview(self) -> None:
        self._set_thinking(True)
        try:
            await self._orchestrator.generate_first_question()
        except Exception as exc:
            self._set_status(f"Error: {exc}")
        finally:
            self._set_thinking(False)

    # ── Shared actions ───────────────────────────────────────────────────────

    def action_toggle_pause(self) -> None:
        timer = self.query_one("#timer-widget", TimerWidget)
        if self._paused:
            self._paused = False
            timer.resume()
            self._session.resume()
            self._set_status("")
        else:
            self._paused = True
            timer.pause()
            self._session.pause()
            self._set_status("PAUSED \u2014 Ctrl+P to resume")

    def action_end_interview(self) -> None:
        self.query_one("#timer-widget", TimerWidget).pause()
        self.run_worker(self._do_debrief(), exclusive=True)

    async def _do_debrief(self) -> None:
        self._set_status("Generating debrief\u2026")
        if not self._debrief_subscribed:
            self._debrief_subscribed = True
            self._bus.subscribe(DebriefReady, self._on_debrief_ready)
        try:
            await self._orchestrator.generate_debrief()
        except Exception as exc:
            self._set_status(f"Debrief error: {exc}")

    def _on_debrief_ready(self, event: DebriefReady) -> None:
        self.call_from_thread(self._show_debrief, event)

    def _show_debrief(self, event: DebriefReady) -> None:
        from mockr.tui.screens.debrief import DebriefScreen

        self.app.push_screen(
            DebriefScreen(
                overall_score=event.overall_score,
                dimension_scores=event.dimension_scores,
                summary=event.summary,
                mode=self._session.mode.value,
            )
        )
