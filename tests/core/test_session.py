from __future__ import annotations

from mockr.core.events import EventBus, SessionStateChanged
from mockr.core.sessions.session import Session
from mockr.core.types import Level, Mode, SessionState


class TestSession:
    def test_initial_state_is_idle(self) -> None:
        bus = EventBus()
        session = Session(bus=bus, mode=Mode.SYSTEM_DESIGN, level=Level.SENIOR)
        assert session.state == SessionState.IDLE

    def test_setup_transitions_to_setup(self) -> None:
        bus = EventBus()
        session = Session(bus=bus, mode=Mode.SYSTEM_DESIGN, level=Level.SENIOR)
        session.setup(challenge_id="cache", timer_minutes=20)
        assert session.state == SessionState.SETUP

    def test_start_transitions_to_active(self) -> None:
        bus = EventBus()
        session = Session(bus=bus, mode=Mode.SYSTEM_DESIGN, level=Level.SENIOR)
        session.setup(challenge_id="cache", timer_minutes=20)
        session.start()
        assert session.state == SessionState.ACTIVE

    def test_state_change_emits_event(self) -> None:
        bus = EventBus()
        events: list[SessionStateChanged] = []
        bus.subscribe(SessionStateChanged, events.append)
        session = Session(bus=bus, mode=Mode.SYSTEM_DESIGN, level=Level.SENIOR)
        session.setup(challenge_id="cache", timer_minutes=20)
        assert len(events) == 1
        assert events[0].new_state == SessionState.SETUP

    def test_pause_and_resume(self) -> None:
        bus = EventBus()
        session = Session(bus=bus, mode=Mode.SYSTEM_DESIGN, level=Level.SENIOR)
        session.setup(challenge_id="cache", timer_minutes=20)
        session.start()
        session.pause()
        assert session.state == SessionState.PAUSED
        session.resume()
        assert session.state == SessionState.ACTIVE

    def test_add_turn(self) -> None:
        bus = EventBus()
        session = Session(bus=bus, mode=Mode.SYSTEM_DESIGN, level=Level.SENIOR)
        session.setup(challenge_id="cache", timer_minutes=20)
        session.start()
        session.add_user_answer("I would use Redis with LRU")
        assert session.turn_number == 1
        assert len(session.history) == 1

    def test_history_sliding_window(self) -> None:
        bus = EventBus()
        session = Session(bus=bus, mode=Mode.SYSTEM_DESIGN, level=Level.SENIOR, max_history=3)
        session.setup(challenge_id="cache", timer_minutes=20)
        session.start()
        for i in range(5):
            session.add_user_answer(f"answer {i}")
            session.add_assistant_response(f"response {i}")
        assert len(session.history) <= 6

    def test_serialize_and_restore(self) -> None:
        bus = EventBus()
        session = Session(bus=bus, mode=Mode.CODING, level=Level.MID)
        session.setup(challenge_id="two-sum", timer_minutes=30)
        session.start()
        session.add_user_answer("def two_sum(): pass")
        blob = session.serialize()
        assert "two-sum" in blob
        restored = Session.from_serialized(bus, blob)
        assert restored.mode == Mode.CODING
        assert restored.turn_number == 1
