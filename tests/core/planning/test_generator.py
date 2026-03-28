from __future__ import annotations

from pathlib import Path

from mockr.core.assessment.models import AssessmentResult, Gap
from mockr.core.jd.models import RoleProfile, Skill
from mockr.core.planning.generator import PlanGenerator
from mockr.core.planning.models import PracticePlan


class TestPlanGenerator:
    def test_generate_plan_from_assessment(self) -> None:
        result = AssessmentResult(
            id="a1",
            target_level="senior",
            inferred_level="mid",
            mode_scores={
                "coding": {
                    "correctness": 2.0,
                    "efficiency": 3.0,
                    "code_quality": 3.5,
                    "edge_cases": 2.5,
                    "communication": 3.5,
                },
            },
            gaps=[
                Gap(dimension="correctness", mode="coding", current_score=2.0, target_score=3.5, gap_size=1.5),
                Gap(dimension="edge_cases", mode="coding", current_score=2.5, target_score=3.5, gap_size=1.0),
            ],
        )
        generator = PlanGenerator(challenges_dir=Path("mockr/challenges"))
        plan = generator.generate(result)
        assert isinstance(plan, PracticePlan)
        assert plan.target_level == "senior"
        assert len(plan.items) == 2
        assert plan.items[0].gap_size >= plan.items[1].gap_size

    def test_generate_plan_with_role_profile(self) -> None:
        result = AssessmentResult(
            id="a1",
            target_level="senior",
            inferred_level="mid",
            mode_scores={},
            gaps=[
                Gap(dimension="correctness", mode="coding", current_score=2.0, target_score=3.5, gap_size=1.5),
                Gap(dimension="tradeoffs", mode="system-design", current_score=2.5, target_score=3.5, gap_size=1.0),
            ],
        )
        profile = RoleProfile(
            id="rp1",
            role_title="Senior Backend Engineer",
            inferred_level="senior",
            raw_text="...",
            key_skills=[
                Skill(name="system design", category="system-design", dimensions=["tradeoffs"], weight=0.9),
            ],
        )
        generator = PlanGenerator(challenges_dir=Path("mockr/challenges"))
        plan = generator.generate(result, role_profile=profile)
        assert plan.role_profile_id == "rp1"
        tradeoffs_item = next(i for i in plan.items if i.dimension == "tradeoffs")
        correctness_item = next(i for i in plan.items if i.dimension == "correctness")
        assert tradeoffs_item.priority > correctness_item.priority

    def test_generate_plan_matches_challenges(self) -> None:
        result = AssessmentResult(
            id="a1",
            target_level="senior",
            inferred_level="mid",
            mode_scores={},
            gaps=[
                Gap(dimension="correctness", mode="coding", current_score=2.0, target_score=3.5, gap_size=1.5),
            ],
        )
        generator = PlanGenerator(challenges_dir=Path("mockr/challenges"))
        plan = generator.generate(result)
        coding_items = [i for i in plan.items if i.mode == "coding"]
        assert any(i.challenge_id is not None for i in coding_items)

    def test_plan_items_sorted_by_priority(self) -> None:
        result = AssessmentResult(
            id="a1",
            target_level="senior",
            inferred_level="mid",
            mode_scores={},
            gaps=[
                Gap(dimension="correctness", mode="coding", current_score=2.0, target_score=3.5, gap_size=1.5),
                Gap(dimension="structure", mode="system-design", current_score=3.0, target_score=3.5, gap_size=0.5),
                Gap(dimension="action", mode="behavioral", current_score=1.5, target_score=3.5, gap_size=2.0),
            ],
        )
        generator = PlanGenerator(challenges_dir=Path("mockr/challenges"))
        plan = generator.generate(result)
        priorities = [item.priority for item in plan.items]
        assert priorities == sorted(priorities, reverse=True)
