"""Turn orchestrator — the central interview loop."""
from __future__ import annotations
import asyncio
from mockr.core.events import (AnswerReceived, DebriefReady, EventBus, QuestionReady, ScoreReady)
from mockr.core.scoring.scorer import Scorer
from mockr.core.sessions.session import Session
from mockr.core.types import Message, ModelConfig
from mockr.core.utils import extract_json_object


class TurnOrchestrator:
    def __init__(self, session: Session, backend: object, scorer: Scorer,
                 bus: EventBus, config: ModelConfig, must_cover: list[str],
                 challenge_context: str = "") -> None:
        self._session = session
        self._backend = backend
        self._scorer = scorer
        self._bus = bus
        self._config = config
        self._must_cover = must_cover
        self._challenge_context = challenge_context

    async def generate_first_question(self) -> str:
        messages = [
            Message(role="system", content=self._challenge_context),
            Message(role="user", content="Start the interview with the first question."),
        ]
        response = await self._backend.generate(messages, self._config)
        self._session.add_assistant_response(response)
        self._bus.emit(QuestionReady(
            session_id=self._session.id, turn_number=0,
            interviewer_text=response, coach_text=None,
        ))
        return response

    async def process_answer(self, answer: str, diagram=None) -> None:
        self._session.add_user_answer(answer)
        self._bus.emit(AnswerReceived(
            session_id=self._session.id, turn_number=self._session.turn_number,
            answer_text=answer, diagram=diagram,
        ))
        score_prompt = self._scorer.build_scoring_prompt(
            mode=self._session.mode.value, level=self._session.level.value,
            answer=answer, must_cover=self._must_cover, turn_number=self._session.turn_number,
        )
        next_q_messages = [
            Message(role="system", content=self._challenge_context),
            *self._session.history,
            Message(role="user", content="Evaluate the last answer and ask the next interview question."),
        ]
        score_raw, next_response = await asyncio.gather(
            self._backend.generate([Message(role="user", content=score_prompt)], self._config),
            self._backend.generate(next_q_messages, self._config),
        )
        score_result = self._scorer.parse_score_response(score_raw, mode=self._session.mode.value)
        self._bus.emit(ScoreReady(
            session_id=self._session.id, turn_number=self._session.turn_number,
            dimensions=score_result.dimensions, strengths=score_result.strengths,
            improvements=score_result.improvements,
        ))
        self._session.add_assistant_response(next_response)
        interviewer_text = next_response
        coach_text = None
        if "COACH:" in next_response:
            parts = next_response.split("COACH:", 1)
            interviewer_text = parts[0].replace("INTERVIEWER:", "").strip()
            coach_text = parts[1].strip()
        self._bus.emit(QuestionReady(
            session_id=self._session.id, turn_number=self._session.turn_number,
            interviewer_text=interviewer_text, coach_text=coach_text,
        ))

    async def generate_debrief(self) -> None:
        self._session.end()
        debrief_prompt = (
            'Generate a final interview debrief. Return JSON: '
            '{"overall_score": <1-5>, "dimension_scores": {...}, "summary": "..."}'
        )
        messages = [
            Message(role="system", content=self._challenge_context),
            *self._session.history,
            Message(role="user", content=debrief_prompt),
        ]
        raw = await self._backend.generate(messages, self._config)
        try:
            data = extract_json_object(raw)
            overall = float(data.get("overall_score", 3.0))
            dim_scores = {k: float(v) for k, v in data.get("dimension_scores", {}).items()}
            summary = data.get("summary", raw)
        except (ValueError, KeyError, TypeError):
            overall, dim_scores, summary = 3.0, {}, raw
        self._bus.emit(DebriefReady(
            session_id=self._session.id, overall_score=overall,
            dimension_scores=dim_scores, summary=summary,
        ))
