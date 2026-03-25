"""Simple synchronous pub/sub event bus."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable

from mockr.core.types import SessionState


class EventBus:
    """Synchronous event bus. Handlers called in registration order."""

    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: Callable) -> None:
        """Register a handler for an event type."""
        self._handlers[event_type].append(handler)

    def emit(self, event: Any) -> None:
        """Dispatch event to all registered handlers for its type."""
        for handler in self._handlers.get(type(event), []):
            handler(event)


@dataclass
class TestResult:
    case_index: int
    passed: bool
    expected: str
    actual: str
    hidden: bool


@dataclass
class AnswerReceived:
    session_id: str
    turn_number: int
    answer_text: str
    diagram: object | None = None


@dataclass
class ScoreReady:
    session_id: str
    turn_number: int
    dimensions: dict[str, float]
    strengths: list[str]
    improvements: list[str]


@dataclass
class QuestionReady:
    session_id: str
    turn_number: int
    interviewer_text: str
    coach_text: str | None = None


@dataclass
class ExecutionResult:
    session_id: str
    language: str
    passed: int
    failed: int
    total: int
    test_details: list[TestResult]
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: int


@dataclass
class SessionStateChanged:
    session_id: str
    old_state: SessionState
    new_state: SessionState


@dataclass
class TimerTick:
    session_id: str
    remaining_seconds: int


@dataclass
class DebriefReady:
    session_id: str
    overall_score: float
    dimension_scores: dict[str, float]
    summary: str
