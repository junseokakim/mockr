from __future__ import annotations

import json
from pathlib import Path

import pytest

from mockr.core.assessment.engine import AssessmentEngine
from mockr.core.assessment.models import AssessmentResult
from mockr.core.types import Message, ModelConfig


class FakeAssessmentBackend:
    """Returns canned scores for each mode."""

    def __init__(self, scores_by_mode: dict[str, dict[str, float]]) -> None:
        self._scores_by_mode = scores_by_mode

    async def generate(self, messages: list[Message], config: ModelConfig) -> str:
        content = " ".join(m.content.lower() for m in messages)
        if "score each dimension" in content:
            for mode, scores in self._scores_by_mode.items():
                if mode.replace("-", " ") in content or mode in content:
                    return json.dumps({
                        "dimensions": scores,
                        "strengths": ["Good"],
                        "improvements": ["Improve"],
                    })
            first_mode = next(iter(self._scores_by_mode))
            return json.dumps({
                "dimensions": self._scores_by_mode[first_mode],
                "strengths": ["Good"],
                "improvements": ["Improve"],
            })
        elif "debrief" in content:
            return json.dumps({
                "overall_score": 3.5,
                "dimension_scores": {},
                "summary": "Diagnostic complete.",
            })
        else:
            return "Tell me about your approach."


@pytest.mark.asyncio
class TestAssessmentEngine:
    async def test_run_diagnostic_returns_result(self) -> None:
        scores = {
            "coding": {"correctness": 4.0, "efficiency": 3.0, "code_quality": 3.5, "edge_cases": 3.0, "communication": 3.5},
            "system-design": {"structure": 3.0, "constraints": 2.5, "tradeoffs": 3.0, "reliability": 2.0, "concreteness": 3.0},
            "behavioral": {"situation": 4.0, "task": 3.5, "action": 3.5, "result": 3.0, "impact": 3.0},
        }
        backend = FakeAssessmentBackend(scores)
        engine = AssessmentEngine(
            backend=backend,
            config=ModelConfig(model="test"),
            challenges_dir=Path("mockr/challenges/diagnostic"),
        )
        result = await engine.run_diagnostic(
            target_level="senior",
            answer_callback=self._fake_answer,
        )
        assert isinstance(result, AssessmentResult)
        assert result.target_level == "senior"
        assert "coding" in result.mode_scores
        assert "system-design" in result.mode_scores
        assert "behavioral" in result.mode_scores

    async def test_diagnostic_detects_gaps(self) -> None:
        scores = {
            "coding": {"correctness": 2.0, "efficiency": 2.0, "code_quality": 2.0, "edge_cases": 2.0, "communication": 2.0},
            "system-design": {"structure": 2.0, "constraints": 2.0, "tradeoffs": 2.0, "reliability": 2.0, "concreteness": 2.0},
            "behavioral": {"situation": 2.0, "task": 2.0, "action": 2.0, "result": 2.0, "impact": 2.0},
        }
        backend = FakeAssessmentBackend(scores)
        engine = AssessmentEngine(
            backend=backend,
            config=ModelConfig(model="test"),
            challenges_dir=Path("mockr/challenges/diagnostic"),
        )
        result = await engine.run_diagnostic(
            target_level="senior",
            answer_callback=self._fake_answer,
        )
        assert len(result.gaps) > 0
        assert all(g.gap_size > 0 for g in result.gaps)

    @staticmethod
    async def _fake_answer(question: str, mode: str) -> str:
        return "Here is my answer to the diagnostic question."
