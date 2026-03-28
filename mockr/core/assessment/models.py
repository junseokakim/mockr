"""Data models for diagnostic assessments."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Gap:
    dimension: str
    mode: str
    current_score: float
    target_score: float
    gap_size: float


@dataclass
class AssessmentResult:
    id: str
    target_level: str
    inferred_level: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    mode_scores: dict[str, dict[str, float]] = field(default_factory=dict)
    gaps: list[Gap] = field(default_factory=list)
