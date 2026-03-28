"""Practice plan generator — turns assessment gaps into actionable plans."""

from __future__ import annotations

import uuid
from pathlib import Path

from mockr.core.assessment.models import AssessmentResult
from mockr.core.challenges.loader import load_challenges_from_dir
from mockr.core.jd.models import RoleProfile
from mockr.core.planning.models import PlanItem, PracticePlan

_FOUNDATIONAL_DIMS = {"correctness", "structure", "situation"}
_FOUNDATIONAL_BOOST = 0.05


class PlanGenerator:
    def __init__(self, challenges_dir: Path) -> None:
        challenges = load_challenges_from_dir(challenges_dir)
        self._challenges_by_mode: dict[str, list] = {}
        for ch in challenges:
            if ch.id.startswith("diagnostic-"):
                continue
            self._challenges_by_mode.setdefault(ch.mode, []).append(ch)

    def generate(
        self,
        assessment: AssessmentResult,
        role_profile: RoleProfile | None = None,
    ) -> PracticePlan:
        jd_weights: dict[tuple[str, str], float] = {}
        if role_profile:
            for skill in role_profile.key_skills:
                for dim in skill.dimensions:
                    key = (skill.category, dim)
                    jd_weights[key] = max(jd_weights.get(key, 0), skill.weight)

        items: list[PlanItem] = []
        for gap in assessment.gaps:
            base_priority = min(gap.gap_size / 4.0, 1.0)
            jd_weight = jd_weights.get((gap.mode, gap.dimension), 0.0)
            jd_boost = jd_weight * 0.3
            foundation_boost = _FOUNDATIONAL_BOOST if gap.dimension in _FOUNDATIONAL_DIMS else 0.0
            priority = min(base_priority + jd_boost + foundation_boost, 1.0)
            mode_challenges = self._challenges_by_mode.get(gap.mode, [])
            challenge_id = mode_challenges[0].id if mode_challenges else None

            items.append(
                PlanItem(
                    dimension=gap.dimension,
                    mode=gap.mode,
                    priority=round(priority, 3),
                    gap_size=gap.gap_size,
                    challenge_id=challenge_id,
                    rationale=f"Your {gap.dimension} score is {gap.current_score}, {assessment.target_level} needs {gap.target_score}",
                )
            )

        items.sort(key=lambda x: x.priority, reverse=True)

        return PracticePlan(
            id=str(uuid.uuid4()),
            assessment_id=assessment.id,
            target_level=assessment.target_level,
            role_profile_id=role_profile.id if role_profile else None,
            items=items,
        )
