"""End-to-end integration test: session -> score -> debrief -> persist."""
from __future__ import annotations
import json
from pathlib import Path
import pytest
from mockr.core.events import EventBus, DebriefReady, ScoreReady, QuestionReady
from mockr.core.sessions.session import Session
from mockr.core.sessions.orchestrator import TurnOrchestrator
from mockr.core.scoring.scorer import Scorer
from mockr.core.progress.store import ProgressStore
from mockr.core.types import Level, Mode, ModelConfig


class FakeLLMBackend:
    async def generate(self, messages, config):
        for m in messages:
            if "score each dimension" in m.content.lower():
                return json.dumps({
                    "dimensions": {"structure": 4, "constraints": 3, "tradeoffs": 3, "reliability": 2, "concreteness": 4},
                    "strengths": ["Good"], "improvements": ["More reliability"],
                })
            if "debrief" in m.content.lower():
                return json.dumps({
                    "overall_score": 3.5, "dimension_scores": {"structure": 4},
                    "summary": "Good session.",
                })
        return "Tell me about failure modes."


@pytest.mark.asyncio
class TestSessionFlow:
    async def test_full_session_roundtrip(self, tmp_path: Path) -> None:
        bus = EventBus()
        session = Session(bus=bus, mode=Mode.SYSTEM_DESIGN, level=Level.SENIOR)
        session.setup(challenge_id="cache", timer_minutes=20)
        session.start()

        backend = FakeLLMBackend()
        scorer = Scorer()
        store = ProgressStore(tmp_path / "test.db")

        # Track events
        scores: list[ScoreReady] = []
        questions: list[QuestionReady] = []
        debriefs: list[DebriefReady] = []
        bus.subscribe(ScoreReady, scores.append)
        bus.subscribe(QuestionReady, questions.append)
        bus.subscribe(DebriefReady, debriefs.append)

        orchestrator = TurnOrchestrator(
            session=session, backend=backend, scorer=scorer, bus=bus,
            config=ModelConfig(model="test"), must_cover=["eviction"],
        )

        # Persist session
        store.save_session(session.id, "system-design", "cache", "senior", "test")

        # First question
        await orchestrator.generate_first_question()
        assert len(questions) == 1

        # Two turns
        await orchestrator.process_answer("I would use Redis with LRU eviction and TTL")
        assert len(scores) == 1
        assert len(questions) == 2

        await orchestrator.process_answer("For failure modes, I would use replication")
        assert len(scores) == 2

        # Debrief
        await orchestrator.generate_debrief()
        assert len(debriefs) == 1
        assert debriefs[0].overall_score == 3.5

        # Persist results
        store.complete_session(session.id, debriefs[0].overall_score, debriefs[0].summary)
        store.update_challenge_stats("cache", "senior", debriefs[0].overall_score)

        # Verify persistence
        saved = store.get_session(session.id)
        assert saved["state"] == "complete"
        assert saved["overall_score"] == 3.5

        stats = store.get_challenge_stats("cache", "senior")
        assert stats["times_attempted"] == 1
        store.close()
