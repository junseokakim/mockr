from __future__ import annotations

import json

from mockr.core.scoring.scorer import DIMENSIONS_BY_MODE, Scorer, ScoreResult


class TestDimensions:
    def test_system_design_dimensions(self) -> None:
        dims = DIMENSIONS_BY_MODE["system-design"]
        assert "structure" in dims
        assert "tradeoffs" in dims
        assert "reliability" in dims

    def test_coding_dimensions(self) -> None:
        dims = DIMENSIONS_BY_MODE["coding"]
        assert "correctness" in dims
        assert "efficiency" in dims

    def test_behavioral_dimensions(self) -> None:
        dims = DIMENSIONS_BY_MODE["behavioral"]
        assert "situation" in dims
        assert "action" in dims
        assert "result" in dims


class TestScorer:
    def test_build_scoring_prompt(self) -> None:
        scorer = Scorer()
        prompt = scorer.build_scoring_prompt(
            mode="system-design",
            level="senior",
            answer="I would use Redis with LRU eviction...",
            must_cover=["eviction policy", "invalidation"],
            turn_number=2,
        )
        assert "senior" in prompt
        assert "eviction policy" in prompt
        assert "JSON" in prompt

    def test_parse_score_response_valid(self) -> None:
        scorer = Scorer()
        raw = json.dumps(
            {
                "dimensions": {"structure": 4, "constraints": 3, "tradeoffs": 3, "reliability": 2, "concreteness": 4},
                "strengths": ["Good structure"],
                "improvements": ["Needs reliability"],
            }
        )
        result = scorer.parse_score_response(raw, mode="system-design")
        assert isinstance(result, ScoreResult)
        assert result.dimensions["structure"] == 4.0
        assert len(result.strengths) == 1

    def test_parse_score_response_invalid_json(self) -> None:
        scorer = Scorer()
        result = scorer.parse_score_response("not json", mode="system-design")
        assert isinstance(result, ScoreResult)
        assert all(v == 3.0 for v in result.dimensions.values())
