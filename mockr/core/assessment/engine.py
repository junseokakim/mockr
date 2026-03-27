"""Diagnostic assessment engine — runs mini-interviews across modes."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path

from mockr.core.assessment.models import AssessmentResult
from mockr.core.assessment.thresholds import detect_gaps, infer_level
from mockr.core.challenges.loader import load_challenges_from_dir
from mockr.core.scoring.scorer import Scorer
from mockr.core.types import Message, Mode, ModelConfig

_DIAGNOSTIC_MODES = [Mode.CODING, Mode.SYSTEM_DESIGN, Mode.BEHAVIORAL]


class AssessmentEngine:
    def __init__(
        self,
        backend: object,
        config: ModelConfig,
        challenges_dir: Path,
    ) -> None:
        self._backend = backend
        self._config = config
        self._challenges_dir = challenges_dir
        self._scorer = Scorer()

    async def run_diagnostic(
        self,
        target_level: str,
        answer_callback: Callable[[str, str], Awaitable[str]],
    ) -> AssessmentResult:
        """Run a 3-mode diagnostic assessment, collecting one answer per mode."""
        challenges = load_challenges_from_dir(self._challenges_dir)
        challenge_by_mode = {ch.mode: ch for ch in challenges}
        mode_scores: dict[str, dict[str, float]] = {}

        for mode in _DIAGNOSTIC_MODES:
            mode_str = mode.value
            challenge = challenge_by_mode.get(mode_str)
            if challenge is None:
                continue

            level_config = challenge.levels.get(target_level)
            if level_config is None:
                available = list(challenge.levels.keys())
                level_config = challenge.levels[available[0]] if available else None
            if level_config is None:
                continue

            question_messages = [
                Message(role="system", content=level_config.interviewer),
                Message(role="user", content="Start the interview with the first question."),
            ]
            question = await self._backend.generate(question_messages, self._config)

            answer = await answer_callback(question, mode_str)

            score_prompt = self._scorer.build_scoring_prompt(
                mode=mode_str,
                level=target_level,
                answer=answer,
                must_cover=level_config.must_cover,
                turn_number=1,
            )
            score_raw = await self._backend.generate(
                [Message(role="user", content=score_prompt)], self._config,
            )
            score_result = self._scorer.parse_score_response(score_raw, mode=mode_str)
            mode_scores[mode_str] = score_result.dimensions

        gaps = detect_gaps(mode_scores, target_level)
        inferred = infer_level(mode_scores)

        return AssessmentResult(
            id=str(uuid.uuid4()),
            target_level=target_level,
            inferred_level=inferred,
            mode_scores=mode_scores,
            gaps=gaps,
        )
