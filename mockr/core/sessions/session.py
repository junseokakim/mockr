"""Session state machine and turn management."""
from __future__ import annotations
import json
import uuid
from mockr.core.events import EventBus, SessionStateChanged
from mockr.core.types import Level, Message, Mode, SessionState


class Session:
    def __init__(self, bus: EventBus, mode: Mode, level: Level,
                 session_id: str | None = None, max_history: int = 8) -> None:
        self.id = session_id or str(uuid.uuid4())
        self.bus = bus
        self.mode = mode
        self.level = level
        self.state = SessionState.IDLE
        self.challenge_id: str = ""
        self.timer_minutes: int = 20
        self.turn_number: int = 0
        self.history: list[Message] = []
        self._max_history_messages = max_history * 2

    def _transition(self, new_state: SessionState) -> None:
        old = self.state
        self.state = new_state
        self.bus.emit(SessionStateChanged(session_id=self.id, old_state=old, new_state=new_state))

    def setup(self, challenge_id: str, timer_minutes: int = 20) -> None:
        self.challenge_id = challenge_id
        self.timer_minutes = timer_minutes
        self._transition(SessionState.SETUP)

    def start(self) -> None:
        self._transition(SessionState.ACTIVE)

    def pause(self) -> None:
        self._transition(SessionState.PAUSED)

    def resume(self) -> None:
        self._transition(SessionState.ACTIVE)

    def end(self) -> None:
        self._transition(SessionState.DEBRIEF)

    def complete(self) -> None:
        self._transition(SessionState.COMPLETE)

    def add_user_answer(self, text: str) -> None:
        self.turn_number += 1
        self.history.append(Message(role="user", content=text))
        self._trim_history()

    def add_assistant_response(self, text: str) -> None:
        self.history.append(Message(role="assistant", content=text))
        self._trim_history()

    def _trim_history(self) -> None:
        if len(self.history) > self._max_history_messages:
            excess = len(self.history) - self._max_history_messages
            self.history = self.history[excess:]

    def serialize(self) -> str:
        return json.dumps({
            "id": self.id, "mode": self.mode.value, "level": self.level.value,
            "state": self.state.value, "challenge_id": self.challenge_id,
            "timer_minutes": self.timer_minutes, "turn_number": self.turn_number,
            "history": [{"role": m.role, "content": m.content} for m in self.history],
        })

    @classmethod
    def from_serialized(cls, bus: EventBus, blob: str) -> Session:
        data = json.loads(blob)
        session = cls(bus=bus, mode=Mode(data["mode"]), level=Level(data["level"]), session_id=data["id"])
        session.state = SessionState(data["state"])
        session.challenge_id = data["challenge_id"]
        session.timer_minutes = data["timer_minutes"]
        session.turn_number = data["turn_number"]
        session.history = [Message(role=m["role"], content=m["content"]) for m in data["history"]]
        return session
