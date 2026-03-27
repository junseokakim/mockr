"""Countdown timer widget."""

from __future__ import annotations

import asyncio

from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static


class TimerWidget(Static):
    """Counts down from a given number of seconds, emitting ticks via the event bus."""

    remaining: reactive[int] = reactive(0)

    DEFAULT_CSS = """
    TimerWidget {
        width: auto;
        height: 1;
        content-align: center middle;
    }
    """

    def __init__(
        self,
        total_seconds: int,
        session_id: str,
        bus=None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._total_seconds = total_seconds
        self._session_id = session_id
        self._bus = bus
        self._running = False
        self._task: asyncio.Task | None = None

    def on_mount(self) -> None:
        self.remaining = self._total_seconds
        self._update_display()

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._task = self.run_worker(self._tick_loop(), exclusive=True)

    def pause(self) -> None:
        self._running = False

    def resume(self) -> None:
        if not self._running:
            self._running = True
            self._task = self.run_worker(self._tick_loop(), exclusive=True)

    async def _tick_loop(self) -> None:
        from mockr.core.events import TimerTick

        while self._running and self.remaining > 0:
            await asyncio.sleep(1)
            if not self._running:
                break
            self.remaining -= 1
            self._update_display()
            if self._bus:
                self._bus.emit(
                    TimerTick(
                        session_id=self._session_id,
                        remaining_seconds=self.remaining,
                    )
                )
            if self.remaining == 0:
                self.post_message(TimerExpired(self))
                break

    def _update_display(self) -> None:
        mins, secs = divmod(self.remaining, 60)
        label = f"  {mins:02d}:{secs:02d}"

        # Update CSS class for visual urgency
        self.remove_class("warning", "danger")
        if self.remaining <= 60:
            self.add_class("danger")
        elif self.remaining <= 300:
            self.add_class("warning")

        self.update(label)

    class TimerExpired(Message):
        """Posted when the timer reaches zero."""

        def __init__(self, timer: TimerWidget) -> None:
            super().__init__()
            self.timer = timer


# Re-export for convenience
TimerExpired = TimerWidget.TimerExpired
