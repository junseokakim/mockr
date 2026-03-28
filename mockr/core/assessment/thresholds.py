"""Level thresholds and gap detection for assessments."""

from __future__ import annotations

from mockr.core.assessment.models import Gap
from mockr.core.scoring.scorer import DIMENSIONS_BY_MODE
from mockr.core.types import Level

_IC_LEVELS = [
    (Level.INTERN, 1.5),
    (Level.JUNIOR, 2.0),
    (Level.MID, 2.5),
    (Level.SENIOR, 3.5),
    (Level.STAFF, 4.0),
    (Level.PRINCIPAL, 4.5),
]

LEVEL_THRESHOLDS: dict[str, dict[str, dict[str, float]]] = {
    level.value: {mode: {dim: threshold for dim in dims} for mode, dims in DIMENSIONS_BY_MODE.items()}
    for level, threshold in _IC_LEVELS
}

_LEVEL_ORDER = [level for level, _ in _IC_LEVELS]


def detect_gaps(
    mode_scores: dict[str, dict[str, float]],
    target_level: str,
) -> list[Gap]:
    thresholds = LEVEL_THRESHOLDS.get(target_level, LEVEL_THRESHOLDS[Level.SENIOR.value])
    gaps: list[Gap] = []
    for mode, dim_thresholds in thresholds.items():
        scores = mode_scores.get(mode, {})
        for dim, threshold in dim_thresholds.items():
            current = scores.get(dim, 0.0)
            if current < threshold:
                gaps.append(
                    Gap(
                        dimension=dim,
                        mode=mode,
                        current_score=current,
                        target_score=threshold,
                        gap_size=round(threshold - current, 2),
                    )
                )
    return gaps


def infer_level(mode_scores: dict[str, dict[str, float]]) -> str:
    inferred = Level.INTERN
    for level in _LEVEL_ORDER:
        gaps = detect_gaps(mode_scores, target_level=level.value)
        if not gaps:
            inferred = level
        else:
            break
    return inferred.value
