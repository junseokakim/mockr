"""Adaptive plan updates after each session."""

from __future__ import annotations

from mockr.core.assessment.thresholds import LEVEL_THRESHOLDS
from mockr.core.planning.models import PlanItem, PracticePlan

_MIN_SESSIONS_FOR_REASSESSMENT = 5
_PLATEAU_IMPROVEMENT_THRESHOLD = 0.2


class PlanAdapter:
    def recalculate(
        self,
        plan: PracticePlan,
        updated_scores: dict[str, dict[str, float]],
        target_level: str,
    ) -> PracticePlan:
        thresholds = LEVEL_THRESHOLDS.get(target_level, LEVEL_THRESHOLDS["senior"])
        new_items: list[PlanItem] = []

        for item in plan.items:
            mode_scores = updated_scores.get(item.mode, {})
            current_score = mode_scores.get(item.dimension)

            if current_score is None:
                new_items.append(item)
                continue

            mode_thresholds = thresholds.get(item.mode, {})
            target_score = mode_thresholds.get(item.dimension, 3.5)

            if current_score >= target_score:
                new_items.append(
                    PlanItem(
                        dimension=item.dimension,
                        mode=item.mode,
                        priority=0.0,
                        gap_size=0.0,
                        challenge_id=item.challenge_id,
                        rationale=f"{item.dimension} reached target ({current_score:.1f} >= {target_score})",
                        status="validated",
                    )
                )
            else:
                new_gap = round(target_score - current_score, 2)
                new_priority = round(min(new_gap / 4.0, 1.0), 3)
                new_items.append(
                    PlanItem(
                        dimension=item.dimension,
                        mode=item.mode,
                        priority=new_priority,
                        gap_size=new_gap,
                        challenge_id=item.challenge_id,
                        rationale=f"Your {item.dimension} score is {current_score:.1f}, {target_level} needs {target_score}",
                        status="pending",
                    )
                )

        new_items.sort(key=lambda x: x.priority, reverse=True)
        return PracticePlan(
            id=plan.id,
            assessment_id=plan.assessment_id,
            target_level=plan.target_level,
            role_profile_id=plan.role_profile_id,
            items=new_items,
            created_at=plan.created_at,
        )

    def should_reassess(self, recent_scores: list[float], threshold: float) -> bool:
        if len(recent_scores) < _MIN_SESSIONS_FOR_REASSESSMENT:
            return False
        last_n = recent_scores[-_MIN_SESSIONS_FOR_REASSESSMENT:]
        if any(s >= threshold for s in last_n):
            return False
        improvement = last_n[-1] - last_n[0]
        return abs(improvement) < _PLATEAU_IMPROVEMENT_THRESHOLD
