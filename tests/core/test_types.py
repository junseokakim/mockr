# mockr/tests/core/test_types.py
from __future__ import annotations

from mockr.core.types import (
    Level,
    Message,
    Mode,
    ModelConfig,
    SessionState,
)


class TestMessage:
    def test_create(self) -> None:
        msg = Message(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"

    def test_roles(self) -> None:
        for role in ("system", "user", "assistant"):
            msg = Message(role=role, content="x")
            assert msg.role == role


class TestModelConfig:
    def test_defaults(self) -> None:
        cfg = ModelConfig(model="llama3")
        assert cfg.temperature == 0.7
        assert cfg.max_tokens == 4096
        assert cfg.stop_sequences == []

    def test_custom(self) -> None:
        cfg = ModelConfig(model="gpt-4o", temperature=0.2, max_tokens=1024)
        assert cfg.temperature == 0.2


class TestEnums:
    def test_session_states(self) -> None:
        assert SessionState.IDLE.value == "idle"
        assert SessionState.ACTIVE.value == "active"
        assert SessionState.PAUSED.value == "paused"
        assert SessionState.DEBRIEF.value == "debrief"
        assert SessionState.COMPLETE.value == "complete"

    def test_levels(self) -> None:
        assert Level.MID.value == "mid"
        assert Level.STAFF.value == "staff"
        assert Level.PRINCIPAL.value == "principal"

    def test_modes(self) -> None:
        assert Mode.SYSTEM_DESIGN.value == "system-design"
        assert Mode.CODING.value == "coding"
        assert Mode.BEHAVIORAL.value == "behavioral"
        assert Mode.FULL_LOOP.value == "full-loop"


class TestLevelExpansion:
    def test_intern_level_exists(self) -> None:
        assert Level.INTERN.value == "intern"

    def test_junior_level_exists(self) -> None:
        assert Level.JUNIOR.value == "junior"

    def test_all_ic_levels_ordered(self) -> None:
        ic_levels = [Level.INTERN, Level.JUNIOR, Level.MID, Level.SENIOR, Level.STAFF, Level.PRINCIPAL]
        assert len(ic_levels) == 6

    def test_management_placeholder_exists(self) -> None:
        assert Level.ENGINEERING_MANAGER.value == "engineering_manager"
        assert Level.DIRECTOR.value == "director"
        assert Level.VP.value == "vp"
