from __future__ import annotations

from mockr.core.planning.adapter import PlanAdapter
from mockr.core.planning.models import PlanItem, PracticePlan


class TestPlanAdapter:
    def test_recalculate_marks_validated_when_gap_closed(self) -> None:
        plan = PracticePlan(
            id="p1",
            assessment_id="a1",
            target_level="senior",
            items=[
                PlanItem(dimension="correctness", mode="coding", priority=0.8, gap_size=1.5, rationale="r"),
            ],
        )
        updated_scores = {"coding": {"correctness": 4.0}}
        adapter = PlanAdapter()
        updated_plan = adapter.recalculate(plan, updated_scores, target_level="senior")
        assert updated_plan.items[0].status == "validated"

    def test_recalculate_updates_priority_when_gap_shrinks(self) -> None:
        plan = PracticePlan(
            id="p1",
            assessment_id="a1",
            target_level="senior",
            items=[
                PlanItem(dimension="correctness", mode="coding", priority=0.8, gap_size=1.5, rationale="r"),
            ],
        )
        updated_scores = {"coding": {"correctness": 3.0}}
        adapter = PlanAdapter()
        updated_plan = adapter.recalculate(plan, updated_scores, target_level="senior")
        assert updated_plan.items[0].status == "pending"
        assert updated_plan.items[0].gap_size < 1.5
        assert updated_plan.items[0].priority < 0.8

    def test_reassessment_trigger_after_plateau(self) -> None:
        adapter = PlanAdapter()
        recent_scores = [2.0, 2.1, 2.0, 2.1, 2.05]
        assert adapter.should_reassess(recent_scores, threshold=3.5) is True

    def test_no_reassessment_when_improving(self) -> None:
        adapter = PlanAdapter()
        recent_scores = [2.0, 2.5, 3.0, 3.3, 3.5]
        assert adapter.should_reassess(recent_scores, threshold=3.5) is False

    def test_no_reassessment_with_few_sessions(self) -> None:
        adapter = PlanAdapter()
        recent_scores = [2.0, 2.5]
        assert adapter.should_reassess(recent_scores, threshold=3.5) is False
