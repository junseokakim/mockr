# mockr/tests/core/test_events.py
from __future__ import annotations

from dataclasses import dataclass

from mockr.core.events import EventBus


@dataclass
class FakeEvent:
    value: int


@dataclass
class OtherEvent:
    text: str


class TestEventBus:
    def test_subscribe_and_emit(self) -> None:
        bus = EventBus()
        received: list[FakeEvent] = []
        bus.subscribe(FakeEvent, received.append)
        bus.emit(FakeEvent(value=42))
        assert received == [FakeEvent(value=42)]

    def test_multiple_subscribers(self) -> None:
        bus = EventBus()
        a: list[FakeEvent] = []
        b: list[FakeEvent] = []
        bus.subscribe(FakeEvent, a.append)
        bus.subscribe(FakeEvent, b.append)
        bus.emit(FakeEvent(value=1))
        assert len(a) == 1
        assert len(b) == 1

    def test_different_event_types_isolated(self) -> None:
        bus = EventBus()
        fakes: list[FakeEvent] = []
        others: list[OtherEvent] = []
        bus.subscribe(FakeEvent, fakes.append)
        bus.subscribe(OtherEvent, others.append)
        bus.emit(FakeEvent(value=1))
        assert len(fakes) == 1
        assert len(others) == 0

    def test_no_subscribers_does_not_error(self) -> None:
        bus = EventBus()
        bus.emit(FakeEvent(value=99))  # should not raise

    def test_handler_ordering(self) -> None:
        bus = EventBus()
        order: list[str] = []
        bus.subscribe(FakeEvent, lambda e: order.append("first"))
        bus.subscribe(FakeEvent, lambda e: order.append("second"))
        bus.emit(FakeEvent(value=0))
        assert order == ["first", "second"]
