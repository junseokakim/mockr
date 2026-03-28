"""End-to-end test: assessment -> plan generation -> adaptive update."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mockr.core.assessment.engine import AssessmentEngine
from mockr.core.assessment.models import AssessmentResult
from mockr.core.jd.parser import JDParser
from mockr.core.planning.adapter import PlanAdapter
from mockr.core.planning.generator import PlanGenerator
from mockr.core.progress.store import ProgressStore
from mockr.core.types import Message, ModelConfig

_DIAGNOSTIC_SCORES: dict[str, dict[str, float]] = {
    "coding": {"correctness": 2.0, "efficiency": 3.0, "code_quality": 3.5, "edge_cases": 2.5, "communication": 3.5},
    "system-design": {"structure": 3.0, "constraints": 2.5, "tradeoffs": 2.0, "reliability": 2.0, "concreteness": 3.0},
    "behavioral": {"situation": 4.0, "task": 3.5, "action": 3.5, "result": 3.0, "impact": 3.0},
}


class FakeBackend:
    """Serves all LLM needs for integration testing."""

    def __init__(self, mode_scores: dict[str, dict[str, float]]) -> None:
        self._scores = mode_scores

    async def generate(self, messages: list[Message], config: ModelConfig) -> str:
        content = " ".join(m.content.lower() for m in messages)
        if "score each dimension" in content:
            for mode, scores in self._scores.items():
                if mode.replace("-", " ") in content or mode in content:
                    return json.dumps({"dimensions": scores, "strengths": ["OK"], "improvements": ["Work harder"]})
            first = next(iter(self._scores.values()))
            return json.dumps({"dimensions": first, "strengths": [], "improvements": []})
        elif "extracting structured information" in content:
            return json.dumps(
                {
                    "company": "TestCorp",
                    "role_title": "Senior Engineer",
                    "inferred_level": "senior",
                    "tech_stack": ["Python"],
                    "domain": "testing",
                    "key_skills": [
                        {
                            "name": "system design",
                            "category": "system-design",
                            "dimensions": ["tradeoffs"],
                            "weight": 0.9,
                        },
                    ],
                }
            )
        elif "debrief" in content:
            return json.dumps({"overall_score": 3.0, "dimension_scores": {}, "summary": "Done."})
        else:
            return "Next question."


@pytest.mark.asyncio
class TestAssessmentFlow:
    async def test_full_flow_assessment_to_plan(self, tmp_path: Path) -> None:
        """assessment -> gaps -> plan -> persist -> adaptive update."""
        backend = FakeBackend(_DIAGNOSTIC_SCORES)
        config = ModelConfig(model="test")

        engine = AssessmentEngine(
            backend=backend,
            config=config,
            challenges_dir=Path("mockr/challenges/diagnostic"),
        )

        async def fake_answer(q: str, mode: str) -> str:
            return "My diagnostic answer."

        result = await engine.run_diagnostic(target_level="senior", answer_callback=fake_answer)
        assert isinstance(result, AssessmentResult)
        assert len(result.gaps) > 0

        generator = PlanGenerator(challenges_dir=Path("mockr/challenges"))
        plan = generator.generate(result)
        assert len(plan.items) > 0
        assert plan.items[0].priority >= plan.items[-1].priority

        store = ProgressStore(tmp_path / "test.db")
        store.save_assessment(result.id, result.target_level, result.inferred_level, result.mode_scores)
        store.save_practice_plan(plan.id, result.id, None, plan.target_level)
        for i, item in enumerate(plan.items):
            store.save_plan_item(
                f"item-{i}",
                plan.id,
                item.dimension,
                item.mode,
                item.priority,
                item.gap_size,
                item.challenge_id,
                item.rationale,
            )

        assert store.get_assessment(result.id) is not None
        assert len(store.get_plan_items(plan.id)) == len(plan.items)

        improved_scores = {
            "coding": {
                "correctness": 4.0,
                "efficiency": 3.5,
                "code_quality": 3.5,
                "edge_cases": 3.5,
                "communication": 3.5,
            },
            "system-design": {
                "structure": 3.5,
                "constraints": 3.5,
                "tradeoffs": 3.5,
                "reliability": 3.5,
                "concreteness": 3.5,
            },
            "behavioral": {"situation": 4.0, "task": 3.5, "action": 3.5, "result": 3.5, "impact": 3.5},
        }
        adapter = PlanAdapter()
        updated_plan = adapter.recalculate(plan, improved_scores, target_level="senior")
        assert sum(1 for item in updated_plan.items if item.status == "validated") > 0

        store.close()

    async def test_flow_with_jd_overlay(self, tmp_path: Path) -> None:
        """assessment -> JD parse -> plan with JD boost."""
        backend = FakeBackend(_DIAGNOSTIC_SCORES)
        config = ModelConfig(model="test")

        engine = AssessmentEngine(
            backend=backend,
            config=config,
            challenges_dir=Path("mockr/challenges/diagnostic"),
        )

        async def fake_answer(q: str, mode: str) -> str:
            return "Answer."

        result = await engine.run_diagnostic(target_level="senior", answer_callback=fake_answer)

        parser = JDParser(backend=backend, config=config)
        profile = await parser.parse_text("Senior Engineer at TestCorp, system design focus.")

        generator = PlanGenerator(challenges_dir=Path("mockr/challenges"))
        plan_without_jd = generator.generate(result)
        plan_with_jd = generator.generate(result, role_profile=profile)

        tradeoffs_no_jd = next((i for i in plan_without_jd.items if i.dimension == "tradeoffs"), None)
        tradeoffs_jd = next((i for i in plan_with_jd.items if i.dimension == "tradeoffs"), None)
        # JD boosting system-design tradeoffs must produce an item and not reduce its priority
        assert tradeoffs_jd is not None
        if tradeoffs_no_jd is not None:
            assert tradeoffs_jd.priority >= tradeoffs_no_jd.priority
