from __future__ import annotations

from mockr.core.planning.models import PlanItem, PracticePlan


class TestPlanModels:
    def test_plan_item_creation(self) -> None:
        item = PlanItem(
            dimension="correctness",
            mode="coding",
            priority=0.8,
            gap_size=1.5,
            rationale="Your correctness score is 2.0, senior needs 3.5",
        )
        assert item.status == "pending"
        assert item.challenge_id is None

    def test_practice_plan_creation(self) -> None:
        item = PlanItem(
            dimension="tradeoffs",
            mode="system-design",
            priority=0.6,
            gap_size=1.0,
            rationale="Tradeoffs need work",
        )
        plan = PracticePlan(
            id="plan-1",
            assessment_id="assess-1",
            target_level="senior",
            items=[item],
        )
        assert len(plan.items) == 1
        assert plan.role_profile_id is None

    def test_plan_items_sortable_by_priority(self) -> None:
        items = [
            PlanItem(dimension="a", mode="coding", priority=0.3, gap_size=0.5, rationale="low"),
            PlanItem(dimension="b", mode="coding", priority=0.9, gap_size=2.0, rationale="high"),
            PlanItem(dimension="c", mode="coding", priority=0.6, gap_size=1.0, rationale="mid"),
        ]
        sorted_items = sorted(items, key=lambda x: x.priority, reverse=True)
        assert sorted_items[0].dimension == "b"
        assert sorted_items[-1].dimension == "a"
