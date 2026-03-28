from __future__ import annotations

from mockr.core.assessment.thresholds import (
    LEVEL_THRESHOLDS,
    detect_gaps,
    infer_level,
)


class TestLevelThresholds:
    def test_senior_thresholds_exist(self) -> None:
        assert "senior" in LEVEL_THRESHOLDS
        senior = LEVEL_THRESHOLDS["senior"]
        assert "coding" in senior
        assert "correctness" in senior["coding"]

    def test_all_ic_levels_have_thresholds(self) -> None:
        for level in ["intern", "junior", "mid", "senior", "staff", "principal"]:
            assert level in LEVEL_THRESHOLDS, f"Missing thresholds for {level}"

    def test_thresholds_increase_with_level(self) -> None:
        mid_coding = LEVEL_THRESHOLDS["mid"]["coding"]["correctness"]
        senior_coding = LEVEL_THRESHOLDS["senior"]["coding"]["correctness"]
        assert senior_coding > mid_coding


class TestDetectGaps:
    def test_detects_gap_below_threshold(self) -> None:
        mode_scores = {
            "coding": {
                "correctness": 2.0,
                "efficiency": 3.0,
                "code_quality": 3.0,
                "edge_cases": 2.5,
                "communication": 3.5,
            },
        }
        gaps = detect_gaps(mode_scores, target_level="senior")
        gap_dims = [g.dimension for g in gaps]
        assert "correctness" in gap_dims

    def test_no_gap_when_above_threshold(self) -> None:
        mode_scores = {
            "coding": {
                "correctness": 5.0,
                "efficiency": 5.0,
                "code_quality": 5.0,
                "edge_cases": 5.0,
                "communication": 5.0,
            },
        }
        gaps = detect_gaps(mode_scores, target_level="senior")
        coding_gaps = [g for g in gaps if g.mode == "coding"]
        assert len(coding_gaps) == 0

    def test_gap_includes_size(self) -> None:
        mode_scores = {
            "coding": {
                "correctness": 2.0,
                "efficiency": 4.0,
                "code_quality": 4.0,
                "edge_cases": 4.0,
                "communication": 4.0,
            },
        }
        gaps = detect_gaps(mode_scores, target_level="senior")
        correctness_gap = next(g for g in gaps if g.dimension == "correctness")
        assert correctness_gap.gap_size > 0


class TestInferLevel:
    def test_infer_level_from_high_scores(self) -> None:
        mode_scores = {
            "coding": {
                "correctness": 4.5,
                "efficiency": 4.5,
                "code_quality": 4.5,
                "edge_cases": 4.5,
                "communication": 4.5,
            },
            "system-design": {
                "structure": 4.5,
                "constraints": 4.5,
                "tradeoffs": 4.5,
                "reliability": 4.5,
                "concreteness": 4.5,
            },
            "behavioral": {"situation": 4.5, "task": 4.5, "action": 4.5, "result": 4.5, "impact": 4.5},
        }
        level = infer_level(mode_scores)
        assert level in ("staff", "principal")

    def test_infer_level_from_low_scores(self) -> None:
        mode_scores = {
            "coding": {
                "correctness": 1.5,
                "efficiency": 1.5,
                "code_quality": 1.5,
                "edge_cases": 1.5,
                "communication": 1.5,
            },
            "system-design": {
                "structure": 1.5,
                "constraints": 1.5,
                "tradeoffs": 1.5,
                "reliability": 1.5,
                "concreteness": 1.5,
            },
            "behavioral": {"situation": 1.5, "task": 1.5, "action": 1.5, "result": 1.5, "impact": 1.5},
        }
        level = infer_level(mode_scores)
        assert level in ("intern", "junior")
