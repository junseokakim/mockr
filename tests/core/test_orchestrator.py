from __future__ import annotations

import json

import pytest

from mockr.core.events import AnswerReceived, DebriefReady, EventBus, QuestionReady, ScoreReady
from mockr.core.scoring.scorer import Scorer
from mockr.core.sessions.orchestrator import TurnOrchestrator
from mockr.core.sessions.session import Session
from mockr.core.types import Level, Mode, ModelConfig, SessionState


class FakeLLMBackend:
    def __init__(self) -> None:
        self.call_count = 0

    async def generate(self, messages, config):
        self.call_count += 1
        if any("score each dimension" in m.content.lower() for m in messages):
            return json.dumps(
                {
                    "dimensions": {
                        "structure": 4,
                        "constraints": 3,
                        "tradeoffs": 3,
                        "reliability": 2,
                        "concreteness": 4,
                    },
                    "strengths": ["Good structure"],
                    "improvements": ["Add reliability"],
                }
            )
        elif any("debrief" in m.content.lower() for m in messages):
            return json.dumps(
                {
                    "overall_score": 3.5,
                    "dimension_scores": {"structure": 4, "tradeoffs": 3},
                    "summary": "Solid session. Focus on reliability.",
                }
            )
        else:
            return "What about failure modes?"

    async def stream(self, messages, config):
        result = await self.generate(messages, config)
        yield result


@pytest.mark.asyncio
class TestTurnOrchestrator:
    async def test_process_answer_emits_events(self) -> None:
        bus = EventBus()
        session = Session(bus=bus, mode=Mode.SYSTEM_DESIGN, level=Level.SENIOR)
        session.setup(challenge_id="cache", timer_minutes=20)
        session.start()
        backend = FakeLLMBackend()
        scorer = Scorer()
        received: dict[str, list] = {"answer": [], "score": [], "question": []}
        bus.subscribe(AnswerReceived, received["answer"].append)
        bus.subscribe(ScoreReady, received["score"].append)
        bus.subscribe(QuestionReady, received["question"].append)
        orchestrator = TurnOrchestrator(
            session=session,
            backend=backend,
            scorer=scorer,
            bus=bus,
            config=ModelConfig(model="test"),
            must_cover=["eviction"],
        )
        await orchestrator.process_answer("I would use Redis with LRU eviction")
        assert len(received["answer"]) == 1
        assert len(received["score"]) == 1
        assert len(received["question"]) == 1
        assert received["score"][0].dimensions["structure"] == 4.0
        assert session.turn_number == 1

    async def test_generate_debrief_emits_event(self) -> None:
        bus = EventBus()
        session = Session(bus=bus, mode=Mode.SYSTEM_DESIGN, level=Level.SENIOR)
        session.setup(challenge_id="cache", timer_minutes=20)
        session.start()
        backend = FakeLLMBackend()
        scorer = Scorer()
        debrief_events: list[DebriefReady] = []
        bus.subscribe(DebriefReady, debrief_events.append)
        orchestrator = TurnOrchestrator(
            session=session,
            backend=backend,
            scorer=scorer,
            bus=bus,
            config=ModelConfig(model="test"),
            must_cover=[],
        )
        await orchestrator.generate_debrief()
        assert len(debrief_events) == 1
        assert debrief_events[0].session_id == session.id
        assert session.state == SessionState.DEBRIEF

    async def test_first_question_no_scoring(self) -> None:
        bus = EventBus()
        session = Session(bus=bus, mode=Mode.SYSTEM_DESIGN, level=Level.SENIOR)
        session.setup(challenge_id="cache", timer_minutes=20)
        session.start()
        backend = FakeLLMBackend()
        scorer = Scorer()
        question_events: list[QuestionReady] = []
        bus.subscribe(QuestionReady, question_events.append)
        orchestrator = TurnOrchestrator(
            session=session,
            backend=backend,
            scorer=scorer,
            bus=bus,
            config=ModelConfig(model="test"),
            must_cover=[],
        )
        await orchestrator.generate_first_question()
        assert len(question_events) == 1
        assert question_events[0].coach_text is None
