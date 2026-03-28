"""Data models for practice plans."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class PlanItem:
    dimension: str
    mode: str
    priority: float
    gap_size: float
    rationale: str
    challenge_id: str | None = None
    status: str = "pending"  # pending, in_progress, validated


@dataclass
class PracticePlan:
    id: str
    assessment_id: str
    target_level: str
    items: list[PlanItem] = field(default_factory=list)
    role_profile_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
